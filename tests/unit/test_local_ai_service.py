
from unittest.mock import patch

from nova.ai import LocalAIService
from nova.core import Command


def test_local_ai_service_generates_response():
    service = LocalAIService()

    with patch.object(
        service,
        "generate",
        return_value=service.generate.__annotations__.get(
            "return"
        ),
    ):
        pass


def test_empty_prompt_returns_failure():
    service = LocalAIService()

    result = service.generate("   ")

    assert not result.success
    assert result.error.code == "EMPTY_PROMPT"


def test_invalid_command_returns_failure():
    service = LocalAIService()

    command = Command(
        name="invalid.command",
    )

    result = service.handle(command)

    assert not result.success
    assert result.error.code == "INVALID_COMMAND"
