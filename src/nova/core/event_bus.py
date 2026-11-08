"""Event Bus de NOVA (DOC-017, DOC-018, DOC-023)."""

from __future__ import annotations

import threading
from collections.abc import Callable

from nova.core.events import Event
from nova.core.logging_setup import get_logger

logger = get_logger(__name__)

EventListener = Callable[[Event], None]
Unsubscribe = Callable[[], None]


class EventBus:
    """Publica eventos a varios suscriptores sin acoplarlos entre sí."""

    def __init__(self) -> None:
        self._subscriptions: list[tuple[str | None, EventListener]] = []
        self._lock = threading.Lock()

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscriptions)

    def subscribe(
        self,
        listener: EventListener,
        event_name: str | None = None,
    ) -> Unsubscribe:
        """Suscribe un oyente. Con event_name=None recibe todos los eventos.

        Devuelve una función que cancela la suscripción.
        """
        subscription = (event_name, listener)

        with self._lock:
            self._subscriptions.append(subscription)

        def unsubscribe() -> None:
            with self._lock:
                if subscription in self._subscriptions:
                    self._subscriptions.remove(subscription)

        return unsubscribe

    def publish(self, event: Event) -> None:
        """Entrega el evento a los suscriptores interesados.

        Un suscriptor que falla se registra en el log y no impide que
        los demás reciban el evento.
        """
        with self._lock:
            subscriptions = list(self._subscriptions)

        for event_name, listener in subscriptions:
            if event_name is not None and event_name != event.name:
                continue

            try:
                listener(event)
            except Exception:
                logger.exception(
                    "Un suscriptor falló al recibir el evento '%s'.",
                    event.name,
                )