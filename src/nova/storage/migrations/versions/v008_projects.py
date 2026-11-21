import sqlite3

from nova.storage.exceptions import MigrationError

VERSION = 8


def apply(connection: sqlite3.Connection) -> None:
    try:
        connection.execute(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'paused', 'done')),
                progress INTEGER NOT NULL DEFAULT 0
                    CHECK (progress BETWEEN 0 AND 100),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX idx_projects_status ON projects(status, created_at)"
        )
    except sqlite3.Error as exc:
        raise MigrationError("Unable to apply projects migration.") from exc