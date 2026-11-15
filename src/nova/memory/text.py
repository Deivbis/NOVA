"""Utilidades de texto para la memoria (sin acentos ni mayúsculas)."""

import re
import unicodedata

_WORD = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    """
    de la el los las un una unos unas y o u que en a al del lo se me mi mis tu
    tus su sus es son soy eres por para con sin como cual cuales quien cuando
    donde no si ya muy mas menos te le les nos ha he hay ser estar esta este
    esto eso esa ese yo usted hola gracias favor puedes puedo quiero dime dame
    sobre acerca
    """.split()
)


def normalize(text: str) -> str:
    """Minúsculas y sin acentos."""
    decomposed = unicodedata.normalize("NFD", text.lower())

    return "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )


def tokens(text: str) -> list[str]:
    return _WORD.findall(normalize(text))


def keywords(text: str) -> set[str]:
    """Palabras con contenido, recortadas a una raíz aproximada."""
    return {
        token[:6]
        for token in tokens(text)
        if token not in STOPWORDS and len(token) > 1
    }