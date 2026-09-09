from pathlib import Path
import os
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from nova.core import CoreOrchestrator
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

    app = QGuiApplication(sys.argv)

    orchestrator = CoreOrchestrator()

    bridge = NovaUiBridge(
        orchestrator,
    )

    engine = QQmlApplicationEngine()

    # IMPORTANTE:
    # El bridge debe estar disponible antes de cargar
    # cualquier QML que lo utilice.
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

    permanent_orb = None

    for obj in engine.rootObjects():
        if obj.objectName() == "PermanentOrb":
            permanent_orb = obj
            break

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


if __name__ == "__main__":
    raise SystemExit(main())