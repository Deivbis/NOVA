from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DONE = "done"


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Project:
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    progress: int = 0
    project_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)