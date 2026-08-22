from collections.abc import Callable
from typing import Any, Protocol

from nova.core.commands import Command
from nova.core.events import Event
from nova.core.result import Result


class AIService(Protocol):
    def process(self, command: Command) -> Result[Any]:
        ...


class VoiceService(Protocol):
    def listen(self) -> Result[str]:
        ...

    def speak(self, text: str) -> Result[None]:
        ...


class MemoryService(Protocol):
    def remember(
        self,
        key: str,
        value: Any,
    ) -> Result[None]:
        ...

    def recall(
        self,
        key: str,
    ) -> Result[Any]:
        ...


class StorageService(Protocol):
    def save(
        self,
        key: str,
        value: Any,
    ) -> Result[None]:
        ...

    def load(
        self,
        key: str,
    ) -> Result[Any]:
        ...


class AutomationService(Protocol):
    def execute(
        self,
        command: Command,
    ) -> Result[Any]:
        ...


class SecurityService(Protocol):
    def authorize(
        self,
        command: Command,
    ) -> Result[bool]:
        ...


class PluginService(Protocol):
    def handle(
        self,
        command: Command,
    ) -> Result[Any]:
        ...


class UIService(Protocol):
    def publish_state(
        self,
        state: str,
    ) -> Result[None]:
        ...

    def publish_event(
        self,
        event: Event,
    ) -> Result[None]:
        ...


CommandHandler = Callable[[Command], Result[Any]]