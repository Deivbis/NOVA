
import sqlite3
from unittest.mock import MagicMock

import pytest

from nova.storage.exceptions import TransactionError
from nova.storage.transaction import Transaction


def create_connection():
    connection = sqlite3.connect(":memory:")

    connection.execute(
        "CREATE TABLE test_items (value TEXT)"
    )

    return connection


def test_transaction_commits_successful_operation():
    connection = create_connection()

    with Transaction(connection):
        connection.execute(
            "INSERT INTO test_items VALUES (?)",
            ("saved",),
        )

    row = connection.execute(
        "SELECT value FROM test_items"
    ).fetchone()

    assert row == ("saved",)

    connection.close()


def test_transaction_rolls_back_failed_operation():
    connection = create_connection()

    with pytest.raises(ValueError):
        with Transaction(connection):
            connection.execute(
                "INSERT INTO test_items VALUES (?)",
                ("not_saved",),
            )

            raise ValueError("Simulated failure")

    row = connection.execute(
        "SELECT value FROM test_items"
    ).fetchone()

    assert row is None

    connection.close()


def test_transaction_begin_failure():
    connection = create_connection()

    connection.execute("BEGIN")

    with pytest.raises(TransactionError):
        with Transaction(connection):
            pass

    connection.rollback()
    connection.close()


def test_transaction_commit_failure_attempts_rollback():
    connection = MagicMock(spec=sqlite3.Connection)

    connection.execute.return_value = None

    connection.commit.side_effect = sqlite3.OperationalError(
        "Simulated commit failure"
    )

    transaction = Transaction(connection)

    with pytest.raises(TransactionError):
        with transaction:
            pass

    connection.execute.assert_called_once_with("BEGIN")
    connection.commit.assert_called_once()
    connection.rollback.assert_called_once()


def test_transaction_commit_and_rollback_failure():
    connection = MagicMock(spec=sqlite3.Connection)

    connection.commit.side_effect = sqlite3.OperationalError(
        "Simulated commit failure"
    )

    connection.rollback.side_effect = sqlite3.OperationalError(
        "Simulated rollback failure"
    )

    transaction = Transaction(connection)

    with pytest.raises(TransactionError) as exc_info:
        with transaction:
            pass

    error_message = str(exc_info.value)

    assert "Commit error" in error_message
    assert "Rollback error" in error_message

    connection.rollback.assert_called_once()


def test_transaction_operation_and_rollback_failure():
    connection = MagicMock(spec=sqlite3.Connection)

    connection.rollback.side_effect = sqlite3.OperationalError(
        "Simulated rollback failure"
    )

    transaction = Transaction(connection)

    with pytest.raises(TransactionError) as exc_info:
        with transaction:
            raise ValueError("Simulated operation failure")

    error_message = str(exc_info.value)

    assert "Original error" in error_message
    assert "Rollback error" in error_message

    connection.rollback.assert_called_once()