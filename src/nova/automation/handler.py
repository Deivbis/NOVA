"""Respuestas deterministas de automatización con confirmación (D-031)."""

from nova.automation.commands import (
    AutomationAction,
    AutomationCommand,
    parse_automation_command,
)
from nova.automation.service import AutomationService
from nova.core.automation import Action, ActionKind, FileOperation, FileOpKind
from nova.core.confirmation import parse_yes_no
from nova.core.logging_setup import get_logger
from nova.storage.exceptions import RepositoryError
from pathlib import Path


logger = get_logger(__name__)

_KIND = {
    ActionKind.OPEN_PROGRAM: "programa",
    ActionKind.OPEN_FOLDER: "carpeta",
    ActionKind.OPEN_WEB: "sitio web",
    ActionKind.OPEN_FILE: "archivo",
    ActionKind.FILES_SCOPE: "carpeta de archivos",
}
_FILE_ACTIONS = frozenset({
    AutomationAction.AUTHORIZE, AutomationAction.SEARCH,
    AutomationAction.LIST, AutomationAction.CREATE_DIR,
    AutomationAction.COPY, AutomationAction.MOVE,
    AutomationAction.RENAME, AutomationAction.DELETE,
    AutomationAction.ORGANIZE, AutomationAction.OPEN_RESULT,
})
_DONE = {
    FileOpKind.CREATE_DIR: "Carpeta creada, Jefe.",
    FileOpKind.COPY: "Copiado, Jefe.",
    FileOpKind.MOVE: "Movido, Jefe.",
    FileOpKind.RENAME: "Renombrado, Jefe.",
    FileOpKind.DELETE: "Enviado a la papelera, Jefe.",
}
_BASIC = (
    "Sin preguntar: Calculadora, Bloc de notas, Paint, Explorador, "
    "carpetas de usuario, YouTube, Google, Gmail, GitHub, WhatsApp "
    "y los controles de música."
)


