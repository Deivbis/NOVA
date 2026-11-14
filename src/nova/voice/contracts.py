"""Contratos de voz (DOC-017, DOC-022, SPEC-014 §16).

El Core y los servicios trabajan contra estos contratos, nunca contra una
librería de audio concreta. Cada implementación (Piper, edge-tts,
faster-whisper...) vive detrás de un provider sustituible.
"""

from dataclasses import dataclass
from typing import Protocol

from nova.core.identity import Identity
from nova.core.result import Result


@dataclass(frozen=True)
class AudioData:
    """Audio PCM de 16 bits, independiente de la librería que lo produjo."""

    pcm: bytes
    sample_rate: int
    channels: int = 1
    provider: str = ""

    @property
    def duration_seconds(self) -> float:
        bytes_per_second = self.sample_rate * self.channels * 2

        if bytes_per_second <= 0:
            return 0.0

        return len(self.pcm) / bytes_per_second


class TTSProvider(Protocol):
    """Convierte texto en voz."""

    name: str
    requires_internet: bool

    def synthesize(
        self,
        text: str,
        identity: Identity,
    ) -> Result[AudioData]: ...


class STTProvider(Protocol):
    """Convierte voz en texto."""

    name: str
    requires_internet: bool

    def transcribe(
        self,
        audio: AudioData,
        language: str = "es",
    ) -> Result[str]: ...


class WakeWordProvider(Protocol):
    """Detecta la palabra clave en el audio entrante."""

    name: str

    def detect(self, audio: AudioData) -> bool: ...