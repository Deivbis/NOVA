
from pathlib import Path
import os
import sys
import tempfile

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from nova.storage.service import StorageService
from nova.core import CoreOrchestrator, NovaState
from nova.ui.qml.bridge import NovaUiBridge


STATES = [
    NovaState.IDLE,
    NovaState.LISTENING,
    NovaState.PROCESSING,
    NovaState.SPEAKING,
    NovaState.ERROR,
]


def main() -> int:
    pyside_path = (
        Path(sys.executable).parent.parent
        / "Lib"
        / "site-packages"
        / "PySide6"
    )

    dll_directory = os.add_dll_directory(str(pyside_path))

    app = QGuiApplication(sys.argv)

    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "nova.db"

        storage_service = StorageService(database_path)
        bridge = None

        try:
            storage_service.initialize()

            orchestrator = CoreOrchestrator()

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
                Path(__file__).parent.parent
                / "src"
                / "nova"
                / "ui"
                / "qml"
            )

            engine.load((qml_path / "Main.qml").as_uri())
            engine.load((qml_path / "PermanentOrb.qml").as_uri())

            if not engine.rootObjects():
                print("ERROR: No se pudieron cargar los archivos QML.")
                return 1

            print("Interfaz QML cargada correctamente.")

            def verify_states(index: int = 0) -> None:
                if index >= len(STATES):
                    print("Verificacion de estados finalizada.")
                    app.quit()
                    return

                state = STATES[index]

                print(f"Verificando estado: {state.name}")

                changed = orchestrator.set_state(state)

                if not changed:
                    print(
                        f"ERROR: Transición no permitida hacia {state.name}. "
                        f"Estado actual: {orchestrator.state.name}"
                    )
                    app.quit()
                    return

                QTimer.singleShot(
                    1000,
                    lambda: verify_states(index + 1),
                )

            QTimer.singleShot(0, verify_states)

            return app.exec()

        finally:
            if bridge is not None:
                bridge.shutdown()

            storage_service.close()

    dll_directory.close()


if __name__ == "__main__":
    raise SystemExit(main())
