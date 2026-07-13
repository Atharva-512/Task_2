"""
Application configuration.

Loads settings from environment variables (via a local .env file in
development, or the host's environment / secrets manager in production).
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load variables from a .env file into the process environment, if present.
# In production, real environment variables set by the host take precedence
# and this call is a no-op if no .env file exists.
load_dotenv()


class Settings:
    """Strongly-typed access to application configuration."""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.database_path: str = os.getenv("DATABASE_PATH", "")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using lru_cache ensures the environment is parsed once and the same
    Settings object is reused across the app (and easily overridden in tests
    via dependency overrides).
    """
    return Settings()
