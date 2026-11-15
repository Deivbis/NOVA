"""Clasificación de recuerdos por palabras clave (D-029).

Se elige la categoría con más coincidencias; en caso de empate gana la
primera de SPEC-005. Sin coincidencias: "General".
"""

from nova.core.memory import (
    ALL_CATEGORIES,
    DEFAULT_CATEGORY,
    MEMORY_CATEGORIES,
)
from nova.memory.text import normalize, tokens

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Programación": (
        "python", "codigo", "programar", "programacion", "programo", "bug",
        "git", "github", "api", "funcion", "framework", "libreria", "java",
        "javascript", "sql", "qml", "pyside", "software", "desarrollo",
    ),
    "Juegos": (
        "juego", "juegos", "videojuego", "videojuegos", "gamer", "steam",
        "xbox", "playstation", "ps5", "nintendo", "minecraft", "fortnite",
        "valorant", "jugar", "juego",
    ),
    "Música": (
        "musica", "cancion", "canciones", "playlist", "spotify", "banda",
        "cantante", "album", "rock", "reggaeton", "guitarra", "piano",
        "escuchar",
    ),
    "Trabajo": (
        "trabajo", "trabajar", "empresa", "reunion", "cliente", "oficina",
        "sueldo", "empleo", "contrato", "jornada",
    ),
    "Estudios": (
        "estudio", "estudiar", "estudios", "universidad", "carrera",
        "examen", "tarea", "clase", "curso", "colegio", "tesis", "profesor",
    ),
    "Salud": (
        "salud", "medico", "medicina", "alergia", "alergico", "dieta",
        "ejercicio", "dolor", "doctor", "hospital", "dormir", "sueno",
    ),
    "Rutinas": (
        "rutina", "cada dia", "todos los dias", "cada manana", "me levanto",
        "me acuesto", "habito", "diario", "cada noche",
    ),
    "Familia": (
        "mama", "papa", "hermano", "hermana", "hijo", "hija", "abuelo",
        "abuela", "tio", "tia", "familia", "esposa", "esposo", "primo",
    ),
    "Amigos": ("amigo", "amiga", "amigos", "amigas", "companero", "colega"),
    "Proyectos": (
        "proyecto", "proyectos", "nova", "aplicacion", "startup", "prototipo",
    ),
}

_KEYWORDS_NORMALIZED = {
    category: tuple(dict.fromkeys(normalize(word) for word in words))
    for category, words in _KEYWORDS.items()
}

_CATEGORY_ALIASES = {
    "programacion": "Programación", "programar": "Programación",
    "juego": "Juegos", "juegos": "Juegos", "videojuegos": "Juegos",
    "musica": "Música",
    "trabajo": "Trabajo",
    "estudio": "Estudios", "estudios": "Estudios",
    "salud": "Salud",
    "rutina": "Rutinas", "rutinas": "Rutinas",
    "familia": "Familia",
    "amigo": "Amigos", "amigos": "Amigos",
    "proyecto": "Proyectos", "proyectos": "Proyectos",
    "general": DEFAULT_CATEGORY,
}


def normalize_category(name: str) -> str | None:
    """Devuelve el nombre oficial de una categoría, o None si no existe."""
    key = normalize(name).strip()

    for category in ALL_CATEGORIES:
        if normalize(category) == key:
            return category

    return _CATEGORY_ALIASES.get(key)


def classify(text: str) -> str:
    padded = f" {' '.join(tokens(text))} "
    best = DEFAULT_CATEGORY
    best_hits = 0

    for category in MEMORY_CATEGORIES:
        hits = sum(
            1
            for word in _KEYWORDS_NORMALIZED[category]
            if f" {word} " in padded
        )

        if hits > best_hits:
            best, best_hits = category, hits

    return best