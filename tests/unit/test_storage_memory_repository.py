from nova.core.memory import Memory, MemoryStatus
from nova.storage import StorageService


def create_repository(tmp_path):
    service = StorageService(tmp_path / "nova.db")
    service.initialize()

    return service, service.memory_repository


def test_memory_tables_exist_after_initialization(tmp_path):
    service, _ = create_repository(tmp_path)

    tables = {
        row[0]
        for row in service.manager.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    assert {"memories", "audit_logs"} <= tables

    service.close()


def test_add_and_get_a_memory(tmp_path):
    service, repository = create_repository(tmp_path)
    memory = Memory(content="me llamo Deivbis", category="General")

    repository.add(memory)
    loaded = repository.get(memory.memory_id)

    assert loaded.content == "me llamo Deivbis"
    assert loaded.category == "General"
    assert loaded.status == MemoryStatus.ACTIVE

    service.close()


def test_get_unknown_memory_returns_none(tmp_path):
    service, repository = create_repository(tmp_path)

    assert repository.get(Memory(content="x").memory_id) is None

    service.close()


def test_list_defaults_to_active_and_filters_by_category(tmp_path):
    service, repository = create_repository(tmp_path)
    rock = Memory(content="me gusta el rock", category="Música")
    work = Memory(content="trabajo de noche", category="Trabajo")
    old = Memory(content="dato viejo", category="Música")

    for memory in (rock, work, old):
        repository.add(memory)

    repository.set_status(old.memory_id, MemoryStatus.INACTIVE)

    active = repository.list_memories()
    music = repository.list_memories(category="Música")
    everything = repository.list_memories(status=None)

    assert {m.content for m in active} == {"me gusta el rock", "trabajo de noche"}
    assert [m.content for m in music] == ["me gusta el rock"]
    assert len(everything) == 3

    service.close()


def test_update_content_and_category(tmp_path):
    service, repository = create_repository(tmp_path)
    memory = Memory(content="color azul")
    repository.add(memory)

    assert repository.update(
        memory.memory_id,
        content="color verde",
        category="Rutinas",
    )

    loaded = repository.get(memory.memory_id)

    assert loaded.content == "color verde"
    assert loaded.category == "Rutinas"

    service.close()


def test_update_unknown_memory_returns_false(tmp_path):
    service, repository = create_repository(tmp_path)

    assert repository.update(Memory(content="x").memory_id, content="y") is False

    service.close()


def test_deactivate_and_reactivate(tmp_path):
    service, repository = create_repository(tmp_path)
    memory = Memory(content="algo")
    repository.add(memory)

    assert repository.set_status(memory.memory_id, MemoryStatus.INACTIVE)
    assert repository.list_memories() == []

    assert repository.set_status(memory.memory_id, MemoryStatus.ACTIVE)
    assert len(repository.list_memories()) == 1

    service.close()


def test_purge_deletes_the_memory_but_keeps_the_audit(tmp_path):
    service, repository = create_repository(tmp_path)
    memory = Memory(content="secreto-123")
    repository.add(memory)

    assert repository.purge(memory.memory_id) is True
    assert repository.get(memory.memory_id) is None
    assert repository.purge(memory.memory_id) is False

    actions = [entry["action"] for entry in repository.list_audit()]

    assert "memory.purged" in actions

    service.close()


def test_every_change_is_audited_without_the_content(tmp_path):
    service, repository = create_repository(tmp_path)
    memory = Memory(content="secreto-123", category="Salud")

    repository.add(memory)
    repository.update(memory.memory_id, content="secreto-456")
    repository.set_status(memory.memory_id, MemoryStatus.INACTIVE)
    repository.set_status(memory.memory_id, MemoryStatus.ACTIVE)
    repository.purge(memory.memory_id)

    audit = repository.list_audit()
    actions = [entry["action"] for entry in audit]

    assert sorted(actions) == sorted(
        [
            "memory.created",
            "memory.updated",
            "memory.deactivated",
            "memory.reactivated",
            "memory.purged",
        ]
    )
    assert "secreto" not in str(audit)
    assert all(entry["target_id"] == str(memory.memory_id) for entry in audit)

    service.close()


def test_list_is_ordered_by_creation(tmp_path):
    service, repository = create_repository(tmp_path)
    first = Memory(content="primero")
    second = Memory(content="segundo")

    repository.add(first)
    repository.add(second)

    assert [m.content for m in repository.list_memories()] == [
        "primero",
        "segundo",
    ]

    service.close()