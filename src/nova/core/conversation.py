from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


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

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
