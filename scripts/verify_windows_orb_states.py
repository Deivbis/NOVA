from __future__ import annotations

from pathlib import Path
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from nova.core import CoreOrchestrator, NovaState
from nova.ui.qml.bridge import NovaUiBridge
from nova.ui.qml.windows_orb import WindowsOrbController


def main() -> int:
    pyside_path = (
        Path(sys.executable).parent.parent
        / "Lib"
        / "site-packages"
        / "PySide6"
    )

    os.add_dll_directory(str(pyside_path))

    print("Iniciando prueba Windows Orb...", flush=True)

    app = QGuiApplication(sys.argv)

    orchestrator = CoreOrchestrator()
    bridge = NovaUiBridge(orchestrator)

    engine = QQmlApplicationEngine()

    # El bridge debe existir en el contexto raíz
    # antes de cargar cualquier QML que lo utilice.
    engine.rootContext().setContextProperty(
        "novaBridge",
        bridge,
    )

    qml_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "nova"
        / "ui"
        / "qml"
    )

    main_qml = qml_path / "Main.qml"
    permanent_qml = qml_path / "PermanentOrb.qml"

    print(
        f"Main QML: {main_qml}",
        flush=True,
    )

    print(
        f"Permanent QML: {permanent_qml}",
        flush=True,
    )

    engine.load(main_qml.as_uri())

    if not engine.rootObjects():
        print(
            "ERROR: Main.qml no creó objetos.",
            flush=True,
        )
        return 1

    engine.load(permanent_qml.as_uri())

    permanent_orb = None

    for obj in engine.rootObjects():
        if obj.objectName() == "PermanentOrb":
            permanent_orb = obj
            break

    if permanent_orb is None:
        print(
            "ERROR: No se encontró PermanentOrb.",
            flush=True,
        )
        return 1

    print(
        f"HWND del Orbe: {int(permanent_orb.winId())}",
        flush=True,
    )

    controller = WindowsOrbController(
        permanent_orb,
    )

    app.installNativeEventFilter(
        controller.native_filter,
    )

    states = [
        NovaState.IDLE,
        NovaState.LISTENING,
        NovaState.PROCESSING,
        NovaState.RESPONDING,
        NovaState.ERROR,
        NovaState.IDLE,
    ]

    index = 0

    def run_next_state() -> None:
        nonlocal index

        if index >= len(states):
            print(
                "Prueba completada. Cerrando NOVA.",
                flush=True,
            )

            QTimer.singleShot(
                500,
                app.quit,
            )

            return

        state = states[index]

        orchestrator.set_state(state)

        bridge._refresh_state()

        controller.set_orb_state(
            bridge.orbState,
        )

        print(
            f"Core: {state.value:<20}"
            f" | Orbe: {bridge.orbState:<12}"
            f" | Click-through: "
            f"{controller.is_idle()}",
            flush=True,
        )

        index += 1

        QTimer.singleShot(
            2000,
            run_next_state,
        )

    print(
        "Ventanas cargadas. Comienza la secuencia...",
        flush=True,
    )

    QTimer.singleShot(
        500,
        run_next_state,
    )

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())