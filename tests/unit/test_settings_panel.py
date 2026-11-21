from types import SimpleNamespace as NS
from uuid import uuid4

from nova.core.learning import LearningCandidate, LearningKind
from nova.core.result import Result
from nova.ui.settings_panel import SettingsPanel


class FakeLearning:
    def __init__(self):
        self.enabled = False
        self.candidate = LearningCandidate(
            key="k", kind=next(iter(LearningKind)), category="gustos", content="Café"
        )
        self.resolved = None

    def set_enabled(self, value):
        self.enabled = value

    def pending(self):
        return [self.candidate]

    def learned(self):
        return []

    def confirm(self, cid):
        self.resolved = ("confirm", cid)
        return Result.ok()

    def reject(self, cid):
        self.resolved = ("reject", cid)
        return Result.ok()


class FakePlugins:
    def __init__(self, enable_ok=True):
        self.missing = ["fs.read"]
        self.enable_ok = enable_ok
        self.revoked = 0
        manifest = NS(
            name="Demo", version="1.0.0", author="yo", description="d",
            permissions=("fs.read",), network_domains=(),
        )
        self.entry = NS(plugin_id="demo", manifest=manifest, error=None)

    def entries(self):
        return [(self.entry, False)]

    def missing_permissions(self, _):
        return list(self.missing)

    def check(self, _):
        return Result.ok()

    def grant_all(self, _):
        self.missing = []

    def enable(self, _):
        return Result.ok() if self.enable_ok else Result.fail("X", "No inicia.")

    def revoke_all(self, _):
        self.missing = ["fs.read"]
        self.revoked += 1
        return 1


def test_learning_flow():
    learning = FakeLearning()
    panel = SettingsPanel(learning, None)

    assert panel.set_learning(True)["ok"] and learning.enabled
    state = panel.learning_state()
    assert state["pending"][0]["content"] == "Café"
    assert panel.resolve_candidate(state["pending"][0]["id"], True)["ok"]
    assert learning.resolved[0] == "confirm"
    assert not panel.resolve_candidate("no-uuid", True)["ok"]


def test_plugin_activation_and_rollback():
    ok = FakePlugins()
    assert SettingsPanel(None, ok).activate_plugin("demo")["ok"]
    assert ok.revoked == 0

    bad = FakePlugins(enable_ok=False)
    result = SettingsPanel(None, bad).activate_plugin("demo")
    assert not result["ok"] and bad.revoked == 1


def test_unavailable_services():
    panel = SettingsPanel(None, None)
    assert panel.learning_state()["available"] is False
    assert panel.plugin_items() == []
    assert not panel.activate_plugin("x")["ok"]