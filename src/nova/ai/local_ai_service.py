
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from nova.core.commands import Command
from nova.core.result import Result


class LocalAIService:
    """Local AI service powered by Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:1.7b",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> Result[str]:
        message = prompt.strip()

        if not message:
            return Result.fail(
                code="EMPTY_PROMPT",
                message="The prompt cannot be empty.",
            )

        payload = {
            "model": self.model,
            "prompt": message,
            "stream": False,
            "think": False,
            "options": {
                "num_ctx": 4096,
                "temperature": 0.7,
            },
        }

        request = Request(
            url=f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

            answer = data.get("response", "").strip()

            if not answer:
                return Result.fail(
                    code="EMPTY_AI_RESPONSE",
                    message="Ollama returned an empty response.",
                )

            return Result.ok(answer)

        except HTTPError as exc:
            return Result.fail(
                code="OLLAMA_HTTP_ERROR",
                message=f"Ollama HTTP error: {exc.code}.",
            )

        except (URLError, TimeoutError, OSError) as exc:
            return Result.fail(
                code="OLLAMA_CONNECTION_ERROR",
                message=f"Unable to connect to Ollama: {exc}",
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            return Result.fail(
                code="OLLAMA_INVALID_RESPONSE",
                message="Ollama returned an invalid response.",
            )

    def handle(self, command: Command) -> Result[str]:
        """Execute a chat generation command."""

        if command.name != "chat.generate":
            return Result.fail(
                code="INVALID_COMMAND",
                message="Unsupported AI command.",
            )

        prompt = command.payload.get("message")

        if not isinstance(prompt, str):
            return Result.fail(
                code="INVALID_MESSAGE",
                message="The command requires a text message.",
            )

        return self.generate(prompt)
