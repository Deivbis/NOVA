"""State Manager de NOVA (DOC-017, DOC-018).

DOC-017 define los estados pero no las transiciones. Estas reglas son una
propuesta mínima basada en el ciclo de vida del Core:

- Los estados activos pueden cambiar libremente entre sí y pasar a
  ERROR o STOPPING.
- STARTING puede ir a cualquier estado activo, ERROR o STOPPING.
- ERROR solo se recupera a IDLE o pasa a STOPPING.
- STOPPING solo puede ir a STOPPED.
- STOPPED es final.
"""

from nova.core.state import NovaState

_ACTIVE_STATES = frozenset(
    {
        NovaState.IDLE,
        NovaState.LISTENING,
        NovaState.PROCESSING,
        NovaState.THINKING,
        NovaState.EXECUTING,
        NovaState.SPEAKING,
        NovaState.WAITING_CONFIRMATION,
        NovaState.OFFLINE,
    }
)

_ACTIVE_TARGETS = _ACTIVE_STATES | {NovaState.ERROR, NovaState.STOPPING}

_TRANSITIONS: dict[NovaState, frozenset[NovaState]] = {
    NovaState.STARTING: _ACTIVE_TARGETS,
    NovaState.ERROR: frozenset({NovaState.IDLE, NovaState.STOPPING}),
    NovaState.STOPPING: frozenset({NovaState.STOPPED}),
    NovaState.STOPPED: frozenset(),
    **{state: _ACTIVE_TARGETS for state in _ACTIVE_STATES},
}


class StateManager:
    """Guarda el estado global y valida sus transiciones."""

    def __init__(
        self,
        initial: NovaState = NovaState.STARTING,
    ) -> None:
        self._state = initial

    @property
    def state(self) -> NovaState:
        return self._state

    def can_transition_to(self, target: NovaState) -> bool:
        return target == self._state or target in _TRANSITIONS[self._state]

    def transition_to(self, target: NovaState) -> bool:
        """Aplica la transición. Devuelve False si no está permitida."""
        if not self.can_transition_to(target):
            return False

        self._state = target
        return True