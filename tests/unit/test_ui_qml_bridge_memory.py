from unittest.mock import MagicMock, patch

from nova.core import CoreOrchestrator, Identity
from nova.memory import MemoryService
from nova.personality import IdentityService
from nova.storage import StorageService
from nova.ui.qml.bridge import NovaUiBridge


class Holder:
    def __init__(self):
        self.identity = Identity.ATLAS

    def get(self):
        return self.identity

    def set(self, identity):
        self.identity = identity


def create_bridge(tmp_path, with_memory=True, with_voice=False):
    repository = MagicMock()
    repository.list_conversations.return_value = []

    conversations = MagicMock(spec=StorageService)
    conversations.conversation_repository = repository

    memory_storage = StorageService(tmp_path / "memory.db")
    memory_storage.initialize()
    memory = MemoryService(memory_storage.memory_repository)

    core = CoreOrchestrator()
    core.start()

    holder = Holder()
    identity = IdentityService(core, holder.get, holder.set)

    voice = MagicMock() if with_voice else None

    if voice is not None:
        voice.is_speaking = False

    bridge = NovaUiBridge(
        core,
        conversations,
        voice,
        None,
        identity,
        memory if with_memory else None,
    )

    return bridge, repository, memory, voice, memory_storage


def send(bridge, text):
    with patch.object(bridge, "_process_next_request"):
        bridge.send_message(text)


def sent_messages(bridge):
    return bridge._request_queue.dequeue().command.payload["messages"]


def test_remember_command_saves_and_replies_without_the_model(qapp, tmp_path):
    bridge, _, memory, _, storage = create_bridge(tmp_path)

    send(bridge, "recuerda que me llamo Deivbis")

    assert [m.content for m in memory.list_memories().value] == [
        "me llamo Deivbis"
    ]
    assert bridge._request_queue.is_empty
    assert bridge.messages[-1]["role"] == "assistant"
    assert bridge.messages[-1]["content"].startswith("Anotado, Jefe")

    storage.close()


def test_memory_replies_are_saved_in_the_conversation_and_spoken(
    qapp,
    tmp_path,
):
    bridge, repository, _, voice, storage = create_bridge(
        tmp_path,
        with_voice=True,
    )

    send(bridge, "recuerda que me llamo Deivbis")

    assert repository.add_message.call_count == 2
    voice.speak.assert_called_once()
    assert voice.speak.call_args.args[0].startswith("Anotado")

    storage.close()


def test_list_command_replies_with_the_memories(qapp, tmp_path):
    bridge, _, memory, _, storage = create_bridge(tmp_path)
    memory.remember("me gusta el rock", "Música")

    send(bridge, "qué recuerdas")

    assert "- Música: me gusta el rock" in bridge.messages[-1]["content"]

    storage.close()


def test_forget_command_deactivates_the_memory(qapp, tmp_path):
    bridge, _, memory, _, storage = create_bridge(tmp_path)
    memory.remember("mi hermano se llama Luis")

    send(bridge, "olvida lo de mi hermano")

    assert memory.list_memories().value == []
    assert bridge.messages[-1]["content"].startswith("Olvidado, Jefe")

    storage.close()


def test_relevant_memories_are_added_to_the_system_prompt(qapp, tmp_path):
    bridge, _, memory, _, storage = create_bridge(tmp_path)
    memory.remember("me llamo Deivbis")

    send(bridge, "¿cómo me llamo?")

    messages = sent_messages(bridge)

    assert "Recuerdos autorizados" in messages[0]["content"]
    assert "me llamo Deivbis" in messages[0]["content"]
    assert bridge._conversation.history() == [
        {"role": "user", "content": "¿cómo me llamo?"}
    ]

    storage.close()


def test_unrelated_messages_do_not_send_memories(qapp, tmp_path):
    bridge, _, memory, _, storage = create_bridge(tmp_path)
    memory.remember("me gusta el rock")

    send(bridge, "Hola")

    assert "Recuerdos autorizados" not in sent_messages(bridge)[0]["content"]

    storage.close()


def test_without_memory_service_the_command_goes_to_the_model(qapp, tmp_path):
    bridge, _, _, _, storage = create_bridge(tmp_path, with_memory=False)

    send(bridge, "recuerda que me llamo Deivbis")

    assert sent_messages(bridge)[-1] == {
        "role": "user",
        "content": "recuerda que me llamo Deivbis",
    }

    storage.close()