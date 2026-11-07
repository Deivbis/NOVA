import sqlite3

from nova.storage.exceptions import MigrationError


VERSION = 1


def apply(connection: sqlite3.Connection) -> None:
    """Create the initial application state table."""
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

    except sqlite3.Error as exc:
        raise MigrationError(
            "Unable to apply initial migration."
        ) from exc