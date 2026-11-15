import logging
from unittest.mock import MagicMock

from nova.core.memory import Memory
from nova.memory import MemoryService
from nova.storage import StorageService
from nova.storage.exceptions import RepositoryError


def create_service(tmp_path):
    storage = StorageService(tmp_path / "nova.db")
    storage.initialize()

    return MemoryService(storage.memory_repository), storage


def test_remember_classifies_and_saves(tmp_path):
    service, storage = create_service(tmp_path)

    result = service.remember("me gusta programar en Python")

    assert result.success
    assert result.value.category == "Programación"
    assert len(storage.memory_repository.list_memories()) == 1

    storage.close()


def test_remember_uses_the_given_category(tmp_path):
    service, storage = create_service(tmp_path)

    result = service.remember("mi color favorito es el azul", "música")

    assert result.value.category == "Música"

    storage.close()


def test_remember_rejects_an_unknown_category(tmp_path):
    service, storage = create_service(tmp_path)

    result = service.remember("algo", "casa")

    assert not result.success
    assert result.error.code == "INVALID_CATEGORY"

    storage.close()


def test_remember_rejects_empty_and_too_long_text(tmp_path):
    service, storage = create_service(tmp_path)

    assert service.remember("   ").error.code == "EMPTY_MEMORY"
    assert service.remember("a" * 501).error.code == "MEMORY_TOO_LONG"

    storage.close()


def test_duplicates_are_detected_ignoring_case_and_accents(tmp_path):
    service, storage = create_service(tmp_path)

    service.remember("Me gusta la música")
    result = service.remember("me gusta la musica")

    assert not result.success
    assert result.error.code == "MEMORY_DUPLICATE"

    storage.close()


def test_list_by_category_and_with_inactive(tmp_path):
    service, storage = create_service(tmp_path)

    service.remember("me gusta el rock", "Música")
    old = service.remember("trabajo de noche", "Trabajo").value
    service.forget(old.memory_id)

    music = service.list_memories(category="Música").value
    active = service.list_memories().value
    everything = service.list_memories(include_inactive=True).value

    assert [m.content for m in music] == ["me gusta el rock"]
    assert len(active) == 1
    assert len(everything) == 2

    storage.close()


def test_forget_deactivates_and_reactivate_restores(tmp_path):
    service, storage = create_service(tmp_path)
    memory = service.remember("me llamo Deivbis").value

    assert service.forget(memory.memory_id).success
    assert service.list_memories().value == []

    assert service.reactivate(memory.memory_id).success
    assert len(service.list_memories().value) == 1

    storage.close()


def test_forget_last_removes_the_most_recent_memory(tmp_path):
    service, storage = create_service(tmp_path)

    service.remember("primero")
    last = service.remember("segundo").value

    result = service.forget_last()

    assert result.value.memory_id == last.memory_id
    assert [m.content for m in service.list_memories().value] == ["primero"]

    storage.close()


def test_forget_last_without_memories_fails(tmp_path):
    service, storage = create_service(tmp_path)

    assert service.forget_last().error.code == "MEMORY_NOT_FOUND"

    storage.close()


def test_forgetting_an_unknown_or_inactive_memory_fails(tmp_path):
    service, storage = create_service(tmp_path)
    memory = service.remember("algo").value

    service.forget(memory.memory_id)

    assert service.forget(memory.memory_id).error.code == "MEMORY_NOT_FOUND"
    assert service.forget(Memory(content="x").memory_id).error.code == (
        "MEMORY_NOT_FOUND"
    )

    storage.close()


def test_edit_changes_content_and_category(tmp_path):
    service, storage = create_service(tmp_path)
    memory = service.remember("color azul").value

    result = service.edit(memory.memory_id, content="color verde", category="Rutinas")

    assert result.value.content == "color verde"
    assert result.value.category == "Rutinas"

    storage.close()


def test_edit_validates_its_input(tmp_path):
    service, storage = create_service(tmp_path)
    memory = service.remember("color azul").value

    assert service.edit(memory.memory_id, content="  ").error.code == "EMPTY_MEMORY"
    assert service.edit(memory.memory_id, category="casa").error.code == (
        "INVALID_CATEGORY"
    )
    assert service.edit(Memory(content="x").memory_id, content="y").error.code == (
        "MEMORY_NOT_FOUND"
    )

    storage.close()


def test_purge_deletes_permanently(tmp_path):
    service, storage = create_service(tmp_path)
    memory = service.remember("algo").value

    assert service.purge(memory.memory_id).success
    assert service.purge(memory.memory_id).error.code == "MEMORY_NOT_FOUND"
    assert service.list_memories(include_inactive=True).value == []

    storage.close()


def test_resolve_id_by_prefix(tmp_path):
    service, storage = create_service(tmp_path)
    memory = service.remember("algo").value

    found = service.resolve_id(str(memory.memory_id)[:8])

    assert found.value == memory.memory_id
    assert service.resolve_id("zzzzzzzz").error.code == "MEMORY_NOT_FOUND"
    assert service.resolve_id("").error.code == "MEMORY_NOT_FOUND"

    storage.close()


def test_relevant_for_returns_only_active_matching_memories(tmp_path):
    service, storage = create_service(tmp_path)

    service.remember("me llamo Deivbis")
    old = service.remember("me llamo Carlos").value
    service.remember("me gusta el rock")
    service.forget(old.memory_id)

    result = service.relevant_for("¿cómo me llamo?")

    assert [m.content for m in result] == ["me llamo Deivbis"]

    storage.close()


def test_find_returns_matching_memories(tmp_path):
    service, storage = create_service(tmp_path)

    service.remember("mi hermano se llama Luis")
    service.remember("me gusta el rock")

    found = service.find("mi hermano").value

    assert [m.content for m in found] == ["mi hermano se llama Luis"]

    storage.close()


def test_audit_never_contains_the_content(tmp_path):
    service, storage = create_service(tmp_path)

    memory = service.remember("secreto-123").value
    service.forget(memory.memory_id)

    audit = service.audit().value

    assert [e["action"] for e in audit] == ["memory.deactivated", "memory.created"]
    assert "secreto" not in str(audit)

    storage.close()


def test_content_is_never_logged(tmp_path, caplog):
    service, storage = create_service(tmp_path)

    with caplog.at_level(logging.DEBUG, logger="nova"):
        memory = service.remember("secreto-123").value
        service.edit(memory.memory_id, content="secreto-456")
        service.forget(memory.memory_id)
        service.purge(memory.memory_id)

    assert "secreto" not in caplog.text

    storage.close()


def test_storage_failures_become_structured_errors():
    repository = MagicMock()
    repository.list_memories.side_effect = RepositoryError("fallo")
    service = MemoryService(repository)

    assert service.remember("algo").error.code == "MEMORY_STORAGE_ERROR"
    assert service.list_memories().error.code == "MEMORY_STORAGE_ERROR"
    assert service.relevant_for("algo") == []