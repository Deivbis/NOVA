import sqlite3
from contextlib import contextmanager
from typing import Iterator
from uuid import uuid4

from nova.storage.exceptions import RepositoryError


@contextmanager
def write_transaction(connection: sqlite3.Connection) -> Iterator[None]:
    """Run repository writes atomically without breaking outer transactions.

    Uses a savepoint when another transaction is already active.
    """
    savepoint = f"nova_repo_{uuid4().hex}"
    owns_transaction = not connection.in_transaction

    try:
        if owns_transaction:
            connection.execute("BEGIN")
        else:
            connection.execute(f"SAVEPOINT {savepoint}")

        yield

        if owns_transaction:
            connection.commit()
        else:
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")

    except Exception:
        try:
            if owns_transaction:
                connection.rollback()
            else:
                connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        except sqlite3.Error as rollback_error:
            raise RepositoryError(
                "Unable to rollback repository transaction."
            ) from rollback_error

        raise