import sys
from pathlib import Path

PLUGIN_RUNNER_FLAG = "--plugin-runner"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) or "__compiled__" in globals()


def app_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def plugins_dir() -> Path:
    return app_root() / "plugins"


def plugin_runner_command(folder: Path) -> list[str]:
    if is_frozen():
        return [sys.executable, PLUGIN_RUNNER_FLAG, str(folder)]

    return [sys.executable, "-m", "nova.plugin_sdk.runner", str(folder)]