"""Reproducción de audio por la salida predeterminada (SPEC-008)."""

from typing import Any, Protocol

from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.voice.contracts import AudioData

logger = get_logger(__name__)


class AudioPlayer(Protocol):
    """Reproduce audio. play() bloquea hasta terminar o hasta stop()."""

    def play(self, audio: AudioData) -> Result[None]: ...

    def stop(self) -> None: ...


class SoundDevicePlayer:
    """Reproductor basado en sounddevice (importado solo al usarlo)."""

    def __init__(self, backend: Any | None = None) -> None:
        self._backend = backend

    def _sounddevice(self) -> Any:
        if self._backend is None:
            import sounddevice

            self._backend = sounddevice

        return self._backend

    def play(self, audio: AudioData) -> Result[None]:
        try:
            import numpy as np

            samples = np.frombuffer(audio.pcm, dtype=np.int16)

            if audio.channels > 1:
                samples = samples.reshape(-1, audio.channels)

            backend = self._sounddevice()
            backend.play(samples, samplerate=audio.sample_rate)
            backend.wait()

        except Exception:
            logger.exception("No se pudo reproducir el audio.")
            return Result.fail(
                code="AUDIO_PLAYBACK_ERROR",
                message=(
                    "No se pudo reproducir el audio por la salida "
                    "predeterminada."
                ),
            )

        return Result.ok()

    def stop(self) -> None:
        try:
            self._sounddevice().stop()
        except Exception:
            logger.exception("No se pudo detener la reproducción.")