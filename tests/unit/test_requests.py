from datetime import datetime, timezone
from uuid import uuid4

from nova.core import (
    Command,
    QueuedRequest,
    RequestStatus,
)


def test_queued_request_starts_pending():
    command = Command(name="test.command")
    conversation_id = uuid4()

    request = QueuedRequest(
        command=command,
        conversation_id=conversation_id,
    )

    assert request.status == RequestStatus.PENDING


def test_queued_request_preserves_command():
    command = Command(name="test.command")

    request = QueuedRequest(
        command=command,
        conversation_id=uuid4(),
    )

    assert request.command is command


def test_queued_request_preserves_conversation_id():
    conversation_id = uuid4()

    request = QueuedRequest(
        command=Command(name="test.command"),
        conversation_id=conversation_id,
    )

    assert request.conversation_id == conversation_id


def test_queued_request_status_can_change():
    request = QueuedRequest(
        command=Command(name="test.command"),
        conversation_id=uuid4(),
    )

    request.status = RequestStatus.RUNNING

    assert request.status == RequestStatus.RUNNING

    request.status = RequestStatus.COMPLETED

    assert request.status == RequestStatus.COMPLETED


def test_queued_request_has_utc_creation_time():
    request = QueuedRequest(
        command=Command(name="test.command"),
        conversation_id=uuid4(),
    )

    assert isinstance(request.created_at, datetime)
    assert request.created_at.tzinfo == timezone.utc


def test_each_queued_request_has_its_own_creation_time():
    first_request = QueuedRequest(
        command=Command(name="first.command"),
        conversation_id=uuid4(),
    )

    second_request = QueuedRequest(
        command=Command(name="second.command"),
        conversation_id=uuid4(),
    )

    assert first_request.created_at is not second_request.created_at