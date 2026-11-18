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
    Event,
    EventNames,
    Identity,
    NovaState,
)
from nova.personality import (
    IdentityService,
    build_messages,
    parse_identity_command,
    profile_for,
)
from nova.memory import (
    MemoryCommandHandler,
    MemoryService,
    parse_memory_command,
)
from nova.core.logging_setup import get_logger
from nova.core.requests import QueuedRequest, RequestStatus
from nova.core.request_queue import RequestQueue
from nova.core.result import Result
from nova.storage.service import StorageService
from nova.ui.state import UIState
from nova.voice import VoiceInputService, VoiceService
from nova.learning import LearningCommandHandler, LearningService
from nova.automation import AutomationCommandHandler, AutomationService
from nova.automation import RoutineHandler
from nova.tasks import TaskCommandHandler, TaskService
from nova.storage.repositories.routine_repository import RoutineRepository
from concurrent.futures import Future
from nova.plugins import MainThread, PluginCommandHandler
import dataclasses
from datetime import datetime
from nova.ui.ui_settings import load_ui_settings, save_ui_settings

logger = get_logger(__name__)

ERROR_DISPLAY_MS = 2500
REMINDER_CHECK_MS = 15000
SHUTDOWN_WAIT_MS = 3000
_WEEKDAYS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
MAIN_CALL_TIMEOUT_S = 10

def _friendly_time(iso: str) -> str:
    try:
        moment = datetime.fromisoformat(iso).astimezone()
    except ValueError:
        return ""

    days = (datetime.now().astimezone().date() - moment.date()).days

    if days <= 0:
        return moment.strftime("%H:%M")

    if days == 1:
        return "Ayer"

    if days < 7:
        return _WEEKDAYS[moment.weekday()]

    return moment.strftime("%d/%m")

