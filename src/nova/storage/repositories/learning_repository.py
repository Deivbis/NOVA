import sqlite3
from datetime import datetime, timezone
from uuid import UUID, uuid4

from nova.core.learning import (
    LearningCandidate,
    LearningKind,
    LearningStatus,
)
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.write_transaction import write_transaction

_COLUMNS = (
    "id, key, kind, category, content, evidence, asked, status, "
    "created_at, updated_at"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LearningRepository:
    """Candidatos y observaciones. La auditoría nunca guarda contenido."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, candidate: LearningCandidate) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    f"INSERT INTO learning_candidates ({_COLUMNS}) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(candidate.candidate_id),
                        candidate.key,
                        candidate.kind.value,
                        candidate.category,
                        candidate.content,
                        candidate.evidence,
                        candidate.asked,
                        candidate.status.value,
                        candidate.created_at.isoformat(),
                        candidate.updated_at.isoformat(),
                    ),
                )
                self._audit(
                    "learning.proposed",
                    candidate.candidate_id,
                    candidate.category,
                )
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save candidate.") from exc

    def get(self, candidate_id: UUID) -> LearningCandidate | None:
        return self._one("id = ?", str(candidate_id))

    def get_by_key(self, key: str) -> LearningCandidate | None:
        return self._one("key = ?", key)

    def list_candidates(
        self,
        status: LearningStatus | None = None,
    ) -> list[LearningCandidate]:
        where = "WHERE status = ?" if status else ""
        params = (status.value,) if status else ()

        try:
            rows = self.connection.execute(
                f"SELECT {_COLUMNS} FROM learning_candidates {where} "
                "ORDER BY created_at ASC, id ASC",
                params,
            ).fetchall()

            return [self._to_candidate(row) for row in rows]
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to list candidates.") from exc

    def set_status(
        self,
        candidate_id: UUID,
        status: LearningStatus,
    ) -> bool:
        try:
            with write_transaction(self.connection):
                cursor = self.connection.execute(
                    "UPDATE learning_candidates "
                    "SET status = ?, updated_at = ? WHERE id = ?",
                    (status.value, _now(), str(candidate_id)),
                )

                if cursor.rowcount != 1:
                    return False

                row = self.connection.execute(
                    "SELECT category FROM learning_candidates WHERE id = ?",
                    (str(candidate_id),),
                ).fetchone()
                self._audit(
                    f"learning.{status.value}",
                    candidate_id,
                    str(row["category"]),
                )

                return True
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to update candidate.") from exc

    def mark_asked(self, candidate_id: UUID) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    "UPDATE learning_candidates "
                    "SET asked = asked + 1, updated_at = ? WHERE id = ?",
                    (_now(), str(candidate_id)),
                )
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to update candidate.") from exc

    def add_observation(
        self,
        topic: str,
        conversation_id: str,
        created_at: str,
    ) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    "INSERT INTO learning_observations "
                    "(id, topic, conversation_id, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (str(uuid4()), topic, conversation_id, created_at),
                )
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to save observation.") from exc

    def pattern_stats(self, topic: str, since: str) -> tuple[int, int]:
        """(mensajes, conversaciones distintas) desde `since`."""
        try:
            row = self.connection.execute(
                "SELECT COUNT(*) AS n, "
                "COUNT(DISTINCT conversation_id) AS c "
                "FROM learning_observations "
                "WHERE topic = ? AND created_at >= ?",
                (topic, since),
            ).fetchone()

            return int(row["n"]), int(row["c"])
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to read observations.") from exc

    def prune_observations(self, before: str) -> None:
        try:
            with write_transaction(self.connection):
                self.connection.execute(
                    "DELETE FROM learning_observations "
                    "WHERE created_at < ?",
                    (before,),
                )
        except sqlite3.Error as exc:
            raise RepositoryError("Unable to prune observations.") from exc

    def _one(self, condition: str, value: str) -> LearningCandidate | None:
        try:
            row = self.connection.execute(
                f"SELECT {_COLUMNS} FROM learning_candidates "
                f"WHERE {condition}",
                (value,),
            ).fetchone()

            return self._to_candidate(row) if row is not None else None
        except (sqlite3.Error, ValueError) as exc:
            raise RepositoryError("Unable to read candidate.") from exc

    def _audit(self, action: str, target: UUID, detail: str) -> None:
        self.connection.execute(
            "INSERT INTO audit_logs "
            "(id, action, target_type, target_id, detail, created_at) "
            "VALUES (?, ?, 'learning', ?, ?, ?)",
            (str(uuid4()), action, str(target), detail, _now()),
        )

    @staticmethod
    def _to_candidate(row: sqlite3.Row) -> LearningCandidate:
        return LearningCandidate(
            candidate_id=UUID(str(row["id"])),
            key=str(row["key"]),
            kind=LearningKind(str(row["kind"])),
            category=str(row["category"]),
            content=str(row["content"]),
            evidence=int(row["evidence"]),
            asked=int(row["asked"]),
            status=LearningStatus(str(row["status"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )