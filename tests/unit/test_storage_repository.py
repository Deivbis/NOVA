import sqlite3

from nova.storage.repositories.system_repository import (
    SystemRepository,
)


def test_system_repository_persists_value(tmp_path) -> None:
    database = tmp_path / "nova.db"

    connection = sqlite3.connect(database)

    connection.execute(
        """
        CREATE TABLE app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    repository = SystemRepository(connection)

    repository.set_value("test_key", "hello")

    assert repository.get_value("test_key") == "hello"

    connection.close()