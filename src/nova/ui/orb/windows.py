import ctypes
from ctypes import wintypes


GWL_EXSTYLE = -20

WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

LWA_ALPHA = 0x00000002

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020


class WindowsWindowStyle:
    """Windows-specific style manager for the NOVA Orb."""

    def __init__(self, hwnd: int):
        self.hwnd = int(hwnd)

        self.user32 = ctypes.windll.user32

        self.get_window_long_ptr = self.user32.GetWindowLongPtrW
        self.set_window_long_ptr = self.user32.SetWindowLongPtrW
        self.set_window_pos = self.user32.SetWindowPos
        self.set_layered_window_attributes = (
            self.user32.SetLayeredWindowAttributes
        )

        self.get_window_long_ptr.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
        ]
        self.get_window_long_ptr.restype = ctypes.c_ssize_t

        self.set_window_long_ptr.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_ssize_t,
        ]
        self.set_window_long_ptr.restype = ctypes.c_ssize_t

        self.set_window_pos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        self.set_window_pos.restype = wintypes.BOOL

        self.set_layered_window_attributes.argtypes = [
            wintypes.HWND,
            wintypes.COLORREF,
            wintypes.BYTE,
            wintypes.DWORD,
        ]
        self.set_layered_window_attributes.restype = wintypes.BOOL

    def _get_extended_style(self) -> int:
        return int(
            self.get_window_long_ptr(
                self.hwnd,
                GWL_EXSTYLE,
            )
        )

    def _set_extended_style(self, style: int) -> None:
        ctypes.set_last_error(0)

        previous = self.set_window_long_ptr(
            self.hwnd,
            GWL_EXSTYLE,
            style,
        )

        if previous == 0 and ctypes.get_last_error() != 0:
            raise ctypes.WinError()

        success = self.set_window_pos(
            self.hwnd,
            0,
            0,
            0,
            0,
            0,
            (
                SWP_NOMOVE
                | SWP_NOSIZE
                | SWP_NOZORDER
                | SWP_NOACTIVATE
                | SWP_FRAMECHANGED
            ),
        )

        if not success:
            raise ctypes.WinError()

    def set_click_through(self, enabled: bool) -> None:
        """
        Configure the Orb for passive or interactive mouse behavior.

        IDLE:
            - layered
            - transparent to mouse
            - cannot activate
            - hidden from normal task switching

        Active states:
            - layered
            - receives mouse input
            - still cannot steal activation unnecessarily
        """
        style = self._get_extended_style()

        # Required for top-level transparent hit-testing.
        style |= WS_EX_LAYERED

        # NOVA Orb should never behave like a normal application window.
        style |= WS_EX_NOACTIVATE
        style |= WS_EX_TOOLWINDOW

        if enabled:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT

        self._set_extended_style(style)

        success = self.set_layered_window_attributes(
            self.hwnd,
            0,
            255,
            LWA_ALPHA,
        )

        if not success:
            raise ctypes.WinError()

    def is_click_through(self) -> bool:
        return bool(
            self._get_extended_style()
            & WS_EX_TRANSPARENT
        )