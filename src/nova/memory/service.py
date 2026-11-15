"""Servicio de memoria (SPEC-005, SPEC-014 §17, D-029).

Único punto de acceso a los recuerdos: el resto de módulos no consulta
SQLite directamente. Privacidad (SPEC-014 §9): nunca se registra el
contenido de un recuerdo.
"""

from uuid import UUID

from nova.core.logging_setup import get_logger
from nova.core.memory import Memory, MemoryStatus
from nova.core.result import Result
from nova.memory.classifier import classify, normalize_category
from nova.memory.relevance import MAX_CHARS, MAX_ITEMS, select_relevant
from nova.memory.text import normalize
from nova.storage.exceptions import RepositoryError
from nova.storage.repositories.memory_repository import MemoryRepository

logger = get_logger(__name__)

MAX_CONTENT_CHARS = 500
FIND_LIMIT = 10


def _storage_error() -> Result:
    return Result.fail(
        code="MEMORY_STORAGE_ERROR",
        message="No se pudo acceder a la memoria.",
    )


class MemoryService:
    """Guarda, busca, edita y olvida recuerdos autorizados por el usuario."""

    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository

    def remember(
        self,
        text: str,
        category: str | None = None,
        source: str = "user",
    ) -> Result[Memory]:
        content = " ".join(text.split())

        if not content:
            return Result.fail(
                code="EMPTY_MEMORY",
                message="No hay nada que recordar.",
            )

        if len(content) > MAX_CONTENT_CHARS:
            return Result.fail(
                code="MEMORY_TOO_LONG",
                message=(
                    f"El recuerdo supera los {MAX_CONTENT_CHARS} caracteres."
                ),
            )

        chosen = normalize_category(category) if category else classify(content)

        if chosen is None:
            return Result.fail(
                code="INVALID_CATEGORY",
                message="Esa categoría no existe.",
            )

        try:
            key = normalize(content)
            active = self._repository.list_memories(status=MemoryStatus.ACTIVE)

            if any(normalize(item.content) == key for item in active):
                return Result.fail(
                    code="MEMORY_DUPLICATE",
                    message="Ya está anotado.",
                )

            memory = Memory(content=content, category=chosen, source=source)
            self._repository.add(memory)

        except RepositoryError:
            logger.exception("No se pudo guardar un recuerdo.")
            return _storage_error()

        logger.info("Recuerdo guardado (categoría: %s).", memory.category)

        return Result.ok(memory)

    def list_memories(
        self,
        category: str | None = None,
        include_inactive: bool = False,
    ) -> Result[list[Memory]]:
        try:
            memories = self._repository.list_memories(
                status=None if include_inactive else MemoryStatus.ACTIVE,
                category=category,
            )
        except RepositoryError:
            logger.exception("No se pudo leer la memoria.")
            return _storage_error()

        return Result.ok(memories)

    def find(self, query: str, limit: int = FIND_LIMIT) -> Result[list[Memory]]:
        listed = self.list_memories()

        if not listed.success:
            return listed

        return Result.ok(
            select_relevant(
                listed.value,
                query,
                max_items=limit,
                max_chars=10_000,
            )
        )

    def relevant_for(
        self,
        text: str,
        max_items: int = MAX_ITEMS,
        max_chars: int = MAX_CHARS,
    ) -> list[Memory]:
        """Recuerdos que vienen al caso para esta frase (para el prompt)."""
        listed = self.list_memories()

        if not listed.success:
            return []

        return select_relevant(listed.value, text, max_items, max_chars)

    def forget(self, memory_id: UUID) -> Result[Memory]:
        """Desactiva un recuerdo (recuperable, DOC-016)."""
        return self._change_status(memory_id, MemoryStatus.INACTIVE)

    def reactivate(self, memory_id: UUID) -> Result[Memory]:
        return self._change_status(memory_id, MemoryStatus.ACTIVE)

    def forget_last(self) -> Result[Memory]:
        listed = self.list_memories()

        if not listed.success:
            return listed

        if not listed.value:
            return Result.fail(
                code="MEMORY_NOT_FOUND",
                message="No hay recuerdos activos.",
            )

        latest = max(listed.value, key=lambda item: item.created_at)

        return self.forget(latest.memory_id)

    def edit(
        self,
        memory_id: UUID,
        content: str | None = None,
        category: str | None = None,
    ) -> Result[Memory]:
        new_content = None

        if content is not None:
            new_content = " ".join(content.split())

            if not new_content:
                return Result.fail(
                    code="EMPTY_MEMORY",
                    message="El recuerdo no puede quedar vacío.",
                )

            if len(new_content) > MAX_CONTENT_CHARS:
                return Result.fail(
                    code="MEMORY_TOO_LONG",
                    message=(
                        f"El recuerdo supera los {MAX_CONTENT_CHARS} "
                        f"caracteres."
                    ),
                )

        new_category = None

        if category is not None:
            new_category = normalize_category(category)

            if new_category is None:
                return Result.fail(
                    code="INVALID_CATEGORY",
                    message="Esa categoría no existe.",
                )

        try:
            if not self._repository.update(
                memory_id,
                content=new_content,
                category=new_category,
            ):
                return self._not_found()

            memory = self._repository.get(memory_id)

        except RepositoryError:
            logger.exception("No se pudo editar un recuerdo.")
            return _storage_error()

        return Result.ok(memory) if memory else self._not_found()

    def purge(self, memory_id: UUID) -> Result[None]:
        """Borrado definitivo (no recuperable). Queda auditado."""
        try:
            if not self._repository.purge(memory_id):
                return self._not_found()
        except RepositoryError:
            logger.exception("No se pudo borrar un recuerdo.")
            return _storage_error()

        logger.info("Recuerdo borrado definitivamente.")

        return Result.ok()

    def resolve_id(self, prefix: str) -> Result[UUID]:
        """Encuentra un recuerdo por el comienzo de su id (para scripts)."""
        start = prefix.strip().lower()

        if not start:
            return self._not_found()

        listed = self.list_memories(include_inactive=True)

        if not listed.success:
            return listed

        matches = [
            item for item in listed.value
            if str(item.memory_id).startswith(start)
        ]

        if not matches:
            return self._not_found()

        if len(matches) > 1:
            return Result.fail(
                code="MEMORY_AMBIGUOUS_ID",
                message="Ese comienzo de id coincide con varios recuerdos.",
            )

        return Result.ok(matches[0].memory_id)

    def audit(self, limit: int = 20) -> Result[list[dict[str, str]]]:
        try:
            return Result.ok(self._repository.list_audit(limit))
        except RepositoryError:
            logger.exception("No se pudo leer la auditoría.")
            return _storage_error()

    def _change_status(
        self,
        memory_id: UUID,
        status: MemoryStatus,
    ) -> Result[Memory]:
        try:
            memory = self._repository.get(memory_id)

            if memory is None or memory.status == status:
                return self._not_found()

            if not self._repository.set_status(memory_id, status):
                return self._not_found()

        except RepositoryError:
            logger.exception("No se pudo cambiar el estado de un recuerdo.")
            return _storage_error()

        return Result.ok(memory)

    @staticmethod
    def _not_found() -> Result:
        return Result.fail(
            code="MEMORY_NOT_FOUND",
            message="No existe ese recuerdo.",
        )