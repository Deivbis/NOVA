class StorageError(Exception):
    """Base exception for NOVA storage errors."""


class DatabaseConnectionError(StorageError):
    """Raised when the database cannot be opened or configured."""


class DatabaseIntegrityError(StorageError):
    """Raised when database integrity validation fails."""


class TransactionError(StorageError):
    """Raised when a transaction operation fails."""


class MigrationError(StorageError):
    """Raised when a migration cannot be executed."""


class BackupError(StorageError):
    """Raised when a backup operation fails."""


class CacheError(StorageError):
    """Raised when a cache operation fails."""


class RepositoryError(StorageError):
    """Raised when a repository operation fails."""