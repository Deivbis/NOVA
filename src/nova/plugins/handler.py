"""Órdenes de plugins por voz/chat y despacho de comandos de plugin."""

import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from nova.core.confirmation import parse_yes_no
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.plugins.gateway import MainThread
from nova.plugins.manager import CommandJob, PluginManager
from nova.plugins.manifest import PluginManifest
from nova.storage.exceptions import RepositoryError

logger = get_logger(__name__)
_F = re.IGNORECASE
_END = r"[.!]*\s*$"

_LIST = re.compile(
    r"^\s*¿?\s*(?:qu[eé]\s+plugins\s+tengo|mis\s+plugins"
    r"|lista\s+(?:los\s+|mis\s+)?plugins)\s*[?.!]*\s*$", _F)
_ENABLE = re.compile(
    r"^\s*(?:activa|habilita|enciende)\s+el\s+plugin\s+(?P<n>.+?)" + _END, _F)
_DISABLE = re.compile(
    r"^\s*(?:desactiva|deshabilita|apaga)\s+el\s+plugin\s+(?P<n>.+?)" + _END, _F)
_PERMS = re.compile(
    r"^\s*¿?\s*qu[eé]\s+permisos\s+tiene\s+(?:el\s+plugin\s+)?(?P<n>.+?)"
    r"\s*[?.!]*\s*$", _F)
_REVOKE = re.compile(
    r"^\s*revoca\s+los\s+permisos\s+de(?:l)?\s+(?:plugin\s+)?(?P<n>.+?)" + _END,
    _F)
_RELOAD = re.compile(
    r"^\s*(?:recarga|actualiza)\s+(?:los\s+)?plugins\s*[.!]*\s*$", _F)

_PERM_TEXT = {
    "commands": "responder a sus frases",
    "speak": "hablarte y escribir en el chat",
    "memory.read": "leer tus recuerdos",
    "automation.open": "abrir webs, carpetas y programas que ya permitiste",
    "automation.media": "controlar la música",
}


def _perm_text(manifest: PluginManifest, permission: str) -> str:
    if permission == "network":
        return f"conectarse a internet ({', '.join(manifest.network_domains)})"

    return _PERM_TEXT[permission]


class PluginCommandHandler:
    def __init__(self, manager: PluginManager, gateway: MainThread) -> None:
        self._manager = manager
        self._gateway = gateway
        self._pending: str | None = None
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="nova-plugin"
        )

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._manager.shutdown()

    # --- órdenes de gestión (síncronas, hilo de la UI) ------------------
    def reply_to(self, text: str) -> str | None:
        try:
            return self._reply(text)
        except RepositoryError:
            logger.exception("Fallo de plugins.")
            return "No pude acceder a los plugins, Jefe."

    def _reply(self, text: str) -> str | None:
        if self._pending is not None:
            plugin_id, self._pending = self._pending, None
            decision = parse_yes_no(text)

            if decision is True:
                self._manager.grant_all(plugin_id)
                return self._enable_now(plugin_id)

            if decision is False:
                return "Entendido, Jefe. No activé el plugin."

        if _LIST.match(text):
            return self._list()

        if _RELOAD.match(text):
            self._manager.reload()

            return f"Plugins recargados, Jefe: {len(self._manager.entries())} encontrados."

        for pattern, action in (
            (_ENABLE, self._enable),
            (_DISABLE, self._disable),
            (_REVOKE, self._revoke),
            (_PERMS, self._permissions),
        ):
            match = pattern.match(text)

            if match:
                found = self._manager.find(match["n"])

                if not found.success:
                    return f"{found.error.message} Lo siento, Jefe."

                return action(found.value)

        return None

    def _list(self) -> str:
        entries = self._manager.entries()

        if not entries:
            return "No hay plugins en la carpeta plugins, Jefe."

        lines = ["Tus plugins:"]

        for entry, enabled in entries:
            if entry.manifest is None:
                lines.append(f"- {entry.plugin_id}: no válido ({entry.error})")
            else:
                state = "activado" if enabled else "desactivado"
                lines.append(
                    f"- {entry.manifest.name} v{entry.manifest.version}: {state}"
                )

        return "\n".join(lines)

    def _enable(self, plugin_id: str) -> str:
        checked = self._manager.check(plugin_id)

        if not checked.success:
            return f"{checked.error.message} Lo siento, Jefe."

        manifest = checked.value
        missing = self._manager.missing_permissions(plugin_id)

        if not missing:
            return self._enable_now(plugin_id)

        self._pending = plugin_id
        wants = "; ".join(_perm_text(manifest, p) for p in missing)

        return (
            f"Jefe, el plugin {manifest.name} v{manifest.version} "
            f"de {manifest.author} pide permiso para: {wants}. "
            "¿Los concedo y lo activo? Responde «sí» o «no»."
        )

    def _enable_now(self, plugin_id: str) -> str:
        result = self._manager.enable(plugin_id)

        if not result.success:
            return f"{result.error.message} Lo siento, Jefe."

        manifest = result.value
        tail = f" Prueba: «{manifest.examples[0]}»." if manifest.examples else ""

        return f"Plugin {manifest.name} activado, Jefe.{tail}"

    def _disable(self, plugin_id: str) -> str:
        result = self._manager.disable(plugin_id)

        if not result.success:
            return f"{result.error.message} Lo siento, Jefe."

        return f"Plugin {result.value.name} desactivado, Jefe."

    def _permissions(self, plugin_id: str) -> str:
        manifest = self._manager.manifest(plugin_id)

        if manifest is None:
            return "Ese plugin no es válido, Jefe."

        missing = set(self._manager.missing_permissions(plugin_id))

        if not manifest.permissions:
            return f"{manifest.name} no pide ningún permiso, Jefe."

        lines = [
            f"- {_perm_text(manifest, p)}: "
            + ("pendiente" if p in missing else "concedido")
            for p in manifest.permissions
        ]

        return "\n".join([f"Permisos de {manifest.name}:", *lines])

    def _revoke(self, plugin_id: str) -> str:
        removed = self._manager.revoke_all(plugin_id)

        return f"Permisos revocados y plugin desactivado, Jefe ({removed})."

    # --- comandos de plugin (asíncronos) --------------------------------
    def dispatch(self, text: str, reply: Callable[[str], None]) -> bool:
        """True si un plugin responde a la frase. `reply` corre en la UI."""
        try:
            job = self._manager.plan_command(text)
        except RepositoryError:
            logger.exception("Fallo de plugins.")
            return False

        if job is None:
            return False

        self._executor.submit(self._work, job, reply)

        return True

    def _work(self, job: CommandJob, reply: Callable[[str], None]) -> None:
        try:
            result = self._manager.run_job(job)
        except Exception as exc:
            logger.warning("Fallo de plugin: %s", type(exc).__name__)
            result = Result.fail("PLUGIN_ERROR", "falló de forma inesperada")

        self._gateway.post(
            lambda: reply(self._manager.finish_job(job, result))
        )