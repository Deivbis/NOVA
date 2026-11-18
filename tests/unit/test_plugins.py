import json
import queue
import time
from concurrent.futures import Future

from nova.automation import AutomationService
from nova.memory import MemoryService
from nova.plugins import (
    NOVA_VERSION,
    MainThread,
    PluginAPI,
    PluginCommandHandler,
    PluginManager,
)
from nova.plugins.manifest import load_manifest
from nova.security import SecurityService
from nova.storage import StorageService

ECHO = '''
from nova.plugin_sdk.sdk import PluginBase
class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        return "eco: " + groups["t"]
'''
BOOM = '''
from nova.plugin_sdk.sdk import PluginBase
class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        raise RuntimeError("x")
'''
SLOW = '''
import time
from nova.plugin_sdk.sdk import PluginBase
class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        time.sleep(5)
'''
NET = '''
from nova.plugin_sdk.sdk import PluginBase, PluginError
class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        try:
            self.ctx.http_get("https://evil.test/x")
        except PluginError as exc:
            return "denegado: " + str(exc)
        return "sin error"
'''
SPEAK = '''
from nova.plugin_sdk.sdk import PluginBase
class Plugin(PluginBase):
    def on_command(self, command, text, groups):
        self.ctx.speak("uno")
        return "listo"
'''


class NullProvider:
    def find_program(self, name):
        return None

    def open_path(self, target):
        pass

    def open_url(self, url):
        pass

    def media(self, command):
        pass


class Pump:
    """Emula el hilo de la UI."""

    def __init__(self):
        self.jobs = queue.Queue()

    def call(self, fn):
        future = Future()
        self.jobs.put((fn, future))

        return future.result(10)

    def post(self, fn):
        self.jobs.put((fn, None))

    def run_until(self, condition, timeout):
        end = time.monotonic() + timeout

        while not condition() and time.monotonic() < end:
            try:
                fn, future = self.jobs.get(timeout=0.05)
            except queue.Empty:
                continue

            try:
                value = fn()
            except Exception as exc:
                if future:
                    future.set_exception(exc)
                continue

            if future:
                future.set_result(value)


def write_plugin(
    root, plugin_id, code, permissions=("commands",), pattern=r"^di\s+eco\s+(?P<t>.+)$",
    min_version="0.9.0", domains=(),
):
    folder = root / plugin_id
    folder.mkdir(parents=True)
    manifest = {
        "id": plugin_id, "name": plugin_id.title(), "version": "1.0.0",
        "author": "t", "description": "d", "nova_min_version": min_version,
        "dependencies": [], "permissions": list(permissions),
        "network_domains": list(domains),
        "commands": [{"name": "eco", "patterns": [pattern]}],
        "events": [], "examples": ["di eco hola"],
    }
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "plugin.py").write_text(code, encoding="utf-8")


def setup(tmp_path, code, gateway=None, timeout=10.0, **kwargs):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    write_plugin(plugins, "eco", code, **kwargs)
    storage = StorageService(tmp_path / "t.db")
    storage.initialize()
    gateway = gateway or MainThread()
    security = SecurityService(storage.permission_repository)
    automation = AutomationService(security, NullProvider())
    memory = MemoryService(storage.memory_repository)
    manager = PluginManager(
        plugins, storage.plugin_repository, storage.permission_repository,
        lambda m: PluginAPI(
            m, storage.permission_repository, security, automation, memory, gateway
        ),
        NOVA_VERSION, command_timeout=timeout,
    )
    manager.reload()

    return storage, manager


def run(manager, text="di eco hola"):
    job = manager.plan_command(text)

    return manager.finish_job(job, manager.run_job(job))


