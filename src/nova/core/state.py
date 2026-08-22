from enum import Enum


class NovaState(str, Enum):
    STARTING = "starting"
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    WAITING_CONFIRMATION = "waiting_confirmation"
    OFFLINE = "offline"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class ConnectivityState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class OrbState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ERROR = "error"