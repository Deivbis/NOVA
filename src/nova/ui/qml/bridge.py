from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import (
    QObject,
    Property,
    QThread,
    QTimer,
    Signal,
    Slot,
)

from nova.core import (
    Command,
    Conversation,
    CoreOrchestrator,
    NovaState,
)
from nova.core.logging_setup import get_logger
from nova.core.requests import QueuedRequest, RequestStatus
from nova.core.request_queue import RequestQueue
from nova.core.result import Result
from nova.storage.service import StorageService
from nova.ui.state import UIState

logger = get_logger(__name__)

ERROR_DISPLAY_MS = 2500
SHUTDOWN_WAIT_MS = 3000

class RequestWorker(QObject):
    """Execute one NOVA request outside the UI thread."""

    completed = Signal(object, object)

    def __init__(
        self,
        orchestrator: CoreOrchestrator,
        request: QueuedRequest,
    ) -> None:
        super().__init__()
        self._orchestrator = orchestrator
        self._request = request

    @Slot()
    def run(self) -> None:
        try:
            result = self._orchestrator.dispatch(
                self._request.command
            )
        except Exception as exc:
            result = Result.fail(
                code="REQUEST_EXECUTION_ERROR",
                message=str(exc),
            )

        self.completed.emit(
            self._request,
            result,
        )


