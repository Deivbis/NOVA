from unittest.mock import MagicMock

from nova.core import OrbState
from nova.ui.orb import NovaOrb


def create_orb(monkeypatch):
    fake_window = MagicMock()
    fake_window.winfo_id.return_value = 1234
    fake_window.winfo_screenwidth.return_value = 1920
    fake_window.winfo_screenheight.return_value = 1080

    fake_canvas = MagicMock()
    fake_canvas.create_oval.return_value = "orb"
    fake_canvas.create_text.return_value = "label"

    import nova.ui.orb.window as orb_window

    monkeypatch.setattr(
        orb_window.tk,
        "Toplevel",
        lambda root: fake_window,
    )

    monkeypatch.setattr(
        orb_window.tk,
        "Canvas",
        lambda *args, **kwargs: fake_canvas,
    )

    fake_window_style = MagicMock()
    fake_window_style.is_click_through.return_value = True

    monkeypatch.setattr(
        orb_window,
        "WindowsWindowStyle",
        lambda hwnd: fake_window_style,
    )

    orb = NovaOrb(MagicMock())

    return orb, fake_window, fake_canvas


def test_orb_creates_window(monkeypatch) -> None:
    orb, window, canvas = create_orb(monkeypatch)

    assert orb.window is window
    assert orb.canvas is canvas


def test_orb_starts_idle(monkeypatch) -> None:
    orb, _, canvas = create_orb(monkeypatch)

    assert orb.state == OrbState.IDLE
    canvas.itemconfigure.assert_any_call(
        orb.orb,
        fill="#4F46E5",
    )


def test_orb_changes_to_listening(monkeypatch) -> None:
    orb, _, canvas = create_orb(monkeypatch)

    orb.set_state(OrbState.LISTENING)

    assert orb.state == OrbState.LISTENING
    canvas.itemconfigure.assert_any_call(
        orb.orb,
        fill="#10B981",
    )


def test_orb_changes_to_processing(monkeypatch) -> None:
    orb, _, canvas = create_orb(monkeypatch)

    orb.set_state(OrbState.PROCESSING)

    assert orb.state == OrbState.PROCESSING
    canvas.itemconfigure.assert_any_call(
        orb.orb,
        fill="#F59E0B",
    )


def test_orb_changes_to_responding(monkeypatch) -> None:
    orb, _, canvas = create_orb(monkeypatch)

    orb.set_state(OrbState.RESPONDING)

    assert orb.state == OrbState.RESPONDING
    canvas.itemconfigure.assert_any_call(
        orb.orb,
        fill="#3B82F6",
    )


def test_orb_changes_to_error(monkeypatch) -> None:
    orb, _, canvas = create_orb(monkeypatch)

    orb.set_state(OrbState.ERROR)

    assert orb.state == OrbState.ERROR
    canvas.itemconfigure.assert_any_call(
        orb.orb,
        fill="#EF4444",
    )


def test_orb_hide_calls_withdraw(monkeypatch) -> None:
    orb, window, _ = create_orb(monkeypatch)

    orb.hide()

    window.withdraw.assert_called_once_with()


def test_orb_show_calls_deiconify(monkeypatch) -> None:
    orb, window, _ = create_orb(monkeypatch)

    orb.show()

    window.deiconify.assert_called_once_with()


def test_orb_close_destroys_window(monkeypatch) -> None:
    orb, window, _ = create_orb(monkeypatch)

    orb.close()

    window.destroy.assert_called_once_with()


def test_orb_can_enable_click_through(monkeypatch) -> None:
    orb, _, _ = create_orb(monkeypatch)

    orb.window_style.set_click_through.reset_mock()

    orb.enable_click_through()

    orb.window_style.set_click_through.assert_called_once_with(True)


def test_orb_can_disable_click_through(monkeypatch) -> None:
    orb, _, _ = create_orb(monkeypatch)

    orb.window_style.set_click_through.reset_mock()

    orb.disable_click_through()

    orb.window_style.set_click_through.assert_called_once_with(False)


def test_orb_can_check_click_through(monkeypatch) -> None:
    orb, _, _ = create_orb(monkeypatch)

    assert orb.is_click_through() is True

    orb.window_style.is_click_through.assert_called_once_with()