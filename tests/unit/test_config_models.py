from nova.config.models import (
    ConnectivityConfig,
    ExecutionConfig,
    NOVAConfig,
    NovaConfig,
    OrbConfig,
    PathsConfig,
    UIConfig,
    VoiceConfig,
)


def test_configuration_models_are_created():
    config = NOVAConfig(
        nova=NovaConfig(
            name="NOVA",
            version="0.1.0",
            environment="development",
            language="es",
        ),
        execution=ExecutionConfig(
            mode="normal",
            debug=False,
        ),
        connectivity=ConnectivityConfig(
            internet_enabled=True,
            offline_mode_allowed=True,
        ),
        ui=UIConfig(
            theme="dark",
            orb=OrbConfig(
                enabled=True,
                position="bottom_right",
                size="small",
                opacity=0.75,
                click_through=True,
                gaming_mode=False,
            ),
        ),
        voice=VoiceConfig(
            enabled=False,
            wake_word_enabled=False,
            stt_enabled=False,
            tts_enabled=False,
        ),
        paths=PathsConfig(
            data="data",
            database="data/database",
            cache="data/cache",
            backups="data/backups",
            logs="data/logs",
            models="models",
        ),
    )

    assert config.nova.name == "NOVA"
    assert config.ui.orb.enabled is True