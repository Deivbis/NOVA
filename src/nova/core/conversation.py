from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

DEFAULT_HISTORY_MAX_MESSAGES = 20
DEFAULT_HISTORY_MAX_CHARS = 8000

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ConversationMessage:
    role: MessageRole
    content: str
    message_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Conversation:
    messages: list[ConversationMessage] = field(
        default_factory=list
    )
    conversation_id: UUID = field(
        default_factory=uuid4
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    title: str = "Nueva conversación"

    def add_user_message(
        self,
        content: str,
    ) -> ConversationMessage:
        message = ConversationMessage(
            role=MessageRole.USER,
            content=content,
        )

        self.messages.append(message)
        self._touch()

        return message

    def add_assistant_message(
        self,
        content: str,
    ) -> ConversationMessage:
        message = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content=content,
        )

        self.messages.append(message)
        self._touch()

        return message
    
    def history(
        self,
        max_messages: int = DEFAULT_HISTORY_MAX_MESSAGES,
        max_chars: int = DEFAULT_HISTORY_MAX_CHARS,
    ) -> list[dict[str, str]]:
        """Return the recent messages in the format used by AI providers.

        Takes the newest messages first until the message or character
        budget is exhausted. The newest message is always included.
        """
        selected: list[dict[str, str]] = []
        total_chars = 0

        for message in reversed(self.messages):
            if len(selected) >= max_messages:
                break

            total_chars += len(message.content)

            if selected and total_chars > max_chars:
                break

            selected.append(
                {
                    "role": message.role.value,
                    "content": message.content,
                }
            )

        selected.reverse()

        return selected
    
    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
