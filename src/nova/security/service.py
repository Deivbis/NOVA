"""Security (SPEC-011): decide si una acción se permite, se confirma o se bloquea."""

from nova.core.automation import Action, ActionKind, SecurityDecision
from nova.core.capabilities import RiskLevel
from nova.memory.text import normalize
from nova.storage.repositories.permission_repository import (
    PermissionRepository,
)


class SecurityService:
    def __init__(self, repository: PermissionRepository) -> None:
        self._repository = repository

    def evaluate(self, action: Action) -> SecurityDecision:
        if action.target.startswith("\\\\"):
            return SecurityDecision(
                False, False, RiskLevel.HIGH,
                "Las rutas de red no están permitidas.",
                "deny.network_path",
            )

        if action.kind == ActionKind.MEDIA:
            return SecurityDecision(
                True, False, RiskLevel.LOW,
                "Control multimedia.", "media",
            )

        if action.builtin:
            return SecurityDecision(
                True, False, RiskLevel.LOW,
                "Destino de la lista blanca incorporada.",
                "allowlist.builtin",
            )

        if self._repository.has(action.kind.value, action.key):
            return SecurityDecision(
                True, False, RiskLevel.LOW,
                "Permiso concedido antes por el usuario.",
                "allowlist.user",
            )

        return SecurityDecision(
            True, True, RiskLevel.MEDIUM,
            "Primera vez con este destino.", "first_use",
        )

    def grant(self, action: Action) -> None:
        self._repository.add(action.kind.value, action.key)

    def revoke(self, text: str) -> int:
        needle = normalize(text).strip()
        removed = 0

        if not needle:
            return 0

        for kind, key in self._repository.list_permissions():
            if needle in normalize(key) and self._repository.remove(kind, key):
                removed += 1

        return removed

    def permissions(self) -> list[tuple[str, str]]:
        return self._repository.list_permissions()

    def audit(self, event: str, action: Action) -> None:
        self._repository.audit(event, action.kind.value)