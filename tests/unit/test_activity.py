from datetime import datetime, timedelta, timezone

import pytest

from nova.activity import ActivityService
from nova.projects import ProjectService
from nova.storage.service import StorageService
from nova.ui.activity_panel import ActivityPanel, describe


@pytest.fixture
def env(tmp_path):
    storage = StorageService(tmp_path / "nova.db")
    storage.initialize()
    yield storage
    storage.close()


def test_recent_and_range(env):
    ProjectService(env.project_repository).create("A")
    future = datetime.now(timezone.utc) + timedelta(days=10)
    old = ActivityService(env.audit_repository, clock=lambda: future)

    assert old.recent(7).value.total == 0
    assert old.recent(30).value.total == 1

    panel = ActivityPanel(ActivityService(env.audit_repository))
    data = panel.recent(7)

    assert data["total"] == 1
    assert data["items"][0]["what"] == "Proyecto creado"


def test_describe_fallback():
    assert describe("x.y")[1:] == ("Sistema", "Actividad registrada")