from nova.core import CoreOrchestrator, EventNames, Identity
from nova.personality import IdentityService


class Holder:
    def __init__(self, identity=Identity.ATLAS):
        self.identity = identity
        self.sets = []

    def get(self):
        return self.identity

    def set(self, identity):
        self.sets.append(identity)
        self.identity = identity


def create_service():
    holder = Holder()
    core = CoreOrchestrator()
    events = []
    core.subscribe(events.append)
    service = IdentityService(
        core=core,
        get_identity=holder.get,
        set_identity=holder.set,
    )

    return service, holder, events


def test_current_reads_the_active_identity():
    service, holder, _ = create_service()

    assert service.current == Identity.ATLAS

    holder.identity = Identity.ASTI

    assert service.current == Identity.ASTI


def test_switch_applies_the_change_and_publishes_an_event():
    service, holder, events = create_service()

    assert service.switch(Identity.ASTI) is True

    assert holder.identity == Identity.ASTI
    assert [e.name for e in events] == [EventNames.IDENTITY_CHANGED]
    assert events[0].payload == {"identity": "asti", "previous": "atlas"}


def test_switching_to_the_active_identity_does_nothing():
    service, holder, events = create_service()

    assert service.switch(Identity.ATLAS) is False

    assert holder.sets == []
    assert events == []