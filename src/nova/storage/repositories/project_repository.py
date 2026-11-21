import sqlite3
from datetime import datetime, timezone
from uuid import UUID, uuid4

from nova.core.projects import Project, ProjectStatus
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction

_COLS = "id, name, description, status, progress, created_at, updated_at"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectRepository:
    """Proyectos. La auditoría no guarda nombre ni descripción."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, project: Project) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    f"INSERT INTO projects ({_COLS}) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(project.project_id),
                        project.name,
                        project.description,
                        project.status.value,
                        project.progress,
                        project.created_at.isoformat(),
                        project.updated_at.isoformat(),
                    ),
                )
                self._audit("project.created", project.project_id)
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save project.") from exc

    def get(self, project_id: UUID) -> Project | None:
        rows = self._query("WHERE id = ?", (str(project_id),))

        return rows[0] if rows else None

    def list_all(self) -> list[Project]:
        return self._query("ORDER BY created_at ASC, id ASC")

    def update(self, project: Project) -> bool:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "UPDATE projects SET name = ?, description = ?, "
                    "status = ?, progress = ?, updated_at = ? WHERE id = ?",
                    (
                        project.name,
                        project.description,
                        project.status.value,
                        project.progress,
                        project.updated_at.isoformat(),
                        str(project.project_id),
                    ),
                )

                if cursor.rowcount != 1:
                    return False

                self._audit("project.updated", project.project_id)

                return True
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to update project.") from exc

    def delete(self, project_id: UUID) -> bool:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "DELETE FROM projects WHERE id = ?", (str(project_id),)
                )

                if cursor.rowcount != 1:
                    return False

                self._audit("project.deleted", project_id)

                return True
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to delete project.") from exc

    def _query(self, tail: str, params: tuple = ()) -> list[Project]:
        try:
            rows = self.connection.execute(
                f"SELECT {_COLS} FROM projects {tail}", params
            ).fetchall()

            return [
                Project(
                    project_id=UUID(str(r["id"])),
                    name=str(r["name"]),
                    description=str(r["description"]),
                    status=ProjectStatus(str(r["status"])),
                    progress=int(r["progress"]),
                    created_at=datetime.fromisoformat(str(r["created_at"])),
                    updated_at=datetime.fromisoformat(str(r["updated_at"])),
                )
                for r in rows
            ]
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to read projects.") from exc

    def _audit(self, action: str, project_id: UUID) -> None:
        self.connection.execute(
            "INSERT INTO audit_logs "
            "(id, action, target_type, target_id, detail, created_at) "
            "VALUES (?, ?, 'project', ?, '', ?)",
            (str(uuid4()), action, str(project_id), _now()),
        )