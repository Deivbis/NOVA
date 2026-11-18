import re
from dataclasses import dataclass
from enum import Enum

_F = re.IGNORECASE
_END = r"[.!]*\s*$"


class TaskAction(str, Enum):
    REMIND = "remind"
    ADD = "add"
    LIST = "list"
    COMPLETE = "complete"
    CANCEL = "cancel"


@dataclass(frozen=True)
class TaskCommand:
    action: TaskAction
    text: str = ""
    index: int | None = None


_REMIND = re.compile(
    r"^\s*(?:recu[eé]rdame|recordarme|av[ií]same"
    r"|ponme\s+un\s+recordatorio(?:\s+para)?"
    r"|crea\s+un\s+recordatorio(?:\s+para)?)\s+(?P<t>.+?)" + _END, _F)
_ADD = (
    re.compile(
        r"^\s*(?:anota|apunta)\s+(?:que\s+)?(?:tengo\s+que\s+|debo\s+)?"
        r"(?P<t>.+?)" + _END, _F),
    re.compile(
        r"^\s*(?:agrega|a[ñn]ade)\s+(?P<t>.+?)\s+a\s+(?:mi\s+)?"
        r"(?:lista|pendientes|tareas)" + _END, _F),
)
_LIST = re.compile(
    r"^\s*¿?\s*(?:qu[eé]\s+(?:tengo\s+pendiente|pendientes\s+tengo"
    r"|recordatorios\s+tengo|tareas\s+tengo)"
    r"|(?:mis|mi)\s+(?:pendientes|tareas|recordatorios|lista\s+de\s+pendientes)"
    r"|mu[eé]strame\s+(?:mis\s+)?(?:pendientes|tareas|recordatorios))"
    r"\s*[?.!]*\s*$", _F)
_DONE = re.compile(
    r"^\s*(?:completa|completar|termina|marca\s+como\s+(?:hecho|hecha"
    r"|completad[oa]|terminad[oa])|ya\s+(?:hice|termin[eé]|complet[eé]))\s+"
    r"(?:el\s+|la\s+|lo\s+)?(?:(?:pendiente|tarea|n[uú]mero)\s+)?"
    r"(?P<t>.+?)" + _END, _F)
_CANCEL = re.compile(
    r"^\s*(?:cancela|borra|elimina|quita)\s+(?:el\s+|la\s+)?"
    r"(?:recordatorio|pendiente|tarea)\s+(?P<t>.+?)" + _END, _F)


def _target(action: TaskAction, text: str) -> TaskCommand:
    text = text.strip()

    if text.isdigit():
        return TaskCommand(action, index=int(text))

    return TaskCommand(action, text=text)


def parse_task_command(text: str) -> TaskCommand | None:
    if match := _LIST.match(text):
        return TaskCommand(TaskAction.LIST)

    if match := _REMIND.match(text):
        return TaskCommand(TaskAction.REMIND, match["t"])

    if match := _CANCEL.match(text):
        return _target(TaskAction.CANCEL, match["t"])

    if match := _DONE.match(text):
        return _target(TaskAction.COMPLETE, match["t"])

    for pattern in _ADD:
        if match := pattern.match(text):
            return TaskCommand(TaskAction.ADD, match["t"])

    return None