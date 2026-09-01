from pathlib import Path


class BackupRotation:
    """Maintains the maximum number of NOVA backups."""

    def __init__(
        self,
        backup_directory: Path,
        maximum_backups: int = 5,
    ) -> None:
        self.backup_directory = backup_directory
        self.maximum_backups = maximum_backups

    def rotate(self) -> None:
        backups = sorted(
            self.backup_directory.glob("nova_*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        for backup in backups[self.maximum_backups:]:
            backup.unlink()