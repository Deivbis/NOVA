from nova.core.events import Event


def test_event_has_name():
    event = Event(name="nova.started")

    assert event.name == "nova.started"


def test_events_have_unique_ids():
    first = Event(name="test.event")
    second = Event(name="test.event")

    assert first.event_id != second.event_id