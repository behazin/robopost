"""Configuration for the API gateway service.
A lightweight ``dataclass`` based configuration is used instead of
Pydantic's ``BaseSettings`` to avoid an extra dependency during the
kata.  Environment variables can still override the defaults.
"""
from dataclasses import dataclass
import os
data_dir = os.path.dirname(__file__)


@dataclass
class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8000"))


settings = Settings()