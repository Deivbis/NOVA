from pathlib import Path
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from nova.core import CoreOrchestrator, NovaState
from nova.ui.qml.bridge import NovaUiBridge


STATES = [
    NovaState.IDLE,
    NovaState.LISTENING,
    NovaState.PROCESSING,
    NovaState.RESPONDING,
    NovaState.ERROR,
]


def main() -> int:
    pyside_path = (
        Path(sys.executable).parent.parent
        / "Lib"
        / "site-packages"
        / "PySide6"
    )

    os.add_dll_directory(str(pyside_path))

    app = QGuiApplication(sys.argv)

    orchestrator = CoreOrchestrator()
    bridge = NovaUiBridge(orchestrator)

    engine = QQmlApplicationEngine()

    engine.rootContext().setContextProperty(
        "novaBridge",
        bridge,
    )

    qml_path = Path(__file__).parent.parent / "src" / "nova" / "ui" / "qml"

    engine.load((qml_path / "Main.qml").as_uri())
    engine.load((qml_path / "PermanentOrb.qml").as_uri())

    if not engine.rootObjects():
        print("❌ No se pudieron cargar las ventanas QML.")
        return 1

    index = 0

    def next_state() -> None:
        nonlocal index

        state = STATES[index]
        orchestrator.set_state(state)
        bridge._refresh_state()

        print(
            f"Estado Core: {state.value:<20} "
            f"→ Orbe: {bridge.orbState}"
        )

        index += 1

        if index >= len(STATES):
            finish_timer.start()
        else:
            state_timer.start()

    def finish() -> None:
        orchestrator.set_state(NovaState.IDLE)
        bridge._refresh_state()

        print("Estado final: idle → orbe: idle")
        print("✅ Prueba de estados QML completada.")
        app.quit()

    state_timer = QTimer()
    state_timer.setSingleShot(True)
    state_timer.timeout.connect(next_state)

    finish_timer = QTimer()
    finish_timer.setSingleShot(True)
    finish_timer.timeout.connect(finish)

    state_timer.start(1000)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())