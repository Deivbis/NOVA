from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import re
from nova.core.commands import Command
from nova.core.logging_setup import get_logger
from nova.core.result import Result

logger = get_logger(__name__)

VALID_ROLES = frozenset({"system", "user", "assistant"})
# Variante sin razonamiento (Qwen3-4B-Instruct-2507). Si la etiqueta en
# Ollama es otra, se cambia aquí.
DEFAULT_MODEL = "qwen3:4b-instruct"
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)

Transport = Callable[[str, dict[str, Any], int], Any]


def _post_json(
    url: str,
    payload: dict[str, Any],
    timeout: int,
) -> Any:
    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
    
def strip_reasoning(text: str) -> str:
    """Remove chain-of-thought that some models include in their answer.

    Handles complete <think>...</think> blocks, answers where only the
    closing tag appears (the chat template adds the opening one) and
    unfinished reasoning.
    """
    cleaned = _THINK_BLOCK.sub("", text)

    if "</think>" in cleaned:
        cleaned = cleaned.rsplit("</think>", 1)[1]

    if "<think>" in cleaned:
        cleaned = cleaned.split("<think>", 1)[0]

    return cleaned.strip()

def _invalid_message(message: str) -> Result[str]:
    return Result.fail(code="INVALID_MESSAGE", message=message)


class LocalAIService:
    """Local AI provider powered by Ollama (DOC-022).

    Privacy (SPEC-014 §9): the content of messages is never logged.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
        keep_alive: str = "2m",
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.keep_alive = keep_alive
        self._transport = transport or _post_json

    def chat(self, messages: list[dict[str, str]]) -> Result[str]:
        """Generate the next assistant answer for a conversation."""
        invalid = self._validate_messages(messages)

        if invalid is not None:
            return invalid

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": self.keep_alive,
            "options": {
                "num_ctx": 4096,
                "temperature": 0.7,
            },
        }

        logger.debug(
            "Solicitud a Ollama: modelo=%s, mensajes=%d",
            self.model,
            len(messages),
        )

        try:
            data = self._transport(
                f"{self.base_url}/api/chat",
                payload,
                self.timeout,
            )

        except HTTPError as exc:
            logger.warning("Ollama respondió con error HTTP %s.", exc.code)
            return Result.fail(
                code="OLLAMA_HTTP_ERROR",
                message=f"Ollama respondió con el error HTTP {exc.code}.",
            )

        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("No se pudo conectar con Ollama: %s", exc)
            return Result.fail(
                code="OLLAMA_CONNECTION_ERROR",
                message="No se pudo conectar con Ollama. ¿Está en ejecución?",
            )

        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Ollama devolvió una respuesta ilegible.")
            return Result.fail(
                code="OLLAMA_INVALID_RESPONSE",
                message="Ollama devolvió una respuesta no válida.",
            )

        if not isinstance(data, dict):
            logger.warning("Ollama devolvió una respuesta con formato inesperado.")
            return Result.fail(
                code="OLLAMA_INVALID_RESPONSE",
                message="Ollama devolvió una respuesta no válida.",
            )

        answer = data.get("message")
        raw_content = (
            answer.get("content") if isinstance(answer, dict) else None
        )
        content = (
            strip_reasoning(raw_content)
            if isinstance(raw_content, str)
            else ""
        )

        if not content:
            return Result.fail(
                code="EMPTY_AI_RESPONSE",
                message="Ollama devolvió una respuesta vacía.",
            )

        return Result.ok(content)

    def generate(self, prompt: str) -> Result[str]:
        """Generate an answer for a single message without history."""
        message = prompt.strip()

        if not message:
            return Result.fail(
                code="EMPTY_PROMPT",
                message="El mensaje no puede estar vacío.",
            )

        return self.chat([{"role": "user", "content": message}])

    def handle(self, command: Command) -> Result[str]:
        """Execute a chat generation command."""
        if command.name != "chat.generate":
            return Result.fail(
                code="INVALID_COMMAND",
                message="Comando de IA no admitido.",
            )

        messages = command.payload.get("messages")

        if messages is not None:
            return self.chat(messages)

        prompt = command.payload.get("message")

        if not isinstance(prompt, str):
            return _invalid_message(
                "El comando requiere 'messages' o 'message'."
            )

        return self.generate(prompt)

    @staticmethod
    def _validate_messages(messages: Any) -> Result[str] | None:
        if not isinstance(messages, list) or not messages:
            return _invalid_message("Se requiere una lista de mensajes.")

        for item in messages:
            if (
                not isinstance(item, dict)
                or item.get("role") not in VALID_ROLES
                or not isinstance(item.get("content"), str)
                or not item["content"].strip()
            ):
                return _invalid_message(
                    "Cada mensaje requiere un rol válido y texto."
                )

        if messages[-1]["role"] != "user":
            return _invalid_message(
                "El último mensaje debe ser del usuario."
            )

        return None