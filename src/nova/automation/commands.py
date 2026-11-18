"""Órdenes de automatización en lenguaje natural (D-031)."""

import re
from dataclasses import dataclass
from enum import Enum
from nova.memory.text import normalize


_F = re.IGNORECASE
_END = r"\s*[?.!]*\s*$"


class AutomationAction(str, Enum):
    OPEN = "open"
    MEDIA = "media"
    PERMISSIONS = "permissions"
    REVOKE = "revoke"
    AUTHORIZE = "authorize"
    SEARCH = "search"
    LIST = "list"
    CREATE_DIR = "create_dir"
    COPY = "copy"
    MOVE = "move"
    RENAME = "rename"
    DELETE = "delete"
    ORGANIZE = "organize"
    OPEN_RESULT = "open_result"

@dataclass(frozen=True)
class AutomationCommand:
    action: AutomationAction
    text: str = ""
    hint: str | None = None  # "folder" | "web" | None
    media: str | None = None
    name: str = ""
    source: str = ""
    dest: str = ""


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

FOLDER_ALIASES = {
    "descargas": "Downloads", "descarga": "Downloads",
    "documentos": "Documents", "escritorio": "Desktop",
    "musica": "Music", "imagenes": "Pictures", "fotos": "Pictures",
    "videos": "Videos",
}
_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")
_PRE = r"(?:el\s+archivo\s+|la\s+carpeta\s+|el\s+|la\s+)?"

_AUTHORIZE = re.compile(
    r"^\s*autoriza\s+(?:la\s+)?carpeta\s+(?P<loc>.+?)" + _END, _F)
_SEARCH = re.compile(
    r"^\s*(?:busca|buscar|encuentra|localiza)\s+(?:(?:el|los|un|mi|mis)\s+)?"
    r"(?:archivos?|ficheros?|documentos?)\s+(?:llamados?\s+|de\s+nombre\s+)?"
    r"(?P<name>.+?)(?:\s+en\s+(?P<loc>.+?))?" + _END, _F)
_LIST = re.compile(
    r"^\s*¿?\s*(?:qu[eé]\s+hay\s+en|lista(?:\s+(?:los\s+archivos\s+de"
    r"|la\s+carpeta))?|mu[eé]strame\s+(?:los\s+archivos\s+de|la\s+carpeta)"
    r"|ens[eé][nñ]ame\s+(?:los\s+archivos\s+de|la\s+carpeta))\s+"
    r"(?P<loc>.+?)" + _END, _F)
_CREATE = re.compile(
    r"^\s*(?:crea|crear|haz)\s+(?:una\s+)?carpeta\s+"
    r"(?:llamada\s+|de\s+nombre\s+)?(?P<name>.+?)\s+"
    r"(?:en|dentro\s+de)\s+(?P<loc>.+?)" + _END, _F)
_COPY_MOVE = re.compile(
    r"^\s*(?P<verb>copia|copiar|mueve|mover)\s+" + _PRE +
    r"(?P<name>.+)\s+de\s+(?P<src>\S+)\s+a\s+(?P<dst>.+?)" + _END, _F)
_RENAME = re.compile(
    r"^\s*(?:renombra|renombrar|cambia\s+el\s+nombre\s+de)\s+" + _PRE +
    r"(?P<name>.+?)\s+(?:a|como|por)\s+(?P<new>.+?)\s+en\s+(?P<loc>.+?)"
    + _END, _F)
_DELETE = re.compile(
    r"^\s*(?:borra|borrar|elimina|eliminar|manda\s+a\s+la\s+papelera)\s+"
    + _PRE + r"(?P<name>.+)\s+(?:de|en)\s+(?P<loc>.+?)" + _END, _F)
_ORGANIZE = re.compile(
    r"^\s*(?:organiza|ordena)\s+(?P<c>la\s+carpeta\s+)?(?P<loc>.+?)" + _END,
    _F)
_RESULT = re.compile(
    r"^\s*abre\s+(?:el\s+)?(?:resultado\s+)?"
    r"(?P<n>\d+|primero|segundo|tercero|cuarto|quinto)" + _END, _F)
_ORDINALS = {"primero": 1, "segundo": 2, "tercero": 3, "cuarto": 4, "quinto": 5}


def _loc_like(text: str) -> bool:
    return normalize(text.strip()) in FOLDER_ALIASES or bool(
        _DRIVE.match(text.strip())
    )


def _parse_files(text: str) -> AutomationCommand | None:
    A = AutomationAction

    if m := _AUTHORIZE.match(text):
        return AutomationCommand(A.AUTHORIZE, m["loc"].strip())

    if m := _SEARCH.match(text):
        return AutomationCommand(
            A.SEARCH, name=m["name"].strip(), source=(m["loc"] or "").strip()
        )

    if (m := _LIST.match(text)) and _loc_like(m["loc"]):
        return AutomationCommand(A.LIST, source=m["loc"].strip())

    if m := _CREATE.match(text):
        return AutomationCommand(
            A.CREATE_DIR, name=m["name"].strip(), source=m["loc"].strip()
        )

    if m := _COPY_MOVE.match(text):
        action = A.COPY if m["verb"].lower().startswith("c") else A.MOVE
        return AutomationCommand(
            action, name=m["name"].strip(),
            source=m["src"].strip(), dest=m["dst"].strip(),
        )

    if m := _RENAME.match(text):
        return AutomationCommand(
            A.RENAME, name=m["name"].strip(),
            source=m["loc"].strip(), dest=m["new"].strip(),
        )

    if m := _DELETE.match(text):
        return AutomationCommand(
            A.DELETE, name=m["name"].strip(), source=m["loc"].strip()
        )

    if (m := _ORGANIZE.match(text)) and (m["c"] or _loc_like(m["loc"])):
        return AutomationCommand(A.ORGANIZE, source=m["loc"].strip())

    if m := _RESULT.match(text):
        n = m["n"].lower()
        return AutomationCommand(
            A.OPEN_RESULT, text=str(_ORDINALS.get(n, n))
        )

    return None

def parse_automation_command(text: str) -> AutomationCommand | None:
    if _PERMISSIONS.match(text):
        return AutomationCommand(AutomationAction.PERMISSIONS)

    match = _REVOKE.match(text)

    if match:
        return AutomationCommand(AutomationAction.REVOKE, match.group("t"))
    
    files = _parse_files(text)
    if files is not None:
        return files

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