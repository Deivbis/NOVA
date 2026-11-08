from nova.core import (
    Command,
    CoreOrchestrator,
    Event,
    NovaState,
    Result,
)
from nova.core.events import EventNames


def collect(core):
    received = []
    core.subscribe(received.append)

    return received


def test_successful_command_publishes_completed_event():
    core = CoreOrchestrator()
    core.register_command("test.ok", lambda c: Result.ok("hecho"))
    events = collect(core)

    core.dispatch(Command(name="test.ok"))

    assert len(events) == 1
    assert events[0].name == EventNames.COMMAND_COMPLETED
    assert events[0].payload["command"] == "test.ok"
    assert events[0].payload["success"] is True
    assert events[0].source == "core"


def test_failed_command_publishes_failed_event():
    core = CoreOrchestrator()
    events = collect(core)

    core.dispatch(Command(name="no.existe"))

    assert len(events) == 1
    assert events[0].name == EventNames.COMMAND_FAILED
    assert events[0].payload["success"] is False
    assert events[0].payload["error_code"] == "COMMAND_NOT_FOUND"


def test_state_change_publishes_event():
    core = CoreOrchestrator()
    events = collect(core)

    core.set_state(NovaState.IDLE)

    assert len(events) == 1
    assert events[0].name == EventNames.STATE_CHANGED
    assert events[0].payload["previous"] == NovaState.STARTING.value
    assert events[0].payload["current"] == NovaState.IDLE.value


def test_setting_same_state_publishes_nothing():
    core = CoreOrchestrator()
    events = collect(core)

    core.set_state(core.state)

    assert events == []


def test_events_never_include_command_payload():
    core = CoreOrchestrator()
    core.register_command("test.echo", lambda c: Result.ok("ok"))
    events = collect(core)

    core.dispatch(
        Command(name="test.echo", payload={"message": "secreto-123"})
    )

    assert "secreto-123" not in str(events[0].payload)
    assert "secreto-123" not in str(events[0].metadata)


def test_subscribe_and_unsubscribe_through_orchestrator():
    core = CoreOrchestrator()
    received = []

    unsubscribe = core.subscribe(received.append)
    core.publish(Event(name="test.event"))
    unsubscribe()
    core.publish(Event(name="test.event"))

    assert len(received) == 1