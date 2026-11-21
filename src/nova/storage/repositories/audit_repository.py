import sqlite3

from nova.storage.exceptions import RepositoryError

_HIDDEN = "action != 'memory.read'"


class AuditRepository:
    """Lectura de la auditoría para el Dashboard."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def recent(self, since: str, limit: int) -> list[tuple[str, str]]:
        try:
            rows = self.connection.execute(
                "SELECT action, created_at FROM audit_logs "
                f"WHERE created_at >= ? AND {_HIDDEN} "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                (since, limit),
            ).fetchall()

            return [(str(r["action"]), str(r["created_at"])) for r in rows]
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to read activity.") from exc

    def count(self, since: str) -> int:
        try:
            row = self.connection.execute(
                "SELECT COUNT(*) AS n FROM audit_logs "
                f"WHERE created_at >= ? AND {_HIDDEN}",
                (since,),
            ).fetchone()

            return int(row["n"])
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to count activity.") from exc