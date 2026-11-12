from unittest.mock import MagicMock

from nova.core import (
    Command,
    CoreOrchestrator,
    Event,
    EventNames,
    Identity,
    NovaState,
    Result,
)
from nova.core.requests import QueuedRequest
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge
from nova.voice import VoiceSettings


def create_voice(speaking=False, enabled=True, identity=Identity.ATLAS):
    voice = MagicMock()
    voice.is_speaking = speaking
    voice.settings = VoiceSettings(enabled=enabled, identity=identity)

    return voice


def create_bridge(voice=None):
    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = repository

    core = CoreOrchestrator()
    core.start()

    return NovaUiBridge(core, storage_service, voice), core, repository


def make_request(bridge):
    request = QueuedRequest(
        command=Command(name="chat.generate", source="user"),
        conversation_id=bridge._conversation.conversation_id,
    )
    bridge._requests_by_conversation[request.conversation_id] = 1

    return request


def test_answer_is_spoken_after_it_is_saved(qapp):
    voice = create_voice()
    bridge, _, repository = create_bridge(voice)
    repository.get.return_value = bridge._conversation

    bridge._on_request_completed(
        make_request(bridge),
        Result.ok("Hola, Jefe."),
    )

    voice.speak.assert_called_once_with("Hola, Jefe.")


def test_failed_request_is_not_spoken(qapp):
    voice = create_voice()
    bridge, _, _ = create_bridge(voice)

    bridge._on_request_completed(
        make_request(bridge),
        Result.fail(code="OLLAMA_CONNECTION_ERROR", message="sin Ollama"),
    )

    voice.speak.assert_not_called()


def test_state_stays_speaking_while_voice_is_speaking(qapp):
    bridge, core, _ = create_bridge(create_voice(speaking=True))
    core.set_state(NovaState.SPEAKING)

    bridge._on_worker_thread_finished()

    assert core.state == NovaState.SPEAKING


def test_state_returns_to_idle_when_voice_is_not_speaking(qapp):
    bridge, core, _ = create_bridge(create_voice(speaking=False))
    core.set_state(NovaState.SPEAKING)

    bridge._on_worker_thread_finished()

    assert core.state == NovaState.IDLE


def test_shutdown_stops_the_voice_service(qapp):
    voice = create_voice()
    bridge, _, _ = create_bridge(voice)

    bridge.shutdown()

    voice.shutdown.assert_called_once()


def test_voice_error_event_shows_a_transient_message(qapp):
    bridge, core, _ = create_bridge(create_voice())

    core.publish(
        Event(
            name=EventNames.VOICE_ERROR,
            payload={
                "code": "VOICE_MODEL_NOT_FOUND",
                "message": "Falta la voz 'es_MX-ald-medium'.",
            },
            source="voice",
        )
    )

    last = bridge.messages[-1]

    assert last["role"] == "error"
    assert "Falta la voz" in last["content"]


def test_voice_slots_delegate_to_the_service(qapp):
    voice = create_voice()
    bridge, _, _ = create_bridge(voice)

    bridge.stop_speaking()
    voice.stop.assert_called_once()

    bridge.set_voice_enabled(False)
    voice.update_settings.assert_called_with(enabled=False)

    bridge.set_voice_identity("asti")
    voice.update_settings.assert_called_with(identity=Identity.ASTI)

    bridge.set_online_voice(True)
    voice.update_settings.assert_called_with(prefer_online=True)


def test_invalid_voice_identity_is_ignored(qapp):
    voice = create_voice()
    bridge, _, _ = create_bridge(voice)

    bridge.set_voice_identity("robot")

    voice.update_settings.assert_not_called()


def test_voice_properties_reflect_the_settings(qapp):
    voice = create_voice(enabled=True, identity=Identity.ASTI)
    bridge, _, _ = create_bridge(voice)

    assert bridge.voiceEnabled is True
    assert bridge.voiceIdentity == "asti"


def test_bridge_without_voice_service_ignores_voice_calls(qapp):
    bridge, _, _ = create_bridge()

    bridge.stop_speaking()
    bridge.set_voice_enabled(True)
    bridge.set_voice_identity("asti")
    bridge.set_online_voice(True)

    assert bridge.voiceEnabled is False
    assert bridge.voiceIdentity == "atlas"