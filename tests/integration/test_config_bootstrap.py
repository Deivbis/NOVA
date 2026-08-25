from pathlib import Path

from nova.config.service import ConfigurationService


def test_configuration_service_bootstrap():
    service = ConfigurationService(
        Path("config/default.toml")
    )

    config = service.initialize()

    assert config.nova.name == "NOVA"
    assert config.connectivity.offline_mode_allowed is True
    assert config.ui.orb.enabled is True

def test_configuration_service_exposes_loaded_configuration():
    service = ConfigurationService(
        Path("config/default.toml")
    )

    service.initialize()

    config = service.get_config()

    assert config.nova.name == "NOVA"
    assert config.ui.orb.opacity == 0.75