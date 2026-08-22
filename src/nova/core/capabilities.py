from enum import Enum


class Capability(str, Enum):
    AI = "ai"
    VOICE_INPUT = "voice_input"
    VOICE_OUTPUT = "voice_output"
    MEMORY = "memory"
    STORAGE = "storage"
    AUTOMATION = "automation"
    SECURITY = "security"
    PLUGINS = "plugins"
    UI = "ui"
    INTERNET = "internet"