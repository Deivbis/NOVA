from nova.memory import MemoryAction as A
from nova.memory import MemoryCommand as C
from nova.memory import parse_memory_command

REMEMBER = {
    "recuerda que me llamo Deivbis": C(A.REMEMBER, "me llamo Deivbis"),
    "Recuerda que mi color favorito es el azul.": C(
        A.REMEMBER, "mi color favorito es el azul."
    ),
    "recuerda en Música que me gusta el rock": C(
        A.REMEMBER, "me gusta el rock", "Música"
    ),
    "Recuerda en musica que odio el reggaeton": C(
        A.REMEMBER, "odio el reggaeton", "Música"
    ),
    "anota que mañana tengo examen": C(A.REMEMBER, "mañana tengo examen"),
    "guarda que mi PC tiene 15 GB de RAM": C(
        A.REMEMBER, "mi PC tiene 15 GB de RAM"
    ),
    "recuerda: la clave del wifi es nova2026": C(
        A.REMEMBER, "la clave del wifi es nova2026"
    ),
    "no olvides que trabajo de noche": C(A.REMEMBER, "trabajo de noche"),
    "por favor, recuerda que soy alérgico al polen": C(
        A.REMEMBER, "soy alérgico al polen"
    ),
}

FORGET = {
    "olvida que me llamo Deivbis": C(A.FORGET, "me llamo Deivbis"),
    "olvida mi color favorito": C(A.FORGET, "mi color favorito"),
    "olvida lo de mi hermano": C(A.FORGET, "mi hermano"),
    "olvida esto": C(A.FORGET, ""),
    "Olvida eso.": C(A.FORGET, ""),
    "borra el recuerdo de la reunión": C(A.FORGET, "la reunión"),
    "elimina de tu memoria lo que dije del wifi": C(
        A.FORGET, "lo que dije del wifi"
    ),
}

LIST = {
    "qué recuerdas": C(A.LIST),
    "¿Qué recuerdas?": C(A.LIST),
    "qué recuerdas de mí": C(A.LIST),
    "qué recuerdas de Música": C(A.LIST, "", "Música"),
    "¿Qué recuerdas sobre mi hermano?": C(A.LIST, "mi hermano"),
    "qué tienes guardado": C(A.LIST),
    "muéstrame tus recuerdos": C(A.LIST),
}

NOT_COMMANDS = [
    "¿recuerdas que te lo dije?",
    "recuerdas cuando fuimos al lago",
    "hola",
    "",
    "recuerda",
    "me gusta recordar cosas",
    "recuerda en casa que apague la luz",
    "borra la conversación",
    "cuéntame qué es olvidar",
    "no olvides",
]


def check(cases):
    for text, expected in cases.items():
        assert parse_memory_command(text) == expected, text


def test_remember_commands():
    check(REMEMBER)


def test_forget_commands():
    check(FORGET)


def test_list_commands():
    check(LIST)


def test_ordinary_sentences_are_not_commands():
    for text in NOT_COMMANDS:
        assert parse_memory_command(text) is None, text