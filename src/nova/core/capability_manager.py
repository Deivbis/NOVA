"""Capability Manager básico (DOC-017, DOC-018, DOC-023)."""

from nova.core.capabilities import Availability, Capability
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.core.state import ConnectivityState

logger = get_logger(__name__)


class CapabilityManager:
    """Registra las capacidades de NOVA y consulta su disponibilidad."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._disabled: set[str] = set()

    def register(self, capability: Capability) -> Result[None]:
        if capability.id in self._capabilities:
            logger.warning(
                "Capacidad duplicada: '%s'.",
                capability.id,
            )
            return Result.fail(
                code="CAPABILITY_ALREADY_REGISTERED",
                message=(
                    f"La capacidad '{capability.id}' ya está registrada."
                ),
            )

        self._capabilities[capability.id] = capability
        logger.debug("Capacidad registrada: '%s'.", capability.id)

        return Result.ok()

    def get(self, capability_id: str) -> Capability | None:
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> tuple[Capability, ...]:
        return tuple(
            self._capabilities[key]
            for key in sorted(self._capabilities)
        )

    def set_enabled(
        self,
        capability_id: str,
        enabled: bool,
    ) -> Result[None]:
        if capability_id not in self._capabilities:
            return Result.fail(
                code="CAPABILITY_NOT_FOUND",
                message=f"No existe la capacidad '{capability_id}'.",
            )

        if enabled:
            self._disabled.discard(capability_id)
        else:
            self._disabled.add(capability_id)

        logger.debug(
            "Capacidad '%s' %s.",
            capability_id,
            "activada" if enabled else "desactivada",
        )

        return Result.ok()

    def availability(
        self,
        capability_id: str,
        connectivity: ConnectivityState,
    ) -> Availability:
        capability = self._capabilities.get(capability_id)

        if capability is None:
            return Availability(
                available=False,
                code="CAPABILITY_NOT_FOUND",
                reason=f"No existe la capacidad '{capability_id}'.",
            )

        if capability_id in self._disabled:
            return Availability(
                available=False,
                code="CAPABILITY_DISABLED",
                reason=f"La capacidad '{capability.name}' está desactivada.",
            )

        if (
            capability.requires_internet
            and connectivity != ConnectivityState.ONLINE
        ):
            return Availability(
                available=False,
                code="INTERNET_REQUIRED",
                reason=(
                    f"La capacidad '{capability.name}' requiere "
                    f"conexión a Internet."
                ),
            )

        return Availability(available=True)