def test_manifest_validation(tmp_path):
    write_plugin(tmp_path, "eco", ECHO)
    assert load_manifest(tmp_path / "eco", NOVA_VERSION).success

    write_plugin(tmp_path, "mal", ECHO, permissions=("nope",))
    assert not load_manifest(tmp_path / "mal", NOVA_VERSION).success

    write_plugin(tmp_path, "red", ECHO, permissions=("commands", "network"))
    assert not load_manifest(tmp_path / "red", NOVA_VERSION).success

    write_plugin(tmp_path, "ancho", ECHO, pattern=".*")
    assert not load_manifest(tmp_path / "ancho", NOVA_VERSION).success

    write_plugin(tmp_path, "nuevo", ECHO, min_version="9.0.0")
    assert load_manifest(tmp_path / "nuevo", NOVA_VERSION).error.code == (
        "PLUGIN_INCOMPATIBLE"
    )


def test_needs_permissions_runs_and_revocation(tmp_path):
    storage, manager = setup(tmp_path, ECHO)

    try:
        assert manager.missing_permissions("eco") == ["commands"]
        assert not manager.enable("eco").success
        assert manager.plan_command("di eco hola") is None

        manager.grant_all("eco")
        assert manager.enable("eco").success
        assert run(manager) == "eco: hola"

        assert manager.revoke_all("eco") == 1
        assert manager.plan_command("di eco hola") is None
        assert manager.missing_permissions("eco") == ["commands"]
    finally:
        manager.shutdown()
        storage.close()


def test_failing_plugin_is_isolated_then_disabled(tmp_path):
    storage, manager = setup(tmp_path, BOOM)

    try:
        manager.grant_all("eco")
        manager.enable("eco")
        messages = [run(manager) for _ in range(3)]

        assert "falló" in messages[0]
        assert "desactivé" in messages[2]
        assert manager.plan_command("di eco hola") is None
    finally:
        manager.shutdown()
        storage.close()


def test_timeout_stops_plugin(tmp_path):
    storage, manager = setup(tmp_path, SLOW, timeout=1.5)

    try:
        manager.grant_all("eco")
        manager.enable("eco")
        job = manager.plan_command("di eco hola")

        assert manager.run_job(job).error.code == "PLUGIN_TIMEOUT"
    finally:
        manager.shutdown()
        storage.close()


def test_api_enforces_permissions_and_domains(tmp_path):
    storage, manager = setup(tmp_path, NET)

    try:
        manager.grant_all("eco")
        manager.enable("eco")
        assert "network" in run(manager)
    finally:
        manager.shutdown()
        storage.close()

    other = tmp_path / "otro"
    other.mkdir()
    storage, manager = setup(
        other, NET, permissions=("commands", "network"), domains=("example.com",)
    )

    try:
        manager.grant_all("eco")
        manager.enable("eco")
        assert "Dominio no permitido" in run(manager)
    finally:
        manager.shutdown()
        storage.close()


def test_speak_lines_come_before_reply(tmp_path):
    storage, manager = setup(tmp_path, SPEAK, permissions=("commands", "speak"))

    try:
        manager.grant_all("eco")
        manager.enable("eco")
        assert run(manager) == "uno\nlisto"
    finally:
        manager.shutdown()
        storage.close()


def test_handler_flow_and_threaded_dispatch(tmp_path):
    gateway, pump = MainThread(), Pump()
    gateway.bind(pump.call, pump.post)
    storage, manager = setup(tmp_path, ECHO, gateway=gateway)
    handler = PluginCommandHandler(manager, gateway)

    try:
        assert "¿Los concedo" in handler.reply_to("activa el plugin eco")
        assert "No activé" in handler.reply_to("no")
        assert not storage.plugin_repository.is_enabled("eco")

        handler.reply_to("activa el plugin eco")
        assert "activado" in handler.reply_to("sí")

        got = []
        assert handler.dispatch("di eco hola", got.append)
        pump.run_until(lambda: got, 10)
        assert got == ["eco: hola"]

        assert "Eco" in handler.reply_to("qué plugins tengo")
        assert "concedido" in handler.reply_to("qué permisos tiene eco")
        assert "desactivado" in handler.reply_to("desactiva el plugin eco")
        assert handler.reply_to("hola") is None
    finally:
        handler.shutdown()
        storage.close()