from dataclasses import dataclass

from nova.core import ConnectivityState, NovaState, OrbState


@dataclass(frozen=True)
class UIState:
    """Presentation state exposed to NOVA user interfaces."""

    nova_state: NovaState
    connectivity: ConnectivityState
    orb_state: OrbState

    @classmethod
    def from_core(
        cls,
        nova_state: NovaState,
        connectivity: ConnectivityState,
    ) -> "UIState":
        """Create a UI state from the current Core state."""
        orb_state = cls._map_orb_state(nova_state)

        return cls(
            nova_state=nova_state,
            connectivity=connectivity,
            orb_state=orb_state,
        )

    @staticmethod
    def _map_orb_state(nova_state: NovaState) -> OrbState:
        """Map a Core state to the state supported by the Orbe."""
        mapping = {
            NovaState.IDLE: OrbState.IDLE,
            NovaState.LISTENING: OrbState.LISTENING,
            NovaState.PROCESSING: OrbState.PROCESSING,
            NovaState.THINKING: OrbState.PROCESSING,
            NovaState.EXECUTING: OrbState.PROCESSING,
            NovaState.SPEAKING: OrbState.RESPONDING,
            NovaState.ERROR: OrbState.ERROR,
        }

        return mapping.get(
            nova_state,
            OrbState.IDLE,
        )