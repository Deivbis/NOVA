import sqlite3

from nova.storage.exceptions import TransactionError


class Transaction:
    """Context manager for SQLite transactions."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def __enter__(self) -> sqlite3.Connection:
        try:
            self.connection.execute("BEGIN")
            return self.connection
        except sqlite3.Error as exc:
            raise TransactionError(
                "Unable to begin transaction."
            ) from exc

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> bool:
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()

        except sqlite3.Error as exc:
            raise TransactionError(
                "Unable to finalize transaction."
            ) from exc

        return False