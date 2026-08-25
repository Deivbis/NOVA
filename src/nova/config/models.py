from dataclasses import dataclass


@dataclass(frozen=True)
class NovaConfig:
    name: str
    version: str
    environment: str
    language: str


@dataclass(frozen=True)
class ExecutionConfig:
    mode: str
    debug: bool


@dataclass(frozen=True)
class ConnectivityConfig:
    internet_enabled: bool
    offline_mode_allowed: bool


@dataclass(frozen=True)
class OrbConfig:
    enabled: bool
    position: str
    size: str
    opacity: float
    click_through: bool
    gaming_mode: bool


@dataclass(frozen=True)
class UIConfig:
    theme: str
    orb: OrbConfig


@dataclass(frozen=True)
class VoiceConfig:
    enabled: bool
    wake_word_enabled: bool
    stt_enabled: bool
    tts_enabled: bool


@dataclass(frozen=True)
class PathsConfig:
    data: str
    database: str
    cache: str
    backups: str
    logs: str
    models: str


@dataclass(frozen=True)
class NOVAConfig:
    nova: NovaConfig
    execution: ExecutionConfig
    connectivity: ConnectivityConfig
    ui: UIConfig
    voice: VoiceConfig
    paths: PathsConfig