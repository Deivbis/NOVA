from collections import deque

from nova.core.requests import QueuedRequest, RequestStatus


class RequestQueue:
    """FIFO queue for pending NOVA requests."""

    def __init__(self) -> None:
        self._pending: deque[QueuedRequest] = deque()
        self._request_ids: set[str] = set()

    def enqueue(self, request: QueuedRequest) -> None:
        if request.status != RequestStatus.PENDING:
            raise ValueError(
                "Only pending requests can be enqueued."
            )

        command_id = str(request.command.command_id)

        if command_id in self._request_ids:
            raise ValueError(
                f"Request '{command_id}' is already queued."
            )

        self._pending.append(request)
        self._request_ids.add(command_id)

    def dequeue(self) -> QueuedRequest | None:
        if not self._pending:
            return None

        request = self._pending.popleft()
        self._request_ids.remove(
            str(request.command.command_id)
        )

        return request

    def peek(self) -> QueuedRequest | None:
        if not self._pending:
            return None

        return self._pending[0]

    @property
    def size(self) -> int:
        return len(self._pending)

    @property
    def is_empty(self) -> bool:
        return not self._pending
