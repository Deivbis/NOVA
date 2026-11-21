"""Lógica de la página Proyectos (Fase 10.3), sin Qt."""

from uuid import UUID

from nova.core.projects import Project, ProjectStatus
from nova.core.result import Result
from nova.projects import ProjectService
from nova.ui.time_format import friendly_time

_BANNERS = 6


def _item(p: Project) -> dict:
    return {
        "id": str(p.project_id),
        "name": p.name,
        "description": p.description,
        "status": p.status.value,
        "progress": p.progress,
        "banner": p.project_id.int % _BANNERS + 1,
        "time": friendly_time(p.updated_at),
    }


def _outcome(result: Result, project_id: str = "") -> dict:
    if result.success:
        return {"ok": True, "error": "", "id": project_id}

    message = result.error.message if result.error else "No se pudo completar."

    return {"ok": False, "error": message, "id": ""}


def _invalid(message: str) -> dict:
    return {"ok": False, "error": message, "id": ""}


class ProjectsPanel:
    def __init__(self, service: ProjectService) -> None:
        self._service = service

    def items(self, query: str, status: str) -> list[dict]:
        listed = self._service.list_projects()
        projects = listed.value if listed.success else []
        needle = query.strip().lower()

        if status:
            projects = [p for p in projects if p.status.value == status]

        if needle:
            projects = [
                p for p in projects
                if needle in p.name.lower() or needle in p.description.lower()
            ]

        return [_item(p) for p in projects]

    def create(self, name: str, description: str) -> dict:
        result = self._service.create(name, description)

        return _outcome(
            result, str(result.value.project_id) if result.success else ""
        )

    def update(
        self,
        project_id: str,
        name: str,
        description: str,
        status: str,
        progress: int,
    ) -> dict:
        try:
            pid = UUID(project_id)
            parsed = ProjectStatus(status)
        except ValueError:
            return _invalid("Proyecto no válido.")

        return _outcome(
            self._service.update(pid, name, description, parsed, progress),
            project_id,
        )

    def delete(self, project_id: str) -> dict:
        try:
            pid = UUID(project_id)
        except ValueError:
            return _invalid("Proyecto no válido.")

        return _outcome(self._service.delete(pid))