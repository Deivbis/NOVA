from pathlib import Path

from nova.storage.manager import StorageManager
from nova.storage.repositories.system_repository import SystemRepository


class StorageService:
    """Public service interface for NOVA storage."""

    def __init__(self, database_path: Path) -> None:
        self.manager = StorageManager(database_path)

        self.system_repository: SystemRepository | None = None

    def initialize(self) -> None:
        self.manager.initialize()

        self.system_repository = SystemRepository(
            self.manager.connection
        )

    def set_system_value(self, key: str, value: str) -> None:
        if self.system_repository is None:
            raise RuntimeError("StorageService is not initialized.")

        self.system_repository.set_value(key, value)

    def get_system_value(self, key: str) -> str | None:
        if self.system_repository is None:
            raise RuntimeError("StorageService is not initialized.")

        return self.system_repository.get_value(key)

    def close(self) -> None:
        self.manager.close()
        self.system_repository = None