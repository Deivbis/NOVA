"""Planifica (resuelve el destino) y ejecuta acciones (SPEC-007, D-031)."""

import re
from pathlib import Path
from urllib.parse import urlsplit

from nova.automation.commands import (
    FOLDER_ALIASES,
    AutomationAction,
    AutomationCommand,
)
from nova.automation.files import FileService
from nova.automation.provider import SystemProvider
from nova.core.automation import Action, ActionKind
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.memory.text import normalize
from nova.security import SecurityService

logger = get_logger(__name__)

_URL = re.compile(r"^(?:https?://)?[\w-]+(?:\.[\w-]+)+(?:[/:?#]\S*)?$")
_DRIVE = re.compile(r"^[A-Za-z]:[\\/]")

WEB_ALIASES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
}

MEDIA_LABELS = {
    "play_pause": "Pausando o reanudando la música",
    "next": "Siguiente canción",
    "previous": "Canción anterior",
    "volume_up": "Subiendo el volumen",
    "volume_down": "Bajando el volumen",
    "mute": "Silenciando",
}


def _invalid(message: str) -> Result:
    return Result.fail("AUTOMATION_INVALID_TARGET", message)


class AutomationService:
    def __init__(
        self,
        security: SecurityService,
        provider: SystemProvider,
        files: FileService | None = None,
        
    ) -> None:
        self.security = security
        self._provider = provider
        self.files = files or FileService(security)
        

    def plan(self, command: AutomationCommand) -> Result[Action]:
        if command.action == AutomationAction.MEDIA:
            return Result.ok(Action(
                ActionKind.MEDIA, command.media,
                MEDIA_LABELS[command.media], command.media, True,
            ))

        text = command.text.strip().strip("\"'")
        key = normalize(text)
        free = command.hint is None

        if command.hint == "program":
            return self._program(text)

        if command.hint == "web" or (
            free and (key in WEB_ALIASES or _URL.match(text))
        ):
            return self._web(text, key)

        if command.hint == "folder" or (free and key in FOLDER_ALIASES):
            return self._folder(text, key)

        return self._program(text)

    def execute(self, action: Action) -> Result:
        try:
            if action.kind == ActionKind.OPEN_WEB:
                self._provider.open_url(action.target)
            elif action.kind == ActionKind.MEDIA:
                self._provider.media(action.target)
            else:
                self._provider.open_path(action.target)
        except Exception as exc:
            logger.warning(
                "Fallo de automatización (%s): %s",
                action.kind.value, type(exc).__name__,
            )
            return Result.fail(
                "AUTOMATION_EXEC_ERROR", "No pude ejecutar la acción."
            )

        return Result.ok()

    def _web(self, text: str, key: str) -> Result[Action]:
        url = WEB_ALIASES.get(key)
        builtin = url is not None

        if url is None:
            candidate = text if "://" in text else f"https://{text}"
            parts = urlsplit(candidate)
            host = parts.hostname or ""

            if (
                " " in text
                or parts.scheme not in ("http", "https")
                or "." not in host
            ):
                return _invalid("Esa dirección web no es válida.")

            url = candidate

        host = (urlsplit(url).hostname or "").removeprefix("www.")

        return Result.ok(Action(ActionKind.OPEN_WEB, url, host, host, builtin))

    def _folder(self, text: str, key: str) -> Result[Action]:
        alias = FOLDER_ALIASES.get(key)

        if alias is not None:
            path, builtin = Path.home() / alias, True
        elif _DRIVE.match(text):
            path, builtin = Path(text), False
        else:
            return _invalid(
                "No conozco esa carpeta. Dime la ruta completa, "
                "por ejemplo C:\\Proyectos."
            )

        if not path.is_dir():
            return _invalid("Esa carpeta no existe.")

        return Result.ok(Action(
            ActionKind.OPEN_FOLDER, str(path), path.name or str(path),
            str(path).lower(), builtin,
        ))

    def _program(self, text: str) -> Result[Action]:
        found = self._provider.find_program(text)

        if found is None:
            return _invalid(
                f"No encontré «{text}» entre tus programas instalados."
            )

        label, target, builtin = found

        return Result.ok(Action(
            ActionKind.OPEN_PROGRAM, target, label,
            normalize(label), builtin,
        ))