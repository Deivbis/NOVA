import logging

from nova.core import CoreOrchestrator, NovaState
from nova.core.events import EventNames


def collect_names(core):
    names = []
    core.subscribe(lambda event: names.append(event.name))

    return names


def test_core_starts_in_starting_state():
    assert CoreOrchestrator().state == NovaState.STARTING


def test_start_moves_core_to_idle_and_publishes_event():
    core = CoreOrchestrator()
    names = collect_names(core)

    assert core.start() is True
    assert core.state == NovaState.IDLE
    assert EventNames.CORE_STARTED in names


def test_start_twice_is_ignored():
    core = CoreOrchestrator()
    core.start()

    assert core.start() is False
    assert core.state == NovaState.IDLE


def test_stop_ends_in_stopped_and_publishes_events():
    core = CoreOrchestrator()
    core.start()
    names = collect_names(core)

    assert core.stop() is True
    assert core.state == NovaState.STOPPED
    assert names.count(EventNames.STATE_CHANGED) == 2
    assert names[-1] == EventNames.CORE_STOPPED


def test_stop_twice_is_ignored():
    core = CoreOrchestrator()
    core.start()

    assert core.stop() is True
    assert core.stop() is False
    assert core.state == NovaState.STOPPED


def test_invalid_transition_is_rejected_and_logged(caplog):
    core = CoreOrchestrator()
    core.start()
    core.stop()

    with caplog.at_level(logging.WARNING, logger="nova"):
        assert core.set_state(NovaState.IDLE) is False

    assert core.state == NovaState.STOPPED
    assert any("stopped" in r.message for r in caplog.records)


def test_core_can_stop_from_error_state():
    core = CoreOrchestrator()
    core.start()
    core.set_state(NovaState.ERROR)

    assert core.stop() is True
    assert core.state == NovaState.STOPPED