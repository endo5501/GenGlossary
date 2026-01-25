"""Dependency injection for API."""

from genglossary.config import Config


def get_config() -> Config:
    """Get application configuration.

    Returns:
        Config: Application configuration instance
    """
    return Config()


def get_db_connection():
    """Get database connection (placeholder).

    This will be implemented in a future ticket when
    database integration is added.

    Returns:
        None: Placeholder for database connection
    """
    # TODO: Implement database connection
    return None
