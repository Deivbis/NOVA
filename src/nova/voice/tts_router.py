"""Selector de voz de salida (D-011).

Privacidad (SPEC-014 §9): nunca se registra el texto que se habla.
"""

import time
from collections.abc import Callable

from nova.core.identity import Identity
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.core.state import ConnectivityState
from nova.voice.contracts import AudioData, TTSProvider

logger = get_logger(__name__)

ONLINE_RETRY_SECONDS = 60.0


class TTSRouter:
    """Elige entre la voz local y la voz en línea.

    - Por defecto solo se usa la voz local (100 % sin conexión).
    - La voz en línea se intenta únicamente si está activada y la
      conectividad no es OFFLINE (UNKNOWN también cuenta, porque aún no
      se detecta Internet).
    - Si la voz en línea falla, se usa la local y la en línea se deja de
      intentar durante ONLINE_RETRY_SECONDS.
    """

    def __init__(
        self,
        local: TTSProvider,
        online: TTSProvider | None = None,
        prefer_online: bool = False,
        connectivity: Callable[[], ConnectivityState] = (
            lambda: ConnectivityState.UNKNOWN
        ),
        clock: Callable[[], float] = time.monotonic,
        retry_seconds: float = ONLINE_RETRY_SECONDS,
    ) -> None:
        self._local = local
        self._online = online
        self._prefer_online = prefer_online
        self._connectivity = connectivity
        self._clock = clock
        self._retry_seconds = retry_seconds
        self._online_blocked_until = 0.0

    @property
    def prefer_online(self) -> bool:
        return self._prefer_online

    @prefer_online.setter
    def prefer_online(self, value: bool) -> None:
        self._prefer_online = value

    def synthesize(
        self,
        text: str,
        identity: Identity,
    ) -> Result[AudioData]:
        if self._should_try_online():
            result = self._online.synthesize(text, identity)

            if result.success:
                return result

            self._online_blocked_until = (
                self._clock() + self._retry_seconds
            )
            logger.warning(
                "La voz en línea falló (%s); se usa la voz local.",
                result.error.code if result.error else "UNKNOWN",
            )

        return self._local.synthesize(text, identity)

    def _should_try_online(self) -> bool:
        if self._online is None or not self._prefer_online:
            return False

        if self._connectivity() == ConnectivityState.OFFLINE:
            return False

        return self._clock() >= self._online_blocked_until