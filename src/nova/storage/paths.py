import os
from collections.abc import Mapping
from pathlib import Path

DATA_DIR_ENV = "NOVA_DATA_DIR"
DATABASE_FILE_NAME = "nova.db"


def default_data_dir(
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Return the NOVA data directory.

    By default: %APPDATA%/NOVA. For development, the NOVA_DATA_DIR
    environment variable replaces it (for example C:\\NOVA\\data,
    as described in DOC-016).
    """

    env = os.environ if environ is None else environ

    override = env.get(DATA_DIR_ENV, "").strip()

    if override:
        return Path(override)

    app_data = env.get("APPDATA")

    if not app_data:
        raise RuntimeError(
            "APPDATA environment variable is not available."
        )

    return Path(app_data) / "NOVA"


def default_database_path(
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Return the default persistent NOVA database path."""

    return default_data_dir(environ) / DATABASE_FILE_NAME


def default_logs_dir(
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Return the NOVA logs directory."""

    return default_data_dir(environ) / "logs"