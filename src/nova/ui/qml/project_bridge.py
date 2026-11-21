"""Puente de la página Proyectos hacia QML (contexto: novaProjects)."""

from PySide6.QtCore import Property, QObject, Signal, Slot

from nova.projects import ProjectService
from nova.projects.service import MAX_DESCRIPTION, MAX_NAME
from nova.ui.projects_panel import ProjectsPanel


class ProjectsUiBridge(QObject):
    changed = Signal()

    def __init__(
        self, service: ProjectService, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._panel = ProjectsPanel(service)

    maxName = Property(int, lambda self: MAX_NAME, constant=True)
    maxDescription = Property(int, lambda self: MAX_DESCRIPTION, constant=True)

    def _mutated(self, outcome: dict) -> dict:
        if outcome["ok"]:
            self.changed.emit()

        return outcome

    @Slot(str, str, result="QVariantList")
    def items(self, query: str, status: str):
        return self._panel.items(query, status)

    @Slot(str, str, result="QVariantMap")
    def create(self, name: str, description: str) -> dict:
        return self._mutated(self._panel.create(name, description))


    @Slot(str, str, result="QVariantMap")
    def update(
        self, project_id: str, name: str, description: str,
        status: str, progress: int,
    ) -> dict:
        return self._mutated(
            self._panel.update(project_id, name, description, status, progress)
        )

    @Slot(str, result="QVariantMap")
    def delete(self, project_id: str) -> dict:
        return self._mutated(self._panel.delete(project_id))