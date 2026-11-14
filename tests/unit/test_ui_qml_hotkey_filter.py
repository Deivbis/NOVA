import ctypes
from ctypes import wintypes

from nova.ui.qml.hotkey_filter import WM_HOTKEY, HotkeyFilter
from nova.voice.hotkey import HOTKEY_ID


def make_message(message, wparam):
    msg = wintypes.MSG()
    msg.message = message
    msg.wParam = wparam

    return msg


def call_filter(event_filter, msg, event_type=b"windows_generic_MSG"):
    return event_filter.nativeEventFilter(event_type, ctypes.addressof(msg))


def test_hotkey_message_triggers_the_callback_and_is_consumed():
    calls = []
    event_filter = HotkeyFilter(lambda: calls.append(1))

    handled, _ = call_filter(event_filter, make_message(WM_HOTKEY, HOTKEY_ID))

    assert handled is True
    assert calls == [1]


def test_other_messages_are_ignored():
    calls = []
    event_filter = HotkeyFilter(lambda: calls.append(1))

    handled, _ = call_filter(event_filter, make_message(0x0100, HOTKEY_ID))

    assert handled is False
    assert calls == []


def test_other_hotkey_ids_are_ignored():
    calls = []
    event_filter = HotkeyFilter(lambda: calls.append(1))

    handled, _ = call_filter(
        event_filter,
        make_message(WM_HOTKEY, HOTKEY_ID + 1),
    )

    assert handled is False
    assert calls == []


def test_other_event_types_are_ignored():
    calls = []
    event_filter = HotkeyFilter(lambda: calls.append(1))

    handled, _ = call_filter(
        event_filter,
        make_message(WM_HOTKEY, HOTKEY_ID),
        event_type=b"xcb_generic_event_t",
    )

    assert handled is False
    assert calls == []