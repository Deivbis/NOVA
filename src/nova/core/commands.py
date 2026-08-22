from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Command:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    requires_internet: bool = False
    command_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )