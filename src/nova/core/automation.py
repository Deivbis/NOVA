from dataclasses import dataclass
from enum import Enum

from nova.core.capabilities import RiskLevel


class ActionKind(str, Enum):
    OPEN_PROGRAM = "program"
    OPEN_FOLDER = "folder"
    OPEN_WEB = "web"
    MEDIA = "media"


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    target: str  # ruta, URL o comando multimedia
    label: str  # lo que se le dice al usuario
    key: str  # clave de permiso
    builtin: bool  # lista blanca incorporada


@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    requires_confirmation: bool
    risk_level: RiskLevel
    reason: str
    policy: str