"""Un plugin = un subproceso (DOC-021: un fallo no tumba NOVA)."""

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import nova
from nova.core.logging_setup import get_logger
from nova.core.result import Result
from nova.plugins.api import PluginAPI
from nova.plugins.manifest import PluginManifest

logger = get_logger(__name__)

READY_TIMEOUT_S = 5.0
_ENV_KEYS = (
    "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC",
    "TEMP", "TMP", "USERPROFILE", "LANG", "LC_ALL",
)


def _clean_env() -> dict[str, str]:
    """Entorno mínimo: el plugin no hereda variables ni credenciales."""
    env = {k: os.environ[k] for k in _ENV_KEYS if k in os.environ}
    env["PYTHONPATH"] = str(Path(nova.__file__).resolve().parent.parent)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    return env


def _reader(proc: subprocess.Popen, out: queue.Queue) -> None:
    try:
        for line in proc.stdout:
            out.put(line)
    except (OSError, ValueError):
        pass
    finally:
        out.put(None)


class PluginProcess:
    def __init__(self, manifest: PluginManifest, api: PluginAPI) -> None:
        self._manifest = manifest
        self._api = api
        self._proc: subprocess.Popen | None = None
        self._queue: queue.Queue = queue.Queue()
        self._ready = False
        self._next = 0
        self._lock = threading.Lock()

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self) -> None:
        self._queue = queue.Queue()
        self._ready = False
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "nova.plugin_sdk.runner",
             str(self._manifest.path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=str(self._manifest.path),
            env=_clean_env(),
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        threading.Thread(
            target=_reader, args=(self._proc, self._queue), daemon=True
        ).start()

    def stop(self) -> None:
        proc, self._proc = self._proc, None

        if proc is None:
            return

        try:
            proc.stdin.write('{"type": "stop"}\n')
            proc.stdin.flush()
        except (OSError, ValueError):
            pass

        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    def call(self, request: dict, timeout: float) -> Result[str]:
        with self._lock:
            if not self.alive:
                return Result.fail(
                    "PLUGIN_NOT_RUNNING", "El plugin no está en ejecución."
                )

            try:
                if not self._ready:
                    message = self._next_message(
                        time.monotonic() + READY_TIMEOUT_S
                    )

                    if message is None:
                        self.stop()
                        return Result.fail(
                            "PLUGIN_CRASHED", "El plugin se cerró al iniciar."
                        )

                    if message.get("type") != "ready":
                        self.stop()
                        return Result.fail(
                            "PLUGIN_LOAD_ERROR", "No pude cargar el plugin."
                        )

                    self._ready = True

                self._next += 1
                request_id = self._next
                self._send({**request, "id": request_id})
                lines: list[str] = []
                deadline = time.monotonic() + timeout

                while True:
                    message = self._next_message(deadline)

                    if message is None:
                        self.stop()
                        return Result.fail(
                            "PLUGIN_CRASHED", "El plugin se cerró."
                        )

                    kind = message.get("type")

                    if kind == "call":
                        outcome = self._api.dispatch(
                            str(message.get("method", "")),
                            message.get("params", {}),
                            lines,
                        )
                        self._send({
                            "type": "result", "id": message.get("id"), **outcome
                        })
                    elif kind == "reply" and message.get("id") == request_id:
                        text = str(message.get("text", ""))

                        return Result.ok("\n".join([*lines, text] if text else lines))
                    elif kind == "error" and message.get("id") == request_id:
                        return Result.fail(
                            "PLUGIN_ERROR",
                            f"lanzó {str(message.get('error', ''))[:60]}",
                        )
            except TimeoutError:
                self.stop()
                return Result.fail(
                    "PLUGIN_TIMEOUT",
                    "tardó demasiado y lo detuve",
                )
            except (OSError, ValueError):
                self.stop()
                return Result.fail("PLUGIN_CRASHED", "El plugin se cerró.")

    def _next_message(self, deadline: float) -> dict | None:
        while True:
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                raise TimeoutError

            try:
                raw = self._queue.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError from None

            if raw is None:
                return None

            try:
                message = json.loads(raw)
            except ValueError:
                continue

            if isinstance(message, dict):
                return message

    def _send(self, message: dict) -> None:
        proc = self._proc

        if proc is None:
            raise OSError("Plugin detenido.")

        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()