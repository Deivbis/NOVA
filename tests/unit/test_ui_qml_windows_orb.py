import ctypes
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from nova.ui.qml import windows_orb


class MessageAddress:
    def __init__(self, address):
        self.address = address

    def __int__(self):
        return self.address


def create_native_message(hwnd, message):
    msg = windows_orb.MSG()
    msg.hwnd = hwnd
    msg.message = message
    return msg, MessageAddress(ctypes.addressof(msg))


def test_native_filter_starts_idle():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    assert event_filter.hwnd == 1234
    assert event_filter.idle is True


def test_native_filter_ignores_other_event_types():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    msg, address = create_native_message(
        1234,
        windows_orb.WM_NCHITTEST,
    )

    result = event_filter.nativeEventFilter(
        b"other_event",
        address,
    )

    assert result == (False, 0)


@pytest.mark.parametrize(
    "event_type",
    [
        b"windows_generic_MSG",
        b"windows_dispatcher_MSG",
        "windows_generic_MSG",
        "windows_dispatcher_MSG",
    ],
)
def test_native_filter_accepts_windows_event_types(event_type):
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    msg, address = create_native_message(
        1234,
        windows_orb.WM_NCHITTEST,
    )

    assert event_filter.nativeEventFilter(
        event_type,
        address,
    ) == (True, windows_orb.HTTRANSPARENT)


def test_native_filter_ignores_invalid_message_pointer():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    result = event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        object(),
    )

    assert result == (False, 0)


def test_native_filter_ignores_other_windows():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    msg, address = create_native_message(
        5678,
        windows_orb.WM_NCHITTEST,
    )

    assert event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        address,
    ) == (False, 0)


def test_native_filter_ignores_messages_when_not_idle():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)
    event_filter.set_idle(False)

    msg, address = create_native_message(
        1234,
        windows_orb.WM_NCHITTEST,
    )

    assert event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        address,
    ) == (False, 0)


def test_native_filter_makes_idle_orb_click_through():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    msg, address = create_native_message(
        1234,
        windows_orb.WM_NCHITTEST,
    )

    assert event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        address,
    ) == (True, windows_orb.HTTRANSPARENT)


def test_native_filter_prevents_mouse_activation():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    msg, address = create_native_message(
        1234,
        windows_orb.WM_MOUSEACTIVATE,
    )

    assert event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        address,
    ) == (True, windows_orb.MA_NOACTIVATE)


def test_native_filter_ignores_unhandled_messages():
    event_filter = windows_orb.WindowsOrbNativeFilter(1234)

    msg, address = create_native_message(
        1234,
        0x000F,
    )

    assert event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        address,
    ) == (False, 0)


@pytest.fixture
def controller_setup(monkeypatch):
    user32 = MagicMock()
    user32.GetWindowLongPtrW.return_value = 0
    user32.SetWindowLongPtrW.return_value = 1

    monkeypatch.setattr(
        windows_orb.ctypes,
        "windll",
        SimpleNamespace(user32=user32),
    )

    window = MagicMock()
    window.winId.return_value = 1234

    controller = windows_orb.WindowsOrbController(window)

    return controller, window, user32


def test_controller_keeps_window_handle(controller_setup):
    controller, _, _ = controller_setup

    assert controller.hwnd == 1234
    assert controller.native_filter.hwnd == 1234


def test_controller_adds_required_native_styles(controller_setup):
    controller, _, user32 = controller_setup

    calls = user32.SetWindowLongPtrW.call_args_list

    assert calls

    for call in calls:
        style = call.args[2].value

        assert style & windows_orb.WS_EX_NOACTIVATE
        assert style & windows_orb.WS_EX_TOOLWINDOW


def test_controller_starts_idle_and_transparent(controller_setup):
    controller, window, _ = controller_setup

    assert controller.is_idle() is True

    window.setFlag.assert_any_call(
        windows_orb.Qt.WindowTransparentForInput,
        True,
    )

    window.setFlag.assert_any_call(
        windows_orb.Qt.WindowDoesNotAcceptFocus,
        True,
    )


def test_controller_disables_transparency_when_active(controller_setup):
    controller, window, _ = controller_setup

    controller.set_idle(False)

    assert controller.is_idle() is False
    assert controller.native_filter.idle is False

    window.setFlag.assert_any_call(
        windows_orb.Qt.WindowTransparentForInput,
        False,
    )


@pytest.mark.parametrize(
    ("state", "expected_idle"),
    [
        ("idle", True),
        ("listening", False),
        ("processing", False),
        ("responding", False),
        ("error", False),
    ],
)
def test_controller_maps_orb_states(
    controller_setup,
    state,
    expected_idle,
):
    controller, _, _ = controller_setup

    controller.set_orb_state(state)

    assert controller.is_idle() is expected_idle


def test_controller_always_prevents_window_focus(controller_setup):
    controller, window, _ = controller_setup

    controller.set_idle(False)

    window.setFlag.assert_any_call(
        windows_orb.Qt.WindowDoesNotAcceptFocus,
        True,
    )
