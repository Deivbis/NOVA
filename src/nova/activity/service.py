from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from nova.core.result import Result
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.audit_repository import AuditRepository

MAX_DAYS = 365


@dataclass(frozen=True)
class ActivityEvent:
    action: str
    created_at: datetime


@dataclass(frozen=True)
class ActivitySummary:
    events: list[ActivityEvent]
    total: int


class ActivityService:
    def __init__(
        self,
        repository: AuditRepository,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._repository = repository
        self._clock = clock

    def recent(self, days: int, limit: int = 50) -> Result[ActivitySummary]:
        days = max(1, min(MAX_DAYS, int(days)))
        since = (self._clock() - timedelta(days=days)).isoformat()

        try:
            rows = self._repository.recent(since, limit)
            total = self._repository.count(since)
        except RepositoryError:
            return Result.fail(
                "ACTIVITY_READ", "No se pudo leer la actividad."
            )

        try:
            events = [
                ActivityEvent(action, datetime.fromisoformat(stamp))
                for action, stamp in rows
            ]
        except ValueError:
            return Result.fail(
                "ACTIVITY_READ", "No se pudo leer la actividad."
            )

        return Result.ok(ActivitySummary(events, total))