from uuid import uuid4

from nova.learning import (
    LearningCommandHandler,
    LearningService,
    detect_explicit,
    parse_learning_command,
)
from nova.memory import MemoryService
from nova.storage import StorageService
from nova.learning.handler import _yes_no

def make(tmp_path):
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    state = {"on": True}
    memory = MemoryService(storage.memory_repository)
    service = LearningService(
        storage.learning_repository,
        memory,
        lambda: state["on"],
        lambda value: state.update(on=value),
    )

    return storage, memory, service


def test_detect_explicit():
    assert detect_explicit("Prefiero mi café sin azúcar")[0] == (
        "Prefiere su café sin azúcar"
    )
    assert detect_explicit("No me gustan las películas de terror")[0] == (
        "No le gustan las películas de terror"
    )
    assert detect_explicit("¿Prefieres el rojo?") is None
    assert detect_explicit("hola") is None


def test_explicit_confirm_saves_learned_memory(tmp_path):
    storage, memory, service = make(tmp_path)
    handler = LearningCommandHandler(service)

    handler.observe("Prefiero programar de noche", uuid4())
    assert "recuerde" in handler.proposal()
    assert "Anotado" in handler.reply_to("sí")
    assert [m.source for m in memory.list_memories().value] == ["learned"]
    storage.close()


def test_rejected_not_proposed_again(tmp_path):
    storage, _, service = make(tmp_path)
    handler = LearningCommandHandler(service)

    handler.observe("Odio el reggaeton", uuid4())
    handler.proposal()
    handler.reply_to("no")
    handler.observe("Odio el reggaeton", uuid4())

    assert handler.proposal() is None
    storage.close()


def test_pattern_needs_messages_and_conversations(tmp_path):
    storage, _, service = make(tmp_path)
    a, b, c = uuid4(), uuid4(), uuid4()

    for conversation in (a, a, b, b):
        service.observe("estuve con la guitarra otra vez", conversation)

    assert service.next_proposal() is None

    service.observe("estuve con la guitarra otra vez", c)

    assert service.next_proposal().content == "Le interesa guitarra"
    storage.close()


def test_disabled_does_not_observe(tmp_path):
    storage, _, service = make(tmp_path)

    service.set_enabled(False)
    service.observe("Prefiero el té", uuid4())

    assert service.next_proposal() is None
    assert parse_learning_command("deja de aprender") is not None
    storage.close()

def test_yes_no_tolerant():
    assert _yes_no("Sí, guárdalo.") is True
    assert _yes_no("No, gracias") is False
    assert _yes_no("quizá luego") is None

def test_open_word_needs_low_share(tmp_path):
    storage, _, service = make(tmp_path)
    ids = [uuid4() for _ in range(3)]

    for i in range(20):
        text = "fui de senderismo" if i % 4 == 0 else f"mensaje normal {i}"
        service.observe(text, ids[i % 3])

    assert service.next_proposal().content == "Le interesa senderismo"
    storage.close()


def test_open_word_blocked_when_everything_is_the_same(tmp_path):
    storage, _, service = make(tmp_path)
    ids = [uuid4() for _ in range(3)]

    for i in range(5):
        service.observe("fui de senderismo", ids[i % 3])

    assert service.next_proposal() is None
    storage.close()