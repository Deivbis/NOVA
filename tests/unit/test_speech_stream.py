import queue
from types import SimpleNamespace
from unittest.mock import MagicMock

from nova.core import Result
from nova.voice import AudioData, VoiceService, VoiceSettings
from nova.voice.speech_stream import SpeechStream


class _Service:
    def __init__(self):
        self.current = True

    def is_current(self, generation):
        return self.current

    def cancel_stream(self, generation):
        self.current = False


def _drain(feed):
    items = []

    while not feed.empty():
        items.append(feed.get())

    return items


def test_sentences_emitted_as_they_arrive():
    feed = queue.Queue()
    stream = SpeechStream(_Service(), 1, feed)

    stream.feed("Hola Jefe, ya revisé todo. Esto es ")
    assert _drain(feed) == ["Hola Jefe, ya revisé todo."]

    stream.feed("la segunda frase del mensaje. Fin")
    stream.end()
    assert _drain(feed) == [
        "Esto es la segunda frase del mensaje.", "Fin", None,
    ]


def test_code_blocks_are_not_spoken():
    feed = queue.Queue()
    stream = SpeechStream(_Service(), 1, feed)

    for part in (
        "Mira este ejemplo de código: ``",
        "`py\nprint(1)\n``",
        "` y con eso queda listo. Ok",
    ):
        stream.feed(part)

    stream.end()
    spoken = " ".join(i for i in _drain(feed) if i)

    assert "print" not in spoken and "listo" in spoken


def test_cancel_stops_feeding():
    service, feed = _Service(), queue.Queue()
    stream = SpeechStream(service, 1, feed)
    stream.cancel()
    stream.feed("Esto ya no debe sonar nunca más. ")

    assert _drain(feed) == [None] and service.current is False


def _service(enabled=True):
    router = SimpleNamespace(prefer_online=False, calls=[])

    def synthesize(text, identity):
        router.calls.append(text)

        return Result.ok(AudioData(pcm=b"\x00\x00" * 10, sample_rate=22050, provider="fake"))

    router.synthesize = synthesize
    player = SimpleNamespace(play=lambda audio: Result.ok(), stop=lambda: None)

    return VoiceService(MagicMock(), router, player, VoiceSettings(enabled=enabled)), router


def test_voice_service_speaks_stream():
    service, router = _service()
    stream = service.begin_stream()

    stream.feed("Hola Jefe, ya revisé todo. Esto es ")
    stream.feed("la segunda frase del mensaje. Fin")
    stream.end()
    service._thread.join(timeout=5)

    assert router.calls[0].startswith("Hola Jefe") and router.calls[-1] == "Fin"
    assert len(router.calls) == 3 and not service.is_speaking


def test_begin_stream_disabled():
    assert _service(enabled=False)[0].begin_stream() is None