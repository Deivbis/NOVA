from pathlib import Path

from .loader import ConfigLoader
from .manager import ConfigManager
from .models import NOVAConfig


class ConfigurationService:
    """Application service for NOVA configuration."""

    def __init__(self, config_path: Path):
        self._manager = ConfigManager(config_path)

    def initialize(self) -> NOVAConfig:
        return self._manager.load()

    def get_config(self) -> NOVAConfig:
        return self._manager.config