from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Event:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)


class EventNames:
    """Nombres de los eventos estándar del Core."""

    COMMAND_COMPLETED = "command.completed"
    COMMAND_FAILED = "command.failed"
    STATE_CHANGED = "state.changed"
    CORE_STARTED = "core.started"
    CORE_STOPPED = "core.stopped"