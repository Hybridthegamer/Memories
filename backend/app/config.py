from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/storage_platform"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT_URL: str = "https://s3.us-west-002.backblazeb2.com"
    S3_REGION: str = "us-west-002"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""

    # Optional: a separate, publicly-readable B2 bucket for thumbnails only,
    # fronted by a CDN (e.g. Cloudflare). If unset, thumbnails fall back to
    # living in the main bucket behind presigned URLs. Originals always stay
    # in S3_BUCKET_NAME regardless.
    S3_THUMBNAIL_BUCKET_NAME: str = ""
    # Public CDN base URL that proxies/caches the thumbnail bucket, e.g.
    # "https://cdn.example.com". When set, thumbnail URLs point directly at
    # the CDN instead of generating a presigned URL per request.
    THUMBNAIL_CDN_BASE_URL: str = ""

    UPLOAD_URL_EXPIRY_SECONDS: int = 900
    DOWNLOAD_URL_EXPIRY_SECONDS: int = 3600
    MULTIPART_PART_SIZE_BYTES: int = 10 * 1024 * 1024
    SINGLE_UPLOAD_THRESHOLD_BYTES: int = 50 * 1024 * 1024

    # Kept as a plain string (not list[str]) because pydantic-settings tries to
    # JSON-decode any env var mapped to a list-typed field before validators
    # run — that breaks on a plain comma-separated value. Parse it ourselves
    # via the property below instead.
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Rate limiting — requests per window, per IP, for upload endpoints. This is
    # the main abuse guard now that uploads are fully anonymous/unauthenticated.
    UPLOAD_RATE_LIMIT_COUNT: int = 30
    UPLOAD_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Read-path rate limits are looser than upload since browsing/downloading
    # is the platform's core normal usage, but still bounded so a single IP
    # can't hammer the DB/B2 with an unbounded request flood.
    READ_RATE_LIMIT_COUNT: int = 300
    READ_RATE_LIMIT_WINDOW_SECONDS: int = 60
    DOWNLOAD_RATE_LIMIT_COUNT: int = 120
    DOWNLOAD_RATE_LIMIT_WINDOW_SECONDS: int = 60
    DELETE_RATE_LIMIT_COUNT: int = 30
    DELETE_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Hard cap on request body size, enforced before FastAPI/Pydantic even
    # parses the body. Sized to comfortably cover a multipart-complete
    # payload listing thousands of parts, while still bounding how much
    # memory/bandwidth a single malicious request can consume.
    MAX_REQUEST_BODY_BYTES: int = 2 * 1024 * 1024

    # Global forever-storage quota across all uploads from everyone, in bytes.
    # Default 1TB, matching the platform's budget target.
    GLOBAL_STORAGE_QUOTA_BYTES: int = 1024 * 1024 * 1024 * 1024

    # A "pending" file (upload URL issued, nothing uploaded yet) still counts
    # toward the quota so a client can't slip past the check and then upload
    # something bigger. But without a cutoff, spamming upload-requests that
    # are never followed through would let anyone exhaust the whole quota
    # with phantom reservations. Rows still pending past this many seconds
    # are treated as abandoned and swept out of the quota accounting. Kept
    # generous (well beyond a single presigned URL's expiry) so a legitimate
    # slow multipart upload of a large file isn't mistaken for abandonment.
    PENDING_UPLOAD_STALE_SECONDS: int = 6 * 60 * 60

    # Anyone can delete their own upload within this many days; after that,
    # it's permanent for everyone, no exceptions.
    DELETE_WINDOW_DAYS: int = 3

    # DB connection pool sizing — tuned so a single backend instance can
    # comfortably serve dozens of concurrent requests without exhausting
    # the Postgres connection limit on free-tier hosts.
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
