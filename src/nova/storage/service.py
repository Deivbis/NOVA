from pathlib import Path

from nova.storage.manager import StorageManager
from nova.storage.repositories.conversation_repository import (
    ConversationRepository,
)
from nova.storage.repositories.system_repository import SystemRepository
from nova.storage.repositories.memory_repository import MemoryRepository
from nova.storage.repositories.learning_repository import LearningRepository


class StorageService:
    """Public service interface for NOVA storage."""

    def __init__(self, database_path: Path) -> None:
        self.manager = StorageManager(database_path)

        self.system_repository: SystemRepository | None = None
        self.memory_repository: MemoryRepository | None = None
        self.learning_repository: LearningRepository | None = None
        self.conversation_repository: ConversationRepository | None = None

    def initialize(self) -> None:
        self.manager.initialize()

        self.system_repository = SystemRepository(
            self.manager.connection
        )
        self.conversation_repository = ConversationRepository(
            self.manager.connection
        )
        self.memory_repository = MemoryRepository(
            self.manager.connection
        )
        self.learning_repository = LearningRepository(
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
        self.conversation_repository = None
        self.memory_repository = None
        self.learning_repository = None