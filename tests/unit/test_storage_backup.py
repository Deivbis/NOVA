import sqlite3

from nova.storage.backup.manager import BackupManager


def test_backup_creates_database_copy(tmp_path) -> None:
    database_path = tmp_path / "nova.db"
    backup_directory = tmp_path / "backups"

    connection = sqlite3.connect(database_path)

    connection.execute(
        """
        CREATE TABLE test (
            id INTEGER PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    connection.execute(
        "INSERT INTO test(value) VALUES (?)",
        ("NOVA",),
    )

    connection.commit()
    connection.close()

    manager = BackupManager(
        database_path,
        backup_directory,
    )

    backup = manager.create_backup()

    assert backup.exists()

    backup_connection = sqlite3.connect(backup)

    value = backup_connection.execute(
        "SELECT value FROM test"
    ).fetchone()[0]

    assert value == "NOVA"

    backup_connection.close()