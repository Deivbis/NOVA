"""Manifest de plugin (DOC-017 PluginManifest, DOC-021)."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from nova.core.result import Result

PERMISSIONS = frozenset({
    "commands", "speak", "network", "memory.read",
    "automation.open", "automation.media",
})
MAX_MANIFEST_BYTES = 64 * 1024
_ID = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_DOMAIN = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,}$")
_TEXT_FIELDS = (
    ("name", 60), ("version", 20), ("author", 60),
    ("description", 300), ("nova_min_version", 20),
)
_PROBES = ("", "hola", "qué tal", "cuéntame un chiste", "abre youtube")


@dataclass(frozen=True)
class CommandSpec:
    name: str
    patterns: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    description: str
    nova_min_version: str
    dependencies: tuple[str, ...]
    permissions: tuple[str, ...]
    network_domains: tuple[str, ...]
    commands: tuple[CommandSpec, ...]
    events: tuple[str, ...]  # reservado (DOC-017); aún sin uso
    examples: tuple[str, ...]
    path: Path


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def _invalid(message: str) -> Result:
    return Result.fail("PLUGIN_INVALID_MANIFEST", message)


def _str_list(data: dict, key: str, limit: int, maxlen: int):
    value = data.get(key, [])

    if not isinstance(value, list) or len(value) > limit:
        return None

    if not all(isinstance(v, str) and 0 < len(v) <= maxlen for v in value):
        return None

    return tuple(value)


def _commands(raw) -> tuple[CommandSpec, ...] | None:
    if not isinstance(raw, list) or len(raw) > 10:
        return None

    specs, names = [], set()

    for item in raw:
        if not isinstance(item, dict):
            return None

        name, patterns = item.get("name"), item.get("patterns")

        if (
            not isinstance(name, str)
            or not 0 < len(name) <= 32
            or name in names
            or not isinstance(patterns, list)
            or not 1 <= len(patterns) <= 5
        ):
            return None

        compiled = []

        for pattern in patterns:
            if not isinstance(pattern, str) or not 0 < len(pattern) <= 200:
                return None

            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error:
                return None

            if any(regex.match(probe) for probe in _PROBES):
                return None  # patrón demasiado amplio

            compiled.append(regex)

        names.add(name)
        specs.append(CommandSpec(name, tuple(compiled)))

    return tuple(specs)


def load_manifest(folder: Path, nova_version: str) -> Result[PluginManifest]:
    file = folder / "manifest.json"

    try:
        if not file.is_file() or file.stat().st_size > MAX_MANIFEST_BYTES:
            return _invalid("Falta manifest.json o es demasiado grande.")

        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _invalid("manifest.json no es JSON válido.")

    if not isinstance(data, dict):
        return _invalid("manifest.json debe ser un objeto.")

    plugin_id = data.get("id")

    if (
        not isinstance(plugin_id, str)
        or not _ID.match(plugin_id)
        or plugin_id != folder.name
    ):
        return _invalid("El id debe ser válido y coincidir con la carpeta.")

    fields: dict[str, str] = {}

    for key, limit in _TEXT_FIELDS:
        value = data.get(key)

        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            return _invalid(f"Campo «{key}» inválido.")

        fields[key] = value.strip()

    if not (
        _VERSION.match(fields["version"])
        and _VERSION.match(fields["nova_min_version"])
    ):
        return _invalid("Las versiones deben tener formato x.y.z.")

    dependencies = _str_list(data, "dependencies", 10, 32)
    permissions = _str_list(data, "permissions", 10, 32)
    domains = _str_list(data, "network_domains", 10, 100)
    events = _str_list(data, "events", 20, 60)
    examples = _str_list(data, "examples", 5, 100)

    if any(v is None for v in (dependencies, permissions, domains, events, examples)):
        return _invalid("Alguna lista del manifest es inválida.")

    permissions = tuple(dict.fromkeys(permissions))
    unknown = [p for p in permissions if p not in PERMISSIONS]

    if unknown:
        return _invalid(f"Permisos desconocidos: {', '.join(unknown)}.")

    if plugin_id in dependencies or any(not _ID.match(d) for d in dependencies):
        return _invalid("Dependencias inválidas.")

    if any(not _DOMAIN.match(d) for d in domains):
        return _invalid("Dominios inválidos.")

    if ("network" in permissions) != bool(domains):
        return _invalid("«network» y network_domains se declaran juntos.")

    commands = _commands(data.get("commands", []))

    if commands is None:
        return _invalid("Comandos inválidos o demasiado amplios.")

    if commands and "commands" not in permissions:
        return _invalid("Declarar comandos requiere el permiso «commands».")

    if not (folder / "plugin.py").is_file():
        return _invalid("Falta plugin.py.")

    if parse_version(nova_version) < parse_version(fields["nova_min_version"]):
        return Result.fail(
            "PLUGIN_INCOMPATIBLE",
            f"Requiere NOVA {fields['nova_min_version']} o superior.",
        )

    return Result.ok(PluginManifest(
        id=plugin_id,
        name=fields["name"],
        version=fields["version"],
        author=fields["author"],
        description=fields["description"],
        nova_min_version=fields["nova_min_version"],
        dependencies=dependencies,
        permissions=permissions,
        network_domains=domains,
        commands=commands,
        events=events,
        examples=examples,
        path=folder,
    ))