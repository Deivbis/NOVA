import threading

import numpy as np
import pytest

from nova.voice import MicrophoneRecorder

SPEECH = 3000
SILENCE = 10


class FakeStream:
    def __init__(self, amplitudes):
        self._amplitudes = list(amplitudes)
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, frames):
        self.read_sizes.append(frames)
        amplitude = self._amplitudes.pop(0)

        return np.full((frames, 1), amplitude, dtype=np.int16), False


class FakeFactory:
    def __init__(self, amplitudes=(), error=None):
        self.stream = FakeStream(amplitudes)
        self.error = error
        self.devices = []

    def __call__(self, device):
        self.devices.append(device)

        if self.error is not None:
            raise self.error

        return self.stream


def record(amplitudes, cancel=None, device=None):
    factory = FakeFactory(amplitudes)
    recorder = MicrophoneRecorder(device=device, stream_factory=factory)
    result = recorder.record(cancel or threading.Event())

    return result, factory


def test_records_until_the_speaker_goes_quiet():
    result, _ = record([SPEECH] * 5 + [SILENCE] * 12)
    recording = result.value

    assert result.success
    assert recording.reason == "speech_ended"
    assert recording.audio.sample_rate == 16000
    assert recording.audio.provider == "microphone"
    assert recording.audio.duration_seconds == pytest.approx(1.7)
    assert recording.seconds == pytest.approx(1.7)


def test_reports_no_speech_without_audio():
    result, _ = record([SILENCE] * 60)

    assert result.value.reason == "no_speech"
    assert result.value.audio is None


def test_cancel_before_recording_returns_cancelled_without_reading():
    cancel = threading.Event()
    cancel.set()

    result, factory = record([], cancel=cancel)

    assert result.value.reason == "cancelled"
    assert result.value.audio is None
    assert factory.stream.read_sizes == []


def test_reports_the_peak_level():
    result, _ = record([SPEECH] * 5 + [SILENCE] * 12)

    assert result.value.peak_rms > 0.05


def test_reads_frames_of_one_hundred_milliseconds():
    _, factory = record([SPEECH] * 5 + [SILENCE] * 12)

    assert set(factory.stream.read_sizes) == {1600}


def test_microphone_error_returns_a_helpful_failure():
    recorder = MicrophoneRecorder(
        stream_factory=FakeFactory(error=OSError("sin micrófono"))
    )

    result = recorder.record(threading.Event())

    assert not result.success
    assert result.error.code == "MICROPHONE_ERROR"
    assert "permisos" in result.error.message


def test_uses_the_configured_input_device():
    _, factory = record([SPEECH] * 5 + [SILENCE] * 12, device=7)

    assert factory.devices == [7]