"""Puente de Configuración hacia QML (contexto: novaSettings)."""

from PySide6.QtCore import QObject, Signal, Slot

from nova.ui.settings_panel import SettingsPanel


class SettingsUiBridge(QObject):
    changed = Signal()

    def __init__(self, learning, plugins, parent: QObject | None = None) -> None:
        if parent is not None and not isinstance(parent, QObject):
            parent = None

        super().__init__(parent)
        self._panel = SettingsPanel(learning, plugins)

    def _mutated(self, outcome: dict) -> dict:
        if outcome["ok"]:
            self.changed.emit()

        return outcome

    @Slot(result="QVariantMap")
    def learningState(self) -> dict:
        return self._panel.learning_state()

    @Slot(bool, result="QVariantMap")
    def setLearning(self, enabled: bool) -> dict:
        return self._mutated(self._panel.set_learning(enabled))

    @Slot(str, bool, result="QVariantMap")
    def resolveCandidate(self, candidate_id: str, accept: bool) -> dict:
        return self._mutated(self._panel.resolve_candidate(candidate_id, accept))

    @Slot(result="QVariantList")
    def plugins(self):
        return self._panel.plugin_items()

    @Slot(str, result="QVariantMap")
    def activatePlugin(self, plugin_id: str) -> dict:
        return self._mutated(self._panel.activate_plugin(plugin_id))

    @Slot(str, result="QVariantMap")
    def deactivatePlugin(self, plugin_id: str) -> dict:
        return self._mutated(self._panel.deactivate_plugin(plugin_id))

    @Slot(str, result="QVariantMap")
    def revokePlugin(self, plugin_id: str) -> dict:
        return self._mutated(self._panel.revoke_plugin(plugin_id))

    @Slot(result="QVariantMap")
    def reloadPlugins(self) -> dict:
        return self._mutated(self._panel.reload_plugins())