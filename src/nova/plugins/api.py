"""API que NOVA presta a los plugins. Cada método exige su permiso."""

import urllib.error
import urllib.request
from urllib.parse import urlsplit

from nova.automation.commands import AutomationAction, AutomationCommand
from nova.automation.service import MEDIA_LABELS, AutomationService
from nova.core.logging_setup import get_logger
from nova.memory import MemoryService
from nova.memory.text import normalize
from nova.plugins.gateway import MainThread
from nova.plugins.manifest import PluginManifest
from nova.security import SecurityService
from nova.storage.repositories.permission_repository import (
    PermissionRepository,
)

logger = get_logger(__name__)

HTTP_TIMEOUT_S = 5
MAX_HTTP_BYTES = 200_000
_REQUIRED = {
    "speak": "speak",
    "http_get": "network",
    "memory_search": "memory.read",
    "open_target": "automation.open",
    "media": "automation.media",
}


class PluginAPIError(Exception):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


class PluginAPI:
    def __init__(
        self,
        manifest: PluginManifest,
        permissions: PermissionRepository,
        security: SecurityService,
        automation: AutomationService,
        memory: MemoryService,
        gateway: MainThread,
    ) -> None:
        self._manifest = manifest
        self._permissions = permissions
        self._security = security
        self._automation = automation
        self._memory = memory
        self._gateway = gateway

    def dispatch(self, method: str, params, lines: list[str]) -> dict:
        """Se ejecuta en el hilo del plugin; la BD solo se toca en la UI."""
        if not isinstance(params, dict):
            params = {}

        try:
            denied = self._gateway.call(lambda: self._gate(method))

            if denied is not None:
                return denied

            if method == "http_get":
                return {"ok": True, "value": self._http_get(params)}

            return {
                "ok": True,
                "value": self._gateway.call(
                    lambda: self._local(method, params, lines)
                ),
            }
        except PluginAPIError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            logger.warning(
                "Fallo en API de plugin (%s): %s", method, type(exc).__name__
            )
            return {"ok": False, "error": "Error interno."}

    def _gate(self, method: str) -> dict | None:
        permission = _REQUIRED.get(method)

        if permission is None:
            return {"ok": False, "error": "Método desconocido."}

        granted = self._permissions.has(
            "plugin", f"{self._manifest.id}:{permission}"
        )

        if permission not in self._manifest.permissions or not granted:
            self._permissions.audit("plugin.denied", "plugin")
            return {"ok": False, "error": f"Permiso «{permission}» no concedido."}

        return None

    def _local(self, method: str, params: dict, lines: list[str]):
        if method == "speak":
            lines.append(str(params.get("text", ""))[:500])
            return True

        if method == "memory_search":
            return self._memory_search(str(params.get("query", "")))

        if method == "open_target":
            return self._open_target(params)

        return self._media(str(params.get("command", "")))

    def _http_get(self, params: dict) -> str:
        url = str(params.get("url", ""))[:500]
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()

        if (
            parts.scheme != "https"
            or host not in self._manifest.network_domains
            or parts.port not in (None, 443)
            or parts.username
        ):
            raise PluginAPIError("Dominio no permitido por el plugin.")

        request = urllib.request.Request(
            url, headers={"User-Agent": "NOVA-plugin/1.0"}
        )

        try:
            with _OPENER.open(request, timeout=HTTP_TIMEOUT_S) as response:
                data = response.read(MAX_HTTP_BYTES + 1)
        except (urllib.error.URLError, OSError, ValueError):
            raise PluginAPIError("No pude conectar con el servicio.") from None

        if len(data) > MAX_HTTP_BYTES:
            raise PluginAPIError("La respuesta es demasiado grande.")

        return data.decode("utf-8", errors="replace")

    def _memory_search(self, query: str) -> list[str]:
        tokens = [t for t in normalize(query).split() if len(t) >= 4][:6]
        listed = self._memory.list_memories()

        if not tokens or not listed.success:
            return []

        return [
            m.content
            for m in listed.value
            if any(t in normalize(m.content) for t in tokens)
        ][:5]

    def _open_target(self, params: dict) -> bool:
        kind = params.get("kind")

        if kind not in ("web", "folder", "program"):
            raise PluginAPIError("Tipo de destino inválido.")

        command = AutomationCommand(
            AutomationAction.OPEN, str(params.get("text", ""))[:300], kind
        )

        return self._perform(command)

    def _media(self, command: str) -> bool:
        if command not in MEDIA_LABELS:
            raise PluginAPIError("Comando multimedia inválido.")

        return self._perform(
            AutomationCommand(AutomationAction.MEDIA, media=command)
        )

    def _perform(self, command: AutomationCommand) -> bool:
        planned = self._automation.plan(command)

        if not planned.success:
            raise PluginAPIError(planned.error.message)

        action = planned.value
        decision = self._security.evaluate(action)

        if not decision.allowed or decision.requires_confirmation:
            raise PluginAPIError("El usuario aún no permitió ese destino.")

        if not self._automation.execute(action).success:
            raise PluginAPIError("No pude ejecutar la acción.")

        self._security.audit("automation.executed", action)

        return True