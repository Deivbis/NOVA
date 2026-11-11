from pathlib import Path
from unittest.mock import patch

from nova.core import CoreOrchestrator
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge


def create_bridge(database_path: Path):
    storage_service = StorageService(database_path)
    storage_service.initialize()

    core = CoreOrchestrator()
    core.start()

    bridge = NovaUiBridge(core, storage_service)

    return bridge, storage_service


def test_conversation_survives_restart(qapp, tmp_path):
    database_path = tmp_path / "nova.db"
    expected = [{"role": "user", "content": "Mensaje persistente"}]

    # Primera ejecución
    bridge, storage_service = create_bridge(database_path)

    with patch.object(bridge, "_process_next_request"):
        bridge.send_message("Mensaje persistente")

    assert bridge.messages == expected

    bridge.shutdown()
    storage_service.close()

    # Segunda ejecución
    bridge, storage_service = create_bridge(database_path)

    assert bridge.messages == expected

    bridge.shutdown()
    storage_service.close()