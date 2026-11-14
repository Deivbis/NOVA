from pathlib import Path
import re
import pytest

from nova.config.manager import ConfigManager


def test_manager_loads_configuration():
    manager = ConfigManager(Path("config/default.toml"))

    config = manager.load()

    assert config.nova.name == "NOVA"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manager.config.nova.version)


def test_manager_requires_loading_before_access():
    manager = ConfigManager(Path("config/default.toml"))

    with pytest.raises(RuntimeError):
        _ = manager.config