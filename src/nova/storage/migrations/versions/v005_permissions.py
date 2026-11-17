import sqlite3

from nova.storage.exceptions import MigrationError

VERSION = 5


def apply(connection: sqlite3.Connection) -> None:
    try:
        connection.execute(
            """
            CREATE TABLE permissions (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (kind, key)
            )
            """
        )
    except sqlite3.Error as exc:
        raise MigrationError(
            "Unable to apply permissions migration."
        ) from exc