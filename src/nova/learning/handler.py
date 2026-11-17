"""Respuestas deterministas del aprendizaje (sin modelo, D-030)."""

from nova.core.learning import LearningCandidate, LearningKind
from nova.learning.commands import LearningAction, parse_learning_command
from nova.learning.service import (
    PATTERN_PREFIX,
    PATTERN_WINDOW_DAYS,
    LearningService,
)
from nova.memory.text import normalize
from nova.core.confirmation import parse_yes_no as _yes_no


class LearningCommandHandler:
    def __init__(self, service: LearningService) -> None:
        self._service = service

    def observe(self, text: str, conversation_id) -> None:
        self._service.observe(text, conversation_id)

    def proposal(self) -> str | None:
        candidate = self._service.next_proposal()

        return self._proposal_text(candidate) if candidate else None

    def reply_to(self, text: str) -> str | None:
        """Respuesta local si el texto es un sí/no pendiente o una orden."""
        if self._service.awaiting:
            result = self._service.resolve(_yes_no(text))

            if result is not None:
                if not result.success:
                    return f"No pude hacerlo, Jefe. {result.error.message}"

                if _yes_no(text):
                    return (
                        f"Anotado, Jefe: {result.value.content}. "
                        "Puedes pedirme que lo olvide cuando quieras."
                    )

                return "Entendido, Jefe. No volveré a proponer eso."

        action = parse_learning_command(text)

        return self._handle(action) if action is not None else None

    def _handle(self, action: LearningAction) -> str:
        service = self._service

        if action == LearningAction.DISABLE:
            service.set_enabled(False)
            return (
                "Aprendizaje desactivado, Jefe. No observaré nada nuevo; "
                "lo ya guardado se conserva."
            )

        if action == LearningAction.ENABLE:
            service.set_enabled(True)
            return "Aprendizaje activado, Jefe."

        if action == LearningAction.ACCEPT_ALL:
            return f"Hecho, Jefe: {service.resolve_all(True)} aprendizajes guardados."

        if action == LearningAction.REJECT_ALL:
            return f"Hecho, Jefe: {service.resolve_all(False)} aprendizajes descartados."

        learned, pending = service.learned(), service.pending()
        state = "activado" if service.enabled else "desactivado"

        if not learned and not pending:
            return f"Aún no he aprendido nada de ti, Jefe. (Aprendizaje {state}.)"

        parts = [f"Aprendizaje {state}, Jefe."]

        if learned:
            parts.append("Lo que he aprendido:")
            parts += [f"- {m.content}" for m in learned[:10]]

        if pending:
            parts.append("Pendiente de tu confirmación:")
            parts += [f"- {c.content}" for c in pending[:10]]
            parts.append("Di «confirma lo aprendido» o «descarta lo aprendido».")

        return "\n".join(parts)

    @staticmethod
    def _proposal_text(c: LearningCandidate) -> str:
        if c.kind == LearningKind.EXPLICIT:
            return (
                f"Jefe, ¿quieres que recuerde esto?: {c.content}. "
                "Responde «sí» o «no»."
            )
        word = c.content.removeprefix(PATTERN_PREFIX)
        return (
            f"Jefe, noto que hablas mucho de {word} "
            f"({c.evidence} mensajes en {PATTERN_WINDOW_DAYS} días). "
            "¿Quieres que lo guarde como un gusto o preferencia tuya? "
            "Responde «sí» o «no»."
        )