class NovaUiBridge(QObject):
    """Bridge between NOVA Core state and the QML visual layer."""

    orbStateChanged = Signal()
    conversationChanged = Signal()
    conversationsChanged = Signal()

    def __init__(
        self,
        orchestrator: CoreOrchestrator,
        storage_service: StorageService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._orchestrator = orchestrator
        self._storage_service = storage_service

        repository = storage_service.conversation_repository

        if repository is None:
            raise RuntimeError(
                "StorageService must be initialized before "
                "NovaUiBridge."
            )

        self._request_queue = RequestQueue()
        self._requests_by_conversation: dict[UUID, int] = {}
        self._transient_errors: dict[UUID, str] = {}
        self._shutting_down = False

        self._active_thread: QThread | None = None
        self._active_worker: RequestWorker | None = None
        self._active_request: QueuedRequest | None = None

        self._conversation = self._load_or_create_conversation()

        self._ui_state = UIState.from_core(
            orchestrator.state,
            orchestrator.connectivity,
        )

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._refresh_state)
        self._timer.start()

    def _repository(self):
        repository = self._storage_service.conversation_repository

        if repository is None:
            raise RuntimeError(
                "Conversation repository is not initialized."
            )

        return repository

    def _load_or_create_conversation(self) -> Conversation:
        repository = self._repository()
        conversations = repository.list_conversations()

        if not conversations:
            conversation = Conversation()
            repository.create(
                conversation,
                title="Nueva conversación",
            )
            return conversation

        conversation_id = UUID(conversations[0]["id"])
        conversation = repository.get(conversation_id)

        if conversation is None:
            raise RuntimeError(
                "Unable to load the active conversation."
            )

        return conversation

    def _refresh_state(self) -> None:
        ui_state = UIState.from_core(
            self._orchestrator.state,
            self._orchestrator.connectivity,
        )

        if ui_state == self._ui_state:
            return

        previous_orb_state = self._ui_state.orb_state
        self._ui_state = ui_state

        if ui_state.orb_state != previous_orb_state:
            self.orbStateChanged.emit()

    def _get_orb_state(self) -> str:
        return self._ui_state.orb_state.value

    orbState = Property(
        str,
        _get_orb_state,
        notify=orbStateChanged,
    )

    def _get_messages(self) -> list[dict[str, str]]:
        messages = [
            {
                "role": message.role.value,
                "content": message.content,
            }
            for message in self._conversation.messages
        ]

        error_text = self._transient_errors.get(
            self._conversation.conversation_id
        )

        if error_text:
            # Mensaje transitorio: se muestra, pero no se guarda en la
            # conversación ni se envía al modelo.
            messages.append({"role": "error", "content": error_text})

        return messages

    messages = Property(
        list,
        _get_messages,
        notify=conversationChanged,
    )

    @staticmethod
    def _conversation_title_from_message(text: str) -> str:
        normalized = " ".join(text.split())

        if len(normalized) <= 45:
            return normalized

        preview = normalized[:42].rstrip()
        last_space = preview.rfind(" ")

        if last_space > 0:
            preview = preview[:last_space]

        return preview + "..."

    @Slot(str)
    def send_message(self, text: str) -> None:
        message = text.strip()

        if not message or self._shutting_down:
            return

        repository = self._repository()
        conversation_id = self._conversation.conversation_id

        self._transient_errors.pop(conversation_id, None)

        is_first_message = not self._conversation.messages

        user_message = self._conversation.add_user_message(message)

        try:
            repository.add_message(
                conversation_id,
                user_message,
            )

            if is_first_message:
                repository.update_title(
                    conversation_id,
                    self._conversation_title_from_message(message),
                )

        except Exception:
            self._reload_conversation(conversation_id)
            raise

        command = Command(
            name="chat.generate",
            payload={"messages": self._conversation.history()},
            source="user",
        )

        request = QueuedRequest(
            command=command,
            conversation_id=conversation_id,
        )

        try:
            self._request_queue.enqueue(request)
        except Exception:
            self._reload_conversation(conversation_id)
            raise

        self._requests_by_conversation[conversation_id] = (
            self._requests_by_conversation.get(conversation_id, 0) + 1
        )

        self.conversationChanged.emit()
        self.conversationsChanged.emit()

        self._enter_processing()

        self._process_next_request()

    def _process_next_request(self) -> None:
        if self._active_thread is not None:
            return

        request = self._request_queue.dequeue()

        if request is None:
            if self._orchestrator.state != NovaState.ERROR:
                self._orchestrator.set_state(NovaState.IDLE)
            return

        request.status = RequestStatus.RUNNING

        thread = QThread(self)
        worker = RequestWorker(
            self._orchestrator,
            request,
        )

        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.completed.connect(self._on_request_completed)
        worker.completed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_worker_thread_finished)
        thread.finished.connect(thread.deleteLater)

        self._active_thread = thread
        self._active_worker = worker
        self._active_request = request

        thread.start()

    @Slot(object, object)
    def _on_request_completed(
        self,
        request: QueuedRequest,
        result: Result,
    ) -> None:

        if self._shutting_down:
            return
        
        conversation_id = request.conversation_id

        if not result.success:
            request.status = RequestStatus.FAILED
            error = result.error

            code = error.code if error else "UNKNOWN"
            detail = error.message if error else "Error desconocido."

            logger.warning("La solicitud falló: %s", code)

            self._show_error(
                conversation_id,
                f"No pude completar tu solicitud. {detail}",
            )
            self._orchestrator.set_state(NovaState.ERROR)

        else:
            try:
                repository = self._repository()
                conversation = repository.get(conversation_id)

                if conversation is None:
                    raise RuntimeError(
                        "Conversation no longer exists."
                    )

                assistant_message = conversation.add_assistant_message(
                    result.value
                )

                repository.add_message(
                    conversation_id,
                    assistant_message,
                )

                request.status = RequestStatus.COMPLETED

                if self._conversation.conversation_id == conversation_id:
                    self._conversation = conversation
                    self.conversationChanged.emit()

                self.conversationsChanged.emit()

            except Exception:
                request.status = RequestStatus.FAILED

                logger.exception("No se pudo guardar la respuesta.")

                self._reload_conversation(conversation_id)
                self._show_error(
                    conversation_id,
                    "No pude guardar la respuesta en el historial.",
                )
                self._orchestrator.set_state(NovaState.ERROR)

        remaining = self._requests_by_conversation.get(
            conversation_id,
            0,
        ) - 1

        if remaining <= 0:
            self._requests_by_conversation.pop(
                conversation_id,
                None,
            )
        else:
            self._requests_by_conversation[conversation_id] = remaining

        if request.status == RequestStatus.COMPLETED:
            self._orchestrator.set_state(NovaState.SPEAKING)

    @Slot()
    def _on_worker_thread_finished(self) -> None:

        if self._shutting_down:
            return
        
        self._active_thread = None
        self._active_worker = None
        self._active_request = None

        if self._orchestrator.state == NovaState.ERROR:
            if self._request_queue.is_empty:
                # Deja visible el error un momento antes de volver a reposo.
                QTimer.singleShot(
                    ERROR_DISPLAY_MS,
                    self._recover_from_error,
                )
            else:
                self._enter_processing()
        elif self._request_queue.is_empty:
            self._orchestrator.set_state(NovaState.IDLE)
        else:
            self._orchestrator.set_state(NovaState.PROCESSING)

        self._process_next_request()

    def _enter_processing(self) -> None:
        if self._orchestrator.state == NovaState.ERROR:
            self._orchestrator.set_state(NovaState.IDLE)

        self._orchestrator.set_state(NovaState.PROCESSING)

    @Slot()
    def _recover_from_error(self) -> None:
        if (
            self._orchestrator.state == NovaState.ERROR
            and self._active_thread is None
        ):
            self._orchestrator.set_state(NovaState.IDLE)

    def _show_error(self, conversation_id: UUID, text: str) -> None:
        self._transient_errors[conversation_id] = text

        if self._conversation.conversation_id == conversation_id:
            self.conversationChanged.emit()

    def shutdown(self, wait_ms: int = SHUTDOWN_WAIT_MS) -> None:
        """Stop the bridge: no timer, no queued work, no running thread."""
        if self._shutting_down:
            return

        self._shutting_down = True
        self._timer.stop()

        while self._request_queue.dequeue() is not None:
            pass

        thread = self._active_thread
        self._active_thread = None
        self._active_worker = None
        self._active_request = None

        if thread is None:
            return

        try:
            thread.quit()

            if not thread.wait(wait_ms):
                logger.warning(
                    "La solicitud activa no terminó a tiempo; "
                    "se fuerza el cierre del hilo."
                )
                thread.terminate()
                thread.wait()
        except RuntimeError:
            # El objeto C++ ya fue destruido: no queda nada que esperar.
            pass

    def _reload_conversation(self, conversation_id: UUID) -> None:
        try:
            conversation = self._repository().get(conversation_id)
        except Exception:
            return

        if conversation is None:
            return

        if self._conversation.conversation_id == conversation_id:
            self._conversation = conversation
            self.conversationChanged.emit()

        self.conversationsChanged.emit()

    def _get_conversations(self) -> list[dict[str, str]]:
        return self._repository().list_conversations()

    conversations = Property(
        list,
        _get_conversations,
        notify=conversationsChanged,
    )

    def _get_active_conversation_id(self) -> str:
        return str(self._conversation.conversation_id)

    activeConversationId = Property(
        str,
        _get_active_conversation_id,
        notify=conversationChanged,
    )

    @Slot(str)
    def load_conversation(self, conversation_id: str) -> None:
        try:
            conversation_uuid = UUID(conversation_id)
        except ValueError as exc:
            raise RuntimeError("Invalid conversation id.") from exc

        conversation = self._repository().get(conversation_uuid)

        if conversation is None:
            raise RuntimeError("Conversation not found.")

        self._conversation = conversation
        self.conversationChanged.emit()

    @Slot(str, str)
    def rename_conversation(
        self,
        conversation_id: str,
        new_title: str,
    ) -> None:
        title = " ".join(new_title.split())

        if not title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        try:
            conversation_uuid = UUID(conversation_id)
        except ValueError as exc:
            raise RuntimeError("Invalid conversation id.") from exc

        self._repository().update_title(
            conversation_uuid,
            title,
        )

        self.conversationsChanged.emit()

    @Slot(str)
    def delete_conversation(self, conversation_id: str) -> None:
        try:
            conversation_uuid = UUID(conversation_id)
        except ValueError as exc:
            raise RuntimeError("Invalid conversation id.") from exc

        if self._requests_by_conversation.get(conversation_uuid, 0) > 0:
            logger.info(
                "No se puede borrar una conversación con solicitudes activas."
            )
            return

        repository = self._repository()
        is_active = conversation_uuid == self._conversation.conversation_id

        deleted = repository.delete(conversation_uuid)

        if not deleted:
            return

        self._transient_errors.pop(conversation_uuid, None)

        if is_active:
            self._conversation = self._load_or_create_conversation()
            self.conversationChanged.emit()

        self.conversationsChanged.emit()

    @Slot()
    def new_conversation(self) -> None:
        conversation = Conversation()

        self._repository().create(
            conversation,
            title="Nueva conversación",
        )

        self._conversation = conversation

        self.conversationsChanged.emit()
        self.conversationChanged.emit()