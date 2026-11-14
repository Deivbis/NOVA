"""Prepara el texto de una respuesta para hablarlo (SPEC-008, D-018).

Quita lo que suena mal en voz (Markdown, emojis, bloques de código, enlaces)
y lo parte en frases para empezar a hablar sin esperar a sintetizarlo todo.
"""

import re

MIN_CHARS = 20
MAX_CHARS = 240

_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`([^`]*)`")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_URL = re.compile(r"https?://\S+")
_BOLD_ITALIC = re.compile(r"(\*\*|__|\*)(.+?)\1")
_LINE_MARKER = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]+|[-*+][ \t]+|>[ \t]?)",
    re.MULTILINE,
)
_EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FAFF"
    "\u2600-\u27BF"
    "\u2B00-\u2BFF"
    "\uFE00-\uFE0F"
    "\u200D"
    "]+"
)
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
_SPACES = re.compile(r"[ \t]+")


def clean_for_speech(text: str) -> str:
    """Quita el formato que no se debe leer en voz alta."""
    cleaned = _CODE_BLOCK.sub(" ", text)
    cleaned = _INLINE_CODE.sub(r"\1", cleaned)
    cleaned = _MD_LINK.sub(r"\1", cleaned)
    cleaned = _URL.sub("enlace", cleaned)
    cleaned = _LINE_MARKER.sub("", cleaned)
    cleaned = _BOLD_ITALIC.sub(r"\2", cleaned)
    cleaned = _EMOJI.sub("", cleaned).replace("*", "")

    return _SPACES.sub(" ", cleaned).strip()


def _split_long(chunk: str) -> list[str]:
    parts: list[str] = []

    while len(chunk) > MAX_CHARS:
        cut = max(
            chunk.rfind(",", 0, MAX_CHARS),
            chunk.rfind(";", 0, MAX_CHARS),
            chunk.rfind(":", 0, MAX_CHARS),
        )

        if cut < MIN_CHARS:
            cut = chunk.rfind(" ", 0, MAX_CHARS)

        if cut < MIN_CHARS:
            cut = MAX_CHARS

        parts.append(chunk[: cut + 1].strip())
        chunk = chunk[cut + 1 :].strip()

    if chunk:
        parts.append(chunk)

    return parts


def split_sentences(text: str) -> list[str]:
    """Parte el texto en trozos para hablar, uniendo las frases muy cortas."""
    sentences: list[str] = []

    for line in text.splitlines():
        sentences.extend(
            part.strip()
            for part in _SENTENCE_END.split(line)
            if part.strip()
        )

    chunks: list[str] = []
    buffer = ""

    for sentence in sentences:
        buffer = f"{buffer} {sentence}".strip()

        if len(buffer) >= MIN_CHARS:
            chunks.append(buffer)
            buffer = ""

    if buffer:
        if chunks:
            chunks[-1] = f"{chunks[-1]} {buffer}"
        else:
            chunks.append(buffer)

    result: list[str] = []

    for chunk in chunks:
        result.extend(_split_long(chunk))

    return result


def prepare_speech(text: str) -> list[str]:
    """Limpia el texto y lo devuelve listo para sintetizar, frase a frase."""
    return split_sentences(clean_for_speech(text))