from urllib.error import URLError

from nova.ai import LocalAIService
from nova.core import Conversation
from nova.storage import StorageService

USER = [{"role": "user", "content": "hola"}]


def make(chunks):
    return LocalAIService(stream_transport=lambda url, payload, timeout: iter(chunks))


def test_stream_delivers_pieces_and_final_text():
    got = []
    chunks = [
        {"message": {"content": "Hola"}},
        {"message": {"content": " mundo"}},
        {"done": True},
    ]

    result = make(chunks).chat_stream(USER, got.append)

    assert result.value == "Hola mundo"
    assert got == ["Hola", " mundo"]


def test_stream_hides_reasoning():
    got = []
    chunks = [
        {"message": {"content": "<think>pienso"}},
        {"message": {"content": "</think>Respuesta"}},
        {"done": True},
    ]

    result = make(chunks).chat_stream(USER, got.append)

    assert result.value == "Respuesta"
    assert "".join(got) == "Respuesta"


def test_stream_errors():
    def boom(url, payload, timeout):
        raise URLError("x")

    service = LocalAIService(stream_transport=boom)

    assert service.chat_stream(USER, lambda t: None).error.code == (
        "OLLAMA_CONNECTION_ERROR"
    )
    assert make([{"done": True}]).chat_stream(USER, lambda t: None).error.code == (
        "EMPTY_AI_RESPONSE"
    )


def test_summaries_include_preview(tmp_path):
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    repo = storage.conversation_repository
    conversation = Conversation()
    repo.create(conversation, title="T")
    repo.add_message(
        conversation.conversation_id, conversation.add_user_message("hola mundo")
    )

    assert repo.list_conversation_summaries()[0]["preview"] == "hola mundo"
    storage.close()