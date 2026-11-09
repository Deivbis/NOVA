import logging

from nova.core import Event, EventBus


def test_publish_reaches_all_subscribers():
    bus = EventBus()
    first, second = [], []

    bus.subscribe(first.append)
    bus.subscribe(second.append)
    bus.publish(Event(name="test.event"))

    assert len(first) == 1
    assert len(second) == 1


def test_subscriber_can_filter_by_event_name():
    bus = EventBus()
    received = []

    bus.subscribe(received.append, event_name="wanted.event")
    bus.publish(Event(name="other.event"))
    bus.publish(Event(name="wanted.event"))

    assert [event.name for event in received] == ["wanted.event"]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    received = []

    unsubscribe = bus.subscribe(received.append)
    bus.publish(Event(name="test.event"))
    unsubscribe()
    bus.publish(Event(name="test.event"))

    assert len(received) == 1
    assert bus.subscriber_count == 0


def test_failing_listener_does_not_block_others(caplog):
    bus = EventBus()
    received = []

    def broken(event):
        raise RuntimeError("boom")

    bus.subscribe(broken)
    bus.subscribe(received.append)

    with caplog.at_level(logging.ERROR, logger="nova"):
        bus.publish(Event(name="test.event"))

    assert len(received) == 1
    assert any("test.event" in r.message for r in caplog.records)


def test_listener_can_unsubscribe_during_publish():
    bus = EventBus()
    received = []
    holder = {}

    def once(event):
        received.append(event)
        holder["unsubscribe"]()

    holder["unsubscribe"] = bus.subscribe(once)

    bus.publish(Event(name="test.event"))
    bus.publish(Event(name="test.event"))

    assert len(received) == 1


def test_publish_without_subscribers_is_safe():
    EventBus().publish(Event(name="test.event"))


def test_event_has_source_and_metadata_defaults():
    event = Event(name="test.event")

    assert event.source == "system"
    assert event.metadata == {}