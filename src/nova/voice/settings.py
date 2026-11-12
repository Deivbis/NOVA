"""Preferencias de voz del usuario (DOC-016: JSON para configuración).

Archivo: %APPDATA%/NOVA/settings.json, sección "voice". Nunca falla al
leer: ante un archivo ausente o inválido se usan los valores por defecto.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nova.core.identity import Identity
from nova.core.logging_setup import get_logger
from nova.storage.paths import default_settings_path

logger = get_logger(__name__)


@dataclass(frozen=True)
class VoiceSettings:
    enabled: bool = False
    identity: Identity = Identity.ATLAS
    prefer_online: bool = False
    hotkey: str = "pause"


def _as_bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _as_identity(value: Any, default: Identity) -> Identity:
    try:
        return Identity(value)
    except ValueError:
        return default


def _as_text(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return default


def load_voice_settings(path: Path | None = None) -> VoiceSettings:
    """Carga las preferencias de voz; nunca lanza excepciones."""
    settings_path = path or default_settings_path()

    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return VoiceSettings()
    except (OSError, ValueError):
        logger.warning(
            "No se pudo leer settings.json; se usan los valores por defecto."
        )
        return VoiceSettings()

    section = raw.get("voice") if isinstance(raw, dict) else None

    if not isinstance(section, dict):
        return VoiceSettings()

    defaults = VoiceSettings()

    return VoiceSettings(
        enabled=_as_bool(section.get("enabled"), defaults.enabled),
        identity=_as_identity(section.get("identity"), defaults.identity),
        prefer_online=_as_bool(
            section.get("prefer_online"),
            defaults.prefer_online,
        ),
        hotkey=_as_text(section.get("hotkey"), defaults.hotkey),
    )


def save_voice_settings(
    settings: VoiceSettings,
    path: Path | None = None,
) -> None:
    """Guarda las preferencias de voz conservando las demás secciones."""
    settings_path = path or default_settings_path()

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}

    if not isinstance(data, dict):
        data = {}

    data["voice"] = {
        "enabled": settings.enabled,
        "identity": settings.identity.value,
        "prefer_online": settings.prefer_online,
        "hotkey": settings.hotkey,
    }

    settings_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = settings_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_path.replace(settings_path)