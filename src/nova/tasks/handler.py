from uuid import UUID

from nova.core.logging_setup import get_logger
from nova.core.tasks import Task
from nova.memory.text import normalize
from nova.storage.exceptions import RepositoryError
from nova.tasks.commands import TaskAction, TaskCommand, parse_task_command
from nova.tasks.service import TaskService, format_due

logger = get_logger(__name__)

MAX_LISTED = 20


class TaskCommandHandler:
    def __init__(self, service: TaskService) -> None:
        self._service = service
        self._listed: list[UUID] = []

    def reply_to(self, text: str) -> str | None:
        command = parse_task_command(text)

        if command is None:
            return None

        try:
            return self._handle(command)
        except RepositoryError:
            logger.exception("Fallo de pendientes.")
            return "No pude acceder a tus pendientes, Jefe."

    def due_messages(self) -> str | None:
        try:
            due = self._service.due_now()
        except RepositoryError:
            logger.exception("Fallo de recordatorios.")
            return None

        if not due:
            return None

        now = self._service.now()
        lines = []

        for task, late in due:
            if late:
                when = format_due(task.due_at, now)
                lines.append(
                    f"Jefe, tenías un recordatorio de {when}: {task.title}."
                )
            else:
                lines.append(f"Jefe, recordatorio: {task.title}.")

        return "\n".join(lines)

    def _handle(self, command: TaskCommand) -> str:
        service, action = self._service, command.action

        if action == TaskAction.REMIND:
            result = service.add_reminder(command.text)

            if not result.success:
                return f"{result.error.message} Lo siento, Jefe."

            when = format_due(result.value.due_at, service.now())

            return f"Anotado, Jefe: te recordaré «{result.value.title}» {when}."

        if action == TaskAction.ADD:
            result = service.add_todo(command.text)

            if not result.success:
                return f"{result.error.message} Lo siento, Jefe."

            return f"Anotado en tus pendientes, Jefe: {result.value.title}."

        if action == TaskAction.LIST:
            tasks = service.list_open()[:MAX_LISTED]
            self._listed = [t.task_id for t in tasks]

            if not tasks:
                return "No tienes pendientes, Jefe."

            now = service.now()
            lines = [
                f"{i}. {t.title}"
                + (f" — {format_due(t.due_at, now)}" if t.due_at else "")
                for i, t in enumerate(tasks, 1)
            ]

            return "\n".join(["Tus pendientes:", *lines])

        task, error = self._pick(command)

        if task is None:
            return error

        if action == TaskAction.COMPLETE:
            service.complete(task.task_id)
            return f"Hecho, Jefe: «{task.title}» completado."

        service.cancel(task.task_id)

        return f"Cancelado, Jefe: «{task.title}»."

    def _pick(self, command: TaskCommand) -> tuple[Task | None, str]:
        open_tasks = {t.task_id: t for t in self._service.list_open()}

        if command.index is not None:
            ids = self._listed or list(open_tasks)

            if not 1 <= command.index <= len(ids):
                return None, "No tengo ese número, Jefe."

            task = open_tasks.get(ids[command.index - 1])

            if task is None:
                return None, "Ese ya no está pendiente, Jefe."

            return task, ""

        needle = normalize(command.text)
        matches = [
            t for t in open_tasks.values() if needle in normalize(t.title)
        ]

        if not matches:
            return None, "No encontré ese pendiente, Jefe."

        if len(matches) > 1:
            return None, (
                "Hay varios, Jefe. Pídeme «qué tengo pendiente» y dime "
                "el número."
            )

        return matches[0], ""