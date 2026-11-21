import tomllib
from pathlib import Path

from nova.plugins import NOVA_VERSION

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> dict:
    return tomllib.loads((ROOT / name).read_text(encoding="utf-8"))


def test_versions_match():
    config = _read("config/default.toml")["nova"]["version"]
    project = _read("pyproject.toml")["project"]["version"]

    assert config == project == NOVA_VERSION