from datetime import datetime, timedelta, timezone

from nova.core.memory import Memory
from nova.memory import select_relevant

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def memories(*contents):
    return [
        Memory(content=text, created_at=BASE + timedelta(minutes=index))
        for index, text in enumerate(contents)
    ]


def contents(items):
    return [item.content for item in items]


def test_only_the_related_memory_is_selected():
    items = memories("me llamo Deivbis", "mi hermano se llama Luis", "me gusta el rock")

    assert contents(select_relevant(items, "¿cómo me llamo?")) == [
        "me llamo Deivbis"
    ]


def test_generic_greetings_select_nothing():
    items = memories("me llamo Deivbis", "me gusta el rock")

    assert select_relevant(items, "hola") == []
    assert select_relevant(items, "") == []


def test_matching_ignores_accents_and_case():
    items = memories("Me gusta la MÚSICA clásica")

    assert len(select_relevant(items, "ponme musica")) == 1


def test_word_stems_match_different_endings():
    items = memories("me gusta programar")

    assert len(select_relevant(items, "estoy programando ahora")) == 1


def test_more_matches_first_then_most_recent():
    items = memories(
        "trabajo de noche",
        "trabajo en casa de noche mucho",
        "trabajo cerca",
    )

    result = contents(select_relevant(items, "trabajo de noche en casa"))

    assert result[0] == "trabajo en casa de noche mucho"
    assert result[1] == "trabajo de noche"


def test_item_limit_is_respected():
    items = memories(*[f"rock número {n}" for n in range(10)])

    assert len(select_relevant(items, "rock", max_items=3)) == 3


def test_character_budget_is_respected_but_keeps_the_best_one():
    items = memories("rock " + "a" * 100, "rock " + "b" * 100)

    result = select_relevant(items, "rock", max_chars=120)

    assert len(result) == 1