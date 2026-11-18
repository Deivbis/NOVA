"""Rutinas (ActionPlan, DOC-017): pasos de Automatización en orden.

Cada paso pasa por el flujo normal (Security + confirmaciones). Solo se
admiten pasos de abrir y de multimedia.
"""

import re

from nova.automation.commands import AutomationAction, parse_automation_command
from nova.automation.handler import AutomationCommandHandler
from nova.automation.service import AutomationService
from nova.core.logging_setup import get_logger
from nova.memory.text import normalize
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.routine_repository import RoutineRepository

logger = get_logger(__name__)

MAX_STEPS = 10
_F = re.IGNORECASE
_ALLOWED = {AutomationAction.OPEN, AutomationAction.MEDIA}
_VERBS = "abre|abrir|ejecuta|inicia|lanza|pausa|pon|sube|baja|silencia|reproduce"

_CREATE = re.compile(
    r"^\s*(?:crea|crear|guarda|define)\s+(?:la\s+|una\s+)?rutina\s+"
    r"(?:llamada\s+)?(?P<name>[^:]{1,40}?)\s*:\s*(?P<steps>.+?)[.!]*\s*$", _F)
_RUN = re.compile(
    r"^\s*(?:ejecuta|inicia|lanza|activa|corre)\s+(?:la\s+)?rutina\s+"
    r"(?P<name>.+?)[.!]*\s*$", _F)
_LIST = re.compile(
    r"^\s*¿?\s*(?:qu[eé]\s+rutinas\s+tengo|mis\s+rutinas"
    r"|lista\s+(?:mis\s+)?rutinas)\s*[?.!]*\s*$", _F)
_SHOW = re.compile(
    r"^\s*¿?\s*qu[eé]\s+hace\s+la\s+rutina\s+(?P<name>.+?)\s*[?.!]*\s*$", _F)
_DELETE = re.compile(
    r"^\s*(?:borra|elimina|quita)\s+la\s+rutina\s+(?P<name>.+?)[.!]*\s*$", _F)
_SPLIT = re.compile(
    rf"\s*(?:;|,|\s+y\s+(?=(?:{_VERBS})\b)|\s+luego\s+|\s+despu[eé]s\s+)\s*",
    _F)


class RoutineHandler:
    def __init__(
        self,
        repository: RoutineRepository,
        automation: AutomationCommandHandler,
        service: AutomationService,
    ) -> None:
        self._repository = repository
        self._automation = automation
        self._service = service
        self._queue: list[str] = []
        self._lines: list[str] = []
        self._waiting = False

    def reply_to(self, text: str) -> str | None:
        try:
            if self._waiting:
                return self._resume(text)

            return self._dispatch(text)
        except RepositoryError:
            logger.exception("Fallo de rutinas.")
            return "No pude acceder a tus rutinas, Jefe."

    def _dispatch(self, text: str) -> str | None:
        if match := _CREATE.match(text):
            return self._create(match["name"], match["steps"])

        if _LIST.match(text):
            routines = self._repository.list_routines()

            if not routines:
                return "No tienes rutinas, Jefe."

            return "\n".join(
                ["Tus rutinas:", *[f"- {n} ({len(s)} pasos)" for n, s in routines]]
            )

        if match := _DELETE.match(text):
            removed = self._repository.remove(normalize(match["name"]).strip())

            return "Rutina borrada, Jefe." if removed else "No tengo esa rutina, Jefe."

        if match := _SHOW.match(text):
            record = self._repository.get_by_key(normalize(match["name"]).strip())

            if record is None:
                return "No tengo esa rutina, Jefe."

            return "\n".join(
                [f"«{record[0]}»:", *[f"{i}. {s}" for i, s in enumerate(record[1], 1)]]
            )

        if match := _RUN.match(text):
            return self._run(match["name"])

        key = normalize(text).strip(" .!?")

        if key and self._repository.get_by_key(key) is not None:
            return self._run(key)

        return None

    def _create(self, name: str, steps_text: str) -> str:
        name = " ".join(name.split())
        steps = [
            s.strip(" .") for s in _SPLIT.split(steps_text) if s.strip(" .")
        ]

        if not 1 <= len(steps) <= MAX_STEPS:
            return f"Una rutina necesita entre 1 y {MAX_STEPS} pasos, Jefe."

        for step in steps:
            command = parse_automation_command(step)

            if command is None or command.action not in _ALLOWED:
                return (
                    f"No puedo usar «{step}» en una rutina, Jefe. "
                    "Solo abrir programas, carpetas, webs y controlar música."
                )

            if command.action == AutomationAction.OPEN:
                planned = self._service.plan(command)

                if not planned.success:
                    return f"Paso «{step}»: {planned.error.message}"

        key = normalize(name)
        existed = self._repository.get_by_key(key) is not None
        self._repository.save(key, name, steps)

        return (
            f"Rutina «{name}» {'actualizada' if existed else 'creada'}, "
            f"Jefe: {len(steps)} pasos. Dila cuando quieras."
        )

    def _run(self, name: str) -> str:
        record = self._repository.get_by_key(normalize(name).strip())

        if record is None:
            return "No tengo esa rutina, Jefe."

        self._queue = list(record[1])
        self._lines = [f"Ejecutando la rutina «{record[0]}», Jefe."]

        return self._advance()

    def _resume(self, text: str) -> str:
        self._waiting = False
        reply = self._automation.reply_to(text)

        if reply is None:
            self._queue.clear()
            self._lines.clear()
            return "Rutina detenida, Jefe."

        self._lines.append(reply)

        return self._advance()

    def _advance(self) -> str:
        while self._queue:
            reply = self._automation.reply_to(self._queue.pop(0))

            if reply:
                self._lines.append(reply)

            if self._automation.pending:
                self._waiting = True
                return "\n".join(self._lines)

        self._repository.audit("routine.executed")
        lines, self._lines = self._lines, []

        return "\n".join([*lines, "Rutina completada, Jefe."])