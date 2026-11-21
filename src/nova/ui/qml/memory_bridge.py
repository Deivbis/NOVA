"""Puente de la página Memoria hacia QML (contexto: novaMemory)."""

from PySide6.QtCore import Property, QObject, Signal, Slot

from nova.core.memory import ALL_CATEGORIES
from nova.memory import MemoryService
from nova.memory.service import MAX_CONTENT_CHARS
from nova.ui.memory_panel import MemoryPanel


class MemoryUiBridge(QObject):
    changed = Signal()

    def __init__(
        self,
        service: MemoryService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._panel = MemoryPanel(service)

    maxChars = Property(int, lambda self: MAX_CONTENT_CHARS, constant=True)
    categories = Property(
        "QVariantList", lambda self: list(ALL_CATEGORIES), constant=True
    )

    def _mutated(self, outcome: dict) -> dict:
        if outcome["ok"]:
            self.changed.emit()

        return outcome

    @Slot(result="QVariantMap")
    def overview(self) -> dict:
        return self._panel.overview()

    @Slot(str, str, str, bool, result="QVariantList")
    def search(self, query: str, category: str, view: str, newest_first: bool):
        return self._panel.search(query, category, view, newest_first)

    @Slot(str, str, result="QVariantMap")
    def add(self, content: str, category: str) -> dict:
        return self._mutated(self._panel.add(content, category))

    @Slot(str, str, str, result="QVariantMap")
    def update(self, memory_id: str, content: str, category: str) -> dict:
        return self._mutated(self._panel.update(memory_id, content, category))

    @Slot(str, result="QVariantMap")
    def forget(self, memory_id: str) -> dict:
        return self._mutated(self._panel.forget(memory_id))

    @Slot(str, result="QVariantMap")
    def reactivate(self, memory_id: str) -> dict:
        return self._mutated(self._panel.reactivate(memory_id))

    @Slot(str, result="QVariantMap")
    def purge(self, memory_id: str) -> dict:
        return self._mutated(self._panel.purge(memory_id))
