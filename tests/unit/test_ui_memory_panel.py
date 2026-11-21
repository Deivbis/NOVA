from nova.memory import MemoryService
from nova.storage import StorageService
from nova.ui.memory_panel import MemoryPanel


def make(tmp_path):
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    service = MemoryService(storage.memory_repository)

    return storage, service, MemoryPanel(service)


def test_add_overview_and_filters(tmp_path):
    storage, service, panel = make(tmp_path)

    assert panel.add("Me gusta el rock", "Música")["ok"]
    assert panel.add("Trabajo en Python", "Programación")["ok"]
    service.remember("Prefiero el té", "Rutinas", source="learned")

    overview = panel.overview()
    assert overview["total"] == 3
    assert overview["learned"] == 1
    assert {c["name"] for c in overview["categories"]} == {
        "Música", "Programación", "Rutinas",
    }

    found = panel.search("ROCK", "", "active", True)
    assert [m["content"] for m in found] == ["Me gusta el rock"]
    assert len(panel.search("", "Música", "active", True)) == 1
    assert [m["source"] for m in panel.search("", "", "learned", True)] == ["learned"]
    storage.close()


def test_duplicate_and_empty_are_reported(tmp_path):
    storage, _, panel = make(tmp_path)

    assert panel.add("Algo importante", "General")["ok"]
    duplicate = panel.add("Algo importante", "General")
    assert not duplicate["ok"] and duplicate["error"]
    assert not panel.add("   ", "")["ok"]
    storage.close()


def test_update_changes_content_and_category(tmp_path):
    storage, _, panel = make(tmp_path)
    memory_id = panel.add("Estudio inglés", "Estudios")["id"]

    assert panel.update(memory_id, "Estudio inglés a diario", "Rutinas")["ok"]

    item = panel.search("", "", "active", True)[0]
    assert item["content"] == "Estudio inglés a diario"
    assert item["category"] == "Rutinas"
    assert not panel.update(memory_id, "x", "NoExiste")["ok"]
    storage.close()


def test_forget_reactivate_purge_flow(tmp_path):
    storage, _, panel = make(tmp_path)
    memory_id = panel.add("Recuerdo temporal", "General")["id"]

    assert panel.forget(memory_id)["ok"]
    assert panel.overview()["total"] == 0
    assert panel.overview()["forgotten"] == 1
    assert panel.search("", "", "active", True) == []
    assert len(panel.search("", "", "forgotten", True)) == 1

    assert panel.reactivate(memory_id)["ok"]
    assert panel.overview()["total"] == 1

    assert panel.forget(memory_id)["ok"]
    assert panel.purge(memory_id)["ok"]
    assert panel.overview() == {
        "total": 0, "learned": 0, "forgotten": 0, "categories": [],
    }
    storage.close()


def test_invalid_id_is_reported(tmp_path):
    storage, _, panel = make(tmp_path)

    assert not panel.forget("no-es-un-uuid")["ok"]
    assert not panel.purge("00000000-0000-0000-0000-000000000000")["ok"]
    storage.close()
