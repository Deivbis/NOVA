import sqlite3

from nova.storage.exceptions import MigrationError


class MigrationRunner:
    """Runs database migrations in order."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def ensure_metadata_table(self) -> None:
        try:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_metadata (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            self.connection.commit()

        except sqlite3.Error as exc:
            raise MigrationError(
                "Unable to create schema metadata table."
            ) from exc

    def current_version(self) -> int:
        self.ensure_metadata_table()

        row = self.connection.execute(
            "SELECT version FROM schema_metadata WHERE id = 1"
        ).fetchone()

        if row is None:
            return 0

        return int(row[0])

    def set_version(self, version: int) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        self.connection.execute(
            """
            INSERT INTO schema_metadata (
                id,
                version,
                created_at,
                updated_at
            )
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id)
            DO UPDATE SET
                version = excluded.version,
                updated_at = excluded.updated_at
            """,
            (version, now, now),
        )

        self.connection.commit()