class RequestWorker(QObject):
    """Execute one NOVA request outside the UI thread."""

    completed = Signal(object, object)
    chunk = Signal(str)

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
            command = self._request.command
            payload = {**command.payload, "on_chunk": self.chunk.emit}
            result = self._orchestrator.dispatch(
                dataclasses.replace(command, payload=payload)
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
    voiceSettingsChanged = Signal()
    voiceErrorRaised = Signal(str)
    voiceTranscriptReady = Signal(str)
    identityChanged = Signal()
    streamChunk = Signal(str, str)
    requestFinished = Signal(str)
    localReply = Signal()
    navigateRequested = Signal(int)
    voiceProviderRaised = Signal(str)
    userNameChanged = Signal()
    permanentOrbChanged = Signal()
    pluginMainCall = Signal(object)

    def __init__(
        self,
        orchestrator: CoreOrchestrator,
        storage_service: StorageService,
        voice_service: VoiceService | None = None,
        voice_input: VoiceInputService | None = None,
        identity_service: IdentityService | None = None,
        memory_service: MemoryService | None = None,
        learning_service: LearningService | None = None,
        automation_service: AutomationService | None = None,
        task_service: TaskService | None = None,
        routine_repository: RoutineRepository | None = None,
        plugin_handler: PluginCommandHandler | None = None,
        plugin_gateway: MainThread | None = None,
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
        self._streams: dict[UUID, str] = {}
        self._current_page = 0
        self._voice_provider = ""
        self._ui_settings = load_ui_settings()
        self._unsubscribe_voice_started = None
        self._voice_service = voice_service
        self._voice_input = voice_input
        self._identity_service = identity_service
        self._memory_service = memory_service

        self._memory_handler = (
            MemoryCommandHandler(memory_service)
            if memory_service is not None
            else None
        )
        self._learning_handler = (
            LearningCommandHandler(learning_service)
            if learning_service is not None
            else None
        )

        self._unsubscribe_voice_errors = None
        self._automation_handler = (
            AutomationCommandHandler(automation_service)
            if automation_service is not None
            else None
        )
        self._task_handler = (
            TaskCommandHandler(task_service)
            if task_service is not None
            else None
        )
        self._routine_handler = (
            RoutineHandler(
                routine_repository,
                self._automation_handler,
                automation_service,
            )
            if routine_repository is not None
            and self._automation_handler is not None
            else None
        )
        self._plugin_handler = plugin_handler
        self.pluginMainCall.connect(self._run_on_main)

        if plugin_gateway is not None:
            plugin_gateway.bind(self._call_main, self._post_main)

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
        self._reminder_timer = QTimer(self)
        self._reminder_timer.setInterval(REMINDER_CHECK_MS)
        self._reminder_timer.timeout.connect(self._check_reminders)

        if self._task_handler is not None:
            self._reminder_timer.start()
            QTimer.singleShot(3000, self._check_reminders)

        if voice_service is not None or voice_input is not None:
            self.voiceErrorRaised.connect(self._on_voice_error)
            self.voiceProviderRaised.connect(self._on_voice_provider)

            self._unsubscribe_voice_errors = orchestrator.subscribe(
                self._on_voice_event,
                event_name=EventNames.VOICE_ERROR,
            )

            self._unsubscribe_voice_started = orchestrator.subscribe(
                self._on_voice_started,
                event_name=EventNames.VOICE_SPEAKING_STARTED,
            )

        if voice_input is not None:
            self.voiceTranscriptReady.connect(self._on_voice_transcript)
            voice_input.on_transcript = self.voiceTranscriptReady.emit

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

        target = parse_identity_command(message)

        if target is not None and self._identity_service is not None:
            self._switch_identity(conversation_id, target)
            return
        
        memory_command = parse_memory_command(message)

        if memory_command is not None and self._memory_handler is not None:
            self._reply_locally(
                conversation_id,
                self._memory_handler.handle(memory_command),
            )
            return
        
        for handler in (self._routine_handler, self._task_handler):
            reply = handler.reply_to(message) if handler is not None else None

            if reply is not None:
                self._reply_locally(conversation_id, reply)
                return
            
        if self._automation_handler is not None:
            automation_reply = self._automation_handler.reply_to(message)

            if automation_reply is not None:
                self._reply_locally(conversation_id, automation_reply)
                return

        if self._learning_handler is not None:
            learning_reply = self._learning_handler.reply_to(message)

            if learning_reply is not None:
                self._reply_locally(conversation_id, learning_reply)
                return

            self._learning_handler.observe(message, conversation_id)
        if self._plugin_handler is not None:
            plugin_reply = self._plugin_handler.reply_to(message)

            if plugin_reply is not None:
                self._reply_locally(conversation_id, plugin_reply)
                return

            if self._plugin_handler.dispatch(
                message,
                lambda text: self._reply_locally(
                    self._conversation.conversation_id, text
                ),
            ):
                return

        command = Command(
            name="chat.generate",
            payload={"messages": self._build_messages()},
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
            self._settle_to_idle()
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
        worker.chunk.connect(self._on_stream_chunk)
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

                reply = self._with_proposal(result.value)
                assistant_message = conversation.add_assistant_message(
                    reply
                )

                repository.add_message(
                    conversation_id,
                    assistant_message,
                )

                self.requestFinished.emit(str(conversation_id))

                request.status = RequestStatus.COMPLETED

                if self._conversation.conversation_id == conversation_id:
                    self._streams.pop(conversation_id, None)
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

            if self._voice_service is not None:
                self._voice_service.speak(reply)

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
            self._settle_to_idle()
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

    def _with_proposal(self, text: str) -> str:
        if self._learning_handler is None:
            return text

        proposal = self._learning_handler.proposal()

        return f"{text}\n\n{proposal}" if proposal else text

    def _build_messages(self) -> list[dict[str, str]]:
        history = self._conversation.history()

        if self._identity_service is None:
            return history

        memories: list[str] = []

        if self._memory_service is not None and history:
            memories = [
                item.content
                for item in self._memory_service.relevant_for(
                    history[-1]["content"]
                )
            ]

        return build_messages(
            self._identity_service.current,
            history,
            memories,
        )

    def _switch_identity(
        self,
        conversation_id: UUID,
        target: Identity,
    ) -> None:
        # Determinista: no pasa por el modelo y no pierde el contexto.
        self._identity_service.switch(target)

        reply = profile_for(target).confirmation
        assistant_message = self._conversation.add_assistant_message(reply)
        self._repository().add_message(conversation_id, assistant_message)

        self.localReply.emit()
        self.conversationChanged.emit()
        self.conversationsChanged.emit()
        self.identityChanged.emit()

        if self._voice_service is not None:
            self._voice_service.speak(reply)
            
    def _check_reminders(self) -> None:
        if self._shutting_down or self._task_handler is None:
            return

        if (
            self._voice_service is not None
            and self._voice_service.is_speaking
        ):
            return

        message = self._task_handler.due_messages()

        if message:
            self._reply_locally(self._conversation.conversation_id, message)
    @Slot(object)
    def _run_on_main(self, job) -> None:
        fn, future = job

        try:
            value = fn()
        except Exception as exc:
            if future is not None:
                future.set_exception(exc)
            else:
                logger.exception("Fallo de plugin en el hilo de la UI.")
            return

        if future is not None:
            future.set_result(value)

    def _call_main(self, fn):
        if self._shutting_down:
            raise RuntimeError("NOVA se está cerrando.")

        future: Future = Future()
        self.pluginMainCall.emit((fn, future))

        return future.result(timeout=MAIN_CALL_TIMEOUT_S)

    def _post_main(self, fn) -> None:
        self.pluginMainCall.emit((fn, None))

    def _reply_locally(self, conversation_id: UUID, reply: str) -> None:
        # Respuesta determinista (sin modelo): órdenes de memoria.
        assistant_message = self._conversation.add_assistant_message(reply)
        self._repository().add_message(conversation_id, assistant_message)

        self.conversationChanged.emit()
        self.conversationsChanged.emit()
        self.localReply.emit()

        if self._voice_service is not None:
            self._voice_service.speak(reply)

    def _get_active_identity(self) -> str:
        if self._identity_service is None:
            return Identity.ATLAS.value

        return self._identity_service.current.value

    activeIdentity = Property(
        str,
        _get_active_identity,
        notify=identityChanged,
    )

    def _settle_to_idle(self) -> None:
        if self._orchestrator.state == NovaState.ERROR:
            return

        if (
            self._voice_service is not None
            and self._voice_service.is_speaking
        ):
            return

        self._orchestrator.set_state(NovaState.IDLE)

    def _on_voice_event(self, event: Event) -> None:
        # Se ejecuta en un hilo de voz: solo emite una señal de Qt.
        detail = str(event.payload.get("message", ""))

        if not detail:
            return

        if event.payload.get("direction") == "input":
            prefix = "No pude escucharte."
        else:
            prefix = "No pude hablar."

        self.voiceErrorRaised.emit(f"{prefix} {detail}")

    @Slot(str)
    def _on_voice_error(self, message: str) -> None:
        if not message or self._shutting_down:
            return

        self._show_error(self._conversation.conversation_id, message)

    @Slot(str)
    def _on_voice_transcript(self, text: str) -> None:
        if self._current_page == 0:  # pantalla de inicio: chat nuevo
            self.start_conversation_with(text)
            self.navigateRequested.emit(1)
        else:
            self.send_message(text)

    @Slot()
    def toggle_voice_input(self) -> None:
        if self._voice_input is not None and not self._shutting_down:
            self._voice_input.toggle()

    def _get_voice_enabled(self) -> bool:
        if self._voice_service is None:
            return False

        return bool(self._voice_service.settings.enabled)

    voiceEnabled = Property(
        bool,
        _get_voice_enabled,
        notify=voiceSettingsChanged,
    )

    def _get_voice_identity(self) -> str:
        if self._voice_service is None:
            return Identity.ATLAS.value

        return self._voice_service.settings.identity.value

    voiceIdentity = Property(
        str,
        _get_voice_identity,
        notify=voiceSettingsChanged,
    )

    @Slot()
    def stop_speaking(self) -> None:
        if self._voice_service is not None:
            self._voice_service.stop()

    @Slot(bool)
    def set_voice_enabled(self, enabled: bool) -> None:
        if self._voice_service is None:
            return

        self._voice_service.update_settings(enabled=enabled)
        self.voiceSettingsChanged.emit()

    @Slot(str)
    def set_voice_identity(self, identity: str) -> None:
        if self._voice_service is None:
            return

        try:
            value = Identity(identity)
        except ValueError:
            return

        self._voice_service.update_settings(identity=value)
        self.voiceSettingsChanged.emit()

    @Slot(bool)
    def set_online_voice(self, enabled: bool) -> None:
        if self._voice_service is None:
            return

        self._voice_service.update_settings(prefer_online=enabled)
        self.voiceSettingsChanged.emit()

    def shutdown(self, wait_ms: int = SHUTDOWN_WAIT_MS) -> None:
        """Stop the bridge: no timer, no queued work, no running thread."""
        if self._shutting_down:
            return

        self._shutting_down = True
        self._timer.stop()
        self._reminder_timer.stop()

        if self._plugin_handler is not None:
            self._plugin_handler.shutdown()

        if self._unsubscribe_voice_errors is not None:
            self._unsubscribe_voice_errors()
            self._unsubscribe_voice_errors = None

        if self._unsubscribe_voice_started is not None:
            self._unsubscribe_voice_started()
            self._unsubscribe_voice_started = None

        if self._voice_input is not None:
            self._voice_input.shutdown()

        if self._voice_service is not None:
            self._voice_service.shutdown()

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

    @Slot(str, result=bool)
    def delete_conversation(self, conversation_id: str) -> bool:
        try:
            conversation_uuid = UUID(conversation_id)
        except ValueError as exc:
            raise RuntimeError("Invalid conversation id.") from exc

        if self._requests_by_conversation.get(conversation_uuid, 0) > 0:
            logger.info(
                "No se puede borrar una conversación con solicitudes activas."
            )
            return False

        repository = self._repository()
        is_active = conversation_uuid == self._conversation.conversation_id

        deleted = repository.delete(conversation_uuid)

        if not deleted:
            return False

        self._transient_errors.pop(conversation_uuid, None)

        if is_active:
            self._conversation = self._load_or_create_conversation()
            self.conversationChanged.emit()

        self.conversationsChanged.emit()

        return True

    @Slot()
    def new_conversation(self) -> None:
        if not self._conversation.messages:
            self.conversationChanged.emit()  # ya hay uno vacío: se reutiliza
            return

        conversation = Conversation()
        self._repository().create(conversation, title="Nueva conversación")
        self._conversation = conversation
        self.conversationsChanged.emit()
        self.conversationChanged.emit()

    # --- Interfaz (Fase 10) ---------------------------------------------
    def _get_chat_messages(self) -> list[dict]:
        cid = self._conversation.conversation_id
        items = [
            {
                "role": m.role.value,
                "content": m.content,
                "time": m.created_at.astimezone().strftime("%H:%M"),
                "streaming": False,
            }
            for m in self._conversation.messages
        ]
        partial = self._streams.get(cid)

        if partial:
            items.append({
                "role": "assistant", "content": partial,
                "time": "", "streaming": True,
            })

        error_text = self._transient_errors.get(cid)

        if error_text:
            items.append({
                "role": "error", "content": error_text,
                "time": "", "streaming": False,
            })

        return items

    chatMessages = Property(list, _get_chat_messages, notify=conversationChanged)

    @staticmethod
    def _preview(text: str) -> str:
        flat = " ".join(text.split())

        if not flat:
            return "Sin mensajes"

        return flat if len(flat) <= 42 else flat[:42] + "…"

    def _get_chat_list(self) -> list[dict[str, str]]:
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "preview": self._preview(row["preview"]),
                "time": _friendly_time(row["updated_at"]),
            }
            for row in self._repository().list_conversation_summaries()
        ]

    chatList = Property(list, _get_chat_list, notify=conversationsChanged)

    @Slot(str, result=bool)
    def is_busy(self, conversation_id: str) -> bool:
        try:
            return self._requests_by_conversation.get(UUID(conversation_id), 0) > 0
        except ValueError:
            return False

    @Slot(str)
    def start_conversation_with(self, text: str) -> None:
        """Inicio: crea un chat nuevo y envía el primer mensaje."""
        if not text.strip() or self._shutting_down:
            return

        self.new_conversation()
        self.send_message(text)

    @Slot(int)
    def set_current_page(self, page: int) -> None:
        self._current_page = page

    @Slot(str)
    def _on_stream_chunk(self, delta: str) -> None:
        request = self._active_request

        if request is None or self._shutting_down or not delta:
            return

        cid = request.conversation_id

        if cid not in self._streams:
            self._streams[cid] = ""

            if self._orchestrator.state == NovaState.PROCESSING:
                self._orchestrator.set_state(NovaState.SPEAKING)

        self._streams[cid] += delta
        self.streamChunk.emit(str(cid), delta)

    # --- Usuario y orbe permanente ----------------------------------------
    userName = Property(
        str, lambda s: s._ui_settings.user_name, notify=userNameChanged
    )
    permanentOrbEnabled = Property(
        bool, lambda s: s._ui_settings.orb_enabled, notify=permanentOrbChanged
    )

    @Slot(bool)
    def set_permanent_orb(self, enabled: bool) -> None:
        self._ui_settings = dataclasses.replace(
            self._ui_settings, orb_enabled=bool(enabled)
        )
        save_ui_settings(self._ui_settings)
        self.permanentOrbChanged.emit()

    # --- Voz: estado real y prueba -----------------------------------------
    voiceOnline = Property(
        bool,
        lambda s: bool(s._voice_service and s._voice_service.settings.prefer_online),
        notify=voiceSettingsChanged,
    )

    def _get_voice_status(self) -> str:
        service = self._voice_service

        if service is None:
            return "La voz no está disponible."

        if not service.settings.enabled:
            return "Voz desactivada."

        if "edge" in self._voice_provider:
            return "En uso: Edge (en línea)."

        error = service.online_error

        if service.settings.prefer_online:
            if error:
                return f"Edge no disponible ({error}); usando Piper."

            return "Voz en línea activada: se usará en la próxima respuesta."

        return "En uso: Piper (local)."

    voiceStatus = Property(str, _get_voice_status, notify=voiceSettingsChanged)

    def _on_voice_started(self, event: Event) -> None:
        # Hilo de voz: solo emite una señal de Qt.
        self.voiceProviderRaised.emit(str(event.payload.get("provider", "")))

    @Slot(str)
    def _on_voice_provider(self, provider: str) -> None:
        self._voice_provider = provider
        self.voiceSettingsChanged.emit()

    @Slot()
    def test_voice(self) -> None:
        if self._voice_service is not None:
            self._voice_service.speak("Hola, Jefe. Esta es mi voz.")