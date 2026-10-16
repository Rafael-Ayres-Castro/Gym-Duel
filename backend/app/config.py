"""Application settings, read from environment variables (and `.env` in development)."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Literal
from pathlib import Path

from fastapi import Request
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TIMEZONE = "America/Sao_Paulo"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    database_url: str = f"sqlite:///{PROJECT_ROOT / 'gymduel.db'}"
    jwt_secret: str
    jwt_expire_days: int = 30
    max_users: int = 2
    max_workouts_per_day: int = 1
    # Proof photos: "local" (disk, development) or "s3" (any S3-compatible private bucket).
    photo_storage: Literal["local", "s3"] = "local"
    photo_dir: str = ""  # local only; default: data/photos in the project
    photo_url_ttl_seconds: int = 600  # signed read URLs expire after 10 minutes
    s3_bucket: str = ""
    s3_endpoint_url: str = ""  # e.g. Cloudflare R2 or Supabase Storage endpoint
    s3_region: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    # Run Alembic migrations on start up. Tests turn it off and create tables directly (faster).
    auto_migrate: bool = True
    # Development only: pretend "today" is this date (YYYY-MM-DD). Never set it in production.
    app_today: date | None = None

    @field_validator("jwt_secret")
    @classmethod
    def strong_secret(cls, secret: str) -> str:
        if len(secret) < 32:
            raise ValueError("JWT_SECRET precisa ter pelo menos 32 caracteres (gere com: openssl rand -hex 32)")
        return secret

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        # Render/Railway hand out postgres:// URLs; SQLAlchemy needs the driver spelled out.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    @field_validator("app_today", mode="before")
    @classmethod
    def empty_today_is_none(cls, value: object) -> object:
        return value or None


@lru_cache
def get_settings() -> Settings:
    """Settings loaded from the environment, used when the real app is built."""
    return Settings()


def app_settings(request: Request) -> Settings:
    """Dependency: the settings of the running app (tests build apps with their own)."""
    return request.app.state.settings
