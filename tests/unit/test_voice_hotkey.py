import pytest

from nova.voice import GlobalHotkey, parse_hotkey
from nova.voice.hotkey import (
    HOTKEY_ID,
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
)


class FakeUser32:
    def __init__(self, succeed=True):
        self.succeed = succeed
        self.registered = []
        self.unregistered = []

    def RegisterHotKey(self, hwnd, hotkey_id, modifiers, key_code):
        self.registered.append((hwnd, hotkey_id, modifiers, key_code))

        return 1 if self.succeed else 0

    def UnregisterHotKey(self, hwnd, hotkey_id):
        self.unregistered.append((hwnd, hotkey_id))

        return 1


def create_hotkey(user32):
    return GlobalHotkey(loader=lambda: user32)


def test_parse_named_keys_and_modifiers():
    assert parse_hotkey("pause") == (0, 0x13)
    assert parse_hotkey("Scroll Lock") == (0, 0x91)
    assert parse_hotkey("ctrl+shift+f9") == (MOD_CONTROL | MOD_SHIFT, 0x78)
    assert parse_hotkey("Ctrl + Alt + N") == (
        MOD_CONTROL | MOD_ALT,
        ord("N"),
    )


def test_parse_function_and_digit_keys():
    assert parse_hotkey("f1") == (0, 0x70)
    assert parse_hotkey("f24") == (0, 0x87)
    assert parse_hotkey("5") == (0, ord("5"))


def test_parse_rejects_invalid_hotkeys():
    for text in ("", "   ", "ctrl+", "banana", "ctrl+alt", "a+b", "f25"):
        with pytest.raises(ValueError):
            parse_hotkey(text)


def test_register_calls_the_windows_api_with_norepeat():
    user32 = FakeUser32()
    hotkey = create_hotkey(user32)

    result = hotkey.register("pause")

    assert result.success
    assert user32.registered == [(None, HOTKEY_ID, MOD_NOREPEAT, 0x13)]
    assert hotkey.is_registered is True


def test_register_failure_is_reported():
    hotkey = create_hotkey(FakeUser32(succeed=False))

    result = hotkey.register("pause")

    assert not result.success
    assert result.error.code == "HOTKEY_REGISTER_FAILED"
    assert hotkey.is_registered is False


def test_invalid_hotkey_does_not_touch_the_api():
    user32 = FakeUser32()
    hotkey = create_hotkey(user32)

    result = hotkey.register("banana")

    assert result.error.code == "HOTKEY_INVALID"
    assert user32.registered == []


def test_register_without_windows_returns_unsupported():
    hotkey = GlobalHotkey(loader=lambda: None)

    result = hotkey.register("pause")

    assert result.error.code == "HOTKEY_UNSUPPORTED"


def test_unregister_is_idempotent():
    user32 = FakeUser32()
    hotkey = create_hotkey(user32)

    hotkey.unregister()

    assert user32.unregistered == []

    hotkey.register("pause")
    hotkey.unregister()
    hotkey.unregister()

    assert user32.unregistered == [(None, HOTKEY_ID)]
    assert hotkey.is_registered is False


def test_registering_again_replaces_the_previous_hotkey():
    user32 = FakeUser32()
    hotkey = create_hotkey(user32)

    hotkey.register("pause")
    hotkey.register("scroll lock")

    assert user32.unregistered == [(None, HOTKEY_ID)]
    assert len(user32.registered) == 2