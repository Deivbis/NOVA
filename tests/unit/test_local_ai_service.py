import json
from urllib.error import HTTPError, URLError

from nova.ai import LocalAIService
from nova.ai.local_ai_service import DEFAULT_MODEL, strip_reasoning
from nova.core import Command


class FakeTransport:
    """Red falsa: devuelve una respuesta o lanza un error."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, url, payload, timeout):
        self.calls.append((url, payload, timeout))

        if self.error is not None:
            raise self.error

        return self.response


def reply(text):
    return {"message": {"role": "assistant", "content": text}}


def user(text):
    return {"role": "user", "content": text}


def assistant(text):
    return {"role": "assistant", "content": text}


def test_chat_returns_model_answer():
    service = LocalAIService(transport=FakeTransport(reply("Hola, Jefe.")))

    result = service.chat([user("Hola")])

    assert result.success
    assert result.value == "Hola, Jefe."


def test_chat_sends_history_to_ollama_chat_endpoint():
    transport = FakeTransport(reply("Ana."))
    service = LocalAIService(transport=transport)
    messages = [
        user("Me llamo Ana"),
        assistant("Un gusto, Ana."),
        user("¿Cómo me llamo?"),
    ]

    service.chat(messages)

    url, payload, _ = transport.calls[0]

    assert url.endswith("/api/chat")
    assert payload["messages"] == messages
    assert payload["model"] == DEFAULT_MODEL
    assert payload["think"] is False
    assert payload["keep_alive"] == "2m"
    assert payload["stream"] is False


def test_generate_wraps_prompt_as_single_user_message():
    transport = FakeTransport(reply("ok"))
    service = LocalAIService(transport=transport)

    service.generate("  Hola  ")

    assert transport.calls[0][1]["messages"] == [user("Hola")]


def test_empty_prompt_returns_failure():
    service = LocalAIService(transport=FakeTransport(reply("ok")))

    result = service.generate("   ")

    assert not result.success
    assert result.error.code == "EMPTY_PROMPT"


def test_invalid_command_returns_failure():
    service = LocalAIService(transport=FakeTransport(reply("ok")))

    result = service.handle(Command(name="invalid.command"))

    assert not result.success
    assert result.error.code == "INVALID_COMMAND"


def test_handle_uses_messages_from_payload():
    transport = FakeTransport(reply("ok"))
    service = LocalAIService(transport=transport)
    messages = [user("Hola"), assistant("Buenas"), user("¿Qué tal?")]

    result = service.handle(
        Command(name="chat.generate", payload={"messages": messages})
    )

    assert result.success
    assert transport.calls[0][1]["messages"] == messages


def test_handle_accepts_legacy_single_message():
    transport = FakeTransport(reply("ok"))
    service = LocalAIService(transport=transport)

    result = service.handle(
        Command(name="chat.generate", payload={"message": "Hola"})
    )

    assert result.success
    assert transport.calls[0][1]["messages"] == [user("Hola")]


def test_handle_rejects_missing_message():
    service = LocalAIService(transport=FakeTransport(reply("ok")))

    result = service.handle(Command(name="chat.generate"))

    assert not result.success
    assert result.error.code == "INVALID_MESSAGE"


def test_handle_rejects_invalid_messages():
    transport = FakeTransport(reply("ok"))
    service = LocalAIService(transport=transport)

    invalid_payloads = [
        "no es una lista",
        [],
        [{"role": "robot", "content": "Hola"}],
        [{"role": "user", "content": "   "}],
        [user("Hola"), assistant("Buenas")],
    ]

    for messages in invalid_payloads:
        result = service.handle(
            Command(name="chat.generate", payload={"messages": messages})
        )

        assert not result.success
        assert result.error.code == "INVALID_MESSAGE"

    assert transport.calls == []


def test_empty_ai_response_returns_failure():
    service = LocalAIService(transport=FakeTransport(reply("   ")))

    result = service.chat([user("Hola")])

    assert not result.success
    assert result.error.code == "EMPTY_AI_RESPONSE"


def test_http_error_returns_failure():
    error = HTTPError("http://localhost", 500, "Error", None, None)
    service = LocalAIService(transport=FakeTransport(error=error))

    result = service.chat([user("Hola")])

    assert not result.success
    assert result.error.code == "OLLAMA_HTTP_ERROR"


def test_connection_problems_return_failure():
    for error in (URLError("rechazada"), TimeoutError("tiempo agotado")):
        service = LocalAIService(transport=FakeTransport(error=error))

        result = service.chat([user("Hola")])

        assert not result.success
        assert result.error.code == "OLLAMA_CONNECTION_ERROR"


def test_invalid_responses_return_failure():
    bad_transports = [
        FakeTransport(error=json.JSONDecodeError("mal", "", 0)),
        FakeTransport(response=["no", "es", "un", "dict"]),
    ]

    for transport in bad_transports:
        result = LocalAIService(transport=transport).chat([user("Hola")])

        assert not result.success
        assert result.error.code == "OLLAMA_INVALID_RESPONSE"


def test_error_messages_never_include_user_content():
    service = LocalAIService(
        transport=FakeTransport(error=URLError("rechazada"))
    )

    result = service.chat([user("secreto-123")])

    assert "secreto-123" not in result.error.message



def test_strip_reasoning_removes_complete_think_block():
    text = "<think>pienso...</think>Hola, Jefe."

    assert strip_reasoning(text) == "Hola, Jefe."


def test_strip_reasoning_handles_closing_tag_only():
    text = "Okay, el usuario pregunta...\n</think>\n\nRespuesta final."

    assert strip_reasoning(text) == "Respuesta final."


def test_strip_reasoning_leaves_plain_answers_untouched():
    assert strip_reasoning("  Hola  ") == "Hola"


def test_strip_reasoning_drops_unfinished_reasoning():
    assert strip_reasoning("Hola<think>sigo pensando") == "Hola"


def test_chat_removes_reasoning_from_model_answer():
    service = LocalAIService(
        transport=FakeTransport(
            reply("razonamiento largo</think>Respuesta limpia.")
        )
    )

    result = service.chat([user("Hola")])

    assert result.value == "Respuesta limpia."


def test_answer_with_only_unfinished_reasoning_is_a_failure():
    service = LocalAIService(
        transport=FakeTransport(reply("<think>sigo pensando"))
    )

    result = service.chat([user("Hola")])

    assert not result.success
    assert result.error.code == "EMPTY_AI_RESPONSE"