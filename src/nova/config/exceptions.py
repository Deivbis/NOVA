class ConfigurationError(Exception):
    """Base exception for NOVA configuration errors."""


class ConfigurationFileNotFoundError(ConfigurationError):
    """Raised when the configuration file does not exist."""


class ConfigurationFormatError(ConfigurationError):
    """Raised when the configuration file has an invalid format."""


class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration values are invalid."""