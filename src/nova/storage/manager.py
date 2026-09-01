from pathlib import Path

from nova.storage.connection import DatabaseConnection
from nova.storage.database import Database
from nova.storage.migrations.runner import MigrationRunner
from nova.storage.migrations.versions import v001_initial


class StorageManager:
    """Coordinates NOVA storage initialization and shutdown."""

    def __init__(self, database_path: Path) -> None:
        self.database_connection = DatabaseConnection(database_path)
        self.database = Database(self.database_connection)

        self._initialized = False

    def initialize(self) -> None:
        connection = self.database.initialize()

        migration_runner = MigrationRunner(connection)

        current_version = migration_runner.current_version()

        if current_version < v001_initial.VERSION:
            v001_initial.apply(connection)
            migration_runner.set_version(v001_initial.VERSION)

        if not self.database.health_check():
            raise RuntimeError("NOVA database integrity check failed.")

        self._initialized = True

    @property
    def connection(self):
        return self.database_connection.connection

    @property
    def initialized(self) -> bool:
        return self._initialized

    def close(self) -> None:
        self.database.close()
        self._initialized = False