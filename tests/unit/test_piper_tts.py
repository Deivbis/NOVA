import logging

from nova.core import Identity
from nova.voice import PiperTTSProvider


class FakeChunk:
    def __init__(self, data, rate=22050):
        self.audio_int16_bytes = data
        self.sample_rate = rate


class FakeVoice:
    def __init__(self, chunks=None, fail=False):
        self.chunks = chunks if chunks is not None else [
            FakeChunk(b"\x01\x00" * 10),
            FakeChunk(b"\x02\x00" * 10),
        ]
        self.fail = fail
        self.texts = []

    def synthesize(self, text):
        self.texts.append(text)

        if self.fail:
            raise RuntimeError("fallo simulado")

        yield from self.chunks


class FakeLoader:
    def __init__(self, voice=None, error=None):
        self.voice = voice or FakeVoice()
        self.error = error
        self.paths = []

    def __call__(self, path):
        self.paths.append(path)

        if self.error is not None:
            raise self.error

        return self.voice


def create_provider(tmp_path, loader=None, with_models=True):
    if with_models:
        (tmp_path / "es_MX-ald-medium.onnx").write_bytes(b"")
        (tmp_path / "es_MX-claude-high.onnx").write_bytes(b"")

    loader = loader or FakeLoader()

    return PiperTTSProvider(tmp_path, loader=loader), loader


def test_synthesizes_pcm_from_chunks(tmp_path):
    provider, _ = create_provider(tmp_path)

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert result.success
    assert len(result.value.pcm) == 40
    assert result.value.sample_rate == 22050
    assert result.value.provider == "piper"


def test_uses_the_voice_of_each_identity(tmp_path):
    provider, loader = create_provider(tmp_path)

    provider.synthesize("Hola", Identity.ATLAS)
    provider.synthesize("Hola", Identity.ASTI)

    names = [path.name for path in loader.paths]

    assert names == ["es_MX-ald-medium.onnx", "es_MX-claude-high.onnx"]


def test_voice_is_loaded_only_once(tmp_path):
    provider, loader = create_provider(tmp_path)

    provider.synthesize("Uno", Identity.ATLAS)
    provider.synthesize("Dos", Identity.ATLAS)

    assert len(loader.paths) == 1


def test_missing_model_returns_download_instructions(tmp_path):
    provider, _ = create_provider(tmp_path, with_models=False)

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "VOICE_MODEL_NOT_FOUND"
    assert "piper.download_voices" in result.error.message


def test_load_error_returns_failure(tmp_path):
    loader = FakeLoader(error=RuntimeError("modelo corrupto"))
    provider, _ = create_provider(tmp_path, loader=loader)

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "VOICE_LOAD_ERROR"


def test_synthesis_error_returns_failure(tmp_path):
    loader = FakeLoader(voice=FakeVoice(fail=True))
    provider, _ = create_provider(tmp_path, loader=loader)

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "TTS_SYNTHESIS_ERROR"


def test_empty_audio_returns_failure(tmp_path):
    loader = FakeLoader(voice=FakeVoice(chunks=[]))
    provider, _ = create_provider(tmp_path, loader=loader)

    result = provider.synthesize("Hola", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "TTS_EMPTY_AUDIO"


def test_empty_text_is_rejected_without_loading_the_voice(tmp_path):
    provider, loader = create_provider(tmp_path)

    result = provider.synthesize("   ", Identity.ATLAS)

    assert not result.success
    assert result.error.code == "EMPTY_TEXT"
    assert loader.paths == []


def test_spoken_text_is_never_logged(tmp_path, caplog):
    loader = FakeLoader(voice=FakeVoice(fail=True))
    provider, _ = create_provider(tmp_path, loader=loader)

    with caplog.at_level(logging.DEBUG, logger="nova"):
        provider.synthesize("secreto-123", Identity.ATLAS)

    assert "secreto-123" not in caplog.text