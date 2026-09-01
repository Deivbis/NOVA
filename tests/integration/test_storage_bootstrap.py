from nova.storage.service import StorageService


def test_storage_bootstrap(tmp_path) -> None:
    database_path = tmp_path / "database" / "nova.db"

    storage = StorageService(database_path)

    storage.initialize()

    assert database_path.exists()
    assert storage.manager.initialized

    storage.set_system_value(
        "startup",
        "complete",
    )

    assert storage.get_system_value(
        "startup"
    ) == "complete"

    storage.close()