from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from nova.core.commands import Command


class RequestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueuedRequest:
    command: Command
    conversation_id: UUID
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )