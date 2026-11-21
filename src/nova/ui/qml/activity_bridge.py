"""Puente de la actividad del Dashboard hacia QML (contexto: novaActivity)."""

from PySide6.QtCore import QObject, Slot

from nova.activity import ActivityService
from nova.ui.activity_panel import ActivityPanel


class ActivityUiBridge(QObject):
    def __init__(
        self, service: ActivityService, parent: QObject | None = None
    ) -> None:
        if parent is not None and not isinstance(parent, QObject):
            parent = None

        super().__init__(parent)
        self._panel = ActivityPanel(service)

    @Slot(int, result="QVariantMap")
    def recent(self, days: int) -> dict:
        return self._panel.recent(days)