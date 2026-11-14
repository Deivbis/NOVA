from nova.core import EventNames, Identity
from nova.voice import AudioData


def test_audio_data_duration():
    audio = AudioData(pcm=b"\x00\x00" * 22050, sample_rate=22050)

    assert audio.duration_seconds == 1.0


def test_audio_data_duration_counts_channels():
    audio = AudioData(
        pcm=b"\x00\x00" * 44100,
        sample_rate=22050,
        channels=2,
    )

    assert audio.duration_seconds == 1.0


def test_identity_values():
    assert Identity.ATLAS.value == "atlas"
    assert Identity.ASTI.value == "asti"


def test_event_names_are_unique():
    names = [
        value
        for key, value in vars(EventNames).items()
        if key.isupper()
    ]

    assert len(names) == len(set(names))


def test_voice_event_names_use_voice_prefix():
    voice_names = [
        value
        for key, value in vars(EventNames).items()
        if key.startswith("VOICE_")
    ]

    assert len(voice_names) == 5
    assert all(name.startswith("voice.") for name in voice_names)