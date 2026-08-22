from nova.core.state import (
    ConnectivityState,
    NovaState,
    OrbState,
)


def test_nova_states_exist():
    assert NovaState.IDLE.value == "idle"
    assert NovaState.LISTENING.value == "listening"
    assert NovaState.PROCESSING.value == "processing"
    assert NovaState.RESPONDING.value == "responding"
    assert NovaState.ERROR.value == "error"


def test_connectivity_states_exist():
    assert ConnectivityState.ONLINE.value == "online"
    assert ConnectivityState.OFFLINE.value == "offline"


def test_orb_states_exist():
    assert OrbState.IDLE.value == "idle"
    assert OrbState.LISTENING.value == "listening"
    assert OrbState.PROCESSING.value == "processing"
    assert OrbState.RESPONDING.value == "responding"