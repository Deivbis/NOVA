import pytest
from uuid import uuid4

from nova.core import (
    Command,
    QueuedRequest,
    RequestStatus,
)
from nova.core.request_queue import RequestQueue


def create_request(name: str = "test.command"):
    return QueuedRequest(
        command=Command(name=name),
        conversation_id=uuid4(),
    )


def test_queue_starts_empty():
    queue = RequestQueue()

    assert queue.is_empty is True
    assert queue.size == 0
    assert queue.dequeue() is None


def test_enqueue_increases_queue_size():
    queue = RequestQueue()

    queue.enqueue(create_request())

    assert queue.size == 1
    assert queue.is_empty is False


def test_queue_preserves_fifo_order():
    queue = RequestQueue()

    first = create_request("first.command")
    second = create_request("second.command")
    third = create_request("third.command")

    queue.enqueue(first)
    queue.enqueue(second)
    queue.enqueue(third)

    assert queue.dequeue() is first
    assert queue.dequeue() is second
    assert queue.dequeue() is third
    assert queue.is_empty is True


def test_peek_does_not_remove_request():
    queue = RequestQueue()
    request = create_request()

    queue.enqueue(request)

    assert queue.peek() is request
    assert queue.size == 1


def test_duplicate_pending_request_is_rejected():
    queue = RequestQueue()
    request = create_request()

    queue.enqueue(request)

    with pytest.raises(ValueError):
        queue.enqueue(request)

    assert queue.size == 1


def test_non_pending_request_is_rejected():
    queue = RequestQueue()

    request = create_request()
    request.status = RequestStatus.RUNNING

    with pytest.raises(ValueError):
        queue.enqueue(request)

    assert queue.is_empty is True


def test_dequeued_request_can_be_enqueued_again():
    queue = RequestQueue()
    request = create_request()

    queue.enqueue(request)
    queue.dequeue()

    queue.enqueue(request)

    assert queue.dequeue() is request