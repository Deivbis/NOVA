
from pathlib import Path
from nova.storage.transaction import Transaction
from nova.storage.connection import DatabaseConnection
from nova.storage.database import Database
from nova.storage.exceptions import MigrationError
from nova.storage.migrations.runner import MigrationRunner
from nova.storage.migrations.versions import (
    v001_initial,
    v002_conversations,
    v003_memories,
)
from nova.storage.migrations.versions import (
     v001_initial,
     v002_conversations,
     v003_memories,
     v004_learning,
     v005_permissions,
     v006_tasks,
     v007_plugins,
 )

class StorageManager:
    """Coordinates NOVA storage initialization and shutdown."""

    MIGRATIONS = (
        v001_initial,
        v002_conversations,
        v003_memories,
        v004_learning,
        v005_permissions,
        v006_tasks,
        v007_plugins,
    )

    def __init__(self, database_path: Path) -> None:
        self.database_connection = DatabaseConnection(database_path)
        self.database = Database(self.database_connection)
        self._initialized = False

    def initialize(self) -> None:
        connection = self.database.initialize()
        migration_runner = MigrationRunner(connection)

        try:
            current_version = migration_runner.current_version()

            for migration in self.MIGRATIONS:
                if migration.VERSION <= current_version:
                    continue

                expected_version = current_version + 1

                if migration.VERSION != expected_version:
                    raise MigrationError(
                        f"Missing migration version "
                        f"{expected_version}."
                    )

                with Transaction(connection):
                    migration.apply(connection)
                    migration_runner.set_version(migration.VERSION)

                current_version = migration.VERSION

            if not self.database.health_check():
                raise MigrationError(
                    "NOVA database integrity check failed."
                )

            self._initialized = True

        except Exception:
            self.database.close()
            self._initialized = False
            raise

    @property
    def connection(self):
        return self.database_connection.connection

    @property
    def initialized(self) -> bool:
        return self._initialized

    def close(self) -> None:
        self.database.close()
        self._initialized = False