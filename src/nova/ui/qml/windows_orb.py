from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import (
    QObject,
    QAbstractNativeEventFilter,
    Qt,
)


GWL_EXSTYLE = -20

WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

WM_NCHITTEST = 0x0084
WM_MOUSEACTIVATE = 0x0021

HTTRANSPARENT = -1
MA_NOACTIVATE = 3


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
        ("lPrivate", wintypes.DWORD),
    ]


class WindowsOrbNativeFilter(QAbstractNativeEventFilter):
    """Filtro nativo de Windows para el Orbe permanente."""

    def __init__(
        self,
        hwnd: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__()

        self.hwnd = int(hwnd)
        self.parent = parent
        self.idle = True

    def set_idle(self, enabled: bool) -> None:
        self.idle = bool(enabled)

    def nativeEventFilter(
        self,
        event_type,
        message,
    ):
        if event_type not in (
            b"windows_generic_MSG",
            b"windows_dispatcher_MSG",
            "windows_generic_MSG",
            "windows_dispatcher_MSG",
        ):
            return False, 0

        try:
            address = int(message.__int__())
            msg = MSG.from_address(address)
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return False, 0

        if not msg.hwnd:
            return False, 0

        if int(msg.hwnd) != self.hwnd:
            return False, 0

        if not self.idle:
            return False, 0

        if msg.message == WM_NCHITTEST:
            return True, HTTRANSPARENT

        if msg.message == WM_MOUSEACTIVATE:
            return True, MA_NOACTIVATE

        return False, 0


class WindowsOrbController(QObject):
    """Control Windows del Orbe permanente de NOVA."""

    def __init__(
        self,
        window,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.window = window
        self.hwnd = int(window.winId())

        self.user32 = ctypes.windll.user32

        # IMPORTANTE:
        # Este atributo es el filtro que application.py instala.
        self.native_filter = WindowsOrbNativeFilter(
            self.hwnd,
            self,
        )

        self._configure_native_window()
        self.set_idle(True)

    def _get_extended_style(self) -> int:
        return int(
            self.user32.GetWindowLongPtrW(
                wintypes.HWND(self.hwnd),
                GWL_EXSTYLE,
            )
        )

    def _set_extended_style(
        self,
        style: int,
    ) -> None:
        ctypes.set_last_error(0)

        result = self.user32.SetWindowLongPtrW(
            wintypes.HWND(self.hwnd),
            GWL_EXSTYLE,
            ctypes.c_ssize_t(style),
        )

        if result == 0:
            error = ctypes.get_last_error()

            if error:
                raise ctypes.WinError(error)

    def _configure_native_window(self) -> None:
        style = self._get_extended_style()

        style |= WS_EX_NOACTIVATE
        style |= WS_EX_TOOLWINDOW

        self._set_extended_style(style)

    def set_idle(
        self,
        enabled: bool,
    ) -> None:
        enabled = bool(enabled)

        self.native_filter.set_idle(enabled)

        self.window.setFlag(
            Qt.WindowTransparentForInput,
            enabled,
        )

        self.window.setFlag(
            Qt.WindowDoesNotAcceptFocus,
            True,
        )

        self._configure_native_window()

    def set_orb_state(
        self,
        state: str,
    ) -> None:
        """Sincroniza el comportamiento Windows con el estado visual."""
        self.set_idle(
            state == "idle",
        )

    def is_idle(self) -> bool:
        return self.native_filter.idle