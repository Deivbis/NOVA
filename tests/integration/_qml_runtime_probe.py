import sys
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
    QUrl,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


qml_messages = []


def message_handler(msg_type, context, message):
    if msg_type in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg):
        qml_messages.append(message)


class FakeBridge(QObject):
    orbStateChanged = Signal()
    conversationChanged = Signal()
    conversationsChanged = Signal()
    voiceSettingsChanged = Signal()
    voiceErrorRaised = Signal(str)
    voiceTranscriptReady = Signal(str)
    identityChanged = Signal()
    streamChunk = Signal(str, str)
    requestFinished = Signal(str)
    localReply = Signal()
    navigateRequested = Signal(int)
    voiceProviderRaised = Signal(str)
    userNameChanged = Signal()
    permanentOrbChanged = Signal()
    pluginMainCall = Signal(object)

    def __init__(self):
        super().__init__()
        self.current_page = None
        self._orb_state = "idle"
        self._permanent_orb_enabled = False

    def get_orb_state(self):
        return self._orb_state

    def get_permanent_orb_enabled(self):
        return self._permanent_orb_enabled
    
    @Slot(str)
    def set_orb_state(self, state):
        self._orb_state = state
        self.orbStateChanged.emit()

    @Slot(bool)
    def set_permanent_orb(self, enabled):
        self._permanent_orb_enabled = enabled
        self.permanentOrbChanged.emit()

    orbState = Property(
        str,
        get_orb_state,
        notify=orbStateChanged,
    )

    permanentOrbEnabled = Property(
        bool,
        get_permanent_orb_enabled,
        notify=permanentOrbChanged,
    )
    userName = Property(str, lambda self: "Prueba", notify=userNameChanged)

    voiceEnabled = Property(
        bool, lambda self: False, notify=voiceSettingsChanged
    )
    voiceIdentity = Property(
        str, lambda self: "atlas", notify=voiceSettingsChanged
    )
    voiceOnline = Property(
        bool, lambda self: False, notify=voiceSettingsChanged
    )
    voiceStatus = Property(
        str, lambda self: "Desactivada", notify=voiceSettingsChanged
    )
    activeIdentity = Property(
        str, lambda self: "default", notify=identityChanged
    )
    messages = Property("QVariantList", lambda self: [])
    conversations = Property("QVariantList", lambda self: [])
    activeConversationId = Property(str, lambda self: "")
    chatMessages = Property("QVariantList", lambda self: [])
    chatList = Property("QVariantList", lambda self: [])

    @Slot(int)
    def set_current_page(self, page):
        self.current_page = page

    @Slot(str, result=bool)
    def is_busy(self, request_id):
        return False

    @Slot(str)
    def load_conversation(self, conversation_id):
        pass

    @Slot()
    def new_conversation(self):
        pass

    @Slot(str, str)
    def rename_conversation(self, conversation_id, name):
        pass

    @Slot(str, result=bool)
    def delete_conversation(self, conversation_id):
        return True

    @Slot(str)
    def send_message(self, message):
        pass

    @Slot(str)
    def start_conversation_with(self, message):
        pass

    @Slot()
    def toggle_voice_input(self):
        pass

    @Slot()
    def stop_speaking(self):
        pass

    @Slot(bool)
    def set_voice_enabled(self, enabled):
        pass

    @Slot(str)
    def set_voice_identity(self, identity):
        pass

    @Slot(bool)
    def set_online_voice(self, enabled):
        pass

    @Slot()
    def test_voice(self):
        pass

