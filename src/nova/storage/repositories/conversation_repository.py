
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from uuid import UUID, uuid4

from nova.core.conversation import (
    Conversation,
    ConversationMessage,
    MessageRole,
)
from nova.storage.exceptions import RepositoryError


class ConversationRepository:
    """Repository for persistent NOVA conversations."""

    def __init__(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self.connection = connection

    @contextmanager
    def _write_transaction(self) -> Iterator[None]:
        """
        Manage repository writes without breaking outer transactions.

        Uses a savepoint when another transaction is already active.
        """
        savepoint = f"nova_repo_{uuid4().hex}"
        owns_transaction = not self.connection.in_transaction

        try:
            if owns_transaction:
                self.connection.execute("BEGIN")
            else:
                self.connection.execute(
                    f"SAVEPOINT {savepoint}"
                )

            yield

            if owns_transaction:
                self.connection.commit()
            else:
                self.connection.execute(
                    f"RELEASE SAVEPOINT {savepoint}"
                )

        except Exception:
            try:
                if owns_transaction:
                    self.connection.rollback()
                else:
                    self.connection.execute(
                        f"ROLLBACK TO SAVEPOINT {savepoint}"
                    )
                    self.connection.execute(
                        f"RELEASE SAVEPOINT {savepoint}"
                    )
            except sqlite3.Error as rollback_error:
                raise RepositoryError(
                    "Unable to rollback repository transaction."
                ) from rollback_error

            raise

    def create(
        self,
        conversation: Conversation,
        title: str = "Nueva conversación",
    ) -> None:
        try:
            with self._write_transaction():
                self.connection.execute(
                    """
                    INSERT INTO conversations (
                        id,
                        title,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(conversation.conversation_id),
                        title,
                        conversation.created_at.isoformat(),
                        conversation.updated_at.isoformat(),
                    ),
                )

        except sqlite3.Error as exc:
            raise RepositoryError(
                "Unable to create conversation."
            ) from exc

    def add_message(
        self,
        conversation_id: UUID,
        message: ConversationMessage,
    ) -> None:
        try:
            with self._write_transaction():
                cursor = self.connection.execute(
                    """
                    INSERT INTO conversation_messages (
                        id,
                        conversation_id,
                        role,
                        content,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(message.message_id),
                        str(conversation_id),
                        message.role.value,
                        message.content,
                        message.created_at.isoformat(),
                    ),
                )

                if cursor.rowcount != 1:
                    raise RepositoryError(
                        "Unable to confirm saved conversation message."
                    )

                self.connection.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        message.created_at.isoformat(),
                        str(conversation_id),
                    ),
                )

                if self.connection.execute(
                    """
                    SELECT changes()
                    """
                ).fetchone()[0] != 1:
                    raise RepositoryError(
                        "Conversation not found."
                    )

        except sqlite3.Error as exc:
            raise RepositoryError(
                "Unable to save conversation message."
            ) from exc

    def update_title(
        self,
        conversation_id: UUID,
        title: str,
    ) -> None:
        normalized_title = " ".join(title.split())

        if not normalized_title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        now = datetime.now(timezone.utc).isoformat()

        try:
            with self._write_transaction():
                cursor = self.connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        normalized_title,
                        now,
                        str(conversation_id),
                    ),
                )

                if cursor.rowcount != 1:
                    raise RepositoryError(
                        "Conversation not found."
                    )

        except sqlite3.Error as exc:
            raise RepositoryError(
                "Unable to update conversation title."
            ) from exc

    def get(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:
        try:
            conversation_row = self.connection.execute(
                """
                SELECT
                    id,
                    created_at,
                    updated_at
                FROM conversations
                WHERE id = ?
                """,
                (str(conversation_id),),
            ).fetchone()

            if conversation_row is None:
                return None

            messages = self.get_messages(
                conversation_id
            )

            return Conversation(
                messages=messages,
                conversation_id=UUID(
                    str(conversation_row["id"])
                ),
                created_at=datetime.fromisoformat(
                    str(conversation_row["created_at"])
                ),
                updated_at=datetime.fromisoformat(
                    str(conversation_row["updated_at"])
                ),
            )

        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError(
                "Unable to retrieve conversation."
            ) from exc

    def list_conversations(
        self,
    ) -> list[dict[str, str]]:
        try:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    title,
                    created_at,
                    updated_at
                FROM conversations
                ORDER BY
                    updated_at DESC,
                    id DESC
                """
            ).fetchall()

            return [
                {
                    "id": str(row["id"]),
                    "title": str(row["title"]),
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                }
                for row in rows
            ]

        except sqlite3.Error as exc:
            raise RepositoryError(
                "Unable to list conversations."
            ) from exc

    def get_messages(
        self,
        conversation_id: UUID,
    ) -> list[ConversationMessage]:
        try:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    role,
                    content,
                    created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY
                    created_at ASC,
                    id ASC
                """,
                (str(conversation_id),),
            ).fetchall()

            return [
                ConversationMessage(
                    message_id=UUID(str(row["id"])),
                    role=MessageRole(str(row["role"])),
                    content=str(row["content"]),
                    created_at=datetime.fromisoformat(
                        str(row["created_at"])
                    ),
                )
                for row in rows
            ]

        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError(
                "Unable to retrieve conversation messages."
            ) from exc

    def delete(
        self,
        conversation_id: UUID,
    ) -> bool:
        try:
            with self._write_transaction():
                cursor = self.connection.execute(
                    """
                    DELETE FROM conversations
                    WHERE id = ?
                    """,
                    (str(conversation_id),),
                )

                return cursor.rowcount > 0

        except sqlite3.Error as exc:
            raise RepositoryError(
                "Unable to delete conversation."
            ) from exc
