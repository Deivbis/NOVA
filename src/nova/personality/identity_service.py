"""Identidad activa de NOVA (SPEC-002, D-017, D-027)."""

from collections.abc import Callable

from nova.core.events import Event, EventNames
from nova.core.identity import Identity
from nova.core.logging_setup import get_logger
from nova.core.orchestrator import CoreOrchestrator

logger = get_logger(__name__)


class IdentityService:
    """Lee y cambia la identidad activa; la persistencia la pone quien lo crea."""

    def __init__(
        self,
        core: CoreOrchestrator,
        get_identity: Callable[[], Identity],
        set_identity: Callable[[Identity], None],
    ) -> None:
        self._core = core
        self._get = get_identity
        self._set = set_identity

    @property
    def current(self) -> Identity:
        return self._get()

    def switch(self, target: Identity) -> bool:
        """Cambia de identidad. Devuelve False si ya estaba activa."""
        previous = self.current

        if target == previous:
            return False

        self._set(target)
        logger.info("Identidad activa: %s", target.value)

        self._core.publish(
            Event(
                name=EventNames.IDENTITY_CHANGED,
                payload={
                    "identity": target.value,
                    "previous": previous.value,
                },
                source="personality",
            )
        )

        return True