import sqlite3
from datetime import datetime, timezone
from uuid import UUID, uuid4

from nova.core.tasks import Task, TaskStatus
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction

_COLS = "id, title, due_at, status, created_at"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskRepository:
    """Pendientes y recordatorios. La auditoría nunca guarda el título."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, task: Task) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO tasks "
                    "(id, title, due_at, status, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(task.task_id),
                        task.title,
                        task.due_at.isoformat() if task.due_at else None,
                        task.status.value,
                        task.created_at.isoformat(),
                        task.created_at.isoformat(),
                    ),
                )
                self._audit(
                    "task.created", "reminder" if task.due_at else "todo"
                )
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save task.") from exc

    def list_open(self) -> list[Task]:
        return self._query(
            "WHERE status = 'pending' "
            "ORDER BY (due_at IS NULL), due_at ASC, created_at ASC"
        )

    def due(self, before: str) -> list[Task]:
        return self._query(
            "WHERE status = 'pending' AND due_at IS NOT NULL "
            "AND due_at <= ? ORDER BY due_at ASC",
            (before,),
        )

    def set_status(self, task_id: UUID, status: TaskStatus) -> bool:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "UPDATE tasks SET status = ?, updated_at = ? "
                    "WHERE id = ? AND status = 'pending'",
                    (status.value, _now(), str(task_id)),
                )

                if cursor.rowcount != 1:
                    return False

                self._audit(f"task.{status.value}", "task")

                return True
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to update task.") from exc

    def _query(self, tail: str, params: tuple = ()) -> list[Task]:
        try:
            rows = self.connection.execute(
                f"SELECT {_COLS} FROM tasks {tail}", params
            ).fetchall()

            return [
                Task(
                    task_id=UUID(str(r["id"])),
                    title=str(r["title"]),
                    due_at=(
                        datetime.fromisoformat(str(r["due_at"]))
                        if r["due_at"]
                        else None
                    ),
                    status=TaskStatus(str(r["status"])),
                    created_at=datetime.fromisoformat(str(r["created_at"])),
                )
                for r in rows
            ]
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to read tasks.") from exc

    def _audit(self, action: str, detail: str) -> None:
        self.connection.execute(
            "INSERT INTO audit_logs "
            "(id, action, target_type, target_id, detail, created_at) "
            "VALUES (?, ?, 'task', ?, ?, ?)",
            (str(uuid4()), action, str(uuid4()), detail, _now()),
        )