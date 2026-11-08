from pathlib import Path
import os
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from nova.ai import LocalAIService
from nova.core import CoreOrchestrator
from nova.storage.paths import default_database_path
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge
from nova.ui.qml.windows_orb import WindowsOrbController


def main() -> int:
    from PySide6 import __file__ as pyside_init

    pyside_path = Path(pyside_init).resolve().parent
    dll_directory = (
        os.add_dll_directory(str(pyside_path))
        if pyside_path.is_dir()
        else None
    )
    storage_service = None
    storage_closed = False

    def close_storage() -> None:
        nonlocal storage_closed

        if storage_service is not None and not storage_closed:
            storage_closed = True
            storage_service.close()

    try:
        app = QGuiApplication(sys.argv)

        storage_service = StorageService(
            default_database_path()
        )

        app.aboutToQuit.connect(close_storage)

        try:
            storage_service.initialize()

            orchestrator = CoreOrchestrator()
            orchestrator.start()

            local_ai_service = LocalAIService()

            orchestrator.register_command(
                "chat.generate",
                local_ai_service.handle,
            )

            bridge = NovaUiBridge(
                orchestrator,
                storage_service,
            )

            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty(
                "novaBridge",
                bridge,
            )

            qml_path = Path(__file__).parent
            main_qml = qml_path / "Main.qml"
            permanent_orb_qml = qml_path / "PermanentOrb.qml"

            # Cargar primero la ventana principal.
            engine.load(main_qml.as_uri())

            if not engine.rootObjects():
                return 1

            # Cargar después el Orbe permanente.
            engine.load(permanent_orb_qml.as_uri())

            if len(engine.rootObjects()) < 2:
                return 1

            permanent_orb = next(
                (
                    obj
                    for obj in engine.rootObjects()
                    if obj.objectName() == "PermanentOrb"
                ),
                None,
            )

            if permanent_orb is None:
                return 1

            orb_controller = WindowsOrbController(
                permanent_orb,
            )

            bridge.orbStateChanged.connect(
                lambda: orb_controller.set_orb_state(
                    bridge.orbState
                )
            )

            app.installNativeEventFilter(
                orb_controller.native_filter,
            )

            return app.exec()

        finally:
            close_storage()

    finally:
        if dll_directory is not None:
            dll_directory.close()


if __name__ == "__main__":
    raise SystemExit(main())
