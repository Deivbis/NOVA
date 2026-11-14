"""Atajo de teclado global (D-013): una pulsación escucha, cancela o interrumpe.

Usa RegisterHotKey de Windows: funciona con cualquier ventana en primer plano
y no necesita librerías. Este módulo no depende de Qt.
"""

import ctypes
from collections.abc import Callable
from typing import Any

from nova.core.logging_setup import get_logger
from nova.core.result import Result

logger = get_logger(__name__)

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

HOTKEY_ID = 0x4E56

_MODIFIERS = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}

_NAMED_KEYS = {
    "pause": 0x13,
    "break": 0x13,
    "scrolllock": 0x91,
    "space": 0x20,
    "insert": 0x2D,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
}


def _key_code(token: str, text: str) -> int:
    if token in _NAMED_KEYS:
        return _NAMED_KEYS[token]

    if token.startswith("f") and token[1:].isdigit():
        number = int(token[1:])

        if 1 <= number <= 24:
            return 0x70 + number - 1

    if len(token) == 1 and token.isalnum() and token.isascii():
        return ord(token.upper())

    raise ValueError(f"Tecla no reconocida en el atajo '{text}': '{token}'.")


def parse_hotkey(text: str) -> tuple[int, int]:
    """Convierte 'ctrl+shift+f9' en (modificadores, código de tecla)."""
    modifiers = 0
    key_code: int | None = None

    for raw in text.split("+"):
        token = raw.strip().lower().replace(" ", "")

        if not token:
            raise ValueError(f"Atajo no válido: '{text}'.")

        if token in _MODIFIERS:
            modifiers |= _MODIFIERS[token]
            continue

        if key_code is not None:
            raise ValueError(f"El atajo '{text}' tiene más de una tecla.")

        key_code = _key_code(token, text)

    if key_code is None:
        raise ValueError(f"El atajo '{text}' no incluye ninguna tecla.")

    return modifiers, key_code


def _load_user32() -> Any | None:
    windll = getattr(ctypes, "windll", None)

    return windll.user32 if windll is not None else None


class GlobalHotkey:
    """Registra y libera un atajo global en el hilo que la crea."""

    def __init__(
        self,
        loader: Callable[[], Any | None] | None = None,
        hotkey_id: int = HOTKEY_ID,
    ) -> None:
        self._loader = loader or _load_user32
        self._hotkey_id = hotkey_id
        self._user32: Any | None = None
        self._registered = False

    @property
    def is_registered(self) -> bool:
        return self._registered

    def register(self, text: str) -> Result[None]:
        try:
            modifiers, key_code = parse_hotkey(text)
        except ValueError as exc:
            return Result.fail(code="HOTKEY_INVALID", message=str(exc))

        user32 = self._loader()

        if user32 is None:
            return Result.fail(
                code="HOTKEY_UNSUPPORTED",
                message="Los atajos globales solo están disponibles en Windows.",
            )

        self._user32 = user32
        self.unregister()

        if not user32.RegisterHotKey(
            None,
            self._hotkey_id,
            modifiers | MOD_NOREPEAT,
            key_code,
        ):
            return Result.fail(
                code="HOTKEY_REGISTER_FAILED",
                message=(
                    f"No se pudo registrar el atajo '{text}'; puede que "
                    f"otra aplicación lo esté usando."
                ),
            )

        self._registered = True

        return Result.ok()

    def unregister(self) -> None:
        if not self._registered or self._user32 is None:
            return

        self._user32.UnregisterHotKey(None, self._hotkey_id)
        self._registered = False