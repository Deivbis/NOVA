from pathlib import Path
import os
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from nova.ai import LocalAIService
from nova.core import Capability
from nova.core.logging_setup import get_logger, setup_logging
from nova.main import create_configuration, create_core
from nova.storage.paths import (
    default_database_path,
    default_logs_dir,
    default_voices_dir,
)
from nova.storage.service import StorageService
from nova.ui.qml.bridge import NovaUiBridge
from nova.ui.qml.hotkey_filter import HotkeyFilter
from nova.ui.qml.windows_orb import WindowsOrbController
from nova.voice import (
    EdgeTTSProvider,
    FasterWhisperSTT,
    GlobalHotkey,
    MicrophoneRecorder,
    PiperTTSProvider,
    SoundDevicePlayer,
    TTSRouter,
    VoiceInputService,
    VoiceService,
    load_voice_settings,
    save_voice_settings,
)
from nova.personality import IdentityService

logger = get_logger(__name__)


def main() -> int:
    from PySide6 import __file__ as pyside_init

    pyside_path = Path(pyside_init).resolve().parent
    dll_directory = (
        os.add_dll_directory(str(pyside_path))
        if pyside_path.is_dir()
        else None
    )

    storage_service = None
    orchestrator = None
    bridge = None
    hotkey = None
    shut_down = False

    def shutdown() -> None:
        """Cierra en orden: atajo, interfaz, Core y base de datos."""
        nonlocal shut_down

        if shut_down:
            return

        shut_down = True

        if hotkey is not None:
            hotkey.unregister()

        if bridge is not None:
            bridge.shutdown()

        if orchestrator is not None:
            orchestrator.stop()

        if storage_service is not None:
            storage_service.close()

    try:
        app = QGuiApplication(sys.argv)

        try:
            config = create_configuration().initialize()
        except Exception:
            setup_logging(default_logs_dir())
            logger.exception("No se pudo cargar la configuración de NOVA.")
            return 1

        setup_logging(default_logs_dir(), debug=config.execution.debug)
        logger.info(
            "NOVA %s iniciando (interfaz de escritorio).",
            config.nova.version,
        )

        storage_service = StorageService(
            default_database_path()
        )

        app.aboutToQuit.connect(shutdown)

        try:
            storage_service.initialize()

            orchestrator = create_core()

            local_ai_service = LocalAIService()

            orchestrator.capabilities.register(
                Capability(
                    id="chat.local",
                    name="Conversación local",
                    description="Conversación con el modelo local (Ollama).",
                    provider="ollama",
                )
            )
            orchestrator.capabilities.register(
                Capability(
                    id="voice.output",
                    name="Voz de salida",
                    description=(
                        "Síntesis de voz local (Piper) y en línea "
                        "(edge-tts, opcional)."
                    ),
                    provider="piper",
                )
            )
            orchestrator.capabilities.register(
                Capability(
                    id="voice.input",
                    name="Entrada de voz",
                    description="Reconocimiento de voz local (faster-whisper).",
                    provider="faster-whisper",
                )
            )
            orchestrator.register_command(
                "chat.generate",
                local_ai_service.handle,
            )

            voice_settings = load_voice_settings()
            voice_service = VoiceService(
                core=orchestrator,
                router=TTSRouter(
                    local=PiperTTSProvider(default_voices_dir()),
                    online=EdgeTTSProvider(),
                    prefer_online=voice_settings.prefer_online,
                    connectivity=lambda: orchestrator.connectivity,
                ),
                player=SoundDevicePlayer(),
                settings=voice_settings,
                save_settings=save_voice_settings,
            )
            voice_input = VoiceInputService(
                core=orchestrator,
                recorder=MicrophoneRecorder(),
                stt=FasterWhisperSTT(
                    vocabulary=voice_settings.vocabulary,
                ),
                voice_output=voice_service,
            )
            identity_service = IdentityService(
                core=orchestrator,
                get_identity=lambda: voice_service.settings.identity,
                set_identity=lambda identity: voice_service.update_settings(
                    identity=identity
                ),
            )

            bridge = NovaUiBridge(
                orchestrator,
                storage_service,
                voice_service,
                voice_input,
                identity_service,
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

            if voice_settings.enabled:
                hotkey = GlobalHotkey()
                registered = hotkey.register(voice_settings.hotkey)

                if registered.success:
                    hotkey_filter = HotkeyFilter(bridge.toggle_voice_input)
                    app.installNativeEventFilter(hotkey_filter)
                    logger.info(
                        "Atajo de voz registrado: %s",
                        voice_settings.hotkey,
                    )
                else:
                    logger.warning(
                        "Atajo de voz no disponible: %s",
                        registered.error.code,
                    )

            logger.info("Interfaz iniciada.")

            return app.exec()

        except Exception:
            logger.exception("Fallo durante el arranque de la interfaz.")
            return 1

        finally:
            shutdown()

    finally:
        if dll_directory is not None:
            dll_directory.close()


if __name__ == "__main__":
    raise SystemExit(main())