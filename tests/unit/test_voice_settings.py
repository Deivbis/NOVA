import json

from nova.core import Identity
from nova.voice import VoiceSettings, load_voice_settings, save_voice_settings


def test_missing_file_returns_defaults(tmp_path):
    settings = load_voice_settings(tmp_path / "settings.json")

    assert settings == VoiceSettings()


def test_defaults_follow_the_decisions():
    settings = VoiceSettings()

    assert settings.enabled is False
    assert settings.prefer_online is False
    assert settings.identity == Identity.ATLAS
    assert settings.hotkey == "pause"


def test_settings_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    expected = VoiceSettings(
        enabled=True,
        identity=Identity.ASTI,
        prefer_online=True,
        hotkey="scroll lock",
    )

    save_voice_settings(expected, path)

    assert load_voice_settings(path) == expected


def test_invalid_json_returns_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ esto no es json", encoding="utf-8")

    assert load_voice_settings(path) == VoiceSettings()


def test_invalid_values_fall_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "voice": {
                    "enabled": "sí",
                    "identity": "robot",
                    "prefer_online": 1,
                    "hotkey": "",
                }
            }
        ),
        encoding="utf-8",
    )

    assert load_voice_settings(path) == VoiceSettings()


def test_save_preserves_other_sections(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"ui": {"theme": "dark"}}), encoding="utf-8")

    save_voice_settings(VoiceSettings(enabled=True), path)

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["ui"] == {"theme": "dark"}
    assert data["voice"]["enabled"] is True


def test_save_creates_missing_folder(tmp_path):
    path = tmp_path / "nested" / "settings.json"

    save_voice_settings(VoiceSettings(), path)

    assert path.exists()