from unittest.mock import MagicMock, patch

from nova.core import CoreOrchestrator, Event, EventNames
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge


def create_bridge(with_voice_input=True):
    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = repository

    core = CoreOrchestrator()
    core.start()

    voice_service = MagicMock()
    voice_service.is_speaking = False
    voice_input = MagicMock() if with_voice_input else None

    bridge = NovaUiBridge(core, storage_service, voice_service, voice_input)

    return bridge, core, repository, voice_input


def publish_voice_error(core, message, direction=None):
    payload = {"code": "ERROR", "message": message}

    if direction is not None:
        payload["direction"] = direction

    core.publish(
        Event(name=EventNames.VOICE_ERROR, payload=payload, source="voice")
    )


def test_transcript_is_sent_as_a_chat_message(qapp):
    bridge, _, _, voice_input = create_bridge()

    with patch.object(bridge, "_process_next_request"):
        voice_input.on_transcript("abre el navegador")

    assert bridge.messages[-1] == {
        "role": "user",
        "content": "abre el navegador",
    }


def test_toggle_slot_delegates_to_the_voice_input(qapp):
    bridge, _, _, voice_input = create_bridge()

    bridge.toggle_voice_input()

    voice_input.toggle.assert_called_once()


def test_toggle_without_voice_input_is_safe(qapp):
    bridge, _, _, _ = create_bridge(with_voice_input=False)

    bridge.toggle_voice_input()


def test_shutdown_stops_the_voice_input(qapp):
    bridge, _, _, voice_input = create_bridge()

    bridge.shutdown()

    voice_input.shutdown.assert_called_once()


def test_input_errors_use_the_listening_prefix(qapp):
    bridge, core, _, _ = create_bridge()

    publish_voice_error(core, "No detecté voz.", direction="input")

    last = bridge.messages[-1]

    assert last["role"] == "error"
    assert last["content"].startswith("No pude escucharte.")
    assert "No detecté voz." in last["content"]


def test_output_errors_keep_the_speaking_prefix(qapp):
    bridge, core, _, _ = create_bridge()

    publish_voice_error(core, "Falta la voz.", direction="output")

    assert bridge.messages[-1]["content"].startswith("No pude hablar.")


def test_transcripts_are_ignored_after_shutdown(qapp):
    bridge, _, repository, voice_input = create_bridge()

    bridge.shutdown()
    voice_input.on_transcript("hola")

    repository.add_message.assert_not_called()


def test_transcript_on_home_starts_conversation_and_requests_navigation(qapp):
    bridge, _, _, voice_input = create_bridge()
    navigation = MagicMock()
    bridge.navigateRequested.connect(navigation)

    with patch.object(bridge, "_process_next_request"):
        voice_input.on_transcript("crear un informe")

    assert bridge.messages[-1] == {
        "role": "user",
        "content": "crear un informe",
    }
    navigation.assert_called_once_with(1)


def test_transcript_on_other_page_does_not_request_navigation(qapp):
    bridge, _, _, voice_input = create_bridge()
    navigation = MagicMock()
    bridge.navigateRequested.connect(navigation)
    bridge.set_current_page(2)

    with patch.object(bridge, "_process_next_request"):
        voice_input.on_transcript("consultar mi memoria")

    assert bridge.messages[-1] == {
        "role": "user",
        "content": "consultar mi memoria",
    }
    navigation.assert_not_called()


def test_empty_transcript_on_home_does_not_request_navigation(qapp):
    bridge, _, repository, voice_input = create_bridge()
    navigation = MagicMock()
    conversation_changed = MagicMock()

    bridge.navigateRequested.connect(navigation)
    bridge.conversationChanged.connect(conversation_changed)

    original_conversation = bridge._conversation
    initial_create_count = repository.create.call_count

    voice_input.on_transcript("")

    assert bridge._conversation is original_conversation
    navigation.assert_not_called()
    conversation_changed.assert_not_called()
    assert repository.create.call_count == initial_create_count
