import sqlite3
from datetime import datetime
from pathlib import Path

from nova.storage.exceptions import BackupError


class BackupManager:
    """Creates and restores SQLite backups."""

    def __init__(
        self,
        database_path: Path,
        backup_directory: Path,
    ) -> None:
        self.database_path = database_path
        self.backup_directory = backup_directory

    def create_backup(self) -> Path:
        if not self.database_path.exists():
            raise BackupError(
                f"Database does not exist: {self.database_path}"
            )

        self.backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_path = (
            self.backup_directory
            / f"nova_{timestamp}.db"
        )

        source = None
        destination = None

        try:
            source = sqlite3.connect(self.database_path)
            destination = sqlite3.connect(backup_path)

            with destination:
                source.backup(destination)

            return backup_path

        except sqlite3.Error as exc:
            if backup_path.exists():
                backup_path.unlink()

            raise BackupError(
                f"Unable to create backup: {backup_path}"
            ) from exc

        finally:
            if source is not None:
                source.close()

            if destination is not None:
                destination.close()