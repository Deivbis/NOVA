import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PermissionRepository:
    """Permisos concedidos. La auditoría guarda solo el tipo de acción."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def has(self, kind: str, key: str) -> bool:
        try:
            row = self.connection.execute(
                "SELECT 1 FROM permissions WHERE kind = ? AND key = ?",
                (kind, key),
            ).fetchone()

            return row is not None
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to read permissions.") from exc

    def add(self, kind: str, key: str) -> None:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "INSERT OR IGNORE INTO permissions "
                    "(id, kind, key, created_at) VALUES (?, ?, ?, ?)",
                    (str(uuid4()), kind, key, _now()),
                )

                if cursor.rowcount == 1:
                    self._audit("permission.granted", kind)
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save permission.") from exc

    def remove(self, kind: str, key: str) -> bool:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "DELETE FROM permissions WHERE kind = ? AND key = ?",
                    (kind, key),
                )

                if cursor.rowcount != 1:
                    return False

                self._audit("permission.revoked", kind)

                return True
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to remove permission.") from exc

    def list_permissions(self) -> list[tuple[str, str]]:
        try:
            rows = self.connection.execute(
                "SELECT kind, key FROM permissions "
                "ORDER BY created_at ASC, id ASC"
            ).fetchall()

            return [(str(r["kind"]), str(r["key"])) for r in rows]
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to list permissions.") from exc

    def audit(self, action: str, detail: str) -> None:
        try:
            with write_transaction(self.connection):
                self._audit(action, detail)
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to write audit log.") from exc

    def _audit(self, action: str, detail: str) -> None:
        self.connection.execute(
            "INSERT INTO audit_logs "
            "(id, action, target_type, target_id, detail, created_at) "
            "VALUES (?, ?, 'automation', ?, ?, ?)",
            (str(uuid4()), action, str(uuid4()), detail, _now()),
        )