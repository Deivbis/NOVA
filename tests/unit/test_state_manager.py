from nova.core import NovaState
from nova.core.state_manager import StateManager

ACTIVE_STATES = (
    NovaState.IDLE,
    NovaState.LISTENING,
    NovaState.PROCESSING,
    NovaState.THINKING,
    NovaState.EXECUTING,
    NovaState.SPEAKING,
    NovaState.WAITING_CONFIRMATION,
    NovaState.OFFLINE,
)


def test_manager_starts_in_starting_state():
    assert StateManager().state == NovaState.STARTING


def test_active_states_can_change_freely():
    manager = StateManager()

    for target in ACTIVE_STATES:
        assert manager.transition_to(target)
        assert manager.state == target


def test_any_active_state_can_go_to_error_or_stopping():
    for state in ACTIVE_STATES:
        manager = StateManager(state)

        assert manager.can_transition_to(NovaState.ERROR)
        assert manager.can_transition_to(NovaState.STOPPING)


def test_error_can_only_recover_to_idle_or_stop():
    manager = StateManager(NovaState.ERROR)

    assert not manager.can_transition_to(NovaState.PROCESSING)
    assert manager.can_transition_to(NovaState.IDLE)
    assert manager.can_transition_to(NovaState.STOPPING)


def test_stopping_only_leads_to_stopped():
    manager = StateManager(NovaState.STOPPING)

    assert not manager.transition_to(NovaState.IDLE)
    assert manager.state == NovaState.STOPPING
    assert manager.transition_to(NovaState.STOPPED)


def test_stopped_is_terminal():
    manager = StateManager(NovaState.STOPPED)

    for state in NovaState:
        if state != NovaState.STOPPED:
            assert not manager.can_transition_to(state)


def test_starting_cannot_jump_to_stopped():
    assert not StateManager().can_transition_to(NovaState.STOPPED)