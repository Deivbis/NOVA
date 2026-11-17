"""Sí/no tolerante a lo que devuelve el STT («Sí, guárdalo.» → True)."""

import unicodedata

_YES = {
    "si", "claro", "dale", "ok", "vale", "confirmo", "correcto",
    "guardalo", "recuerdalo", "afirmativo", "adelante", "perfecto",
    "permitelo", "hazlo",
}
_NO = {"no", "nunca", "negativo", "descartalo", "nada", "cancela"}


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())

    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def parse_yes_no(text: str) -> bool | None:
    words = [w.strip(".,!¡¿?") for w in _plain(text).split()]

    if not words:
        return None

    if words[0] in _NO:
        return False

    if words[0] in _YES or words[:2] == ["por", "supuesto"]:
        return True

    return None