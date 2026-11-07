from pathlib import Path

from nova.storage.paths import default_database_path


def test_default_database_path(monkeypatch):
    monkeypatch.setenv(
        "APPDATA",
        r"C:\Users\Test\AppData\Roaming",
    )

    path = default_database_path()

    assert path == Path(
        r"C:\Users\Test\AppData\Roaming"
        r"\NOVA\nova.db"
    )