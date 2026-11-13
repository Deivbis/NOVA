"""Detección de fin de frase por energía (D-013).

Recibe el nivel (RMS) de bloques consecutivos de audio y decide si hay que
seguir grabando. El umbral se adapta al ruido de fondo: nunca baja de
min_threshold ni sube de max_noise_floor * noise_multiplier, para que la
voz suave no se confunda con ruido aunque se empiece a hablar de inmediato.
"""

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    CONTINUE = "continue"
    SPEECH_ENDED = "speech_ended"
    NO_SPEECH = "no_speech"
    MAX_DURATION = "max_duration"


@dataclass(frozen=True)
class EndOfSpeechConfig:
    frame_seconds: float = 0.1
    min_threshold: float = 0.008
    noise_multiplier: float = 2.5
    max_noise_floor: float = 0.01
    min_speech_seconds: float = 0.3
    silence_seconds: float = 1.2
    no_speech_timeout: float = 6.0
    max_seconds: float = 20.0


class EndOfSpeechDetector:
    def __init__(self, config: EndOfSpeechConfig | None = None) -> None:
        self._config = config or EndOfSpeechConfig()

        self._min_speech_frames = self._frames(self._config.min_speech_seconds)
        self._silence_frames = self._frames(self._config.silence_seconds)
        self._no_speech_frames = self._frames(self._config.no_speech_timeout)
        self._max_frames = self._frames(self._config.max_seconds)

        self._frames_seen = 0
        self._speech_frames = 0
        self._silent_frames = 0
        self._speech_started = False
        self._floor: float | None = None
        self._peak = 0.0

    @property
    def speech_started(self) -> bool:
        return self._speech_started

    @property
    def peak_rms(self) -> float:
        return self._peak

    @property
    def noise_floor(self) -> float:
        return self._floor if self._floor is not None else 0.0

    def feed(self, rms: float) -> Decision:
        config = self._config

        self._frames_seen += 1
        self._peak = max(self._peak, rms)
        self._floor = rms if self._floor is None else min(self._floor, rms)

        floor = min(max(self._floor, 0.0005), config.max_noise_floor)
        threshold = max(config.min_threshold, floor * config.noise_multiplier)

        if rms >= threshold:
            self._speech_frames += 1
            self._silent_frames = 0

            if self._speech_frames >= self._min_speech_frames:
                self._speech_started = True

        else:
            if self._speech_started:
                self._silent_frames += 1
            else:
                self._speech_frames = 0

        if self._speech_started and self._silent_frames >= self._silence_frames:
            return Decision.SPEECH_ENDED

        if not self._speech_started and self._frames_seen >= self._no_speech_frames:
            return Decision.NO_SPEECH

        if self._frames_seen >= self._max_frames:
            return Decision.MAX_DURATION

        return Decision.CONTINUE

    def _frames(self, seconds: float) -> int:
        return max(1, round(seconds / self._config.frame_seconds))