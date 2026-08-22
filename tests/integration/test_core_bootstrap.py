from nova.core import CoreOrchestrator, NovaState
from nova.main import create_core


def test_core_bootstrap():
    core = create_core()

    assert isinstance(core, CoreOrchestrator)
    assert core.state == NovaState.IDLE