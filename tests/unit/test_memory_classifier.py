from nova.memory import classify, normalize_category

CASES = {
    "me gusta programar en Python": "Programación",
    "mi canción favorita es de Queen": "Música",
    "juego Minecraft los fines de semana": "Juegos",
    "tengo examen en la universidad": "Estudios",
    "soy alérgico al polen": "Salud",
    "mi hermano se llama Luis": "Familia",
    "trabajo en una empresa de software": "Trabajo",
    "me levanto cada día a las 6": "Rutinas",
    "mi color favorito es el azul": "General",
    "trabajo en mi proyecto NOVA": "Proyectos",
    "mi amigo Carlos vive lejos": "Amigos",
}


def test_text_is_classified_by_keywords():
    for text, expected in CASES.items():
        assert classify(text) == expected, text


def test_a_tie_goes_to_the_first_category_of_the_spec():
    assert classify("juego y estudio") == "Juegos"


def test_category_names_are_normalized():
    expected = {
        "música": "Música",
        "MUSICA": "Música",
        "juego": "Juegos",
        "general": "General",
        "Proyecto": "Proyectos",
        "programacion": "Programación",
        "casa": None,
        "": None,
    }

    for name, category in expected.items():
        assert normalize_category(name) == category, name