import sqlite3
from pathlib import Path

from nova.storage.exceptions import DatabaseConnectionError


class DatabaseConnection:
    """Manages SQLite connections for NOVA."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection

        try:
            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            connection = sqlite3.connect(
                self.database_path,
                timeout=10.0,
            )

            connection.row_factory = sqlite3.Row

            connection.execute("PRAGMA foreign_keys = ON;")

            journal_mode = connection.execute(
                "PRAGMA journal_mode = WAL;"
            ).fetchone()[0]

            if journal_mode.lower() != "wal":
                connection.close()
                raise DatabaseConnectionError(
                    f"Unable to enable WAL mode. Current mode: {journal_mode}"
                )

            self._connection = connection

            return connection

        except DatabaseConnectionError:
            raise

        except sqlite3.Error as exc:
            raise DatabaseConnectionError(
                f"Unable to connect to database: {self.database_path}"
            ) from exc

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            return self.connect()

        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None