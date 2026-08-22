class NovaError(Exception):
    """Base exception for NOVA."""


class NovaConfigurationError(NovaError):
    """Raised when NOVA configuration is invalid."""


class NovaServiceError(NovaError):
    """Raised when a NOVA service fails."""


class NovaCommandError(NovaError):
    """Raised when a command cannot be processed."""


class NovaSecurityError(NovaError):
    """Raised when a security policy blocks an operation."""


class NovaOfflineError(NovaError):
    """Raised when an operation requires internet access."""