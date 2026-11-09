from pathlib import Path

import pytest

from nova.storage.paths import (
    DATA_DIR_ENV,
    default_data_dir,
    default_database_path,
    default_logs_dir,
)

APPDATA = r"C:\Users\Test\AppData\Roaming"


def test_default_database_path(monkeypatch):
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    monkeypatch.setenv("APPDATA", APPDATA)

    path = default_database_path()

    assert path == Path(APPDATA) / "NOVA" / "nova.db"


def test_data_dir_defaults_to_appdata_nova():
    assert default_data_dir({"APPDATA": APPDATA}) == Path(APPDATA) / "NOVA"


def test_data_dir_can_be_overridden_for_development():
    environ = {"APPDATA": APPDATA, DATA_DIR_ENV: r"C:\NOVA\data"}

    assert default_data_dir(environ) == Path(r"C:\NOVA\data")
    assert default_database_path(environ) == (
        Path(r"C:\NOVA\data") / "nova.db"
    )


def test_blank_override_is_ignored():
    environ = {"APPDATA": APPDATA, DATA_DIR_ENV: "   "}

    assert default_data_dir(environ) == Path(APPDATA) / "NOVA"


def test_logs_dir_lives_inside_data_dir():
    assert default_logs_dir({"APPDATA": APPDATA}) == (
        Path(APPDATA) / "NOVA" / "logs"
    )


def test_missing_appdata_without_override_raises():
    with pytest.raises(RuntimeError):
        default_data_dir({})