from nova.core import Identity
from nova.personality import build_messages, profile_for

HISTORY = [
    {"role": "user", "content": "Hola"},
    {"role": "assistant", "content": "Buenas, Jefe."},
    {"role": "user", "content": "¿Qué tal?"},
]


def test_system_prompt_comes_first_and_history_follows():
    messages = build_messages(Identity.ATLAS, HISTORY)

    assert messages[0]["role"] == "system"
    assert messages[1:] == HISTORY


def test_identity_selects_the_prompt():
    atlas = build_messages(Identity.ATLAS, HISTORY)[0]["content"]
    asti = build_messages(Identity.ASTI, HISTORY)[0]["content"]

    assert atlas == profile_for(Identity.ATLAS).system_prompt
    assert asti == profile_for(Identity.ASTI).system_prompt


def test_history_is_not_modified():
    history = list(HISTORY)

    build_messages(Identity.ATLAS, history)

    assert history == HISTORY


def test_builder_returns_a_new_list():
    messages = build_messages(Identity.ATLAS, HISTORY)

    assert messages is not HISTORY
    assert len(messages) == len(HISTORY) + 1