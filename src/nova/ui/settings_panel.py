"""Lógica de Configuración (Fase 10.5), sin Qt."""

from uuid import UUID

from nova.core.result import Result


def _ok(item_id: str = "") -> dict:
    return {"ok": True, "error": "", "id": item_id}


def _err(message: str) -> dict:
    return {"ok": False, "error": message, "id": ""}


def _outcome(result: Result, item_id: str = "") -> dict:
    if result.success:
        return _ok(item_id)

    return _err(result.error.message if result.error else "No se pudo completar.")


class SettingsPanel:
    def __init__(self, learning, plugins) -> None:
        self._learning = learning
        self._plugins = plugins

    # --- aprendizaje ---------------------------------------------------
    def learning_state(self) -> dict:
        if self._learning is None:
            return {"available": False, "enabled": False, "pending": [], "learned": 0}

        return {
            "available": True,
            "enabled": bool(self._learning.enabled),
            "pending": [
                {
                    "id": str(c.candidate_id),
                    "content": c.content,
                    "category": c.category,
                    "evidence": c.evidence,
                }
                for c in self._learning.pending()
            ],
            "learned": len(self._learning.learned()),
        }

    def set_learning(self, enabled: bool) -> dict:
        if self._learning is None:
            return _err("El aprendizaje no está disponible.")

        self._learning.set_enabled(bool(enabled))

        return _ok()

    def resolve_candidate(self, candidate_id: str, accept: bool) -> dict:
        if self._learning is None:
            return _err("El aprendizaje no está disponible.")

        try:
            cid = UUID(candidate_id)
        except ValueError:
            return _err("Propuesta no válida.")

        result = (
            self._learning.confirm(cid) if accept else self._learning.reject(cid)
        )

        return _outcome(result, candidate_id)

    # --- plugins -------------------------------------------------------
    def plugin_items(self) -> list[dict]:
        if self._plugins is None:
            return []

        items = []

        for entry, enabled in self._plugins.entries():
            m = entry.manifest
            items.append(
                {
                    "id": entry.plugin_id,
                    "name": m.name if m else entry.plugin_id,
                    "version": m.version if m else "",
                    "author": m.author if m else "",
                    "description": m.description if m else "",
                    "permissions": list(m.permissions) if m else [],
                    "network": list(m.network_domains) if m else [],
                    "enabled": bool(enabled),
                    "granted": bool(m)
                    and not self._plugins.missing_permissions(entry.plugin_id),
                    "error": "" if m else (entry.error or "Plugin no válido."),
                }
            )

        return sorted(items, key=lambda i: i["name"].lower())

    def activate_plugin(self, plugin_id: str) -> dict:
        if self._plugins is None:
            return _err("Los plugins no están disponibles.")

        checked = self._plugins.check(plugin_id)

        if not checked.success:
            return _outcome(checked)

        was_granted = not self._plugins.missing_permissions(plugin_id)
        self._plugins.grant_all(plugin_id)
        enabled = self._plugins.enable(plugin_id)

        if not enabled.success and not was_granted:
            self._plugins.revoke_all(plugin_id)

        return _outcome(enabled, plugin_id)

    def deactivate_plugin(self, plugin_id: str) -> dict:
        if self._plugins is None:
            return _err("Los plugins no están disponibles.")

        return _outcome(self._plugins.disable(plugin_id), plugin_id)

    def revoke_plugin(self, plugin_id: str) -> dict:
        if self._plugins is None:
            return _err("Los plugins no están disponibles.")

        self._plugins.revoke_all(plugin_id)

        return _ok(plugin_id)

    def reload_plugins(self) -> dict:
        if self._plugins is None:
            return _err("Los plugins no están disponibles.")

        self._plugins.reload()

        return _ok()