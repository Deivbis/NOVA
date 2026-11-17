"""Respuestas deterministas de automatización con confirmación (D-031)."""

from nova.automation.commands import (
    AutomationAction,
    AutomationCommand,
    parse_automation_command,
)
from nova.automation.service import AutomationService
from nova.core.automation import Action, ActionKind
from nova.core.confirmation import parse_yes_no
from nova.core.logging_setup import get_logger
from nova.storage.exceptions import RepositoryError

logger = get_logger(__name__)

_KIND = {
    ActionKind.OPEN_PROGRAM: "programa",
    ActionKind.OPEN_FOLDER: "carpeta",
    ActionKind.OPEN_WEB: "sitio web",
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

    def reply_to(self, text: str) -> str | None:
        try:
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

        self._security.audit("automation.executed", action)

        if action.kind == ActionKind.MEDIA:
            return f"{action.label}, Jefe."

        return f"Abriendo {action.label}, Jefe."