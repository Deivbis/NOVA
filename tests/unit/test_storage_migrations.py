
import sqlite3
import pytest
from nova.storage.manager import StorageManager
from nova.storage.migrations.runner import MigrationRunner
from nova.storage.migrations.versions import (
    v001_initial,
    v002_conversations,
    v003_memories,
)


def test_initial_migration_creates_schema(tmp_path) -> None:
    database = tmp_path / "nova.db"
    connection = sqlite3.connect(database)
    runner = MigrationRunner(connection)

    assert runner.current_version() == 0

    v001_initial.apply(connection)
    runner.set_version(v001_initial.VERSION)

    assert runner.current_version() == 1

    table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'app_state'
        """
    ).fetchone()

    assert table is not None
    connection.close()


def test_conversation_migration_creates_tables(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "nova.db")

    v001_initial.apply(connection)
    v002_conversations.apply(connection)

    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )
    }

    assert "app_state" in tables
    assert "conversations" in tables
    assert "conversation_messages" in tables

    connection.close()


def test_conversation_messages_have_cascade_delete(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "nova.db")
    connection.execute("PRAGMA foreign_keys = ON")

    v001_initial.apply(connection)
    v002_conversations.apply(connection)

    connection.execute(
        """
        INSERT INTO conversations (
            id, title, created_at, updated_at
        )
        VALUES ('conversation-1', 'Prueba', '2026-10-02', '2026-10-02')
        """
    )

    connection.execute(
        """
        INSERT INTO conversation_messages (
            id, conversation_id, role, content, created_at
        )
        VALUES (
            'message-1',
            'conversation-1',
            'user',
            'Hola',
            '2026-10-02'
        )
        """
    )

    connection.commit()

    connection.execute(
        "DELETE FROM conversations WHERE id = ?",
        ("conversation-1",),
    )
    connection.commit()

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM conversation_messages
        WHERE conversation_id = ?
        """,
        ("conversation-1",),
    ).fetchone()[0]

    assert count == 0
    connection.close()

def test_failed_migration_rolls_back_changes_and_closes_connection(
    tmp_path,
    monkeypatch,
) -> None:
    class FailingMigration:
        VERSION = 1

        def apply(self, connection: sqlite3.Connection) -> None:
            connection.execute(
                """
                CREATE TABLE partial_migration_table (
                    id INTEGER PRIMARY KEY
                )
                """
            )

            raise RuntimeError("Simulated migration failure.")

    database_path = tmp_path / "nova.db"
    manager = StorageManager(database_path)

    monkeypatch.setattr(
        StorageManager,
        "MIGRATIONS",
        (FailingMigration(),),
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated migration failure.",
    ):
        manager.initialize()

    assert manager.initialized is False
    assert manager.database_connection._connection is None

    connection = sqlite3.connect(database_path)

    table = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'partial_migration_table'
        """
    ).fetchone()

    version = connection.execute(
        """
        SELECT version
        FROM schema_metadata
        WHERE id = 1
        """
    ).fetchone()

    assert table is None
    assert version is None

    connection.close()



def test_memory_migration_creates_tables(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "nova.db")

    v001_initial.apply(connection)
    v002_conversations.apply(connection)
    v003_memories.apply(connection)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    assert "memories" in tables
    assert "audit_logs" in tables

    connection.close()