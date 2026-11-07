import os
from pathlib import Path


def default_database_path() -> Path:
    """Return the default persistent NOVA database path."""

    app_data = os.environ.get("APPDATA")

    if not app_data:
        raise RuntimeError(
            "APPDATA environment variable is not available."
        )

    return (
        Path(app_data)
        / "NOVA"
        / "nova.db"
    )