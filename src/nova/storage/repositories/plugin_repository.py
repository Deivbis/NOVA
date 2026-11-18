import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PluginRepository:
    """Estado de plugins. Los permisos viven en `permissions` (kind=plugin)."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def set_enabled(self, plugin_id: str, version: str, enabled: bool) -> None:
        try:
            with write_transaction(self.connection):
                stamp = _now()
                self.connection.execute(
                    "INSERT INTO plugins "
                    "(id, version, enabled, installed_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET "
                    "version = excluded.version, enabled = excluded.enabled, "
                    "updated_at = excluded.updated_at",
                    (plugin_id, version, int(enabled), stamp, stamp),
                )
                self._audit(
                    "plugin.enabled" if enabled else "plugin.disabled"
                )
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save plugin state.") from exc

    def is_enabled(self, plugin_id: str) -> bool:
        try:
            row = self.connection.execute(
                "SELECT enabled FROM plugins WHERE id = ?", (plugin_id,)
            ).fetchone()

            return bool(row["enabled"]) if row else False
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to read plugin state.") from exc

    def enabled_ids(self) -> list[str]:
        try:
            rows = self.connection.execute(
                "SELECT id FROM plugins WHERE enabled = 1 ORDER BY id"
            ).fetchall()

            return [str(r["id"]) for r in rows]
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to list plugins.") from exc

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
            "VALUES (?, ?, 'plugin', ?, 'plugin', ?)",
            (str(uuid4()), action, str(uuid4()), _now()),
        )