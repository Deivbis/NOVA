import sqlite3

from nova.storage.exceptions import MigrationError


VERSION = 2


def apply(connection: sqlite3.Connection) -> None:
    """Create persistent conversation and message tables."""
    try:
        connection.execute(
            """
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE conversation_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX idx_conversation_messages_order
            ON conversation_messages(
                conversation_id,
                created_at,
                id
            )
            """
        )

    except sqlite3.Error as exc:
        raise MigrationError(
            "Unable to apply conversation migration."
        ) from exc