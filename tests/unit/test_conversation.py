from datetime import datetime, timezone
from uuid import UUID

from nova.core.conversation import (
    Conversation,
    ConversationMessage,
    MessageRole,
)


def test_conversation_creates_unique_id():
    first = Conversation()
    second = Conversation()

    assert isinstance(first.conversation_id, UUID)
    assert isinstance(second.conversation_id, UUID)

    assert first.conversation_id != second.conversation_id


def test_conversation_starts_without_messages():
    conversation = Conversation()

    assert conversation.messages == []
    assert conversation.created_at.tzinfo == timezone.utc
    assert conversation.updated_at.tzinfo == timezone.utc


def test_add_user_message():
    conversation = Conversation()

    message = conversation.add_user_message(
        "Hola NOVA"
    )

    assert len(conversation.messages) == 1
    assert message.role == MessageRole.USER
    assert message.content == "Hola NOVA"
    assert message in conversation.messages


def test_add_assistant_message():
    conversation = Conversation()

    message = conversation.add_assistant_message(
        "Hola, Jefe."
    )

    assert len(conversation.messages) == 1
    assert message.role == MessageRole.ASSISTANT
    assert message.content == "Hola, Jefe."
    assert message in conversation.messages


def test_message_ids_are_unique():
    first = ConversationMessage(
        role=MessageRole.USER,
        content="Uno",
    )

    second = ConversationMessage(
        role=MessageRole.USER,
        content="Dos",
    )

    assert first.message_id != second.message_id


def test_updated_at_changes_when_message_is_added():
    conversation = Conversation()

    before = conversation.updated_at

    conversation.add_user_message(
        "Mensaje"
    )

    assert conversation.updated_at >= before


def test_conversation_preserves_message_order():
    conversation = Conversation()

    first = conversation.add_user_message(
        "Primer mensaje"
    )

    second = conversation.add_assistant_message(
        "Segundo mensaje"
    )

    assert conversation.messages == [
        first,
        second,
    ]
