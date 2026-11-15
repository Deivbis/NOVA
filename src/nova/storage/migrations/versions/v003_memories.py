import sqlite3

from nova.storage.exceptions import MigrationError


VERSION = 3


def apply(connection: sqlite3.Connection) -> None:
    """Create the persistent memory and audit tables (DOC-016)."""
    try:
        connection.execute(
            """
            CREATE TABLE memories (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_memories_status_category
            ON memories(status, category)
            """
        )

        # El registro de auditoría nunca guarda el contenido de un recuerdo.
        connection.execute(
            """
            CREATE TABLE audit_logs (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_audit_logs_created
            ON audit_logs(created_at, id)
            """
        )

    except sqlite3.Error as exc:
        raise MigrationError(
            "Unable to apply memory migration."
        ) from exc