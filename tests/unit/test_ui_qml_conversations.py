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
    storage_service = MagicMock(spec=StorageService)
    storage_service.conversation_repository = repository
    return storage_service


def test_bridge_exposes_conversation_history(
    qapp,
):
    repository = MagicMock()

    repository.list_conversations.return_value = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "title": "Primera conversación",
            "created_at": "2026-09-01T10:00:00+00:00",
            "updated_at": "2026-09-01T10:05:00+00:00",
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "title": "Segunda conversación",
            "created_at": "2026-09-02T10:00:00+00:00",
            "updated_at": "2026-09-02T10:05:00+00:00",
        },
    ]

    repository.get.return_value = None

    storage_service = create_storage_service(repository)

    with pytest.raises(RuntimeError):
        NovaUiBridge(
            CoreOrchestrator(),
            storage_service,
        )


def test_bridge_creates_new_conversation_when_history_is_empty(
    qapp,
):
    repository = MagicMock()
    repository.list_conversations.return_value = []

    storage_service = create_storage_service(repository)

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    repository.create.assert_called_once()

    assert bridge.messages == []