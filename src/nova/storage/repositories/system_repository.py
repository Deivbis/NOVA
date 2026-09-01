import sqlite3
from datetime import datetime, timezone

from nova.storage.exceptions import RepositoryError


class SystemRepository:
    """Repository for technical NOVA system state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def set_value(self, key: str, value: str) -> None:
        try:
            now = datetime.now(timezone.utc).isoformat()

            self.connection.execute(
                """
                INSERT INTO app_state (
                    key,
                    value,
                    updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(key)
                DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, now),
            )

            self.connection.commit()

        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Unable to save system state: {key}"
            ) from exc

    def get_value(self, key: str) -> str | None:
        try:
            row = self.connection.execute(
                """
                SELECT value
                FROM app_state
                WHERE key = ?
                """,
                (key,),
            ).fetchone()

            if row is None:
                return None

            return str(row[0])

        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Unable to read system state: {key}"
            ) from exc

    def delete_value(self, key: str) -> None:
        try:
            self.connection.execute(
                "DELETE FROM app_state WHERE key = ?",
                (key,),
            )

            self.connection.commit()

        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Unable to delete system state: {key}"
            ) from exc