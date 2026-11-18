"""Preferencias de la interfaz (DOC-016: JSON). Sección «ui» de settings.json."""

import json
from dataclasses import dataclass
from pathlib import Path

from nova.core.logging_setup import get_logger
from nova.storage.paths import default_settings_path

logger = get_logger(__name__)

MAX_NAME = 30


@dataclass(frozen=True)
class UiSettings:
    user_name: str = "Deivis"
    orb_enabled: bool = True


def load_ui_settings(path: Path | None = None) -> UiSettings:
    defaults = UiSettings()

    try:
        raw = json.loads(
            (path or default_settings_path()).read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        return defaults
    except (OSError, ValueError):
        logger.warning("No se pudo leer settings.json; se usan los valores por defecto.")
        return defaults

    section = raw.get("ui") if isinstance(raw, dict) else None

    if not isinstance(section, dict):
        return defaults

    name, orb = section.get("user_name"), section.get("orb_enabled")

    return UiSettings(
        user_name=(
            name.strip()[:MAX_NAME]
            if isinstance(name, str) and name.strip()
            else defaults.user_name
        ),
        orb_enabled=orb if isinstance(orb, bool) else defaults.orb_enabled,
    )


def save_ui_settings(settings: UiSettings, path: Path | None = None) -> None:
    target = path or default_settings_path()

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}

    if not isinstance(data, dict):
        data = {}

    data["ui"] = {
        "user_name": settings.user_name,
        "orb_enabled": settings.orb_enabled,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary.replace(target)