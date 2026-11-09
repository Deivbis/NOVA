from nova.core import Command, CoreOrchestrator, SystemService


def create_core():
    core = CoreOrchestrator()
    SystemService(core).register()

    return core


def test_ping_returns_pong():
    result = create_core().dispatch(Command(name=SystemService.PING))

    assert result.success
    assert result.value == "pong"


def test_status_reports_state_connectivity_and_capabilities():
    core = create_core()
    core.start()

    result = core.dispatch(Command(name=SystemService.STATUS))

    assert result.success
    assert result.value["state"] == "idle"
    assert result.value["connectivity"] == "unknown"
    assert "system" in result.value["capabilities"]


def test_registering_twice_does_not_fail():
    core = create_core()
    SystemService(core).register()

    assert core.dispatch(Command(name=SystemService.PING)).success