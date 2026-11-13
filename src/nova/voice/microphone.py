"""Grabación del micrófono con fin de frase automático (D-013, D-016).

El audio nunca se guarda en disco: vive en memoria y se descarta tras
transcribirlo.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.voice.contracts import AudioData
from nova.voice.end_of_speech import (
    Decision,
    EndOfSpeechConfig,
    EndOfSpeechDetector,
)

logger = get_logger(__name__)

SAMPLE_RATE = 16000

_REASONS = {
    Decision.SPEECH_ENDED: "speech_ended",
    Decision.NO_SPEECH: "no_speech",
    Decision.MAX_DURATION: "max_duration",
}


@dataclass(frozen=True)
class RecordingResult:
    audio: AudioData | None
    reason: str
    seconds: float
    peak_rms: float
    noise_floor: float = 0.0


def _default_stream_factory(device: int | str | None) -> Any:
    import sounddevice

    return sounddevice.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        device=device,
    )


class MicrophoneRecorder:
    """Graba hasta que dejas de hablar, se cancela o se agota el tiempo."""

    def __init__(
        self,
        device: int | str | None = None,
        config: EndOfSpeechConfig | None = None,
        stream_factory: Callable[[int | str | None], Any] | None = None,
    ) -> None:
        self._device = device
        self._config = config or EndOfSpeechConfig()
        self._stream_factory = stream_factory or _default_stream_factory

    def record(
        self,
        cancel_event: threading.Event,
    ) -> Result[RecordingResult]:
        import numpy as np

        detector = EndOfSpeechDetector(self._config)
        frame_size = int(SAMPLE_RATE * self._config.frame_seconds)
        chunks: list[bytes] = []
        reason = "cancelled"

        try:
            with self._stream_factory(self._device) as stream:
                while not cancel_event.is_set():
                    data, _overflowed = stream.read(frame_size)
                    samples = np.asarray(data, dtype=np.int16).reshape(-1)
                    chunks.append(samples.tobytes())

                    normalized = samples.astype(np.float32) / 32768.0
                    rms = float(np.sqrt(np.mean(normalized**2)))

                    decision = detector.feed(rms)

                    if decision != Decision.CONTINUE:
                        reason = _REASONS[decision]
                        break

        except Exception:
            logger.exception("No se pudo grabar del micrófono.")
            return Result.fail(
                code="MICROPHONE_ERROR",
                message=(
                    "No se pudo abrir el micrófono. Revisa los permisos de "
                    "privacidad de Windows y el dispositivo de entrada."
                ),
            )

        audio = None

        if reason in ("speech_ended", "max_duration") and detector.speech_started:
            audio = AudioData(
                pcm=b"".join(chunks),
                sample_rate=SAMPLE_RATE,
                channels=1,
                provider="microphone",
            )

        return Result.ok(
            RecordingResult(
                audio=audio,
                reason=reason,
                seconds=len(chunks) * self._config.frame_seconds,
                peak_rms=detector.peak_rms,
                noise_floor=detector.noise_floor,
            )
        )