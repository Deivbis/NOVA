import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RoutineRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save(self, key: str, name: str, steps: list[str]) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO routines (id, key, name, steps, created_at) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET "
                    "name = excluded.name, steps = excluded.steps",
                    (
                        str(uuid4()), key, name,
                        json.dumps(steps, ensure_ascii=False), _now(),
                    ),
                )
                self._audit("routine.saved")
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save routine.") from exc

    def get_by_key(self, key: str) -> tuple[str, list[str]] | None:
        try:
            row = self.connection.execute(
                "SELECT name, steps FROM routines WHERE key = ?", (key,)
            ).fetchone()

            return (
                (str(row["name"]), json.loads(row["steps"])) if row else None
            )
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to read routine.") from exc

    def list_routines(self) -> list[tuple[str, list[str]]]:
        try:
            rows = self.connection.execute(
                "SELECT name, steps FROM routines ORDER BY created_at ASC"
            ).fetchall()

            return [(str(r["name"]), json.loads(r["steps"])) for r in rows]
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to list routines.") from exc

    def remove(self, key: str) -> bool:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "DELETE FROM routines WHERE key = ?", (key,)
                )

                if cursor.rowcount != 1:
                    return False

                self._audit("routine.removed")

                return True
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to remove routine.") from exc

    def audit(self, action: str) -> None:
        try:
            with write_transaction(self.connection):
                self._audit(action)
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to write audit log.") from exc

    def _audit(self, action: str) -> None:
        self.connection.execute(
            "INSERT INTO audit_logs "
            "(id, action, target_type, target_id, detail, created_at) "
            "VALUES (?, ?, 'routine', ?, 'routine', ?)",
            (str(uuid4()), action, str(uuid4()), _now()),
        )