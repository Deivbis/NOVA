"""Contratos de capacidades (DOC-017).

DOC-017 menciona un "nivel de riesgo" sin definir los niveles. Se proponen
LOW, MEDIUM y HIGH, pendientes de ajustar cuando exista el módulo Security.
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Capability:
    """Algo que NOVA puede hacer."""

    id: str
    name: str
    description: str
    provider: str | None = None
    requires_internet: bool = False
    risk_level: RiskLevel = RiskLevel.LOW


@dataclass(frozen=True)
class Availability:
    """Si una capacidad está disponible ahora y, si no, por qué."""

    available: bool
    code: str | None = None
    reason: str | None = None