"""Órdenes de memoria en lenguaje natural (SPEC-005, D-029).

Solo se reconocen frases que empiezan con el verbo ("recuerda que...",
"olvida ...", "qué recuerdas"), para no confundirlas con una conversación
normal. Una pregunta como "¿recuerdas que...?" no es una orden.
"""

import re
from dataclasses import dataclass
from enum import Enum

from nova.memory.classifier import normalize_category


class MemoryAction(str, Enum):
    REMEMBER = "remember"
    FORGET = "forget"
    LIST = "list"


@dataclass(frozen=True)
class MemoryCommand:
    action: MemoryAction
    text: str = ""
    category: str | None = None


_PLEASE = r"^\s*(?:por favor[ ,]*)?"
_CAT = r"[a-záéíóúñ]+"

_REMEMBER_IN = re.compile(
    _PLEASE
    + r"(?:recuerda|rec[uú]erdame|anota|apunta|guarda|memoriza)"
    + rf"\s+en\s+(?P<cat>{_CAT})\s+que\s+(?P<text>.+?)\s*$",
    re.IGNORECASE | re.DOTALL,
)
_REMEMBER = re.compile(
    _PLEASE
    + r"(?:(?:recuerda|rec[uú]erdame|anota|apunta|guarda|memoriza)"
    + r"(?:\s+esto)?\s*(?::|\s+que)|no\s+olvides\s+que)"
    + r"\s*(?P<text>.+?)\s*$",
    re.IGNORECASE | re.DOTALL,
)

_FORGET = re.compile(
    _PLEASE
    + r"(?:olvida|olv[ií]date\s+de)\s+"
    + r"(?:que\s+|lo\s+de\s+|lo\s+que\s+|sobre\s+|acerca\s+de\s+)?"
    + r"(?P<text>.+?)\s*[.!]*\s*$",
    re.IGNORECASE | re.DOTALL,
)
_FORGET_MEMORY = re.compile(
    _PLEASE
    + r"(?:borra|elimina)\s+(?:el\s+recuerdo|los\s+recuerdos|de\s+tu\s+memoria)"
    + r"\s+(?:de\s+|sobre\s+|que\s+)?(?P<text>.+?)\s*[.!]*\s*$",
    re.IGNORECASE | re.DOTALL,
)

_LIST = re.compile(
    r"^\s*[¿]?\s*"
    r"(?:qu[eé]\s+(?:es\s+lo\s+que\s+)?recuerdas"
    r"|qu[eé]\s+sabes\s+de\s+m[ií]"
    r"|qu[eé]\s+tienes\s+(?:guardado|anotado)"
    r"|mu[eé]strame\s+(?:tus\s+)?(?:recuerdos|memorias)"
    r"|lista(?:me)?\s+(?:tus\s+)?(?:recuerdos|memorias))"
    r"(?:\s+(?:de|sobre|en|acerca\s+de)\s+(?P<topic>[^?.!]+?))?"
    r"\s*[?.!]*\s*$",
    re.IGNORECASE,
)

_THIS = {"esto", "eso", "lo anterior", "lo ultimo", "lo último"}
_SELF = {"mi", "mí", "ti", "me"}


def parse_memory_command(text: str) -> MemoryCommand | None:
    message = text.strip()

    match = _REMEMBER_IN.match(message)

    if match:
        category = normalize_category(match.group("cat"))

        if category is not None:
            return MemoryCommand(
                MemoryAction.REMEMBER,
                match.group("text").strip(),
                category,
            )

    match = _REMEMBER.match(message)

    if match:
        return MemoryCommand(MemoryAction.REMEMBER, match.group("text").strip())

    match = _FORGET.match(message) or _FORGET_MEMORY.match(message)

    if match:
        target = match.group("text").strip()

        if target.lower() in _THIS:
            return MemoryCommand(MemoryAction.FORGET, "")

        return MemoryCommand(MemoryAction.FORGET, target)

    match = _LIST.match(message)

    if match:
        topic = (match.group("topic") or "").strip()

        if not topic or topic.lower() in _SELF:
            return MemoryCommand(MemoryAction.LIST)

        category = normalize_category(topic)

        if category is not None:
            return MemoryCommand(MemoryAction.LIST, "", category)

        return MemoryCommand(MemoryAction.LIST, topic)

    return None