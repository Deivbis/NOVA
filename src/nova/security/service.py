"""Security (SPEC-011): decide si una acción se permite, se confirma o se bloquea."""

from nova.core.automation import Action, ActionKind, SecurityDecision
from nova.core.capabilities import RiskLevel
from nova.memory.text import normalize
from nova.storage.repositories.permission_repository import (
    PermissionRepository,
)
import os
from pathlib import Path
from nova.core.automation import (
    Action,
    ActionKind,
    FileOperation,
    FileOpKind,
    SecurityDecision,
)

USER_FOLDERS = ("Desktop", "Documents", "Downloads", "Music", "Pictures", "Videos")
_SYSTEM_ENV = ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData")


def _inside(path: Path, root: Path) -> bool:
    p = os.path.normcase(str(path))
    r = os.path.normcase(str(root)).rstrip("\\/")

    return p == r or p.startswith(r + os.sep)


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

    def allowed_roots(self) -> list[Path]:
        roots = [Path.home() / name for name in USER_FOLDERS]
        roots += [
            Path(key)
            for kind, key in self._repository.list_permissions()
            if kind == ActionKind.FILES_SCOPE.value
        ]

        return [root.resolve() for root in roots]

    def scope_error(self, path: Path) -> str | None:
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError):
            return "Ruta no válida."

        if str(resolved).startswith("\\\\"):
            return "Las rutas de red no están permitidas."

        if resolved.parent == resolved:
            return "No opero sobre la raíz de un disco."

        for name in _SYSTEM_ENV:
            system = os.environ.get(name)

            if system and _inside(resolved, Path(system)):
                return "No toco carpetas del sistema."

        if not any(_inside(resolved, r) for r in self.allowed_roots()):
            return "Esa ruta está fuera de las carpetas autorizadas."

        return None

    def is_scope_root(self, path: Path) -> bool:
        target = os.path.normcase(str(path.resolve()))

        return any(
            target == os.path.normcase(str(root))
            for root in self.allowed_roots()
        )

    def evaluate_file(self, op: FileOperation) -> SecurityDecision:
        for raw in (op.source, op.dest):
            reason = self.scope_error(Path(raw)) if raw else None

            if reason:
                return SecurityDecision(
                    False, False, RiskLevel.HIGH, reason, "deny.scope"
                )

        if (
            op.kind != FileOpKind.ORGANIZE
            and op.source
            and self.is_scope_root(Path(op.source))
        ):
            return SecurityDecision(
                False, False, RiskLevel.HIGH,
                "No opero sobre una carpeta raíz autorizada.",
                "deny.scope_root",
            )

        if op.kind in (FileOpKind.CREATE_DIR, FileOpKind.COPY):
            return SecurityDecision(
                True, False, RiskLevel.LOW, "Operación no destructiva.",
                "file.safe",
            )

        if op.kind in (FileOpKind.MOVE, FileOpKind.RENAME):
            return SecurityDecision(
                True, True, RiskLevel.MEDIUM, "Modifica archivos.",
                "file.confirm",
            )

        return SecurityDecision(
            True, True, RiskLevel.HIGH, "Operación de alto riesgo.",
            "file.confirm_high",
        )

    def audit_file(self, event: str, op: FileOperation) -> None:
        self._repository.audit(event, f"file.{op.kind.value}")