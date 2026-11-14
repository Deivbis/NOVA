import numpy as np

from nova.voice import AudioData, SoundDevicePlayer


class FakeBackend:
    def __init__(self, fail=False):
        self.fail = fail
        self.played = []
        self.waited = 0
        self.stopped = 0

    def play(self, samples, samplerate):
        if self.fail:
            raise RuntimeError("sin salida de audio")

        self.played.append((samples, samplerate))

    def wait(self):
        self.waited += 1

    def stop(self):
        self.stopped += 1


def make_audio():
    return AudioData(
        pcm=np.array([1, 2, 3], dtype=np.int16).tobytes(),
        sample_rate=22050,
    )


def test_player_sends_int16_samples_to_backend():
    backend = FakeBackend()

    result = SoundDevicePlayer(backend).play(make_audio())

    samples, rate = backend.played[0]

    assert result.success
    assert samples.tolist() == [1, 2, 3]
    assert rate == 22050
    assert backend.waited == 1


def test_player_reports_backend_errors():
    result = SoundDevicePlayer(FakeBackend(fail=True)).play(make_audio())

    assert not result.success
    assert result.error.code == "AUDIO_PLAYBACK_ERROR"


def test_player_rejects_invalid_pcm():
    audio = AudioData(pcm=b"\x01", sample_rate=22050)

    result = SoundDevicePlayer(FakeBackend()).play(audio)

    assert not result.success
    assert result.error.code == "AUDIO_PLAYBACK_ERROR"


def test_player_stop_calls_backend():
    backend = FakeBackend()

    SoundDevicePlayer(backend).stop()

    assert backend.stopped == 1