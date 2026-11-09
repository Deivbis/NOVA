import logging

from nova.core import (
    Command,
    CoreOrchestrator,
    NovaState,
    SystemService,
)
from nova.core.events import EventNames


def create_core():
    core = CoreOrchestrator()
    SystemService(core).register()

    return core


def test_command_flows_from_core_to_event_and_log(caplog):
    core = create_core()
    received = []
    core.subscribe(
        received.append,
        event_name=EventNames.COMMAND_COMPLETED,
    )
    core.start()

    with caplog.at_level(logging.DEBUG, logger="nova"):
        result = core.dispatch(
            Command(name=SystemService.PING, source="test")
        )

    assert result.success
    assert result.value == "pong"
    assert len(received) == 1
    assert received[0].payload["command"] == SystemService.PING
    assert any(SystemService.PING in r.message for r in caplog.records)
    assert core.state == NovaState.IDLE

    assert core.stop()


def test_full_lifecycle_publishes_events_in_order():
    core = create_core()
    names = []
    core.subscribe(lambda event: names.append(event.name))

    core.start()
    core.dispatch(Command(name=SystemService.PING))
    core.stop()

    assert names == [
        EventNames.STATE_CHANGED,
        EventNames.CORE_STARTED,
        EventNames.COMMAND_COMPLETED,
        EventNames.STATE_CHANGED,
        EventNames.STATE_CHANGED,
        EventNames.CORE_STOPPED,
    ]


def test_internet_command_is_rejected_without_connection():
    core = create_core()
    failed = []
    core.subscribe(failed.append, event_name=EventNames.COMMAND_FAILED)
    core.start()

    result = core.dispatch(
        Command(name=SystemService.PING, requires_internet=True)
    )

    assert not result.success
    assert result.error.code == "INTERNET_REQUIRED"
    assert len(failed) == 1
    assert failed[0].payload["error_code"] == "INTERNET_REQUIRED"