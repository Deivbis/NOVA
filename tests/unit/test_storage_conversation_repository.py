import sqlite3
from uuid import UUID

from nova.core.conversation import (
    Conversation,
    ConversationMessage,
    MessageRole,
)
from nova.storage.migrations.versions import (
    v001_initial,
    v002_conversations,
)
from nova.storage.repositories.conversation_repository import (
    ConversationRepository,
)


def create_repository(tmp_path):
    connection = sqlite3.connect(
        tmp_path / "nova.db"
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    v001_initial.apply(connection)
    v002_conversations.apply(connection)

    return (
        connection,
        ConversationRepository(connection),
    )


def test_create_conversation(tmp_path):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = Conversation()

    repository.create(
        conversation,
        title="Prueba",
    )

    conversations = (
        repository.list_conversations()
    )

    assert len(conversations) == 1

    assert (
        conversations[0]["id"]
        == str(conversation.conversation_id)
    )

    assert (
        conversations[0]["title"]
        == "Prueba"
    )

    connection.close()


def test_create_preserves_conversation_identity(
    tmp_path,
):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = Conversation()

    repository.create(conversation)

    loaded = repository.get(
        conversation.conversation_id
    )

    assert loaded is not None

    assert (
        loaded.conversation_id
        == conversation.conversation_id
    )

    connection.close()


def test_save_and_retrieve_messages(tmp_path):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = Conversation()

    repository.create(conversation)

    message = conversation.add_user_message(
        "Hola NOVA"
    )

    repository.add_message(
        conversation.conversation_id,
        message,
    )

    loaded = repository.get(
        conversation.conversation_id
    )

    assert loaded is not None
    assert len(loaded.messages) == 1

    assert (
        loaded.messages[0].message_id
        == message.message_id
    )

    assert (
        loaded.messages[0].content
        == "Hola NOVA"
    )

    assert (
        loaded.messages[0].role
        == MessageRole.USER
    )

    connection.close()


def test_save_multiple_messages_preserves_order(
    tmp_path,
):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = Conversation()

    repository.create(conversation)

    first = conversation.add_user_message(
        "Primer mensaje"
    )

    second = conversation.add_assistant_message(
        "Segundo mensaje"
    )

    repository.add_message(
        conversation.conversation_id,
        first,
    )

    repository.add_message(
        conversation.conversation_id,
        second,
    )

    loaded = repository.get(
        conversation.conversation_id
    )

    assert loaded is not None

    assert loaded.messages == [
        first,
        second,
    ]

    connection.close()


def test_get_missing_conversation_returns_none(
    tmp_path,
):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = repository.get(
        UUID(
            "00000000-0000-0000-0000-000000000001"
        )
    )

    assert conversation is None

    connection.close()


def test_delete_conversation(tmp_path):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = Conversation()

    repository.create(conversation)

    message = conversation.add_user_message(
        "Mensaje"
    )

    repository.add_message(
        conversation.conversation_id,
        message,
    )

    assert repository.delete(
        conversation.conversation_id
    ) is True

    assert repository.get(
        conversation.conversation_id
    ) is None

    assert repository.get_messages(
        conversation.conversation_id
    ) == []

    assert repository.delete(
        conversation.conversation_id
    ) is False

    connection.close()

def test_update_title(tmp_path):
    connection, repository = create_repository(
        tmp_path
    )

    conversation = Conversation()

    repository.create(
        conversation,
        title="Nueva conversaci?n",
    )

    repository.update_title(
        conversation.conversation_id,
        "Mi conversaci?n",
    )

    conversations = (
        repository.list_conversations()
    )

    assert conversations[0]["title"] == (
        "Mi conversaci?n"
    )

    connection.close()

