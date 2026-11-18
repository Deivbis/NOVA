from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"
    FIRED = "fired"


@dataclass
class Task:
    title: str
    due_at: datetime | None = None  # UTC; None = pendiente sin hora
    status: TaskStatus = TaskStatus.PENDING
    task_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )