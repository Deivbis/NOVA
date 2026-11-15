import sqlite3
from datetime import datetime, timezone
from uuid import UUID, uuid4

from nova.core.memory import Memory, MemoryStatus
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction


class MemoryRepository:
    """Repository for persistent memories and their audit trail.

    Cada cambio se guarda junto con su entrada de auditoría en la misma
    transacción. La auditoría registra la acción, el id y la categoría,
    nunca el contenido (DOC-016, SPEC-014 §9).
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, memory: Memory) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    """
                    INSERT INTO memories (
                        id, category, content, status, source,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(memory.memory_id),
                        memory.category,
                        memory.content,
                        memory.status.value,
                        memory.source,
                        memory.created_at.isoformat(),
                        memory.updated_at.isoformat(),
                    ),
                )
                self._audit(
                    "memory.created",
                    memory.memory_id,
                    memory.category,
                )

        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save memory.") from exc

    def get(self, memory_id: UUID) -> Memory | None:
        try:
            row = self.connection.execute(
                """
                SELECT id, category, content, status, source,
                       created_at, updated_at
                FROM memories
                WHERE id = ?
                """,
                (str(memory_id),),
            ).fetchone()

            return self._to_memory(row) if row is not None else None

        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to retrieve memory.") from exc

    def list_memories(
        self,
        status: MemoryStatus | None = MemoryStatus.ACTIVE,
        category: str | None = None,
    ) -> list[Memory]:
        conditions: list[str] = []
        parameters: list[str] = []

        if status is not None:
            conditions.append("status = ?")
            parameters.append(status.value)

        if category is not None:
            conditions.append("category = ?")
            parameters.append(category)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        try:
            rows = self.connection.execute(
                f"""
                SELECT id, category, content, status, source,
                       created_at, updated_at
                FROM memories
                {where}
                ORDER BY created_at ASC, id ASC
                """,
                parameters,
            ).fetchall()

            return [self._to_memory(row) for row in rows]

        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to list memories.") from exc

    def update(
        self,
        memory_id: UUID,
        *,
        content: str | None = None,
        category: str | None = None,
    ) -> bool:
        """Edit a memory. Returns False if it does not exist."""
        assignments: list[str] = []
        parameters: list[str] = []

        if content is not None:
            assignments.append("content = ?")
            parameters.append(content)

        if category is not None:
            assignments.append("category = ?")
            parameters.append(category)

        if not assignments:
            return self.get(memory_id) is not None

        assignments.append("updated_at = ?")
        parameters.append(datetime.now(timezone.utc).isoformat())
        parameters.append(str(memory_id))

        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    f"""
                    UPDATE memories
                    SET {', '.join(assignments)}
                    WHERE id = ?
                    """,
                    parameters,
                )

                if cursor.rowcount != 1:
                    return False

                self._audit(
                    "memory.updated",
                    memory_id,
                    self._category_of(memory_id),
                )

                return True

        except sqlite3.Error as exc:
            raise RepositoryError("Unable to update memory.") from exc

    def set_status(
        self,
        memory_id: UUID,
        status: MemoryStatus,
    ) -> bool:
        """Deactivate or reactivate a memory (recoverable, DOC-016)."""
        action = (
            "memory.reactivated"
            if status == MemoryStatus.ACTIVE
            else "memory.deactivated"
        )

        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    """
                    UPDATE memories
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        status.value,
                        datetime.now(timezone.utc).isoformat(),
                        str(memory_id),
                    ),
                )

                if cursor.rowcount != 1:
                    return False

                self._audit(action, memory_id, self._category_of(memory_id))

                return True

        except sqlite3.Error as exc:
            raise RepositoryError("Unable to change memory status.") from exc

    def purge(self, memory_id: UUID) -> bool:
        """Delete a memory permanently. The audit entry is kept."""
        try:
            with write_transaction(self.connection):
                category = self._category_of(memory_id)

                cursor = self.connection.execute(
                    "DELETE FROM memories WHERE id = ?",
                    (str(memory_id),),
                )

                if cursor.rowcount != 1:
                    return False

                self._audit("memory.purged", memory_id, category)

                return True

        except sqlite3.Error as exc:
            raise RepositoryError("Unable to purge memory.") from exc

    def list_audit(self, limit: int = 50) -> list[dict[str, str]]:
        try:
            rows = self.connection.execute(
                """
                SELECT action, target_type, target_id, detail, created_at
                FROM audit_logs
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            return [
                {
                    "action": str(row["action"]),
                    "target_type": str(row["target_type"]),
                    "target_id": str(row["target_id"]),
                    "detail": str(row["detail"]),
                    "created_at": str(row["created_at"]),
                }
                for row in rows
            ]

        except sqlite3.Error as exc:
            raise RepositoryError("Unable to read the audit log.") from exc

    def _category_of(self, memory_id: UUID) -> str:
        row = self.connection.execute(
            "SELECT category FROM memories WHERE id = ?",
            (str(memory_id),),
        ).fetchone()

        return str(row["category"]) if row is not None else ""

    def _audit(self, action: str, memory_id: UUID, detail: str) -> None:
        self.connection.execute(
            """
            INSERT INTO audit_logs (
                id, action, target_type, target_id, detail, created_at
            )
            VALUES (?, ?, 'memory', ?, ?, ?)
            """,
            (
                str(uuid4()),
                action,
                str(memory_id),
                detail,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    @staticmethod
    def _to_memory(row: sqlite3.Row) -> Memory:
        return Memory(
            memory_id=UUID(str(row["id"])),
            category=str(row["category"]),
            content=str(row["content"]),
            status=MemoryStatus(str(row["status"])),
            source=str(row["source"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )