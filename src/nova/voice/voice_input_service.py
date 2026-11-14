"""Servicio de entrada de voz: escuchar, transcribir y entregar (D-013).

Privacidad (SPEC-014 §9, D-016): ni el log ni los eventos contienen lo que
dijiste; la transcripción solo viaja por el callback on_transcript.
"""

import threading
from collections.abc import Callable
from typing import Any, Protocol

from nova.core.events import Event, EventNames
from nova.core.logging_setup import get_logger
from nova.core.orchestrator import CoreOrchestrator
from nova.core.result import Failure
from nova.core.state import NovaState
from nova.voice.contracts import STTProvider
from nova.voice.microphone import MicrophoneRecorder

logger = get_logger(__name__)

SHUTDOWN_JOIN_SECONDS = 2.0
STARTABLE_STATES = frozenset(
    {NovaState.IDLE, NovaState.OFFLINE, NovaState.ERROR}
)


class SpeechOutput(Protocol):
    @property
    def is_speaking(self) -> bool: ...

    def stop(self) -> None: ...


class VoiceInputService:
    """Escucha el micrófono y entrega lo que dices como texto."""

    def __init__(
        self,
        core: CoreOrchestrator,
        recorder: MicrophoneRecorder,
        stt: STTProvider,
        voice_output: SpeechOutput | None = None,
        on_transcript: Callable[[str], None] | None = None,
        thread_factory: Callable[..., Any] = threading.Thread,
    ) -> None:
        self._core = core
        self._recorder = recorder
        self._stt = stt
        self._voice_output = voice_output
        self.on_transcript = on_transcript
        self._thread_factory = thread_factory

        self._lock = threading.Lock()
        self._generation = 0
        self._active = False
        self._closed = False
        self._cancel_event = threading.Event()
        self._thread: Any = None

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    def toggle(self) -> str:
        """Una pulsación: cancela, interrumpe la voz o empieza a escuchar."""
        if self.is_active:
            self.cancel()
            return "cancelled"

        if self._voice_output is not None and self._voice_output.is_speaking:
            self._voice_output.stop()
            return "stopped_speaking"

        return "started" if self.start_listening() else "ignored"

    def start_listening(self) -> bool:
        if self._core.state not in STARTABLE_STATES:
            logger.info(
                "Escucha ignorada: NOVA está en estado '%s'.",
                self._core.state.value,
            )
            return False

        with self._lock:
            if self._closed or self._active:
                return False

            self._generation += 1
            generation = self._generation
            self._active = True
            cancel_event = threading.Event()
            self._cancel_event = cancel_event

        if self._core.state == NovaState.ERROR:
            self._core.set_state(NovaState.IDLE)

        self._core.set_state(NovaState.LISTENING)
        self._publish(EventNames.VOICE_LISTENING_STARTED, {})

        thread = self._thread_factory(
            target=self._run,
            args=(generation, cancel_event),
            name="nova-listen",
            daemon=True,
        )
        self._thread = thread
        thread.start()

        return True

    def cancel(self) -> None:
        """Cancela la escucha o la transcripción en curso."""
        with self._lock:
            if not self._active:
                return

            self._generation += 1
            self._active = False
            cancel_event = self._cancel_event

        cancel_event.set()

        if self._core.state in (NovaState.LISTENING, NovaState.PROCESSING):
            self._core.set_state(NovaState.IDLE)

        self._publish(
            EventNames.VOICE_LISTENING_STOPPED,
            {"reason": "cancelled"},
        )

    def shutdown(self) -> None:
        with self._lock:
            self._closed = True

        self.cancel()

        thread = self._thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=SHUTDOWN_JOIN_SECONDS)

        close = getattr(self._stt, "shutdown", None)

        if callable(close):
            close()

    def _run(
        self,
        generation: int,
        cancel_event: threading.Event,
    ) -> None:
        delivered = False

        try:
            recorded = self._recorder.record(cancel_event)

            if self._is_stale(generation):
                return

            if not recorded.success:
                self._publish_error(recorded.error)
                return

            recording = recorded.value

            self._publish(
                EventNames.VOICE_LISTENING_STOPPED,
                {
                    "reason": recording.reason,
                    "seconds": round(recording.seconds, 1),
                },
            )

            if recording.audio is None:
                self._publish_error(
                    Failure(
                        code="NO_SPEECH_DETECTED",
                        message=(
                            "No detecté voz. Pulsa de nuevo y habla con "
                            "claridad."
                        ),
                    )
                )
                return

            self._core.set_state(NovaState.PROCESSING)

            transcript = self._stt.transcribe(recording.audio)

            if self._is_stale(generation):
                return

            if not transcript.success:
                self._publish_error(transcript.error)
                return

            delivered = self._deliver(transcript.value)

        except Exception:
            logger.exception("Fallo inesperado en la entrada de voz.")

            if not self._is_stale(generation):
                self._publish_error(
                    Failure(
                        code="VOICE_INPUT_UNEXPECTED_ERROR",
                        message="Ocurrió un error inesperado al escucharte.",
                    )
                )

        finally:
            self._finish(generation, delivered)

    def _deliver(self, text: str) -> bool:
        handler = self.on_transcript

        if handler is None:
            return False

        try:
            handler(text)
        except Exception:
            logger.exception("El receptor de la transcripción falló.")
            return False

        return True

    def _is_stale(self, generation: int) -> bool:
        with self._lock:
            return generation != self._generation

    def _finish(self, generation: int, delivered: bool) -> None:
        with self._lock:
            if generation != self._generation:
                # Una cancelación o una escucha más reciente se encarga.
                return

            self._active = False

        # Si la transcripción se entregó, el receptor (el chat) toma el
        # estado desde PROCESSING; si no, se vuelve a reposo.
        if not delivered and self._core.state in (
            NovaState.LISTENING,
            NovaState.PROCESSING,
        ):
            self._core.set_state(NovaState.IDLE)

    def _publish_error(self, error: Failure | None) -> None:
        code = error.code if error else "UNKNOWN"
        message = error.message if error else "Error de voz desconocido."

        logger.warning("Error de entrada de voz: %s", code)

        self._publish(
            EventNames.VOICE_ERROR,
            {"code": code, "message": message, "direction": "input"},
        )

    def _publish(self, name: str, payload: dict[str, Any]) -> None:
        self._core.publish(
            Event(name=name, payload=payload, source="voice")
        )