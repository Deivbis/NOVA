"""Selección de recuerdos relevantes para una frase (SPEC-005, D-029).

Coincidencia de palabras con contenido (sin acentos, con raíz aproximada).
No se envía nada al modelo si no hay coincidencias.
"""

from nova.core.memory import Memory
from nova.memory.text import keywords

MAX_ITEMS = 5
MAX_CHARS = 600


def score(memory: Memory, query_keywords: set[str]) -> int:
    return len(keywords(memory.content) & query_keywords)


def select_relevant(
    memories: list[Memory],
    query: str,
    max_items: int = MAX_ITEMS,
    max_chars: int = MAX_CHARS,
) -> list[Memory]:
    query_keywords = keywords(query)

    if not query_keywords:
        return []

    scored = [
        (score(memory, query_keywords), memory) for memory in memories
    ]
    matches = [item for item in scored if item[0] > 0]

    # Más coincidencias primero; a igualdad, el recuerdo más reciente.
    matches.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)

    selected: list[Memory] = []
    total = 0

    for _, memory in matches:
        if len(selected) >= max_items:
            break

        if selected and total + len(memory.content) > max_chars:
            break

        selected.append(memory)
        total += len(memory.content)

    return selected