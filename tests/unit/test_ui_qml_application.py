from unittest.mock import MagicMock

import pytest

from nova.core import Result
from nova.ui.qml import application
from nova.voice import VoiceSettings


class FakeSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback

    def emit(self):
        if self.callback is not None:
            self.callback()


class FakeApplication:
    def __init__(self, _args):
        self.aboutToQuit = FakeSignal()
        self.native_filters = []
        self.on_exec = None

    def installNativeEventFilter(self, event_filter):
        self.native_filters.append(event_filter)

    def exec(self):
        if self.on_exec is not None:
            self.on_exec()

        self.aboutToQuit.emit()
        return 0


class FakeEngine:
    def __init__(self, root_objects):
        self._root_objects = root_objects
        self._context = MagicMock()

    def rootContext(self):
        return self._context

    def addImportPath(self, _path):
        pass

    def load(self, _url):
        pass

    def rootObjects(self):
        return self._root_objects

class FakeOrb:
    def objectName(self):
        return "PermanentOrb"

@pytest.fixture
def startup_mocks(monkeypatch, tmp_path):
    fake_app = FakeApplication([])
    storage = MagicMock()
    orchestrator = MagicMock()
    engine = FakeEngine(
        [
            MagicMock(),
            FakeOrb(),
        ]
    )
    controller = MagicMock()
    bridge = MagicMock()
    bridge.orbStateChanged = FakeSignal()
    bridge.orbState = "idle"
    hotkey = MagicMock()
    hotkey.register.return_value = Result.ok()

    # Registra el orden en que se cierran los componentes.
    calls = MagicMock()
    calls.attach_mock(hotkey.unregister, "hotkey_unregister")
    calls.attach_mock(bridge.shutdown, "bridge_shutdown")
    calls.attach_mock(orchestrator.stop, "core_stop")
    calls.attach_mock(storage.close, "storage_close")

    dll_directory = MagicMock()

    monkeypatch.setattr(
        application.os,
        "add_dll_directory",
        lambda _path: dll_directory,
    )
    monkeypatch.setattr(
        application,
        "QGuiApplication",
        lambda _args: fake_app,
    )
    monkeypatch.setattr(
        application,
        "StorageService",
        lambda _path: storage,
    )
    monkeypatch.setattr(
        application,
        "create_core",
        lambda: orchestrator,
    )
    monkeypatch.setattr(
        application,
        "create_configuration",
        lambda: MagicMock(),
    )
    monkeypatch.setattr(
        application,
        "setup_logging",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        application,
        "default_logs_dir",
        lambda: tmp_path / "logs",
    )
    monkeypatch.setattr(
        application,
        "load_voice_settings",
        lambda: VoiceSettings(enabled=True),
    )
    monkeypatch.setattr(
        application,
        "GlobalHotkey",
        lambda: hotkey,
    )
    monkeypatch.setattr(
        application,
        "HotkeyFilter",
        lambda _callback: MagicMock(),
    )
    monkeypatch.setattr(
        application,
        "NovaUiBridge",
        lambda *_args: bridge,
    )
    monkeypatch.setattr(
        application,
        "QQmlApplicationEngine",
        lambda: engine,
    )
    monkeypatch.setattr(
        application,
        "WindowsOrbController",
        lambda _orb: controller,
    )
    monkeypatch.setattr(
        application,
        "default_database_path",
        lambda: tmp_path / "nova.db",
    )
    monkeypatch.setattr(
    application,
    "MemoryUiBridge",
    lambda _service, _parent: MagicMock(),
    )

    return {
        "app": fake_app,
        "storage": storage,
        "engine": engine,
        "controller": controller,
        "dll_directory": dll_directory,
        "orchestrator": orchestrator,
        "bridge": bridge,
        "hotkey": hotkey,
        "calls": calls,
    }


