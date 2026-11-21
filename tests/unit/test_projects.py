import pytest

from nova.core.projects import ProjectStatus
from nova.projects import ProjectService
from nova.storage.service import StorageService


@pytest.fixture
def service(tmp_path):
    storage = StorageService(tmp_path / "nova.db")
    storage.initialize()
    yield ProjectService(storage.project_repository)
    storage.close()


def test_crud(service):
    created = service.create("  NOVA  ", "desc")
    assert created.success and created.value.name == "NOVA"

    pid = created.value.project_id
    updated = service.update(pid, "NOVA 2", "", ProjectStatus.DONE, 10)
    assert updated.value.progress == 100

    assert [p.name for p in service.list_projects().value] == ["NOVA 2"]
    assert service.delete(pid).success
    assert service.list_projects().value == []


def test_validation(service):
    assert service.create("   ").error.code == "PROJECT_INVALID"
    assert service.create("x" * 81).error.code == "PROJECT_INVALID"
    assert service.delete(__import__("uuid").uuid4()).error.code == "PROJECT_NOT_FOUND"