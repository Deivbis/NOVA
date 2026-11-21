from datetime import datetime, timezone
from uuid import UUID

from nova.core.projects import Project, ProjectStatus
from nova.core.result import Result
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.project_repository import ProjectRepository

MAX_NAME = 80
MAX_DESCRIPTION = 300


def _clean(name: str, description: str) -> tuple[str, str, str]:
    name = " ".join(name.split())
    description = " ".join(description.split())

    if not name:
        return name, description, "El proyecto necesita un nombre."

    if len(name) > MAX_NAME:
        return name, description, f"El nombre admite {MAX_NAME} caracteres."

    if len(description) > MAX_DESCRIPTION:
        return name, description, (
            f"La descripción admite {MAX_DESCRIPTION} caracteres."
        )

    return name, description, ""


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def list_projects(self) -> Result[list[Project]]:
        try:
            return Result.ok(self._repository.list_all())
        except RepositoryError:
            return Result.fail(
                "PROJECT_READ", "No se pudieron leer los proyectos."
            )

    def create(self, name: str, description: str = "") -> Result[Project]:
        name, description, error = _clean(name, description)

        if error:
            return Result.fail("PROJECT_INVALID", error)

        project = Project(name=name, description=description)

        try:
            self._repository.add(project)
        except RepositoryError:
            return Result.fail(
                "PROJECT_SAVE", "No se pudo guardar el proyecto."
            )

        return Result.ok(project)

    def update(
        self,
        project_id: UUID,
        name: str,
        description: str,
        status: ProjectStatus,
        progress: int,
    ) -> Result[Project]:
        name, description, error = _clean(name, description)

        if error:
            return Result.fail("PROJECT_INVALID", error)

        try:
            project = self._repository.get(project_id)

            if project is None:
                return Result.fail(
                    "PROJECT_NOT_FOUND", "Ese proyecto ya no existe."
                )

            project.name = name
            project.description = description
            project.status = status
            project.progress = (
                100 if status == ProjectStatus.DONE
                else max(0, min(100, int(progress)))
            )
            project.updated_at = datetime.now(timezone.utc)

            if not self._repository.update(project):
                return Result.fail(
                    "PROJECT_NOT_FOUND", "Ese proyecto ya no existe."
                )
        except RepositoryError:
            return Result.fail(
                "PROJECT_SAVE", "No se pudo guardar el proyecto."
            )

        return Result.ok(project)

    def delete(self, project_id: UUID) -> Result[None]:
        try:
            if not self._repository.delete(project_id):
                return Result.fail(
                    "PROJECT_NOT_FOUND", "Ese proyecto ya no existe."
                )
        except RepositoryError:
            return Result.fail(
                "PROJECT_SAVE", "No se pudo borrar el proyecto."
            )

        return Result.ok()