from typing import Any
from nova.core.capabilities import Availability
from nova.core.capability_manager import CapabilityManager
from nova.core.commands import Command
from nova.core.event_bus import EventBus, EventListener, Unsubscribe
from nova.core.events import Event, EventNames
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.core.services import CommandHandler
from nova.core.state import ConnectivityState, NovaState
from nova.core.state_manager import StateManager

logger = get_logger(__name__)


class CoreOrchestrator:
    def __init__(self) -> None:
        self._state_manager = StateManager()
        self._connectivity = ConnectivityState.UNKNOWN
        self._handlers: dict[str, CommandHandler] = {}
        self._event_bus = EventBus()
        self._capabilities = CapabilityManager()

    @property
    def state(self) -> NovaState:
        return self._state_manager.state

    @property
    def connectivity(self) -> ConnectivityState:
        return self._connectivity

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def capabilities(self) -> CapabilityManager:
        return self._capabilities

    def capability_availability(
        self,
        capability_id: str,
    ) -> Availability:
        """Disponibilidad de una capacidad con la conectividad actual."""
        return self._capabilities.availability(
            capability_id,
            self._connectivity,
        )

    def start(self) -> bool:
        """Inicia el Core: STARTING -> IDLE. Devuelve False si ya inició."""
        if self.state != NovaState.STARTING:
            logger.warning(
                "start() ignorado: el Core ya está en estado '%s'.",
                self.state.value,
            )
            return False

        self.set_state(NovaState.IDLE)
        self._event_bus.publish(
            Event(name=EventNames.CORE_STARTED, source="core")
        )
        logger.info("Core iniciado.")

        return True

    def stop(self) -> bool:
        """Detiene el Core: -> STOPPING -> STOPPED. Es seguro repetirlo."""
        if self.state in (NovaState.STOPPING, NovaState.STOPPED):
            return False

        self.set_state(NovaState.STOPPING)
        self.set_state(NovaState.STOPPED)
        self._event_bus.publish(
            Event(name=EventNames.CORE_STOPPED, source="core")
        )
        logger.info("Core detenido.")

        return True

    def set_state(self, state: NovaState) -> bool:
        """Cambia el estado. Devuelve False si la transición no es válida."""
        previous = self.state

        if not self._state_manager.transition_to(state):
            logger.warning(
                "Transición de estado no permitida: %s -> %s",
                previous.value,
                state.value,
            )
            return False

        if state == previous:
            return True

        logger.debug(
            "Estado: %s -> %s",
            previous.value,
            state.value,
        )

        self._event_bus.publish(
            Event(
                name=EventNames.STATE_CHANGED,
                payload={
                    "previous": previous.value,
                    "current": state.value,
                },
                source="core",
            )
        )

        return True

    def set_connectivity(
        self,
        connectivity: ConnectivityState,
    ) -> None:
        logger.debug(
            "Conectividad: %s -> %s",
            self._connectivity.value,
            connectivity.value,
        )
        self._connectivity = connectivity

    def register_command(
        self,
        command_name: str,
        handler: CommandHandler,
    ) -> None:
        self._handlers[command_name] = handler

    def subscribe(
        self,
        listener: EventListener,
        event_name: str | None = None,
    ) -> Unsubscribe:
        return self._event_bus.subscribe(listener, event_name)

    def publish(self, event: Event) -> None:
        self._event_bus.publish(event)

    def dispatch(
        self,
        command: Command,
    ) -> Result[Any]:
        result = self._execute(command)
        self._publish_command_result(command, result)

        return result

    def _execute(
        self,
        command: Command,
    ) -> Result[Any]:
        # Privacidad (SPEC-014 §9): se registra el nombre del comando,
        # nunca su payload.
        logger.debug(
            "Comando recibido: %s (id=%s, origen=%s)",
            command.name,
            command.command_id,
            command.source,
        )

        if (
            command.requires_internet
            and self._connectivity != ConnectivityState.ONLINE
        ):
            logger.warning(
                "Comando '%s' rechazado: requiere Internet "
                "(conectividad: %s).",
                command.name,
                self._connectivity.value,
            )
            return Result.fail(
                code="INTERNET_REQUIRED",
                message=(
                    "Esta solicitud requiere conexión a Internet "
                    "y NOVA no tiene conexión disponible."
                ),
            )

        handler = self._handlers.get(command.name)

        if handler is None:
            logger.warning(
                "Comando '%s' sin controlador registrado.",
                command.name,
            )
            return Result.fail(
                code="COMMAND_NOT_FOUND",
                message=(
                    f"No existe un controlador registrado para "
                    f"'{command.name}'."
                ),
            )

        try:
            result = handler(command)
        except Exception as exc:
            logger.exception(
                "Error ejecutando el comando '%s'.",
                command.name,
            )
            return Result.fail(
                code="COMMAND_EXECUTION_ERROR",
                message=str(exc),
            )

        logger.debug(
            "Comando '%s' terminado (éxito=%s).",
            command.name,
            result.success,
        )
        return result

    def _publish_command_result(
        self,
        command: Command,
        result: Result[Any],
    ) -> None:
        # Solo metadatos: nunca el payload ni el contenido del resultado.
        self._event_bus.publish(
            Event(
                name=(
                    EventNames.COMMAND_COMPLETED
                    if result.success
                    else EventNames.COMMAND_FAILED
                ),
                payload={
                    "command": command.name,
                    "command_id": str(command.command_id),
                    "success": result.success,
                    "error_code": (
                        result.error.code if result.error else None
                    ),
                },
                source="core",
            )
        )