"""Servicio de aprendizaje (SPEC-006, SPEC-015 §9-10, D-030).

Observar → detectar → pedir confirmación → guardar en memoria.
Nada se guarda sin un «sí» del usuario. Privacidad: nunca se registra
contenido.
"""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

from nova.core.learning import (
    LearningCandidate,
    LearningKind,
    LearningStatus,
)
from nova.core.logging_setup import get_logger
from nova.core.memory import Memory
from nova.core.result import Result
from nova.learning.detector import detect_explicit, detect_topics
from nova.memory.service import MemoryService
from nova.memory.text import normalize
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.learning_repository import (
    LearningRepository,
)
from nova.learning.detector import Topic, detect_explicit, detect_topics

logger = get_logger(__name__)

PATTERN_MIN_MESSAGES = 5
PATTERN_MIN_CONVERSATIONS = 3
PATTERN_WINDOW_DAYS = 30
SOURCE = "learned"
PATTERN_PREFIX = "Le interesa "
ALL_MESSAGES = "*"
MAX_OPEN_SHARE = 0.3


def _storage_error() -> Result:
    return Result.fail(
        code="LEARNING_STORAGE_ERROR",
        message="No se pudo acceder al aprendizaje.",
    )


class LearningService:
    def __init__(
        self,
        repository: LearningRepository,
        memory: MemoryService,
        get_enabled: Callable[[], bool],
        set_enabled: Callable[[bool], None],
    ) -> None:
        self._repository = repository
        self._memory = memory
        self._get_enabled = get_enabled
        self._set_enabled = set_enabled
        self._awaiting: UUID | None = None

    @property
    def enabled(self) -> bool:
        return self._get_enabled()

    @property
    def awaiting(self) -> bool:
        return self._awaiting is not None

    def set_enabled(self, value: bool) -> None:
        self._set_enabled(value)

        if not value:
            self._awaiting = None

    def observe(self, text: str, conversation_id: UUID) -> None:
        if not self.enabled:
            return

        try:
            explicit = detect_explicit(text)

            if explicit is not None:
                content, category = explicit
                self._register(
                    LearningKind.EXPLICIT,
                    category,
                    content,
                    normalize(content),
                )

            now = datetime.now(timezone.utc)
            since = (now - timedelta(days=PATTERN_WINDOW_DAYS)).isoformat()
            stamp, cid = now.isoformat(), str(conversation_id)

            self._repository.prune_observations(since)
            self._repository.add_observation(ALL_MESSAGES, cid, stamp)

            for topic in detect_topics(text):
                self._observe_topic(topic, cid, stamp, since)

        except RepositoryError:
            logger.exception("No se pudo registrar una observación.")

    def next_proposal(self) -> LearningCandidate | None:
        if not self.enabled or self._awaiting is not None:
            return None

        try:
            pending = self._repository.list_candidates(
                LearningStatus.PENDING
            )
            candidate = next((c for c in pending if c.asked == 0), None)

            if candidate is None:
                return None

            self._repository.mark_asked(candidate.candidate_id)
        except RepositoryError:
            logger.exception("No se pudo preparar una propuesta.")
            return None

        self._awaiting = candidate.candidate_id

        return candidate

    def resolve(
        self,
        accept: bool | None,
    ) -> Result[LearningCandidate] | None:
        """Aplica el sí/no a la propuesta en curso. None si no aplica."""
        candidate_id, self._awaiting = self._awaiting, None

        if candidate_id is None or accept is None:
            return None

        return (
            self.confirm(candidate_id)
            if accept
            else self.reject(candidate_id)
        )

    def confirm(self, candidate_id: UUID) -> Result[LearningCandidate]:
        try:
            candidate = self._repository.get(candidate_id)

            if candidate is None or candidate.status != LearningStatus.PENDING:
                return self._not_found()

            saved = self._memory.remember(
                candidate.content,
                candidate.category,
                source=SOURCE,
            )

            if not saved.success and saved.error.code != "MEMORY_DUPLICATE":
                return saved

            self._repository.set_status(
                candidate_id,
                LearningStatus.CONFIRMED,
            )
        except RepositoryError:
            logger.exception("No se pudo confirmar un aprendizaje.")
            return _storage_error()

        return Result.ok(candidate)

    def reject(self, candidate_id: UUID) -> Result[LearningCandidate]:
        try:
            candidate = self._repository.get(candidate_id)

            if candidate is None or candidate.status != LearningStatus.PENDING:
                return self._not_found()

            self._repository.set_status(
                candidate_id,
                LearningStatus.REJECTED,
            )
        except RepositoryError:
            logger.exception("No se pudo rechazar un aprendizaje.")
            return _storage_error()

        return Result.ok(candidate)

    def resolve_all(self, accept: bool) -> int:
        self._awaiting = None
        done = 0

        for candidate in self.pending():
            action = self.confirm if accept else self.reject

            if action(candidate.candidate_id).success:
                done += 1

        return done

    def pending(self) -> list[LearningCandidate]:
        try:
            return self._repository.list_candidates(LearningStatus.PENDING)
        except RepositoryError:
            return []

    def learned(self) -> list[Memory]:
        listed = self._memory.list_memories()

        if not listed.success:
            return []

        return [m for m in listed.value if m.source == SOURCE]

    def _register(
        self,
        kind: LearningKind,
        category: str,
        content: str,
        key: str,
        evidence: int = 1,
    ) -> None:
        # Cualquier estado previo (también «rechazado») evita repetir.
        if self._repository.get_by_key(key) is not None:
            return

        self._repository.add(
            LearningCandidate(
                key=key,
                kind=kind,
                category=category,
                content=content,
                evidence=evidence,
            )
        )

    def _observe_topic(
        self,
        topic: Topic,
        conversation_id: str,
        stamp: str,
        since: str,
    ) -> None:
        self._repository.add_observation(topic.key, conversation_id, stamp)
        messages, conversations = self._repository.pattern_stats(
            topic.key, since
        )

        if (
            messages < PATTERN_MIN_MESSAGES
            or conversations < PATTERN_MIN_CONVERSATIONS
        ):
            return

        if not topic.curated:
            total, _ = self._repository.pattern_stats(ALL_MESSAGES, since)

            if messages / total > MAX_OPEN_SHARE:
                return  # palabra demasiado común para ser un gusto

        self._register(
            LearningKind.PATTERN,
            topic.category,
            f"{PATTERN_PREFIX}{topic.display}",
            f"pattern:{topic.key}",
            evidence=messages,
        )

    @staticmethod
    def _not_found() -> Result:
        return Result.fail(
            code="LEARNING_NOT_FOUND",
            message="No existe ese aprendizaje pendiente.",
        )