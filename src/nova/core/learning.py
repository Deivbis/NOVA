from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class LearningKind(str, Enum):
    EXPLICIT = "explicit"
    PATTERN = "pattern"


class LearningStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class LearningCandidate:
    key: str
    kind: LearningKind
    category: str
    content: str
    evidence: int = 1
    asked: int = 0
    status: LearningStatus = LearningStatus.PENDING
    candidate_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)