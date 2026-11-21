"""Lógica de la página Memoria (Fase 10.2), sin Qt. Solo usa MemoryService."""

from uuid import UUID

from nova.core.memory import Memory, MemoryStatus
from nova.core.result import Result
from nova.memory import MemoryService
from nova.memory.text import normalize
from nova.ui.time_format import friendly_time, full_time

MAX_ROWS = 500
_SOURCES = {
    "user": "Lo guardaste tú",
    "learned": "Aprendido por NOVA (con tu confirmación)",
}


def _item(memory: Memory) -> dict:
    return {
        "id": str(memory.memory_id),
        "content": memory.content,
        "category": memory.category,
        "source": memory.source,
        "sourceLabel": _SOURCES.get(memory.source, memory.source),
        "active": memory.status == MemoryStatus.ACTIVE,
        "time": friendly_time(memory.updated_at),
        "created": full_time(memory.created_at),
        "updated": full_time(memory.updated_at),
    }


def _outcome(result: Result, memory_id: str = "") -> dict:
    if result.success:
        return {"ok": True, "error": "", "id": memory_id}

    message = result.error.message if result.error else "No se pudo completar."

    return {"ok": False, "error": message, "id": ""}


class MemoryPanel:
    def __init__(self, service: MemoryService) -> None:
        self._service = service

    def _all(self) -> list[Memory]:
        listed = self._service.list_memories(include_inactive=True)

        return listed.value if listed.success else []

    def overview(self) -> dict:
        items = self._all()
        active = [m for m in items if m.status == MemoryStatus.ACTIVE]
        counts: dict[str, int] = {}

        for memory in active:
            counts[memory.category] = counts.get(memory.category, 0) + 1

        ordered = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))

        return {
            "total": len(active),
            "learned": sum(1 for m in active if m.source == "learned"),
            "forgotten": len(items) - len(active),
            "categories": [{"name": n, "count": c} for n, c in ordered],
        }

    def search(
        self,
        query: str,
        category: str,
        view: str,
        newest_first: bool,
    ) -> list[dict]:
        items = self._all()

        if view == "forgotten":
            items = [m for m in items if m.status == MemoryStatus.INACTIVE]
        else:
            items = [m for m in items if m.status == MemoryStatus.ACTIVE]

            if view == "learned":
                items = [m for m in items if m.source == "learned"]

        if category:
            items = [m for m in items if m.category == category]

        needle = normalize(query).strip()

        if needle:
            items = [m for m in items if needle in normalize(m.content)]

        items.sort(key=lambda m: m.updated_at, reverse=newest_first)

        return [_item(m) for m in items[:MAX_ROWS]]

    def add(self, content: str, category: str) -> dict:
        result = self._service.remember(content, category or None, source="user")

        return _outcome(
            result, str(result.value.memory_id) if result.success else ""
        )

    def update(self, memory_id: str, content: str, category: str) -> dict:
        uid = self._uuid(memory_id)

        if uid is None:
            return self._missing()

        return _outcome(
            self._service.edit(uid, content=content, category=category or None),
            memory_id,
        )

    def forget(self, memory_id: str) -> dict:
        return self._run(self._service.forget, memory_id)

    def reactivate(self, memory_id: str) -> dict:
        return self._run(self._service.reactivate, memory_id)

    def purge(self, memory_id: str) -> dict:
        return self._run(self._service.purge, memory_id)

    def _run(self, action, memory_id: str) -> dict:
        uid = self._uuid(memory_id)

        return self._missing() if uid is None else _outcome(action(uid), memory_id)

    @staticmethod
    def _uuid(text: str) -> UUID | None:
        try:
            return UUID(text)
        except ValueError:
            return None

    @staticmethod
    def _missing() -> dict:
        return {"ok": False, "error": "Ese recuerdo ya no existe.", "id": ""}
