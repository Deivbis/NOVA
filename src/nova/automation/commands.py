"""Órdenes de automatización en lenguaje natural (D-031)."""

import re
from dataclasses import dataclass
from enum import Enum

_F = re.IGNORECASE
_END = r"\s*[?.!]*\s*$"


class AutomationAction(str, Enum):
    OPEN = "open"
    MEDIA = "media"
    PERMISSIONS = "permissions"
    REVOKE = "revoke"


@dataclass(frozen=True)
class AutomationCommand:
    action: AutomationAction
    text: str = ""
    hint: str | None = None  # "folder" | "web" | None
    media: str | None = None


_OPEN = re.compile(
    r"^\s*(?:por favor[ ,]*)?(?:abre|abrir|[aá]breme|ejecuta|inicia|lanza)"
    r"\s+(?P<what>.+?)" + _END, _F,
)
_FOLDER = re.compile(
    r"^(?:la\s+|mi\s+)?carpeta(?:\s+de)?\s+(?P<t>.+)$", _F)
_WEB = re.compile(
    r"^(?:la\s+)?(?:web|p[aá]gina|sitio)(?:\s+web)?(?:\s+de)?\s+(?P<t>.+)$",
    _F)
_PROGRAM = re.compile(
    r"^(?:el\s+programa|la\s+aplicaci[oó]n|la\s+app|el|la)\s+(?P<t>.+)$", _F)

_MUSIC = r"(?:\s+(?:la\s+)?(?:m[uú]sica|canci[oó]n|pista|tema|reproducci[oó]n))?"
_MEDIA = (
    ("play_pause", re.compile(
        r"^\s*(?:por favor[ ,]*)?(?:pausa|pausar|reanuda|reanudar"
        r"|contin[uú]a|reproduce|play|pon)" + _MUSIC + _END, _F)),
    ("next", re.compile(
        r"^\s*(?:siguiente|pasa|salta|next)" + _MUSIC
        + r"|^\s*(?:canci[oó]n|pista|tema)\s+siguiente" + _END, _F)),
    ("previous", re.compile(
        r"^\s*(?:(?:canci[oó]n|pista|tema)\s+)?anterior" + _END
        + r"|^\s*(?:vuelve|regresa)\s+(?:a\s+la\s+)?"
        r"(?:canci[oó]n\s+)?anterior" + _END, _F)),
    ("volume_up", re.compile(r"^\s*sube\s+(?:el\s+)?volumen" + _END, _F)),
    ("volume_down", re.compile(r"^\s*baja\s+(?:el\s+)?volumen" + _END, _F)),
    ("mute", re.compile(
        r"^\s*(?:silencia(?:r)?(?:\s+(?:el\s+)?(?:volumen|sonido))?"
        r"|mutea|quita\s+el\s+sonido)" + _END, _F)),
)

_PERMISSIONS = re.compile(
    r"^\s*¿?\s*qu[eé]\s+(?:permisos\s+tienes|puedes\s+abrir"
    r"(?:\s+sin\s+preguntar)?)" + _END, _F)
_REVOKE = re.compile(
    r"^\s*(?:revoca|quita|elimina|borra)\s+(?:el\s+)?permiso\s+"
    r"(?:de|para)\s+(?P<t>.+?)\s*[.!]*\s*$", _F)


def parse_automation_command(text: str) -> AutomationCommand | None:
    if _PERMISSIONS.match(text):
        return AutomationCommand(AutomationAction.PERMISSIONS)

    match = _REVOKE.match(text)

    if match:
        return AutomationCommand(AutomationAction.REVOKE, match.group("t"))

    for command, pattern in _MEDIA:
        if pattern.match(text):
            return AutomationCommand(AutomationAction.MEDIA, media=command)

    match = _OPEN.match(text)

    if match is None:
        return None

    what = match.group("what").strip()

    for hint, pattern in (("folder", _FOLDER), ("web", _WEB)):
        found = pattern.match(what)

        if found:
            return AutomationCommand(
                AutomationAction.OPEN, found.group("t").strip(), hint
            )

    found = _PROGRAM.match(what)

    return AutomationCommand(
        AutomationAction.OPEN, (found.group("t") if found else what).strip()
    )