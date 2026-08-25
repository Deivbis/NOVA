import pytest

from nova.config.exceptions import ConfigurationValidationError
from nova.config.validator import ConfigValidator


def valid_config() -> dict:
    return {
        "nova": {
            "name": "NOVA",
            "version": "0.1.0",
            "environment": "development",
            "language": "es",
        },
        "execution": {
            "mode": "normal",
            "debug": False,
        },
        "connectivity": {
            "internet_enabled": True,
            "offline_mode_allowed": True,
        },
        "ui": {
            "theme": "dark",
            "orb": {
                "enabled": True,
                "position": "bottom_right",
                "size": "small",
                "opacity": 0.75,
                "click_through": True,
                "gaming_mode": False,
            },
        },
        "voice": {
            "enabled": False,
            "wake_word_enabled": False,
            "stt_enabled": False,
            "tts_enabled": False,
        },
        "paths": {
            "data": "data",
            "database": "data/database",
            "cache": "data/cache",
            "backups": "data/backups",
            "logs": "data/logs",
            "models": "models",
        },
    }


def test_valid_configuration_passes():
    ConfigValidator().validate(valid_config())


def test_invalid_environment_is_rejected():
    data = valid_config()
    data["nova"]["environment"] = "invalid"

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)


def test_invalid_language_is_rejected():
    data = valid_config()
    data["nova"]["language"] = "fr"

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)


def test_invalid_orb_position_is_rejected():
    data = valid_config()
    data["ui"]["orb"]["position"] = "center"

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)


def test_invalid_orb_size_is_rejected():
    data = valid_config()
    data["ui"]["orb"]["size"] = "huge"

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)


@pytest.mark.parametrize("opacity", [-0.1, 1.1, 7])
def test_invalid_orb_opacity_is_rejected(opacity):
    data = valid_config()
    data["ui"]["orb"]["opacity"] = opacity

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)


def test_missing_configuration_value_is_rejected():
    data = valid_config()
    del data["nova"]["language"]

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)


def test_invalid_configuration_type_is_rejected():
    data = valid_config()
    data["execution"]["debug"] = "false"

    with pytest.raises(ConfigurationValidationError):
        ConfigValidator().validate(data)