from unittest.mock import MagicMock

import nova.ui.orb.windows as windows


def create_window_style(monkeypatch):
    user32 = MagicMock()

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        MagicMock(user32=user32),
    )

    style = windows.WindowsWindowStyle(
        hwnd=1234
    )

    return style, user32


def test_window_keeps_provided_hwnd(monkeypatch):
    style, _ = create_window_style(monkeypatch)

    assert style.hwnd == 1234


def test_click_through_adds_required_styles(monkeypatch):
    style, user32 = create_window_style(monkeypatch)

    user32.GetWindowLongPtrW.return_value = 0
    user32.SetLayeredWindowAttributes.return_value = 1

    style.set_click_through(True)

    user32.SetWindowLongPtrW.assert_called_once()

    _, _, new_style = (
        user32.SetWindowLongPtrW.call_args.args
    )

    assert new_style & windows.WS_EX_LAYERED
    assert new_style & windows.WS_EX_TRANSPARENT
    assert new_style & windows.WS_EX_NOACTIVATE


def test_click_through_can_be_disabled(monkeypatch):
    style, user32 = create_window_style(monkeypatch)

    user32.GetWindowLongPtrW.return_value = (
        windows.WS_EX_LAYERED
        | windows.WS_EX_TRANSPARENT
        | windows.WS_EX_NOACTIVATE
    )

    user32.SetLayeredWindowAttributes.return_value = 1

    style.set_click_through(False)

    _, _, new_style = (
        user32.SetWindowLongPtrW.call_args.args
    )

    assert new_style & windows.WS_EX_LAYERED
    assert new_style & windows.WS_EX_NOACTIVATE
    assert not (
        new_style & windows.WS_EX_TRANSPARENT
    )


def test_click_through_refreshes_window_frame(monkeypatch):
    style, user32 = create_window_style(monkeypatch)

    user32.GetWindowLongPtrW.return_value = 0
    user32.SetLayeredWindowAttributes.return_value = 1

    style.set_click_through(True)

    user32.SetWindowPos.assert_called_once()

    args = user32.SetWindowPos.call_args.args
    flags = args[-1]

    assert flags & windows.SWP_FRAMECHANGED
    assert flags & windows.SWP_NOACTIVATE


def test_is_click_through_returns_true(monkeypatch):
    style, user32 = create_window_style(monkeypatch)

    user32.GetWindowLongPtrW.return_value = (
        windows.WS_EX_TRANSPARENT
    )

    assert style.is_click_through() is True


def test_is_click_through_returns_false(monkeypatch):
    style, user32 = create_window_style(monkeypatch)

    user32.GetWindowLongPtrW.return_value = 0

    assert style.is_click_through() is False