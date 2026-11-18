from dataclasses import dataclass
from enum import Enum

from nova.core.capabilities import RiskLevel


class ActionKind(str, Enum):
    OPEN_PROGRAM = "program"
    OPEN_FOLDER = "folder"
    OPEN_WEB = "web"
    MEDIA = "media"
    OPEN_FILE = "file"
    FILES_SCOPE = "files"



class FileOpKind(str, Enum):
    CREATE_DIR = "create_dir"
    COPY = "copy"
    MOVE = "move"
    RENAME = "rename"
    DELETE = "delete"
    ORGANIZE = "organize"


@dataclass(frozen=True)
class FileOperation:
    kind: FileOpKind
    label: str
    source: str | None = None
    dest: str | None = None
    moves: tuple[tuple[str, str], ...] = ()

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