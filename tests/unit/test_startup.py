from nova.main import create_core, main
from nova.core import ConnectivityState, CoreOrchestrator, NovaState


def test_main_exists():
    assert callable(main)


def test_create_core_returns_orchestrator():
    core = create_core()

    assert isinstance(core, CoreOrchestrator)


def test_core_starts_idle():
    core = create_core()

    assert core.state == NovaState.IDLE


def test_core_starts_with_unknown_connectivity():
    core = create_core()

    assert core.connectivity == ConnectivityState.UNKNOWN