"""Órdenes de aprendizaje en lenguaje natural (D-030)."""

import re
from enum import Enum

_END = r"\s*[?.!]*\s*$"
_F = re.IGNORECASE


class LearningAction(str, Enum):
    LIST = "list"
    ENABLE = "enable"
    DISABLE = "disable"
    ACCEPT_ALL = "accept_all"
    REJECT_ALL = "reject_all"


_PATTERNS = (
    (LearningAction.LIST, re.compile(
        r"^\s*¿?\s*qu[eé]\s+(?:has\s+aprendido|aprendiste)"
        r"(?:\s+de\s+m[ií])?" + _END, _F)),
    (LearningAction.DISABLE, re.compile(
        r"^\s*(?:deja\s+de\s+aprender|no\s+aprendas(?:\s+m[aá]s)?"
        r"|desactiva\s+el\s+aprendizaje)" + _END, _F)),
    (LearningAction.ENABLE, re.compile(
        r"^\s*(?:vuelve\s+a\s+aprender|activa\s+el\s+aprendizaje)"
        + _END, _F)),
    (LearningAction.ACCEPT_ALL, re.compile(
        r"^\s*(?:confirma|acepta)\s+lo\s+(?:aprendido|que\s+aprendiste)"
        + _END, _F)),
    (LearningAction.REJECT_ALL, re.compile(
        r"^\s*(?:descarta|rechaza)\s+lo\s+(?:aprendido|que\s+aprendiste)"
        + _END, _F)),
)


def parse_learning_command(text: str) -> LearningAction | None:
    for action, pattern in _PATTERNS:
        if pattern.match(text):
            return action

    return None