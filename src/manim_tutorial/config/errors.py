class ManimTutorialConfigError(ValueError):
    """Raised when tutorial configuration is unavailable or invalid."""


class ConfigurationValidationError(ManimTutorialConfigError):
    """Raised when a TOML file does not match the exact public schema."""
