import sqlite3

from nova.storage.exceptions import TransactionError


class Transaction:
    """Context manager for SQLite transactions."""

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
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
        if exc_type is not None:
            try:
                self.connection.rollback()

            except sqlite3.Error as rollback_error:
                raise TransactionError(
                    "The operation failed and rollback also failed. "
                    f"Original error: {exc_value!r}. "
                    f"Rollback error: {rollback_error!r}."
                ) from exc_value

            return False

        try:
            self.connection.commit()
            return False

        except sqlite3.Error as commit_error:
            try:
                self.connection.rollback()

            except sqlite3.Error as rollback_error:
                raise TransactionError(
                    "Commit failed and rollback also failed. "
                    f"Commit error: {commit_error!r}. "
                    f"Rollback error: {rollback_error!r}."
                ) from commit_error

            raise TransactionError(
                "Unable to commit transaction."
            ) from commit_error