"""Respuestas deterministas a las órdenes de memoria (SPEC-012 §5, D-029).

No pasan por el modelo: nunca se finge haber guardado u olvidado algo.
"""

from nova.core.memory import Memory
from nova.memory.commands import MemoryAction, MemoryCommand
from nova.memory.service import MemoryService

MAX_SHOWN = 10
MAX_CONTENT_SHOWN = 120


def _short(text: str) -> str:
    if len(text) <= MAX_CONTENT_SHOWN:
        return text

    return text[: MAX_CONTENT_SHOWN - 1].rstrip() + "…"


def _line(memory: Memory) -> str:
    return f"- {memory.category}: {_short(memory.content)}"


class MemoryCommandHandler:
    def __init__(self, service: MemoryService) -> None:
        self._service = service

    def handle(self, command: MemoryCommand) -> str:
        if command.action == MemoryAction.REMEMBER:
            return self._remember(command)

        if command.action == MemoryAction.FORGET:
            return self._forget(command)

        return self._list(command)

    def _remember(self, command: MemoryCommand) -> str:
        result = self._service.remember(command.text, command.category)

        if result.success:
            memory = result.value

            return (
                f"Anotado, Jefe, en «{memory.category}»: "
                f"{_short(memory.content)}"
            )

        if result.error.code == "MEMORY_DUPLICATE":
            return "Ya lo tenía anotado, Jefe."

        return f"No pude guardarlo, Jefe. {result.error.message}"

    def _forget(self, command: MemoryCommand) -> str:
        if not command.text:
            result = self._service.forget_last()

            if result.success:
                return self._forgotten(result.value)

            return "No tengo nada guardado que olvidar, Jefe."

        found = self._service.find(command.text)

        if not found.success:
            return "No pude buscar en la memoria, Jefe."

        matches = found.value

        if not matches:
            return "No encuentro ningún recuerdo sobre eso, Jefe."

        if len(matches) > 1:
            shown = "\n".join(_line(item) for item in matches[:5])

            return (
                f"Encontré {len(matches)} recuerdos sobre eso, Jefe:\n"
                f"{shown}\n"
                "Dime con más detalle cuál olvidar."
            )

        result = self._service.forget(matches[0].memory_id)

        if result.success:
            return self._forgotten(result.value)

        return "No pude olvidarlo, Jefe."

    def _list(self, command: MemoryCommand) -> str:
        if command.text:
            result = self._service.find(command.text)
            empty = "No encuentro nada sobre eso, Jefe."
        else:
            result = self._service.list_memories(category=command.category)
            empty = (
                f"No tengo nada anotado en «{command.category}», Jefe."
                if command.category
                else "Aún no tengo nada anotado, Jefe."
            )

        if not result.success:
            return "No pude leer la memoria, Jefe."

        memories = result.value

        if not memories:
            return empty

        lines = "\n".join(_line(item) for item in memories[:MAX_SHOWN])
        extra = len(memories) - MAX_SHOWN
        tail = f"\nY {extra} más." if extra > 0 else ""

        return f"Esto es lo que recuerdo, Jefe:\n{lines}{tail}"

    @staticmethod
    def _forgotten(memory: Memory) -> str:
        return (
            f"Olvidado, Jefe: {_short(memory.content)}. "
            "Queda desactivado y se puede recuperar."
        )