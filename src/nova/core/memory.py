"""Modelo de la memoria persistente autorizada (NOVA-SPEC-005, DOC-016)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

MEMORY_CATEGORIES = (
    "Programación",
    "Juegos",
    "Música",
    "Trabajo",
    "Estudios",
    "Salud",
    "Rutinas",
    "Familia",
    "Amigos",
    "Proyectos",
)

DEFAULT_CATEGORY = "General"

ALL_CATEGORIES = MEMORY_CATEGORIES + (DEFAULT_CATEGORY,)


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Memory:
    """Un recuerdo que el usuario ordenó guardar."""

    content: str
    category: str = DEFAULT_CATEGORY
    status: MemoryStatus = MemoryStatus.ACTIVE
    source: str = "user"
    memory_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)