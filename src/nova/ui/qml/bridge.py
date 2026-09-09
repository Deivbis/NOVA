from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal

from nova.core import CoreOrchestrator
from nova.ui.state import UIState


class NovaUiBridge(QObject):
    """Bridge between NOVA Core state and the QML visual layer."""

    orbStateChanged = Signal()

    def __init__(
        self,
        orchestrator: CoreOrchestrator,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._orchestrator = orchestrator
        self._ui_state = UIState.from_core(
            orchestrator.state,
            orchestrator.connectivity,
        )

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._refresh_state)
        self._timer.start()

    def _refresh_state(self) -> None:
        ui_state = UIState.from_core(
            self._orchestrator.state,
            self._orchestrator.connectivity,
        )

        if ui_state == self._ui_state:
            return

        previous_orb_state = self._ui_state.orb_state

        self._ui_state = ui_state

        if ui_state.orb_state != previous_orb_state:
            self.orbStateChanged.emit()

    def _get_orb_state(self) -> str:
        return self._ui_state.orb_state.value

    orbState = Property(
        str,
        _get_orb_state,
        notify=orbStateChanged,
    )