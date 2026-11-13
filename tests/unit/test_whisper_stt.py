import logging

import numpy as np
import pytest

from nova.voice import AudioData, FasterWhisperSTT


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, texts=("Hola mundo",), error=None):
        self.texts = texts
        self.error = error
        self.calls = []

    def transcribe(self, samples, **options):
        self.calls.append((samples, options))

        if self.error is not None:
            raise self.error

        return iter([FakeSegment(text) for text in self.texts]), object()


class FakeLoader:
    def __init__(self, model=None, error=None):
        self.model = model or FakeModel()
        self.error = error
        self.calls = []

    def __call__(self, model_name):
        self.calls.append(model_name)

        if self.error is not None:
            raise self.error

        return self.model


class FakeTimer:
    instances = []

    def __init__(self, interval, function):
        self.interval = interval
        self.function = function
        self.daemon = False
        self.started = False
        self.cancelled = False
        FakeTimer.instances.append(self)

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make_audio(amplitude=16384, samples=16000):
    return AudioData(
        pcm=np.full(samples, amplitude, dtype=np.int16).tobytes(),
        sample_rate=16000,
        provider="microphone",
    )


def create_stt(model=None, vocabulary=(), clock=None, loader=None):
    FakeTimer.instances = []
    loader = loader or FakeLoader(model)

    stt = FasterWhisperSTT(
        model_name="small",
        vocabulary=vocabulary,
        idle_seconds=300.0,
        loader=loader,
        clock=clock or FakeClock(),
        timer_factory=FakeTimer,
    )

    return stt, loader


def test_transcribes_and_joins_the_segments():
    stt, _ = create_stt(model=FakeModel(texts=(" Hola ", "mundo ")))

    result = stt.transcribe(make_audio())

    assert result.success
    assert result.value == "Hola mundo"


def test_model_receives_normalized_samples_and_options():
    stt, loader = create_stt()

    stt.transcribe(make_audio())

    samples, options = loader.model.calls[0]

    assert samples.dtype == np.float32
    assert samples.max() == pytest.approx(0.5)
    assert options["language"] == "es"
    assert options["vad_filter"] is True
    assert options["beam_size"] == 1


def test_vocabulary_is_passed_as_hotwords():
    stt, loader = create_stt(vocabulary=("Atlas", "Deivbis"))

    stt.transcribe(make_audio())

    assert loader.model.calls[0][1]["hotwords"] == "Atlas Deivbis"


def test_empty_vocabulary_sends_no_hotwords():
    stt, loader = create_stt(vocabulary=())

    stt.transcribe(make_audio())

    assert loader.model.calls[0][1]["hotwords"] is None


def test_model_is_loaded_lazily_and_only_once():
    stt, loader = create_stt()

    assert loader.calls == []

    stt.transcribe(make_audio())
    stt.transcribe(make_audio())

    assert loader.calls == ["small"]


def test_empty_transcription_reports_no_speech():
    stt, _ = create_stt(model=FakeModel(texts=("  ",)))

    result = stt.transcribe(make_audio())

    assert not result.success
    assert result.error.code == "NO_SPEECH_DETECTED"


def test_model_error_returns_failure_without_leaking_details(caplog):
    model = FakeModel(error=RuntimeError("falló con secreto-123"))
    stt, _ = create_stt(model=model)

    with caplog.at_level(logging.DEBUG, logger="nova"):
        result = stt.transcribe(make_audio())

    assert not result.success
    assert result.error.code == "STT_ERROR"
    assert "secreto-123" not in result.error.message
    assert "secreto-123" not in caplog.text


def test_invalid_audio_is_rejected_without_loading_the_model():
    stt, loader = create_stt()
    audio = AudioData(pcm=b"\x00\x00" * 100, sample_rate=44100)

    result = stt.transcribe(audio)

    assert not result.success
    assert result.error.code == "INVALID_AUDIO"
    assert loader.calls == []


def test_loader_failure_returns_failure():
    loader = FakeLoader(error=RuntimeError("sin red"))
    stt, _ = create_stt(loader=loader)

    result = stt.transcribe(make_audio())

    assert not result.success
    assert result.error.code == "STT_MODEL_ERROR"


def test_model_is_released_after_the_idle_time():
    clock = FakeClock()
    stt, loader = create_stt(clock=clock)

    stt.transcribe(make_audio())

    clock.now = 299.0
    assert stt.release_if_idle() is False

    clock.now = 301.0
    assert stt.release_if_idle() is True

    stt.transcribe(make_audio())

    assert loader.calls == ["small", "small"]


def test_release_timer_is_scheduled_after_use_and_cancelled_on_shutdown():
    stt, _ = create_stt()

    stt.transcribe(make_audio())

    timer = FakeTimer.instances[-1]

    assert timer.interval == 300.0
    assert timer.daemon is True
    assert timer.started is True

    stt.shutdown()

    assert timer.cancelled is True