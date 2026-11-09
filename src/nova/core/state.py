from enum import Enum


class NovaState(str, Enum):
    """Estados globales de NOVA (DOC-017)."""

    STARTING = "starting"
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    THINKING = "thinking"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    WAITING_CONFIRMATION = "waiting_confirmation"
    OFFLINE = "offline"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ConnectivityState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class OrbState(str, Enum):
    """Estados visuales del orbe (SPEC-008 y SPEC-009)."""

    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ERROR = "error"