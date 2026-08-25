from pathlib import Path

from .loader import ConfigLoader
from .models import NOVAConfig


class ConfigManager:
    """Provides centralized access to NOVA configuration."""

    def __init__(self, config_path: Path):
        self._config_path = config_path
        self._loader = ConfigLoader()
        self._config: NOVAConfig | None = None

    def load(self) -> NOVAConfig:
        self._config = self._loader.load(self._config_path)
        return self._config

    @property
    def config(self) -> NOVAConfig:
        if self._config is None:
            raise RuntimeError("Configuration has not been loaded.")

        return self._config