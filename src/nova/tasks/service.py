from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

from nova.core.result import Result
from nova.core.tasks import Task, TaskStatus
from nova.storage.repositories.task_repository import TaskRepository
from nova.tasks.timeparse import parse_when

MAX_TITLE = 200
LATE_MINUTES = 2


def format_due(due: datetime, now: datetime) -> str:
    local = due.astimezone(now.tzinfo)
    hour = local.strftime("%H:%M")
    days = (local.date() - now.date()).days

    if days == 0:
        return f"hoy a las {hour}"

    if days == 1:
        return f"mañana a las {hour}"

    return f"el {local:%d/%m} a las {hour}"


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        clock: Callable[[], datetime] = lambda: datetime.now().astimezone(),
    ) -> None:
        self._repository = repository
        self._clock = clock

    def now(self) -> datetime:
        return self._clock()

    def add_todo(self, title: str) -> Result[Task]:
        title = " ".join(title.split()).strip(" .")

        if not title:
            return Result.fail("TASK_EMPTY", "¿Qué quieres anotar?")

        if len(title) > MAX_TITLE:
            return Result.fail("TASK_TOO_LONG", "Eso es demasiado largo.")

        task = Task(title=title)
        self._repository.add(task)

        return Result.ok(task)

    def add_reminder(self, text: str) -> Result[Task]:
        title, due, error = parse_when(text, self._clock())

        if error:
            return Result.fail("TASK_INVALID_TIME", error)

        if due is None:
            return Result.fail(
                "TASK_NO_TIME",
                "¿Cuándo quieres que te lo recuerde? Por ejemplo "
                "«en 10 minutos» o «mañana a las 9».",
            )

        if not title:
            return Result.fail("TASK_EMPTY", "¿Qué quieres que te recuerde?")

        if len(title) > MAX_TITLE:
            return Result.fail("TASK_TOO_LONG", "Eso es demasiado largo.")

        task = Task(title=title, due_at=due.astimezone(timezone.utc))
        self._repository.add(task)

        return Result.ok(task)

    def list_open(self) -> list[Task]:
        return self._repository.list_open()

    def complete(self, task_id: UUID) -> bool:
        return self._repository.set_status(task_id, TaskStatus.DONE)

    def cancel(self, task_id: UUID) -> bool:
        return self._repository.set_status(task_id, TaskStatus.CANCELLED)

    def due_now(self) -> list[tuple[Task, bool]]:
        """Recordatorios vencidos (se marcan como avisados). bool = tarde."""
        now = self._clock()
        cutoff = (
            now.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        )
        result = []

        for task in self._repository.due(cutoff):
            if self._repository.set_status(task.task_id, TaskStatus.FIRED):
                late = now - task.due_at > timedelta(minutes=LATE_MINUTES)
                result.append((task, late))

        return result