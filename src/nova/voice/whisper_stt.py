"""Reconocimiento de voz local con faster-whisper (D-015, D-020).

Funciona sin Internet (la primera vez descarga el modelo). Privacidad
(SPEC-014 §9): nunca se registra lo que se transcribe ni el mensaje de las
excepciones, solo su tipo.
"""

import threading
import time
from collections.abc import Callable, Sequence
from typing import Any

from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.voice.contracts import AudioData

logger = get_logger(__name__)

SAMPLE_RATE = 16000
IDLE_SECONDS = 300.0


def _load_whisper_model(model_name: str) -> Any:
    # Importación diferida: el Core no depende de faster-whisper.
    from faster_whisper import WhisperModel

    return WhisperModel(model_name, device="cpu", compute_type="int8")


class FasterWhisperSTT:
    name = "faster-whisper"
    requires_internet = False

    def __init__(
        self,
        model_name: str = "small",
        vocabulary: Sequence[str] = (),
        idle_seconds: float = IDLE_SECONDS,
        loader: Callable[[str], Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
        timer_factory: Callable[..., Any] = threading.Timer,
    ) -> None:
        self._model_name = model_name
        self._hotwords = " ".join(
            word.strip() for word in vocabulary if word.strip()
        )
        self._idle_seconds = idle_seconds
        self._loader = loader or _load_whisper_model
        self._clock = clock
        self._timer_factory = timer_factory

        self._model: Any = None
        self._last_used = 0.0
        self._timer: Any = None
        self._lock = threading.Lock()

    def transcribe(
        self,
        audio: AudioData,
        language: str = "es",
    ) -> Result[str]:
        if (
            audio.sample_rate != SAMPLE_RATE
            or audio.channels != 1
            or len(audio.pcm) < 2
            or len(audio.pcm) % 2
        ):
            return Result.fail(
                code="INVALID_AUDIO",
                message="El audio debe ser mono a 16 kHz.",
            )

        with self._lock:
            loaded = self._ensure_model()

            if not loaded.success:
                return Result.fail(
                    code=loaded.error.code,
                    message=loaded.error.message,
                )

            result = self._run(loaded.value, audio, language)
            self._last_used = self._clock()

        self._schedule_release()

        return result

    def release_if_idle(self) -> bool:
        """Libera el modelo si lleva demasiado tiempo sin usarse."""
        with self._lock:
            if self._model is None:
                return False

            if self._clock() - self._last_used < self._idle_seconds:
                return False

            self._model = None

        logger.info("Modelo de reconocimiento liberado por inactividad.")

        return True

    def shutdown(self) -> None:
        timer = self._timer

        if timer is not None:
            timer.cancel()

        with self._lock:
            self._model = None

    def _ensure_model(self) -> Result[Any]:
        if self._model is not None:
            return Result.ok(self._model)

        try:
            self._model = self._loader(self._model_name)
        except Exception as exc:
            logger.warning(
                "No se pudo cargar el modelo de reconocimiento: %s",
                type(exc).__name__,
            )
            return Result.fail(
                code="STT_MODEL_ERROR",
                message=(
                    f"No se pudo cargar el modelo de reconocimiento "
                    f"'{self._model_name}'. La primera vez necesita "
                    f"Internet para descargarlo."
                ),
            )

        logger.info(
            "Modelo de reconocimiento '%s' cargado.",
            self._model_name,
        )

        return Result.ok(self._model)

    def _run(
        self,
        model: Any,
        audio: AudioData,
        language: str,
    ) -> Result[str]:
        import numpy as np

        samples = (
            np.frombuffer(audio.pcm, dtype=np.int16).astype(np.float32)
            / 32768.0
        )

        try:
            segments, _info = model.transcribe(
                samples,
                language=language,
                vad_filter=True,
                beam_size=1,
                hotwords=self._hotwords or None,
            )
            text = " ".join(
                segment.text.strip() for segment in segments
            ).strip()

        except Exception as exc:
            logger.warning(
                "El reconocimiento de voz falló: %s",
                type(exc).__name__,
            )
            return Result.fail(
                code="STT_ERROR",
                message="No se pudo transcribir el audio.",
            )

        if not text:
            return Result.fail(
                code="NO_SPEECH_DETECTED",
                message="No detecté voz en el audio.",
            )

        return Result.ok(text)

    def _schedule_release(self) -> None:
        previous = self._timer

        if previous is not None:
            previous.cancel()

        timer = self._timer_factory(self._idle_seconds, self.release_if_idle)
        timer.daemon = True
        timer.start()
        self._timer = timer