from nova.core.state import (
    ConnectivityState,
    NovaState,
    OrbState,
)

DOC_017_STATES = {
    "STARTING",
    "IDLE",
    "LISTENING",
    "PROCESSING",
    "THINKING",
    "EXECUTING",
    "SPEAKING",
    "WAITING_CONFIRMATION",
    "OFFLINE",
    "ERROR",
    "STOPPING",
    "STOPPED",
}


def test_nova_states_match_doc_017():
    assert {state.name for state in NovaState} == DOC_017_STATES


def test_nova_state_values_are_lowercase_names():
    for state in NovaState:
        assert state.value == state.name.lower()


def test_connectivity_states_exist():
    assert ConnectivityState.ONLINE.value == "online"
    assert ConnectivityState.OFFLINE.value == "offline"


def test_orb_states_exist():
    assert OrbState.IDLE.value == "idle"
    assert OrbState.LISTENING.value == "listening"
    assert OrbState.PROCESSING.value == "processing"
    assert OrbState.RESPONDING.value == "responding"