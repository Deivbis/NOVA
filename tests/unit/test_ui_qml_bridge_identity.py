from unittest.mock import MagicMock, patch

from nova.core import CoreOrchestrator, Identity
from nova.personality import IdentityService, profile_for
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge


class Holder:
    def __init__(self):
        self.identity = Identity.ATLAS

    def get(self):
        return self.identity

    def set(self, identity):
        self.identity = identity


def create_bridge(with_identity=True, with_voice=False):
    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = repository

    core = CoreOrchestrator()
    core.start()

    holder = Holder()
    identity_service = (
        IdentityService(core, holder.get, holder.set)
        if with_identity
        else None
    )

    voice = MagicMock() if with_voice else None

    if voice is not None:
        voice.is_speaking = False

    bridge = NovaUiBridge(
        core,
        storage_service,
        voice,
        None,
        identity_service,
    )

    return bridge, repository, holder, voice


def send(bridge, text):
    with patch.object(bridge, "_process_next_request"):
        bridge.send_message(text)


def sent_messages(bridge):
    return bridge._request_queue.dequeue().command.payload["messages"]


def test_identity_command_switches_without_calling_the_model(qapp):
    bridge, _, holder, _ = create_bridge()

    send(bridge, "cambia a Asti")

    assert holder.identity == Identity.ASTI
    assert bridge._request_queue.is_empty
    assert bridge.messages[-1] == {
        "role": "assistant",
        "content": profile_for(Identity.ASTI).confirmation,
    }


def test_identity_switch_is_saved_in_the_conversation(qapp):
    bridge, repository, _, _ = create_bridge()

    send(bridge, "cambia a Asti")

    assert repository.add_message.call_count == 2
    assert [m["role"] for m in bridge.messages] == ["user", "assistant"]


def test_identity_switch_is_spoken_with_the_new_identity(qapp):
    bridge, _, _, voice = create_bridge(with_voice=True)

    send(bridge, "cambia a Asti")

    voice.speak.assert_called_once_with(
        profile_for(Identity.ASTI).confirmation
    )


def test_normal_messages_start_with_the_system_prompt(qapp):
    bridge, _, _, _ = create_bridge()

    send(bridge, "Hola")

    messages = sent_messages(bridge)

    assert messages[0] == {
        "role": "system",
        "content": profile_for(Identity.ATLAS).system_prompt,
    }
    assert messages[-1] == {"role": "user", "content": "Hola"}


def test_the_system_prompt_is_not_stored_in_the_conversation(qapp):
    bridge, _, _, _ = create_bridge()

    send(bridge, "Hola")

    assert bridge._conversation.history() == [
        {"role": "user", "content": "Hola"}
    ]


def test_the_prompt_follows_the_active_identity_and_keeps_the_context(qapp):
    bridge, _, _, _ = create_bridge()

    send(bridge, "cambia a Asti")
    send(bridge, "Hola")

    messages = sent_messages(bridge)

    assert messages[0]["content"] == profile_for(Identity.ASTI).system_prompt
    assert [m["role"] for m in messages] == [
        "system",
        "user",
        "assistant",
        "user",
    ]


def test_active_identity_property(qapp):
    bridge, _, _, _ = create_bridge()

    assert bridge.activeIdentity == "atlas"

    send(bridge, "pasa a Abi")

    assert bridge.activeIdentity == "asti"


def test_without_identity_service_the_command_goes_to_the_model(qapp):
    bridge, _, _, _ = create_bridge(with_identity=False)

    send(bridge, "cambia a Asti")

    assert sent_messages(bridge) == [
        {"role": "user", "content": "cambia a Asti"}
    ]