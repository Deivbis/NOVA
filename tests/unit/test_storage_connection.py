from pathlib import Path

from nova.storage.connection import DatabaseConnection


def test_database_connection_creates_database(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"

    connection = DatabaseConnection(database_path)

    connection.connect()

    assert database_path.exists()

    connection.close()


def test_database_uses_wal(tmp_path: Path) -> None:
    database_path = tmp_path / "nova.db"

    connection = DatabaseConnection(database_path)

    connection.connect()

    mode = connection.connection.execute(
        "PRAGMA journal_mode;"
    ).fetchone()[0]

    assert mode.lower() == "wal"

    connection.close()