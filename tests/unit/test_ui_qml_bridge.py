from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from nova.core import CoreOrchestrator
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge


@pytest.fixture
def qapp():
    application = QCoreApplication.instance()

    if application is None:
        application = QCoreApplication([])

    return application


def create_storage_service(repository):
    storage_service = MagicMock(
        spec=StorageService
    )

    storage_service.conversation_repository = (
        repository
    )

    return storage_service


def test_bridge_creates_initial_conversation(
    qapp,
):
    repository = MagicMock()

    repository.list_conversations.return_value = []

    storage_service = create_storage_service(
        repository
    )

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    repository.create.assert_called_once()

    assert bridge.messages == []


def test_bridge_rejects_uninitialized_storage(
    qapp,
):
    storage_service = MagicMock(
        spec=StorageService
    )

    storage_service.conversation_repository = None

    with pytest.raises(
        RuntimeError,
        match="StorageService must be initialized",
    ):
        NovaUiBridge(
            CoreOrchestrator(),
            storage_service,
        )

def test_first_message_generates_conversation_title(qapp):
    repository = MagicMock()

    repository.list_conversations.return_value = []

    storage_service = create_storage_service(
        repository
    )

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    bridge.send_message(
        "Necesito configurar la persistencia de conversaciones en SQLite"
    )

    repository.update_title.assert_called_once_with(
        bridge._conversation.conversation_id,
        "Necesito configurar la persistencia de...",
    )

def test_second_message_does_not_change_conversation_title(
    qapp,
):
    repository = MagicMock()

    repository.list_conversations.return_value = []

    storage_service = create_storage_service(
        repository
    )

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    bridge.send_message("Primer mensaje")
    bridge.send_message("Segundo mensaje")

    assert repository.update_title.call_count == 1


def test_delayed_response_stays_in_original_conversation(
    qapp,
    monkeypatch,
):
    from nova.core import Conversation
    from nova.ui.qml import bridge as bridge_module

    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = create_storage_service(repository)

    scheduled_callbacks = []

    monkeypatch.setattr(
        bridge_module.QTimer,
        "singleShot",
        lambda delay, callback: scheduled_callbacks.append(
            (delay, callback)
        ),
    )

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    original_conversation = bridge._conversation
    original_id = original_conversation.conversation_id
    repository.get.return_value = original_conversation

    bridge.send_message("Mensaje de prueba")

    assert len(scheduled_callbacks) == 1

    # Simular que el usuario cambia de conversación.
    bridge._conversation = Conversation()
    new_conversation_id = bridge._conversation.conversation_id

    # Ejecutar la respuesta pendiente.
    scheduled_callbacks[0][1]()

    # La respuesta debe pertenecer a la conversación original.
    assistant_call = repository.add_message.call_args

    assert assistant_call.args[0] == original_id
    assert assistant_call.args[0] != new_conversation_id
    assert assistant_call.args[1].role.value == "assistant"


def test_delayed_response_is_skipped_if_conversation_was_deleted(
    qapp,
    monkeypatch,
):
    from nova.ui.qml import bridge as bridge_module

    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = create_storage_service(repository)

    scheduled_callbacks = []

    monkeypatch.setattr(
        bridge_module.QTimer,
        "singleShot",
        lambda delay, callback: scheduled_callbacks.append(
            (delay, callback)
        ),
    )

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    bridge.send_message("Mensaje de prueba")

    # Simular que la conversación original ya no existe.
    repository.get.return_value = None

    scheduled_callbacks[0][1]()

    # No debe intentar guardar una respuesta huérfana.
    assert repository.add_message.call_count == 1
