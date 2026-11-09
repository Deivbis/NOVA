from nova.core import ConnectivityState, NovaState, OrbState
from nova.ui import UIState


def test_ui_state_maps_idle() -> None:
    state = UIState.from_core(
        NovaState.IDLE,
        ConnectivityState.ONLINE,
    )

    assert state.nova_state == NovaState.IDLE
    assert state.connectivity == ConnectivityState.ONLINE
    assert state.orb_state == OrbState.IDLE


def test_ui_state_maps_listening() -> None:
    state = UIState.from_core(
        NovaState.LISTENING,
        ConnectivityState.ONLINE,
    )

    assert state.orb_state == OrbState.LISTENING


def test_ui_state_maps_processing() -> None:
    state = UIState.from_core(
        NovaState.PROCESSING,
        ConnectivityState.ONLINE,
    )

    assert state.orb_state == OrbState.PROCESSING


def test_ui_state_maps_responding() -> None:
    state = UIState.from_core(
        NovaState.SPEAKING,
        ConnectivityState.ONLINE,
    )

    assert state.orb_state == OrbState.RESPONDING


def test_ui_state_maps_error() -> None:
    state = UIState.from_core(
        NovaState.ERROR,
        ConnectivityState.UNKNOWN,
    )

    assert state.orb_state == OrbState.ERROR


def test_ui_state_defaults_unsupported_orb_states_to_idle() -> None:
    unsupported_states = (
        NovaState.STARTING,
        NovaState.WAITING_CONFIRMATION,
        NovaState.OFFLINE,
        NovaState.STOPPING,
        NovaState.STOPPED,
    )

    for nova_state in unsupported_states:
        state = UIState.from_core(
            nova_state,
            ConnectivityState.UNKNOWN,
        )

        assert state.orb_state == OrbState.IDLE

def test_ui_state_maps_thinking_and_executing_to_processing() -> None:
    for nova_state in (NovaState.THINKING, NovaState.EXECUTING):
        state = UIState.from_core(
            nova_state,
            ConnectivityState.ONLINE,
        )

        assert state.orb_state == OrbState.PROCESSING