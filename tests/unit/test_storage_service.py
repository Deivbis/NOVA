from nova.storage.service import StorageService


def test_storage_service_persists_data(tmp_path) -> None:
    database_path = tmp_path / "nova.db"

    service = StorageService(database_path)

    service.initialize()

    service.set_system_value(
        "test",
        "NOVA",
    )

    assert service.get_system_value("test") == "NOVA"

    service.close()