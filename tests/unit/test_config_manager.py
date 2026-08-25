from pathlib import Path

import pytest

from nova.config.manager import ConfigManager


def test_manager_loads_configuration():
    manager = ConfigManager(Path("config/default.toml"))

    config = manager.load()

    assert config.nova.name == "NOVA"
    assert manager.config.nova.version == "0.1.0"


def test_manager_requires_loading_before_access():
    manager = ConfigManager(Path("config/default.toml"))

    with pytest.raises(RuntimeError):
        _ = manager.config