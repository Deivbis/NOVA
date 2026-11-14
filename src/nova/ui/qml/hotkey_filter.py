"""Filtro de eventos nativos de Windows para el atajo global de voz."""

import ctypes
from collections.abc import Callable
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter

from nova.core.logging_setup import get_logger
from nova.voice.hotkey import HOTKEY_ID

logger = get_logger(__name__)

WM_HOTKEY = 0x0312

_MESSAGE_TYPES = (b"windows_generic_MSG", b"windows_dispatcher_MSG")


class HotkeyFilter(QAbstractNativeEventFilter):
    """Llama al callback cuando Windows avisa de que se pulsó el atajo."""

    def __init__(
        self,
        callback: Callable[[], None],
        hotkey_id: int = HOTKEY_ID,
    ) -> None:
        super().__init__()
        self._callback = callback
        self._hotkey_id = hotkey_id

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) not in _MESSAGE_TYPES:
            return False, 0

        address = int(message)

        if address == 0:
            return False, 0

        msg = wintypes.MSG.from_address(address)

        if msg.message == WM_HOTKEY and msg.wParam == self._hotkey_id:
            try:
                self._callback()
            except Exception:
                logger.exception("El atajo de voz falló.")

            return True, 0

        return False, 0