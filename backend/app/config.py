from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = "changeme-generate-a-real-random-secret"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/storage_platform"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT_URL: str = "https://s3.us-west-002.backblazeb2.com"
    S3_REGION: str = "us-west-002"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""

    UPLOAD_URL_EXPIRY_SECONDS: int = 900
    DOWNLOAD_URL_EXPIRY_SECONDS: int = 3600
    MULTIPART_PART_SIZE_BYTES: int = 10 * 1024 * 1024
    SINGLE_UPLOAD_THRESHOLD_BYTES: int = 50 * 1024 * 1024

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # Rate limiting (Phase 3 hardening) — requests per window, per user, for upload endpoints.
    UPLOAD_RATE_LIMIT_COUNT: int = 30
    UPLOAD_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Per-user forever-storage quota, in bytes. Default 50GB.
    USER_STORAGE_QUOTA_BYTES: int = 50 * 1024 * 1024 * 1024

    # DB connection pool sizing — tuned so a single backend instance can
    # comfortably serve dozens of concurrent requests without exhausting
    # the Postgres connection limit on free-tier hosts.
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
