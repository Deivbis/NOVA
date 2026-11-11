from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication

from nova.core import Command, CoreOrchestrator, NovaState, Result
from nova.core.requests import QueuedRequest, RequestStatus
from nova.storage.service import StorageService
from nova.ui.qml.bridge import ERROR_DISPLAY_MS, NovaUiBridge


@pytest.fixture
def qapp():
    application = QCoreApplication.instance()

    if application is None:
        application = QCoreApplication([])

    return application


def create_bridge():
    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = repository

    core = CoreOrchestrator()
    core.start()

    return NovaUiBridge(core, storage_service), core, repository


def make_request(bridge):
    request = QueuedRequest(
        command=Command(name="chat.generate", source="user"),
        conversation_id=bridge._conversation.conversation_id,
    )
    bridge._requests_by_conversation[request.conversation_id] = 1

    return request


def fail(bridge, request):
    bridge._on_request_completed(
        request,
        Result.fail(
            code="OLLAMA_CONNECTION_ERROR",
            message="No se pudo conectar con Ollama. ¿Está en ejecución?",
        ),
    )


def test_failed_request_shows_transient_error_message(qapp):
    bridge, _, _ = create_bridge()
    request = make_request(bridge)

    fail(bridge, request)

    last = bridge.messages[-1]

    assert last["role"] == "error"
    assert "Ollama" in last["content"]
    assert request.status == RequestStatus.FAILED


def test_failed_request_sets_error_state(qapp):
    bridge, core, _ = create_bridge()

    fail(bridge, make_request(bridge))

    assert core.state == NovaState.ERROR


def test_transient_error_is_not_saved_or_sent_to_the_model(qapp):
    bridge, _, repository = create_bridge()

    fail(bridge, make_request(bridge))

    assert bridge._conversation.history() == []
    repository.add_message.assert_not_called()


def test_error_state_is_held_and_then_recovers(qapp):
    bridge, core, _ = create_bridge()
    fail(bridge, make_request(bridge))

    with patch("nova.ui.qml.bridge.QTimer.singleShot") as single_shot:
        bridge._on_worker_thread_finished()

    assert core.state == NovaState.ERROR
    assert single_shot.call_args.args[0] == ERROR_DISPLAY_MS

    bridge._recover_from_error()

    assert core.state == NovaState.IDLE


def test_sending_a_new_message_clears_the_error(qapp):
    bridge, core, _ = create_bridge()
    fail(bridge, make_request(bridge))

    with patch.object(bridge, "_process_next_request"):
        bridge.send_message("Hola")

    assert all(item["role"] != "error" for item in bridge.messages)
    assert core.state == NovaState.PROCESSING


def test_failure_with_queued_requests_goes_straight_to_processing(qapp):
    bridge, core, _ = create_bridge()
    fail(bridge, make_request(bridge))
    bridge._request_queue.enqueue(make_request(bridge))

    with patch.object(bridge, "_process_next_request"):
        bridge._on_worker_thread_finished()

    assert core.state == NovaState.PROCESSING