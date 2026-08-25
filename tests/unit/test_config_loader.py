from pathlib import Path

import pytest

from nova.config.exceptions import (
    ConfigurationFileNotFoundError,
    ConfigurationFormatError,
)
from nova.config.loader import ConfigLoader


def test_loader_reads_default_configuration():
    path = Path("config/default.toml")

    config = ConfigLoader().load(path)

    assert config.nova.name == "NOVA"
    assert config.nova.language == "es"
    assert config.ui.theme == "dark"
    assert config.ui.orb.position == "bottom_right"


def test_loader_raises_when_file_does_not_exist(tmp_path):
    path = tmp_path / "missing.toml"

    with pytest.raises(ConfigurationFileNotFoundError):
        ConfigLoader().load(path)


def test_loader_rejects_invalid_toml(tmp_path):
    path = tmp_path / "invalid.toml"
    path.write_text(
        "[nova\nname = 'NOVA'",
        encoding="utf-8",
    )

def test_loader_rejects_incomplete_configuration(tmp_path):
    path = tmp_path / "incomplete.toml"

    path.write_text(
        """
[nova]
name = "NOVA"
version = "0.1.0"
environment = "development"
language = "es"

[execution]
mode = "normal"
debug = false
""",
        encoding="utf-8",
    )

    from nova.config.exceptions import ConfigurationValidationError

    with pytest.raises(ConfigurationValidationError):
        ConfigLoader().load(path)