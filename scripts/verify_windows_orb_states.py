
from __future__ import annotations

from pathlib import Path
import os
import sys
import tempfile

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from nova.core import CoreOrchestrator, NovaState
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge
from nova.ui.qml.windows_orb import WindowsOrbController


def main() -> int:
    pyside_path = (
        Path(sys.executable).parent.parent
        / "Lib"
        / "site-packages"
        / "PySide6"
    )

    dll_directory = os.add_dll_directory(
        str(pyside_path)
    )

    temporary_directory = tempfile.TemporaryDirectory(
        prefix="nova-orb-test-"
    )

    storage_service = StorageService(
        Path(temporary_directory.name) / "nova.db"
    )

    storage_initialized = False

    try:
        print(
            "Iniciando prueba Windows Orb...",
            flush=True,
        )

        app = QGuiApplication(sys.argv)

        orchestrator = CoreOrchestrator()

        storage_service.initialize()
        storage_initialized = True

        bridge = NovaUiBridge(
            orchestrator,
            storage_service,
        )

        engine = QQmlApplicationEngine()

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

    finally:
        if storage_initialized:
            storage_service.close()

        temporary_directory.cleanup()
        dll_directory.close()


if __name__ == "__main__":
    raise SystemExit(main())
