import asyncio
import logging

from nova.core import Identity
from nova.voice import EdgeTTSProvider


class FakeFetch:
    def __init__(self, data=b"mp3", error=None, delay=0.0):
        self.data = data
        self.error = error
        self.delay = delay
        self.calls = []

    async def __call__(self, text, voice_name):
        self.calls.append((text, voice_name))

        if self.delay:
            await asyncio.sleep(self.delay)

        if self.error is not None:
            raise self.error

        return self.data


class FakeDecode:
    def __init__(self, pcm=b"\x00\x00" * 100, error=None):
        self.pcm = pcm
        self.error = error
        self.calls = 0

    def __call__(self, data):
        self.calls += 1

        if self.error is not None:
            raise self.error

        return self.pcm, 24000


def create_provider(fetch=None, decode=None, timeout=5.0):
    fetch = fetch or FakeFetch()
    decode = decode or FakeDecode()

    return EdgeTTSProvider(fetch=fetch, decode=decode, timeout=timeout), fetch


def test_requires_internet():
    provider, _ = create_provider()

    assert provider.requires_internet is True


def test_synthesizes_audio_with_the_voice_of_each_identity():
    provider, fetch = create_provider()

    atlas = provider.synthesize("Hola", Identity.ATLAS)
    asti = provider.synthesize("Hola", Identity.ASTI)

    assert atlas.success
    assert atlas.value.provider == "edge-tts"
    assert atlas.value.sample_rate == 24000
    assert asti.success
    assert [call[1] for call in fetch.calls] == [
        "es-MX-JorgeNeural",
        "es-MX-DaliaNeural",
    ]


def test_fetch_error_returns_failure():
    provider, _ = create_provider(
        fetch=FakeFetch(error=RuntimeError("sin red"))
    )

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "ONLINE_TTS_ERROR"


def test_timeout_returns_failure():
    provider, _ = create_provider(
        fetch=FakeFetch(delay=1.0),
        timeout=0.05,
    )

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "ONLINE_TTS_TIMEOUT"


def test_decode_error_returns_failure():
    provider, _ = create_provider(
        decode=FakeDecode(error=RuntimeError("mp3 corrupto"))
    )

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "ONLINE_TTS_DECODE_ERROR"


def test_empty_download_returns_failure_without_decoding():
    decode = FakeDecode()
    provider, _ = create_provider(fetch=FakeFetch(data=b""), decode=decode)

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "TTS_EMPTY_AUDIO"
    assert decode.calls == 0


def test_empty_text_is_rejected():
    provider, fetch = create_provider()

    result = provider.synthesize("   ", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "EMPTY_TEXT"
    assert fetch.calls == []


def test_text_and_error_messages_are_never_logged(caplog):
    provider, _ = create_provider(
        fetch=FakeFetch(error=RuntimeError("falló con secreto-123"))
    )

    with caplog.at_level(logging.DEBUG, logger="nova"):
        provider.synthesize("secreto-123", Identity.ATLAS)

    assert "secreto-123" not in caplog.text