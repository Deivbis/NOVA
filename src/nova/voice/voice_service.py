"""Servicio de voz de salida (SPEC-008, D-011, D-016, D-018).

Habla las respuestas de NOVA fuera del hilo de la interfaz, con el estado
SPEAKING mientras dura, eventos de voz y cancelación inmediata.

Privacidad (SPEC-014 §9): ni el log ni los eventos contienen el texto
hablado.
"""

import dataclasses
import threading
from collections.abc import Callable
from typing import Any

from nova.core.events import Event, EventNames
from nova.core.identity import Identity
from nova.core.logging_setup import get_logger
from nova.core.orchestrator import CoreOrchestrator
from nova.core.result import Failure
from nova.core.state import NovaState
from nova.voice.audio_player import AudioPlayer
from nova.voice.settings import VoiceSettings
from nova.voice.tts_router import TTSRouter

logger = get_logger(__name__)

SHUTDOWN_JOIN_SECONDS = 2.0


class VoiceService:
    """Habla las respuestas de NOVA con la voz de la identidad activa."""

    def __init__(
        self,
        core: CoreOrchestrator,
        router: TTSRouter,
        player: AudioPlayer,
        settings: VoiceSettings,
        save_settings: Callable[[VoiceSettings], None] | None = None,
        thread_factory: Callable[..., Any] = threading.Thread,
    ) -> None:
        self._core = core
        self._router = router
        self._player = player
        self._settings = settings
        self._save_settings = save_settings
        self._thread_factory = thread_factory

        self._lock = threading.Lock()
        self._synthesis_lock = threading.Lock()
        self._generation = 0
        self._speaking = False
        self._closed = False
        self._thread: Any = None

        self._router.prefer_online = settings.prefer_online

    @property
    def settings(self) -> VoiceSettings:
        return self._settings

    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._speaking

    def speak(self, text: str) -> bool:
        """Habla el texto sin bloquear. Reemplaza lo que esté sonando.

        Devuelve False si la voz está apagada, el texto está vacío o el
        servicio ya se cerró.
        """
        message = text.strip()

        with self._lock:
            if self._closed or not self._settings.enabled or not message:
                return False

            self._generation += 1
            generation = self._generation
            interrupting = self._speaking
            self._speaking = True
            identity = self._settings.identity

        if interrupting:
            self._player.stop()

        self._core.set_state(NovaState.SPEAKING)

        thread = self._thread_factory(
            target=self._run,
            args=(generation, message, identity),
            name="nova-voice",
            daemon=True,
        )
        self._thread = thread
        thread.start()

        return True

    def stop(self) -> None:
        """Corta de inmediato lo que esté sonando."""
        with self._lock:
            if not self._speaking:
                return

            self._generation += 1
            self._speaking = False

        self._player.stop()

        if self._core.state == NovaState.SPEAKING:
            self._core.set_state(NovaState.IDLE)

        self._publish(
            EventNames.VOICE_SPEAKING_FINISHED,
            {"cancelled": True},
        )

    def update_settings(
        self,
        *,
        enabled: bool | None = None,
        identity: Identity | None = None,
        prefer_online: bool | None = None,
    ) -> None:
        """Cambia las preferencias de voz y las guarda."""
        changes = {
            key: value
            for key, value in (
                ("enabled", enabled),
                ("identity", identity),
                ("prefer_online", prefer_online),
            )
            if value is not None
        }

        if not changes:
            return

        self._settings = dataclasses.replace(self._settings, **changes)
        self._router.prefer_online = self._settings.prefer_online

        if not self._settings.enabled:
            self.stop()

        if self._save_settings is not None:
            try:
                self._save_settings(self._settings)
            except Exception:
                logger.exception(
                    "No se pudieron guardar las preferencias de voz."
                )

    def shutdown(self) -> None:
        """Detiene la voz y rechaza nuevas peticiones."""
        with self._lock:
            self._closed = True
            self._generation += 1
            self._speaking = False

        self._player.stop()

        thread = self._thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=SHUTDOWN_JOIN_SECONDS)

    def _run(
        self,
        generation: int,
        text: str,
        identity: Identity,
    ) -> None:
        try:
            with self._synthesis_lock:
                if self._is_stale(generation):
                    return

                synthesized = self._router.synthesize(text, identity)

            if self._is_stale(generation):
                return

            if not synthesized.success:
                self._publish_error(synthesized.error)
                return

            audio = synthesized.value

            self._publish(
                EventNames.VOICE_SPEAKING_STARTED,
                {
                    "provider": audio.provider,
                    "identity": identity.value,
                    "seconds": round(audio.duration_seconds, 1),
                },
            )

            played = self._player.play(audio)

            if self._is_stale(generation):
                return

            if not played.success:
                self._publish_error(played.error)

        except Exception:
            logger.exception("Fallo inesperado en el servicio de voz.")

            if not self._is_stale(generation):
                self._publish_error(
                    Failure(
                        code="VOICE_UNEXPECTED_ERROR",
                        message="Ocurrió un error inesperado al hablar.",
                    )
                )

        finally:
            self._finish(generation)

    def _is_stale(self, generation: int) -> bool:
        with self._lock:
            return generation != self._generation

    def _finish(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation:
                # Una voz más reciente (o un stop) se encarga del estado.
                return

            self._speaking = False

        if self._core.state == NovaState.SPEAKING:
            self._core.set_state(NovaState.IDLE)

        self._publish(EventNames.VOICE_SPEAKING_FINISHED, {})

    def _publish_error(self, error: Failure | None) -> None:
        code = error.code if error else "UNKNOWN"
        message = error.message if error else "Error de voz desconocido."

        logger.warning("Error de voz: %s", code)

        self._publish(
            EventNames.VOICE_ERROR,
            {"code": code, "message": message, "direction": "output"},
        )

    def _publish(self, name: str, payload: dict[str, Any]) -> None:
        self._core.publish(
            Event(name=name, payload=payload, source="voice")
        )