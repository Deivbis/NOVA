"""Gestor de plugins: descubrir → validar → permisos → iniciar → detener."""

from dataclasses import dataclass
from pathlib import Path

from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.memory.text import normalize
from nova.plugins.manifest import PluginManifest, load_manifest
from nova.plugins.process import PluginProcess
from nova.storage.repositories.permission_repository import (
    PermissionRepository,
)
from nova.storage.repositories.plugin_repository import PluginRepository

logger = get_logger(__name__)

COMMAND_TIMEOUT_S = 10.0
MAX_FAILURES = 3


@dataclass(frozen=True)
class PluginEntry:
    plugin_id: str
    manifest: PluginManifest | None
    error: str | None


@dataclass(frozen=True)
class CommandJob:
    plugin_id: str
    command: str
    text: str
    groups: dict


class PluginManager:
    def __init__(
        self,
        directory: Path,
        repository: PluginRepository,
        permissions: PermissionRepository,
        api_factory,
        nova_version: str,
        command_timeout: float = COMMAND_TIMEOUT_S,
    ) -> None:
        self._directory = directory
        self._repository = repository
        self._permissions = permissions
        self._api_factory = api_factory
        self._nova_version = nova_version
        self._timeout = command_timeout
        self._entries: dict[str, PluginEntry] = {}
        self._processes: dict[str, PluginProcess] = {}
        self._failures: dict[str, int] = {}

    # --- ciclo de vida -------------------------------------------------
    def reload(self) -> None:
        self.shutdown()
        self._entries = {}

        if self._directory.is_dir():
            for folder in sorted(self._directory.iterdir()):
                if not folder.is_dir() or folder.name.startswith((".", "_")):
                    continue

                loaded = load_manifest(folder, self._nova_version)
                self._entries[folder.name] = PluginEntry(
                    folder.name,
                    loaded.value if loaded.success else None,
                    None if loaded.success else loaded.error.message,
                )

        for plugin_id in self._repository.enabled_ids():
            self._start(plugin_id)

    def shutdown(self) -> None:
        for process in self._processes.values():
            process.stop()

        self._processes = {}

    def _start(self, plugin_id: str) -> bool:
        entry = self._entries.get(plugin_id)

        if (
            entry is None
            or entry.manifest is None
            or plugin_id in self._processes
            or self.missing_permissions(plugin_id)
        ):
            return False

        process = PluginProcess(entry.manifest, self._api_factory(entry.manifest))

        try:
            process.start()
        except OSError:
            logger.warning("No se pudo iniciar un plugin.")
            return False

        self._processes[plugin_id] = process

        return True

    # --- consulta ------------------------------------------------------
    def entries(self) -> list[tuple[PluginEntry, bool]]:
        return [
            (entry, self._repository.is_enabled(entry.plugin_id))
            for entry in self._entries.values()
        ]

    def manifest(self, plugin_id: str) -> PluginManifest | None:
        entry = self._entries.get(plugin_id)

        return entry.manifest if entry else None

    def is_enabled(self, plugin_id: str) -> bool:
        return self._repository.is_enabled(plugin_id)

    def find(self, text: str) -> Result[str]:
        needle = normalize(text).strip()

        def names(entry: PluginEntry) -> tuple[str, str]:
            name = normalize(entry.manifest.name) if entry.manifest else ""

            return entry.plugin_id, name

        exact = [e.plugin_id for e in self._entries.values() if needle in names(e)]

        if len(exact) == 1:
            return Result.ok(exact[0])

        partial = [
            e.plugin_id
            for e in self._entries.values()
            if needle and any(needle in n for n in names(e) if n)
        ]

        if len(partial) == 1:
            return Result.ok(partial[0])

        if not partial:
            return Result.fail(
                "PLUGIN_NOT_FOUND", f"No encontré el plugin «{text}»."
            )

        return Result.fail("PLUGIN_AMBIGUOUS", "Hay varios con ese nombre.")

    def check(self, plugin_id: str) -> Result[PluginManifest]:
        entry = self._entries.get(plugin_id)

        if entry is None:
            return Result.fail("PLUGIN_NOT_FOUND", "No existe ese plugin.")

        if entry.manifest is None:
            return Result.fail("PLUGIN_INVALID", entry.error or "Plugin no válido.")

        for dependency in entry.manifest.dependencies:
            if dependency not in self._entries or not self._repository.is_enabled(
                dependency
            ):
                return Result.fail(
                    "PLUGIN_DEPENDENCY",
                    f"Requiere activar primero el plugin «{dependency}».",
                )

        return Result.ok(entry.manifest)

    # --- permisos ------------------------------------------------------
    def missing_permissions(self, plugin_id: str) -> list[str]:
        manifest = self.manifest(plugin_id)

        if manifest is None:
            return []

        return [
            p for p in manifest.permissions
            if not self._permissions.has("plugin", f"{plugin_id}:{p}")
        ]

    def grant_all(self, plugin_id: str) -> None:
        manifest = self.manifest(plugin_id)

        for permission in manifest.permissions if manifest else ():
            self._permissions.add("plugin", f"{plugin_id}:{permission}")

    def revoke_all(self, plugin_id: str) -> int:
        removed = 0

        for kind, key in self._permissions.list_permissions():
            if kind == "plugin" and key.startswith(f"{plugin_id}:"):
                removed += self._permissions.remove(kind, key)

        self._force_disable(plugin_id)

        return removed

    # --- activación ----------------------------------------------------
    def enable(self, plugin_id: str) -> Result[PluginManifest]:
        checked = self.check(plugin_id)

        if not checked.success:
            return checked

        if self.missing_permissions(plugin_id):
            return Result.fail("PLUGIN_PERMISSIONS_MISSING", "Faltan permisos.")

        if plugin_id not in self._processes and not self._start(plugin_id):
            return Result.fail("PLUGIN_START", "No pude iniciar el plugin.")

        self._failures[plugin_id] = 0
        self._repository.set_enabled(plugin_id, checked.value.version, True)

        return checked

    def disable(self, plugin_id: str) -> Result[PluginManifest]:
        checked = self.check(plugin_id)

        if not checked.success:
            return checked

        for other, entry in self._entries.items():
            if (
                other != plugin_id
                and entry.manifest
                and plugin_id in entry.manifest.dependencies
                and self._repository.is_enabled(other)
            ):
                return Result.fail(
                    "PLUGIN_DEPENDENT",
                    f"«{other}» depende de este plugin; desactívalo primero.",
                )

        self._force_disable(plugin_id)

        return checked

    def _force_disable(self, plugin_id: str) -> None:
        process = self._processes.pop(plugin_id, None)

        if process is not None:
            process.stop()

        manifest = self.manifest(plugin_id)
        self._repository.set_enabled(
            plugin_id, manifest.version if manifest else "0.0.0", False
        )

    # --- comandos ------------------------------------------------------
    def plan_command(self, text: str) -> CommandJob | None:
        """Hilo de la UI: busca qué plugin responde a la frase."""
        stripped = text.strip()

        for plugin_id in sorted(self._processes):
            manifest = self.manifest(plugin_id)

            if manifest is None or not self._permissions.has(
                "plugin", f"{plugin_id}:commands"
            ):
                continue

            for spec in manifest.commands:
                for pattern in spec.patterns:
                    match = pattern.match(stripped)

                    if match is None:
                        continue

                    process = self._processes[plugin_id]

                    if not process.alive:
                        try:
                            process.start()
                        except OSError:
                            continue

                    groups = {k: v or "" for k, v in match.groupdict().items()}

                    return CommandJob(plugin_id, spec.name, stripped, groups)

        return None

    def run_job(self, job: CommandJob) -> Result[str]:
        """Hilo de trabajo: solo habla con el subproceso (sin BD)."""
        process = self._processes.get(job.plugin_id)

        if process is None:
            return Result.fail("PLUGIN_NOT_RUNNING", "El plugin no está activo.")

        return process.call(
            {
                "type": "command",
                "command": job.command,
                "text": job.text,
                "groups": job.groups,
            },
            self._timeout,
        )

    def finish_job(self, job: CommandJob, result: Result[str]) -> str:
        """Hilo de la UI: contabiliza fallos y devuelve el texto final."""
        if result.success:
            self._failures[job.plugin_id] = 0

            return result.value or "Hecho, Jefe."

        manifest = self.manifest(job.plugin_id)
        name = manifest.name if manifest else job.plugin_id
        count = self._failures.get(job.plugin_id, 0) + 1
        self._failures[job.plugin_id] = count
        self._repository.audit("plugin.failed")
        message = f"El plugin {name} falló: {result.error.message}."

        if count >= MAX_FAILURES:
            self._force_disable(job.plugin_id)
            message += f" Lo desactivé tras {MAX_FAILURES} fallos seguidos."

        return f"{message} Lo siento, Jefe."