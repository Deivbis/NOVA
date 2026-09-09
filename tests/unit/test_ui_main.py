from unittest.mock import MagicMock

import pytest

from nova.core import ConnectivityState, NovaState, OrbState
from nova.ui import UIState
from nova.ui.main import MainWindow


def create_ui_state() -> UIState:
    return UIState(
        nova_state=NovaState.IDLE,
        connectivity=ConnectivityState.ONLINE,
        orb_state=OrbState.IDLE,
    )


def test_main_window_configures_root() -> None:
    root = MagicMock()

    MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    root.title.assert_called_once_with("NOVA")
    root.geometry.assert_called_once_with("1100x700")
    root.minsize.assert_called_once_with(900, 600)


def test_main_window_has_expected_navigation_items() -> None:
    root = MagicMock()

    window = MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    assert window.NAVIGATION_ITEMS == (
        "Inicio",
        "Chat",
        "Memoria",
        "Proyectos",
        "Sistema",
        "Configuración",
    )

    assert set(window.navigation_buttons) == set(
        window.NAVIGATION_ITEMS
    )


def test_main_window_starts_on_home_section() -> None:
    root = MagicMock()

    window = MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    assert window.current_section == "Inicio"


def test_main_window_changes_section() -> None:
    root = MagicMock()

    window = MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    window.show_section("Chat")

    assert window.current_section == "Chat"


def test_main_window_rejects_invalid_section() -> None:
    root = MagicMock()

    window = MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    with pytest.raises(ValueError):
        window.show_section("SeccionInexistente")


def test_main_window_run_starts_event_loop() -> None:
    root = MagicMock()

    window = MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    window.run()

    root.mainloop.assert_called_once_with()


def test_main_window_close_destroys_root() -> None:
    root = MagicMock()

    window = MainWindow(
        root=root,
        ui_state=create_ui_state(),
    )

    window.close()

    root.destroy.assert_called_once_with()