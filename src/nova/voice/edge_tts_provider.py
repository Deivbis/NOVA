"""Voz de salida en línea con edge-tts (D-011, D-012).

Envía el texto a servidores de Microsoft: solo se usa si el usuario lo
activa. Privacidad (SPEC-014 §9): nunca se registra el texto ni el
mensaje de las excepciones (podría contenerlo), solo su tipo.
"""

import asyncio
import io
from collections.abc import Awaitable, Callable, Mapping

from nova.core.identity import Identity
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.voice.contracts import AudioData

logger = get_logger(__name__)

EDGE_VOICES: dict[Identity, str] = {
    Identity.ATLAS: "es-MX-JorgeNeural",
    Identity.ASTI: "es-MX-DaliaNeural",
}

TIMEOUT_SECONDS = 15.0
OUTPUT_SAMPLE_RATE = 24000


async def _fetch_mp3(text: str, voice_name: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice_name)
    data = bytearray()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data.extend(chunk["data"])

    return bytes(data)


def _decode_mp3(data: bytes) -> tuple[bytes, int]:
    """Decodifica MP3 a PCM de 16 bits mono con PyAV."""
    import av

    pcm = bytearray()
    resampler = av.AudioResampler(
        format="s16",
        layout="mono",
        rate=OUTPUT_SAMPLE_RATE,
    )

    with av.open(io.BytesIO(data)) as container:
        for frame in container.decode(audio=0):
            for resampled in resampler.resample(frame):
                pcm.extend(resampled.to_ndarray().tobytes())

    try:
        for resampled in resampler.resample(None):
            pcm.extend(resampled.to_ndarray().tobytes())
    except Exception:
        logger.debug("No se pudo vaciar el remuestreador de audio.")

    return bytes(pcm), OUTPUT_SAMPLE_RATE


class EdgeTTSProvider:
    name = "edge-tts"
    requires_internet = True

    def __init__(
        self,
        voices: Mapping[Identity, str] | None = None,
        fetch: Callable[[str, str], Awaitable[bytes]] | None = None,
        decode: Callable[[bytes], tuple[bytes, int]] | None = None,
        timeout: float = TIMEOUT_SECONDS,
    ) -> None:
        self._voices = dict(voices or EDGE_VOICES)
        self._fetch = fetch or _fetch_mp3
        self._decode = decode or _decode_mp3
        self._timeout = timeout

    def synthesize(
        self,
        text: str,
        identity: Identity,
    ) -> Result[AudioData]:
        message = text.strip()

        if not message:
            return Result.fail(
                code="EMPTY_TEXT",
                message="No hay texto que sintetizar.",
            )

        voice_name = self._voices.get(identity)

        if voice_name is None:
            return Result.fail(
                code="VOICE_NOT_CONFIGURED",
                message=f"No hay una voz configurada para '{identity.value}'.",
            )

        try:
            mp3 = asyncio.run(
                asyncio.wait_for(
                    self._fetch(message, voice_name),
                    timeout=self._timeout,
                )
            )

        except TimeoutError:
            logger.warning("edge-tts no respondió a tiempo.")
            return Result.fail(
                code="ONLINE_TTS_TIMEOUT",
                message="La voz en línea no respondió a tiempo.",
            )

        except Exception as exc:
            logger.warning("edge-tts falló: %s", type(exc).__name__)
            return Result.fail(
                code="ONLINE_TTS_ERROR",
                message="La voz en línea no está disponible.",
            )

        if not mp3:
            return Result.fail(
                code="TTS_EMPTY_AUDIO",
                message="La voz en línea no devolvió audio.",
            )

        try:
            pcm, sample_rate = self._decode(mp3)
        except Exception as exc:
            logger.warning(
                "No se pudo decodificar el audio en línea: %s",
                type(exc).__name__,
            )
            return Result.fail(
                code="ONLINE_TTS_DECODE_ERROR",
                message="No se pudo decodificar el audio de la voz en línea.",
            )

        if not pcm:
            return Result.fail(
                code="TTS_EMPTY_AUDIO",
                message="La voz en línea no devolvió audio.",
            )

        return Result.ok(
            AudioData(
                pcm=pcm,
                sample_rate=sample_rate,
                channels=1,
                provider=self.name,
            )
        )