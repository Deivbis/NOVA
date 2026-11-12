"""Voz de salida local con Piper (D-011, D-012). Funciona sin Internet.

Privacidad (SPEC-014 §9): nunca se registra el texto que se sintetiza.
"""

import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from nova.core.identity import Identity
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.voice.contracts import AudioData

logger = get_logger(__name__)

VOICE_MODELS: dict[Identity, str] = {
    Identity.ATLAS: "es_MX-ald-medium",
    Identity.ASTI: "es_MX-claude-high",
}


def _load_piper_voice(model_path: Path) -> Any:
    # Importación diferida: el Core no depende de Piper.
    from piper import PiperVoice

    return PiperVoice.load(str(model_path))


class PiperTTSProvider:
    name = "piper"
    requires_internet = False

    def __init__(
        self,
        voices_dir: Path,
        voice_models: Mapping[Identity, str] | None = None,
        loader: Callable[[Path], Any] | None = None,
    ) -> None:
        self._voices_dir = voices_dir
        self._voice_models = dict(voice_models or VOICE_MODELS)
        self._loader = loader or _load_piper_voice
        self._voices: dict[Identity, Any] = {}
        self._lock = threading.Lock()

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

        model_name = self._voice_models.get(identity)

        if model_name is None:
            return Result.fail(
                code="VOICE_NOT_CONFIGURED",
                message=f"No hay una voz configurada para '{identity.value}'.",
            )

        loaded = self._get_voice(identity, model_name)

        if not loaded.success:
            return Result.fail(
                code=loaded.error.code,
                message=loaded.error.message,
            )

        pcm = bytearray()
        sample_rate = 0

        try:
            for chunk in loaded.value.synthesize(message):
                sample_rate = chunk.sample_rate
                pcm.extend(chunk.audio_int16_bytes)

        except Exception:
            logger.exception("Piper falló al sintetizar con '%s'.", model_name)
            return Result.fail(
                code="TTS_SYNTHESIS_ERROR",
                message="Piper no pudo sintetizar la voz.",
            )

        if not pcm:
            return Result.fail(
                code="TTS_EMPTY_AUDIO",
                message="Piper no generó audio.",
            )

        return Result.ok(
            AudioData(
                pcm=bytes(pcm),
                sample_rate=sample_rate,
                channels=1,
                provider=self.name,
            )
        )

    def _get_voice(
        self,
        identity: Identity,
        model_name: str,
    ) -> Result[Any]:
        with self._lock:
            voice = self._voices.get(identity)

            if voice is not None:
                return Result.ok(voice)

            model_path = self._voices_dir / f"{model_name}.onnx"

            if not model_path.exists():
                return Result.fail(
                    code="VOICE_MODEL_NOT_FOUND",
                    message=(
                        f"Falta la voz '{model_name}'. Descárgala con "
                        f"'python -m piper.download_voices {model_name}' "
                        f"y cópiala a {self._voices_dir}."
                    ),
                )

            try:
                voice = self._loader(model_path)
            except Exception:
                logger.exception("No se pudo cargar la voz '%s'.", model_name)
                return Result.fail(
                    code="VOICE_LOAD_ERROR",
                    message=f"No se pudo cargar la voz '{model_name}'.",
                )

            self._voices[identity] = voice

            return Result.ok(voice)