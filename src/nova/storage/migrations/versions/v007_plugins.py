import sqlite3

from nova.storage.exceptions import MigrationError

VERSION = 7


def apply(connection: sqlite3.Connection) -> None:
    try:
        connection.execute(
            """
            CREATE TABLE plugins (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0
                    CHECK (enabled IN (0, 1)),
                installed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
    except sqlite3.Error as exc:
        raise MigrationError("Unable to apply plugins migration.") from exc