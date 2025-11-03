from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    APP_NAME: str = "SmartPDF Shrinker"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me"
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Storage configuration
    STORAGE_BACKEND: Literal["local", "minio"] = "local"
    STORAGE_PATH: Path = Path("/app-data/files")

    # MinIO configuration
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password"
    MINIO_BUCKET: str = "pdf-files"

    # Database
    DATABASE_URL: str = "sqlite:///./data/db.sqlite3"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # Upload constraints
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf",)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    if settings.STORAGE_BACKEND == "local":
        storage_root = Path(settings.STORAGE_PATH)
        storage_root.mkdir(parents=True, exist_ok=True)
        for subdir in ("original", "compressed", "temp"):
            (storage_root / subdir).mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