class AutomationCommandHandler:
    def __init__(self, service: AutomationService) -> None:
        self._service = service
        self._security = service.security
        self._pending: Action | None = None
        self._files = service.files
        self._pending_file: FileOperation | None = None
        self._results: list[Path] = []

    @property
    def pending(self) -> bool:
        return self._pending is not None or self._pending_file is not None

    def reply_to(self, text: str) -> str | None:
        try:
            if self._pending_file is not None:
                op, self._pending_file = self._pending_file, None
                decision = parse_yes_no(text)

                if decision is True:
                    return self._run_file(op)

                if decision is False:
                    self._security.audit_file("automation.cancelled", op)
                    return "Entendido, Jefe. No lo haré."
                
            if self._pending is not None:
                action, self._pending = self._pending, None
                decision = parse_yes_no(text)

                if decision is True:
                    return self._confirmed(action)

                if decision is False:
                    self._security.audit("automation.cancelled", action)
                    return "Entendido, Jefe. No lo haré."

            command = parse_automation_command(text)

            return self._handle(command) if command is not None else None
        except RepositoryError:
            logger.exception("Fallo de permisos.")
            return "No pude consultar los permisos, Jefe."

    def _handle(self, command: AutomationCommand) -> str:
        if command.action in _FILE_ACTIONS:
            return self._handle_files(command)
        
        if command.action == AutomationAction.PERMISSIONS:
            granted = [
                f"- {_KIND.get(ActionKind(kind), kind)}: {key}"
                for kind, key in self._security.permissions()
            ]
            lines = [_BASIC, "Permisos que me diste:"]

            return "\n".join(lines + (granted or ["- ninguno"]))

        if command.action == AutomationAction.REVOKE:
            removed = self._security.revoke(command.text)

            if removed:
                return f"Permiso revocado, Jefe ({removed})."

            return (
                "No tengo permisos guardados para eso, Jefe. "
                "Los básicos no se pueden revocar."
            )

        planned = self._service.plan(command)

        if not planned.success:
            return f"{planned.error.message} Lo siento, Jefe."

        action = planned.value
        decision = self._security.evaluate(action)

        if not decision.allowed:
            self._security.audit("automation.denied", action)
            return f"No puedo hacerlo, Jefe. {decision.reason}"

        if decision.requires_confirmation:
            self._pending = action
            return (
                f"Jefe, voy a abrir {action.label} "
                f"({_KIND[action.kind]}). Es la primera vez; "
                "¿lo permito? Responde «sí» o «no»."
            )

        return self._run(action)

    def _confirmed(self, action: Action) -> str:
        self._security.grant(action)
        self._security.audit("automation.confirmed", action)

        return (
            f"Permiso guardado; puedes quitarlo con «revoca el permiso "
            f"de {action.label}». {self._run(action)}"
        )

    def _run(self, action: Action) -> str:
        result = self._service.execute(action)

        if not result.success:
            return f"No pude hacerlo, Jefe. {result.error.message}"

        self._security.grant(action)
        self._security.audit("automation.executed", action)

        if action.kind == ActionKind.FILES_SCOPE:
            return (
                f"Carpeta autorizada para archivos: {action.label}. "
                f"Puedes quitarla con «revoca el permiso de {action.label}»."
            )

        if action.kind == ActionKind.MEDIA:
            return f"{action.label}, Jefe."

        return f"Abriendo {action.label}, Jefe."

    def _handle_files(self, command: AutomationCommand) -> str:
        files, security, kind = self._files, self._security, command.action

        if kind == AutomationAction.AUTHORIZE:
            return self._authorize(command)

        if kind == AutomationAction.SEARCH:
            result = files.search(command.name, command.source or None)

            if not result.success:
                return f"{result.error.message} Lo siento, Jefe."

            self._results = result.value

            if not self._results:
                return "No encontré nada con ese nombre, Jefe."

            lines = [
                f"{i}. {p.name} ({p.parent.name})"
                for i, p in enumerate(self._results, 1)
            ]

            return "\n".join(
                ["Encontré:", *lines, "Di «abre el 1» para abrir uno."]
            )

        if kind == AutomationAction.LIST:
            result = files.list_dir(command.source)

            if not result.success:
                return f"{result.error.message} Lo siento, Jefe."

            folder, names, extra = result.value

            if not names:
                return f"{folder.name} está vacía, Jefe."

            tail = [f"… y {extra} más"] if extra else []

            return "\n".join(
                [f"{folder.name}:", *[f"- {n}" for n in names], *tail]
            )

        if kind == AutomationAction.OPEN_RESULT:
            index = int(command.text) - 1

            if not 0 <= index < len(self._results):
                return "No tengo ese resultado, Jefe. Haz una búsqueda primero."

            path = self._results[index]

            if security.scope_error(path) or not path.exists():
                return "Ya no puedo abrir ese archivo, Jefe."

            return self._run(
                Action(ActionKind.OPEN_FILE, str(path), path.name,
                       path.name.lower(), True)
            )

        planned = files.plan(command)

        if not planned.success:
            return f"{planned.error.message} Lo siento, Jefe."

        op = planned.value
        decision = security.evaluate_file(op)

        if not decision.allowed:
            security.audit_file("automation.denied", op)
            return f"No puedo hacerlo, Jefe. {decision.reason}"

        if decision.requires_confirmation:
            self._pending_file = op
            return (
                f"Jefe, voy a {op.label}. ¿Confirmas? "
                "Responde «sí» o «no»."
            )

        return self._run_file(op)

    def _authorize(self, command: AutomationCommand) -> str:
        planned = self._service.plan(
            AutomationCommand(AutomationAction.OPEN, command.text, "folder")
        )

        if not planned.success:
            return f"{planned.error.message} Lo siento, Jefe."

        base = planned.value

        if base.builtin:
            return "Esa carpeta ya está permitida, Jefe."

        if Path(base.target).parent == Path(base.target):
            return "No autorizo discos completos, Jefe."

        scope = Action(
            ActionKind.FILES_SCOPE, base.target, base.label, base.key, False
        )

        if not self._security.evaluate(scope).requires_confirmation:
            return "Ya tenía autorizada esa carpeta, Jefe."

        self._pending = scope

        return (
            f"Jefe, ¿autorizo la carpeta {scope.label}? Podré buscar, "
            "copiar, mover y mandar a la papelera archivos dentro. "
            "Responde «sí» o «no»."
        )

    def _run_file(self, op: FileOperation) -> str:
        decision = self._security.evaluate_file(op)

        if not decision.allowed:
            self._security.audit_file("automation.denied", op)
            return f"No puedo hacerlo, Jefe. {decision.reason}"

        result = self._files.execute(op)

        if not result.success:
            return f"No pude hacerlo, Jefe. {result.error.message}"

        self._security.audit_file("automation.executed", op)

        if op.kind == FileOpKind.ORGANIZE:
            return f"Organizados {result.value} archivos, Jefe."

        return _DONE[op.kind]