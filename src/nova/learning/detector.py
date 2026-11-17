"""Señales de aprendizaje (SPEC-006): frases explícitas y temas."""
import re
from dataclasses import dataclass

from nova.core.memory import DEFAULT_CATEGORY
from nova.memory.classifier import classify, find_keywords, normalize_category
from nova.memory.text import STOPWORDS, normalize

MAX_FRAGMENT = 200
_WORDS = {"mi": "su", "mis": "sus", "me": "le"}
_F = re.IGNORECASE

_TOKEN = re.compile(r"[a-záéíóúñü]{4,}")

_GENERIC = frozenset({
    "nova", "atlas", "asti", "abi", "jefe", "senor", "escuchar", "jugar",
    "trabajar", "estudiar", "programo", "tarea", "clase", "codigo",
    "software", "desarrollo", "dormir", "sueno", "dolor", "diario",
    "habito", "cada dia", "todos los dias", "cada manana", "cada noche",
    "me levanto", "me acuesto",
    "hacer", "hago", "haces", "hace", "tengo", "tienes", "tiene", "tener",
    "estoy", "estas", "estamos", "estan", "estaba", "estuve", "voy",
    "vamos", "hoy", "ayer", "manana", "ahora", "luego", "despues",
    "antes", "siempre", "nunca", "tambien", "pero", "porque", "aunque",
    "entonces", "ademas", "cosa", "cosas", "algo", "nada", "todo",
    "todos", "toda", "todas", "mucho", "mucha", "muchos", "muchas",
    "poco", "poca", "bien", "mejor", "peor", "gracias", "puedes",
    "puedo", "podria", "quiero", "quieres", "queria", "necesito",
    "ayuda", "ayudame", "sabes", "saber", "creo", "pienso", "parece",
    "veces", "semana", "tiempo", "momento", "forma", "manera", "parte",
    "otra", "otro", "otras", "otros", "esta", "estos", "estas", "eso",
    "aqui", "alli", "mismo", "misma", "dijiste", "dices", "dime",
})

_RULES = (
    (re.compile(r"no\s+me\s+gusta(?P<n>n?)\s+(?P<x>.+)", _F),
     "No le gusta{n} {x}"),
    (re.compile(r"me\s+(?P<v>gusta|encanta)(?P<n>n?)\s+(?P<x>.+)", _F),
     "Le {v}{n} {x}"),
    (re.compile(r"prefiero\s+(?P<x>.+)", _F), "Prefiere {x}"),
    (re.compile(
        r"(?:siempre|normalmente|generalmente|casi\s+siempre)\s+"
        r"(?:uso|utilizo)\s+(?P<x>.+)", _F), "Suele usar {x}"),
    (re.compile(r"suelo\s+(?P<x>.+)", _F), "Suele {x}"),
    (re.compile(r"odio\s+(?P<x>.+)", _F), "Odia {x}"),
)

@dataclass(frozen=True)
class Topic:
    display: str
    key: str
    category: str
    curated: bool  # palabra del clasificador (sin filtro de frecuencia)

def _third_person(fragment: str) -> str:
    return " ".join(_WORDS.get(w.lower(), w) for w in fragment.split())


def detect_explicit(text: str) -> tuple[str, str] | None:
    """(contenido en tercera persona, categoría) si hay una preferencia."""
    message = " ".join(text.split()).strip(" .!")

    if "?" in message or "¿" in message:
        return None

    for pattern, template in _RULES:
        match = pattern.fullmatch(message)

        if match is None:
            continue

        values = match.groupdict()
        fragment = _third_person(values["x"].strip())

        if not 3 <= len(fragment) <= MAX_FRAGMENT:
            return None

        content = template.format(
            n=values.get("n") or "",
            v=(values.get("v") or "").lower(),
            x=fragment,
        )

        return content, classify(content)

    return None


def topic_key(word: str) -> str:
    key = normalize(word)

    return key[:-1] if len(key) > 4 and key.endswith("s") else key

def detect_topics(text: str) -> list[Topic]:
    """Palabras del mensaje que podrían ser un tema recurrente."""
    seen: set[str] = set()
    topics: list[Topic] = []

    for word, category in find_keywords(text):
        key = topic_key(word)
        seen.add(key)

        if normalize(word) not in _GENERIC and normalize_category(word) is None:
            topics.append(Topic(word, key, category, True))

    for token in _TOKEN.findall(text.lower()):
        norm = normalize(token)
        key = topic_key(token)

        if (
            norm in STOPWORDS
            or norm in _GENERIC
            or key in seen
            or normalize_category(token) is not None
        ):
            continue

        seen.add(key)
        topics.append(Topic(token, key, DEFAULT_CATEGORY, False))

    return topics