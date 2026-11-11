import threading
import time
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication

from nova.core import Conversation, CoreOrchestrator, NovaState, Result
from nova.core.requests import RequestStatus
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge


def create_storage_service(repository):
    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = repository

    return storage_service


def create_bridge(repository=None):
    if repository is None:
        repository = MagicMock()

    repository.list_conversations.return_value = []

    core = CoreOrchestrator()
    core.start()

    bridge = NovaUiBridge(core, create_storage_service(repository))

    return bridge, core, repository


def wait_until(condition, timeout=5.0):
    """Procesa eventos de Qt hasta que se cumpla la condición."""
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        QCoreApplication.processEvents()

        if condition():
            return True

        time.sleep(0.01)

    return False


def test_bridge_creates_initial_conversation(qapp):
    bridge, _, repository = create_bridge()

    repository.create.assert_called_once()

    assert bridge.messages == []


def test_bridge_rejects_uninitialized_storage(qapp):
    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = None

    with pytest.raises(
        RuntimeError,
        match="StorageService must be initialized",
    ):
        NovaUiBridge(CoreOrchestrator(), storage_service)


def test_first_message_generates_conversation_title(qapp):
    bridge, _, repository = create_bridge()

    with patch.object(bridge, "_process_next_request"):
        bridge.send_message(
            "Necesito configurar la persistencia de conversaciones en SQLite"
        )

    repository.update_title.assert_called_once_with(
        bridge._conversation.conversation_id,
        "Necesito configurar la persistencia de...",
    )


def test_second_message_does_not_change_conversation_title(qapp):
    bridge, _, repository = create_bridge()

    with patch.object(bridge, "_process_next_request"):
        bridge.send_message("Primer mensaje")
        bridge.send_message("Segundo mensaje")

    assert repository.update_title.call_count == 1


def test_response_stays_in_original_conversation(qapp):
    bridge, _, repository = create_bridge()
    original = bridge._conversation
    original_id = original.conversation_id
    repository.get.return_value = original

    with patch.object(bridge, "_process_next_request"):
        bridge.send_message("Mensaje de prueba")

    request = bridge._request_queue.dequeue()

    # El usuario cambia de conversación mientras la respuesta está pendiente.
    bridge._conversation = Conversation()
    new_id = bridge._conversation.conversation_id

    bridge._on_request_completed(request, Result.ok("Respuesta"))

    assistant_call = repository.add_message.call_args

    assert assistant_call.args[0] == original_id
    assert assistant_call.args[0] != new_id
    assert assistant_call.args[1].role.value == "assistant"


def test_response_is_skipped_if_conversation_was_deleted(qapp):
    bridge, _, repository = create_bridge()

    with patch.object(bridge, "_process_next_request"):
        bridge.send_message("Mensaje de prueba")

    request = bridge._request_queue.dequeue()

    # La conversación original ya no existe.
    repository.get.return_value = None

    bridge._on_request_completed(request, Result.ok("Respuesta"))

    # Solo se guardó el mensaje del usuario, no una respuesta huérfana.
    assert repository.add_message.call_count == 1
    assert request.status == RequestStatus.FAILED


def test_request_runs_in_a_thread_and_the_answer_is_saved(qapp):
    bridge, core, repository = create_bridge()
    core.register_command(
        "chat.generate",
        lambda command: Result.ok("Hola, Jefe."),
    )
    repository.get.return_value = bridge._conversation

    try:
        bridge.send_message("Hola")

        assert wait_until(lambda: bridge._active_thread is None)
        assert bridge.messages == [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola, Jefe."},
        ]
        assert core.state == NovaState.IDLE
    finally:
        bridge.shutdown()


def test_failed_request_in_a_thread_shows_error(qapp):
    # Sin controlador registrado: el Core responde COMMAND_NOT_FOUND.
    bridge, core, _ = create_bridge()

    try:
        with patch("nova.ui.qml.bridge.QTimer.singleShot"):
            bridge.send_message("Hola")

            assert wait_until(lambda: bridge._active_thread is None)

        assert bridge.messages[-1]["role"] == "error"
        assert core.state == NovaState.ERROR
    finally:
        bridge.shutdown()


def test_shutdown_waits_for_the_active_request(qapp):
    bridge, core, repository = create_bridge()
    release = threading.Event()

    def slow(command):
        release.wait(5)
        return Result.ok("tarde")

    core.register_command("chat.generate", slow)

    bridge.send_message("Hola")

    assert bridge._active_thread is not None

    release.set()
    bridge.shutdown()

    assert bridge._active_thread is None

    # Las señales tardías se ignoran: no se guarda la respuesta ni falla nada.
    QCoreApplication.processEvents()

    assert repository.add_message.call_count == 1


def test_shutdown_is_safe_without_active_request_and_repeatable(qapp):
    bridge, _, _ = create_bridge()

    bridge.shutdown()
    bridge.shutdown()


def test_messages_are_ignored_after_shutdown(qapp):
    bridge, _, repository = create_bridge()

    bridge.shutdown()
    bridge.send_message("Hola")

    repository.add_message.assert_not_called()