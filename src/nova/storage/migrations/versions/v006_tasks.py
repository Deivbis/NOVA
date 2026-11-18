import sqlite3

from nova.storage.exceptions import MigrationError

VERSION = 6


def apply(connection: sqlite3.Connection) -> None:
    try:
        connection.execute(
            """
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                due_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'done', 'cancelled', 'fired')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX idx_tasks_due ON tasks(status, due_at)"
        )
        connection.execute(
            """
            CREATE TABLE routines (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                steps TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    except sqlite3.Error as exc:
        raise MigrationError("Unable to apply tasks migration.") from exc