class FakeMemoryBridge(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()

    maxChars = Property(int, lambda self: 10000, constant=True)

    categories = Property(
        "QVariantList",
        lambda self: [
            "Programación",
            "Juegos",
            "Música",
            "Trabajo",
            "Estudios",
            "Salud",
            "Rutinas",
            "Familia",
            "Amigos",
            "Proyectos",
            "General",
        ],
        constant=True,
    )

    @Slot(result="QVariantMap")
    def overview(self):
        return {
            "total": 0,
            "learned": 0,
            "forgotten": 0,
            "categories": [],
        }

    @Slot(str, str, str, bool, result="QVariantList")
    def search(self, query, category, view, newest_first):
        return []

    @Slot(str, str, result="QVariantMap")
    def add(self, content, category):
        return {"ok": True, "id": "test-memory"}

    @Slot(str, str, str, result="QVariantMap")
    def update(self, memory_id, content, category):
        return {"ok": True, "id": memory_id}

    @Slot(str, result="QVariantMap")
    def forget(self, memory_id):
        return {"ok": True}

    @Slot(str, result="QVariantMap")
    def reactivate(self, memory_id):
        return {"ok": True}

    @Slot(str, result="QVariantMap")
    def purge(self, memory_id):
        return {"ok": True}


class FakeMetrics(QObject):
    cpu = Property(float, lambda self: 0.0)
    ram = Property(float, lambda self: 0.0)
    disk = Property(float, lambda self: 0.0)
    net = Property(float, lambda self: 0.0)

    cpuHistory = Property("QVariantList", lambda self: [])
    ramHistory = Property("QVariantList", lambda self: [])
    diskHistory = Property("QVariantList", lambda self: [])
    netHistory = Property("QVariantList", lambda self: [])

    sysUptime = Property(str, lambda self: "-")
    sysProcs = Property(str, lambda self: "-")
    sysCores = Property(str, lambda self: "-")
    sysRam = Property(str, lambda self: "-")


def main():
    qInstallMessageHandler(message_handler)

    app = QGuiApplication([])
    bridge = FakeBridge()
    metrics = FakeMetrics()
    memory_bridge = FakeMemoryBridge()
    engine = QQmlApplicationEngine()

    qml_dir = Path(__file__).resolve().parents[2] / "src" / "nova" / "ui" / "qml"

    engine.rootContext().setContextProperty("novaBridge", bridge)
    engine.rootContext().setContextProperty("systemMetrics", metrics)
    engine.rootContext().setContextProperty("novaMemory", memory_bridge)

    main_qml = qml_dir / "Main.qml"
    orb_qml = qml_dir / "PermanentOrb.qml"

    engine.load(QUrl.fromLocalFile(str(main_qml)))

    if not engine.rootObjects():
        raise RuntimeError("Main.qml no creó ningún objeto raíz")

    engine.load(QUrl.fromLocalFile(str(orb_qml)))

    if len(engine.rootObjects()) < 2:
        raise RuntimeError("PermanentOrb.qml no creó su ventana")

    main_window = engine.rootObjects()[0]
    orb_window = next(
        (
            obj for obj in engine.rootObjects()
            if obj.objectName() == "PermanentOrb"
        ),
        None,
    )

    if orb_window is None:
        raise RuntimeError("No se encontró la ventana PermanentOrb")

    if orb_window.property("visible") is not False:
        raise RuntimeError(
            "El orbe permanente debería iniciar oculto"
        )

    bridge.set_permanent_orb(True)
    app.processEvents()

    if orb_window.property("visible") is not True:
        raise RuntimeError(
            "El orbe permanente no se mostró al activarlo"
        )

    bridge.set_permanent_orb(False)
    app.processEvents()

    if orb_window.property("visible") is not False:
        raise RuntimeError(
            "El orbe permanente no se ocultó al desactivarlo"
        )

    if main_window.property("title") != "NOVA":
        raise RuntimeError("El título de la ventana principal no es NOVA")

    bridge.navigateRequested.emit(4)
    app.processEvents()

    if bridge.current_page != 4:
        raise RuntimeError(
            f"La navegación no llegó al bridge: {bridge.current_page}"
        )

    app.processEvents()

    serious_errors = [
        message for message in qml_messages
        if any(
            term in message.lower()
            for term in (
                "cannot read property",
                "referenceerror",
                "typeerror",
                "failed to load",
                "unable to assign",
                "is not a function",
            )
        )
    ]

    if serious_errors:
        raise RuntimeError(
            "Se detectaron errores QML:\n" + "\n".join(serious_errors)
        )

    print("QML_RUNTIME_OK")
    print(f"Ventanas cargadas: {len(engine.rootObjects())}")
    print(f"Título: {main_window.property('title')}")
    print(f"Página recibida por el bridge: {bridge.current_page}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"QML_RUNTIME_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
