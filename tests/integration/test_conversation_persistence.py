from pathlib import Path

from nova.core import CoreOrchestrator
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge


def create_bridge(database_path: Path):
    storage_service = StorageService(
        database_path
    )

    storage_service.initialize()

    bridge = NovaUiBridge(
        CoreOrchestrator(),
        storage_service,
    )

    return bridge, storage_service


def test_conversation_survives_restart(
    tmp_path,
):
    database_path = (
        tmp_path / "nova.db"
    )

    # -------------------------------------------------
    # Primera ejecución
    # -------------------------------------------------

    bridge, storage_service = (
        create_bridge(database_path)
    )

    bridge.send_message(
        "Mensaje persistente"
    )

    assert bridge.messages == [
        {
            "role": "user",
            "content": "Mensaje persistente",
        }
    ]

    storage_service.close()

    # -------------------------------------------------
    # Segunda ejecución
    # -------------------------------------------------

    bridge, storage_service = (
        create_bridge(database_path)
    )

    assert bridge.messages == [
        {
            "role": "user",
            "content": "Mensaje persistente",
        }
    ]

    storage_service.close()