"""Servicio básico del sistema (DOC-017, DOC-018, DOC-023)."""

from typing import Any

from nova.core.capabilities import Capability
from nova.core.commands import Command
from nova.core.orchestrator import CoreOrchestrator
from nova.core.result import Result


class SystemService:
    """Comprobaciones básicas de salud del Core."""

    PING = "system.ping"
    STATUS = "system.status"

    def __init__(self, core: CoreOrchestrator) -> None:
        self._core = core

    def register(self) -> None:
        """Registra la capacidad y los comandos del servicio."""
        self._core.capabilities.register(
            Capability(
                id="system",
                name="Sistema",
                description="Comprobaciones básicas del estado de NOVA.",
            )
        )
        self._core.register_command(self.PING, self.ping)
        self._core.register_command(self.STATUS, self.status)

    def ping(self, command: Command) -> Result[str]:
        return Result.ok("pong")

    def status(self, command: Command) -> Result[dict[str, Any]]:
        return Result.ok(
            {
                "state": self._core.state.value,
                "connectivity": self._core.connectivity.value,
                "capabilities": [
                    item.id
                    for item in self._core.capabilities.list_capabilities()
                ],
            }
        )