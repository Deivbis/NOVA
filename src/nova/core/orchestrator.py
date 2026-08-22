from collections.abc import Callable
from typing import Any

from nova.core.commands import Command
from nova.core.events import Event
from nova.core.result import Result
from nova.core.services import CommandHandler
from nova.core.state import ConnectivityState, NovaState


class CoreOrchestrator:
    def __init__(self) -> None:
        self._state = NovaState.STARTING
        self._connectivity = ConnectivityState.UNKNOWN
        self._handlers: dict[str, CommandHandler] = {}
        self._event_listeners: list[Callable[[Event], None]] = []

    @property
    def state(self) -> NovaState:
        return self._state

    @property
    def connectivity(self) -> ConnectivityState:
        return self._connectivity

    def set_state(self, state: NovaState) -> None:
        self._state = state

    def set_connectivity(
        self,
        connectivity: ConnectivityState,
    ) -> None:
        self._connectivity = connectivity

    def register_command(
        self,
        command_name: str,
        handler: CommandHandler,
    ) -> None:
        self._handlers[command_name] = handler

    def subscribe(
        self,
        listener: Callable[[Event], None],
    ) -> None:
        self._event_listeners.append(listener)

    def publish(self, event: Event) -> None:
        for listener in self._event_listeners:
            listener(event)

    def dispatch(
        self,
        command: Command,
    ) -> Result[Any]:
        if (
            command.requires_internet
            and self._connectivity != ConnectivityState.ONLINE
        ):
            return Result.fail(
                code="INTERNET_REQUIRED",
                message=(
                    "Esta solicitud requiere conexión a Internet "
                    "y NOVA no tiene conexión disponible."
                ),
            )

        handler = self._handlers.get(command.name)

        if handler is None:
            return Result.fail(
                code="COMMAND_NOT_FOUND",
                message=(
                    f"No existe un controlador registrado para "
                    f"'{command.name}'."
                ),
            )

        try:
            return handler(command)
        except Exception as exc:
            self._state = NovaState.ERROR

            return Result.fail(
                code="COMMAND_EXECUTION_ERROR",
                message=str(exc),
            )