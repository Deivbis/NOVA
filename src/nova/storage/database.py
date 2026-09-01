import sqlite3

from nova.storage.connection import DatabaseConnection
from nova.storage.exceptions import DatabaseIntegrityError


class Database:
    """Provides database-level operations."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def initialize(self) -> sqlite3.Connection:
        return self.connection.connect()

    def health_check(self) -> bool:
        try:
            result = self.connection.connection.execute(
                "PRAGMA integrity_check;"
            ).fetchone()

            return result[0] == "ok"

        except sqlite3.Error as exc:
            raise DatabaseIntegrityError(
                "Database integrity check failed."
            ) from exc

    def journal_mode(self) -> str:
        result = self.connection.connection.execute(
            "PRAGMA journal_mode;"
        ).fetchone()

        return result[0]

    def close(self) -> None:
        self.connection.close()