def test_storage_closes_when_main_qml_fails(
    startup_mocks,
):
    storage = startup_mocks["storage"]
    engine = startup_mocks["engine"]

    engine._root_objects = []

    result = application.main()

    assert result == 1
    storage.initialize.assert_called_once()
    storage.close.assert_called_once()
    startup_mocks["dll_directory"].close.assert_called_once()


def test_storage_closes_when_orb_qml_fails(
    startup_mocks,
):
    storage = startup_mocks["storage"]
    engine = startup_mocks["engine"]

    engine._root_objects = [
        MagicMock(),
    ]

    result = application.main()

    assert result == 1
    storage.close.assert_called_once()
    startup_mocks["dll_directory"].close.assert_called_once()


def test_storage_closes_when_orb_object_is_missing(
    startup_mocks,
):
    storage = startup_mocks["storage"]
    engine = startup_mocks["engine"]

    engine._root_objects = [
        MagicMock(),
        MagicMock(),
    ]

    result = application.main()

    assert result == 1
    storage.close.assert_called_once()


def test_storage_closes_after_normal_shutdown(
    startup_mocks,
):
    storage = startup_mocks["storage"]

    result = application.main()

    assert result == 0
    storage.close.assert_called_once()
    startup_mocks["dll_directory"].close.assert_called_once()


def test_components_shut_down_in_order_hotkey_ui_core_storage(
    startup_mocks,
):
    application.main()

    names = [call[0] for call in startup_mocks["calls"].mock_calls]

    assert names == [
        "hotkey_unregister",
        "bridge_shutdown",
        "core_stop",
        "storage_close",
    ]


def test_configuration_failure_returns_error_without_starting(
    startup_mocks,
    monkeypatch,
):
    def broken_configuration():
        raise RuntimeError("configuración rota")

    monkeypatch.setattr(
        application,
        "create_configuration",
        broken_configuration,
    )

    result = application.main()

    assert result == 1
    startup_mocks["storage"].initialize.assert_not_called()
    startup_mocks["dll_directory"].close.assert_called_once()


def test_hotkey_is_registered_when_voice_is_enabled(
    startup_mocks,
):
    application.main()

    startup_mocks["hotkey"].register.assert_called_once_with("pause")


def test_hotkey_is_not_registered_when_voice_is_disabled(
    startup_mocks,
    monkeypatch,
):
    monkeypatch.setattr(
        application,
        "load_voice_settings",
        lambda: VoiceSettings(enabled=False),
    )

    result = application.main()

    assert result == 0
    startup_mocks["hotkey"].register.assert_not_called()


def test_startup_continues_when_the_hotkey_cannot_be_registered(
    startup_mocks,
):
    startup_mocks["hotkey"].register.return_value = Result.fail(
        code="HOTKEY_REGISTER_FAILED",
        message="Otra aplicación usa el atajo.",
    )

    result = application.main()

    assert result == 0
    startup_mocks["storage"].close.assert_called_once()

def test_native_event_filter_is_installed(
    startup_mocks,
):
    result = application.main()

    assert result == 0

    controller = startup_mocks["controller"]
    app = startup_mocks["app"]

    assert any(
        event_filter is controller.native_filter
        for event_filter in app.native_filters
    )

    assert len(app.native_filters) == 2

def test_orb_state_changes_are_forwarded_to_controller(
    startup_mocks,
):
    app = startup_mocks["app"]
    bridge = startup_mocks["bridge"]
    controller = startup_mocks["controller"]

    def emit_state_changes():
        bridge.orbState = "listening"
        bridge.orbStateChanged.emit()

        bridge.orbState = "processing"
        bridge.orbStateChanged.emit()

        bridge.orbState = "idle"
        bridge.orbStateChanged.emit()

    app.on_exec = emit_state_changes

    result = application.main()

    assert result == 0

    assert controller.set_orb_state.call_args_list == [
        (("listening",),),
        (("processing",),),
        (("idle",),),
    ]