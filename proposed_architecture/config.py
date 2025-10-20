"""Application configuration

Centralized configuration for database paths and other settings.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """
        Load database configuration from environment variables.

        Environment variables:
            DATABASE_PATH: Path to SQLite database file (default: data/evaluation.db)

        Returns:
            DatabaseConfig instance
        """
        db_path = os.getenv('DATABASE_PATH', 'data/evaluation.db')
        return cls(path=db_path)

    @classmethod
    def for_testing(cls) -> 'DatabaseConfig':
        """
        Configuration for tests.

        Uses in-memory SQLite database (fast, isolated, no cleanup needed).
        """
        return cls(path=':memory:')

    @classmethod
    def for_development(cls) -> 'DatabaseConfig':
        """Configuration for development"""
        return cls(path='data/evaluation_dev.db')

    @classmethod
    def for_production(cls) -> 'DatabaseConfig':
        """Configuration for production"""
        return cls(path='data/evaluation.db')


@dataclass
class AppConfig:
    """
    Application-wide configuration.

    Single source of truth for all application settings.
    """
    database: DatabaseConfig
    environment: str
    debug: bool = False

    @classmethod
    def load(cls, env: Optional[str] = None) -> 'AppConfig':
        """
        Load configuration based on environment.

        Args:
            env: Environment name ('development', 'testing', 'production')
                 If None, reads from ENV environment variable

        Returns:
            AppConfig instance

        Example:
            # Load from environment variable
            config = AppConfig.load()

            # Explicit environment
            config = AppConfig.load('testing')
        """
        if env is None:
            env = os.getenv('ENV', 'development')

        # Load database config based on environment
        if env == 'production':
            db_config = DatabaseConfig.for_production()
            debug = False
        elif env == 'testing':
            db_config = DatabaseConfig.for_testing()
            debug = True
        else:  # development
            db_config = DatabaseConfig.for_development()
            debug = True

        return cls(
            database=db_config,
            environment=env,
            debug=debug
        )

    def get_db_path(self) -> str:
        """Convenience method to get database path"""
        return self.database.path


# Global config instance (initialized on first import)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get application configuration (singleton).

    Loads configuration on first call, returns cached instance afterward.

    Returns:
        AppConfig instance

    Example:
        from config import get_config

        config = get_config()
        db_path = config.get_db_path()
    """
    global _config
    if _config is None:
        _config = AppConfig.load()
    return _config


def set_config(config: AppConfig):
    """
    Set application configuration (useful for testing).

    Args:
        config: AppConfig instance

    Example:
        # In tests
        test_config = AppConfig.load('testing')
        set_config(test_config)
    """
    global _config
    _config = config


def reset_config():
    """
    Reset configuration (useful for testing).

    Forces configuration to be reloaded on next get_config() call.
    """
    global _config
    _config = None
