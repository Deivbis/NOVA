from pathlib import Path
import tomllib

from .exceptions import (
    ConfigurationFileNotFoundError,
    ConfigurationFormatError,
)
from .models import (
    ConnectivityConfig,
    ExecutionConfig,
    NOVAConfig,
    NovaConfig,
    OrbConfig,
    PathsConfig,
    UIConfig,
    VoiceConfig,
)
from .validator import ConfigValidator


class ConfigLoader:
    """Loads and validates NOVA configuration from TOML files."""

    def __init__(self) -> None:
        self._validator = ConfigValidator()

    def load(self, path: Path) -> NOVAConfig:
        if not path.exists():
            raise ConfigurationFileNotFoundError(
                f"Configuration file not found: {path}"
            )

        try:
            with path.open("rb") as file:
                data = tomllib.load(file)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigurationFormatError(
                f"Invalid TOML configuration: {path}"
            ) from exc

        self._validator.validate(data)

        return self._build_config(data)

    def _build_config(self, data: dict) -> NOVAConfig:
        nova = NovaConfig(
            name=data["nova"]["name"],
            version=data["nova"]["version"],
            environment=data["nova"]["environment"],
            language=data["nova"]["language"],
        )

        execution = ExecutionConfig(
            mode=data["execution"]["mode"],
            debug=data["execution"]["debug"],
        )

        connectivity = ConnectivityConfig(
            internet_enabled=data["connectivity"]["internet_enabled"],
            offline_mode_allowed=data["connectivity"]["offline_mode_allowed"],
        )

        orb = OrbConfig(
            enabled=data["ui"]["orb"]["enabled"],
            position=data["ui"]["orb"]["position"],
            size=data["ui"]["orb"]["size"],
            opacity=float(data["ui"]["orb"]["opacity"]),
            click_through=data["ui"]["orb"]["click_through"],
            gaming_mode=data["ui"]["orb"]["gaming_mode"],
        )

        ui = UIConfig(
            theme=data["ui"]["theme"],
            orb=orb,
        )

        voice = VoiceConfig(
            enabled=data["voice"]["enabled"],
            wake_word_enabled=data["voice"]["wake_word_enabled"],
            stt_enabled=data["voice"]["stt_enabled"],
            tts_enabled=data["voice"]["tts_enabled"],
        )

        paths = PathsConfig(
            data=data["paths"]["data"],
            database=data["paths"]["database"],
            cache=data["paths"]["cache"],
            backups=data["paths"]["backups"],
            logs=data["paths"]["logs"],
            models=data["paths"]["models"],
        )

        return NOVAConfig(
            nova=nova,
            execution=execution,
            connectivity=connectivity,
            ui=ui,
            voice=voice,
            paths=paths,
        )