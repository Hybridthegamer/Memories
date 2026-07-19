import logging
import os
import subprocess
import tempfile
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from PIL import Image
from sqlalchemy import create_engine, text

from app.config import settings
from app.files import storage_service
from app.queue import get_queue

logger = logging.getLogger("jobs")

# The worker runs outside the FastAPI async event loop, so it uses a plain
# synchronous engine (psycopg2) rather than the app's async engine.
_sync_engine = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        parts = urlsplit(settings.DATABASE_URL)
        # asyncpg wants `ssl=require` in the URL (see app/config.py); psycopg2
        # (libpq) only understands the equivalent `sslmode=require`. Reusing
        # the same DATABASE_URL for both drivers means this has to be
        # translated, not just have its scheme swapped — passing `ssl=` straight
        # through makes psycopg2 raise "invalid dsn: invalid connection option
        # ssl" on every connection attempt.
        query_pairs = [("sslmode" if k == "ssl" else k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)]
        sync_url = urlunsplit(
            ("postgresql+psycopg2", parts.netloc, parts.path, urlencode(query_pairs), parts.fragment)
        )
        _sync_engine = create_engine(sync_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
    return _sync_engine


def enqueue_process_file(file_id: str, storage_key: str, media_type: str) -> None:
    get_queue().enqueue(
        process_uploaded_file,
        file_id,
        storage_key,
        media_type,
        job_timeout=600,
        result_ttl=3600,
    )


def process_uploaded_file(file_id: str, storage_key: str, media_type: str) -> None:
    """RQ job: download the original, generate a thumbnail/poster frame,
    upload it, and mark the file row 'ready' (or 'failed' on error)."""
    client = storage_service.get_s3_client()
    thumb_key = storage_service.build_thumbnail_key(storage_key)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            src_path = os.path.join(tmp, "original")
            thumb_path = os.path.join(tmp, "thumb.jpg")
            client.download_file(settings.S3_BUCKET_NAME, storage_key, src_path)

            if media_type == "image":
                with Image.open(src_path) as img:
                    img.thumbnail((600, 600))
                    img.convert("RGB").save(thumb_path, "JPEG", quality=80)
            else:
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", src_path, "-ss", "00:00:01.000",
                        "-vframes", "1", "-vf", "scale=600:-1", thumb_path,
                    ],
                    check=True, capture_output=True, timeout=300,
                )

            client.upload_file(
                thumb_path, settings.S3_BUCKET_NAME, thumb_key,
                ExtraArgs={"ContentType": "image/jpeg"},
            )

        _update_file_status(file_id, status="ready", thumbnail_key=thumb_key)
    except Exception:
        logger.exception("Failed to process file %s", file_id)
        _update_file_status(file_id, status="failed", thumbnail_key=None)
        raise


def _update_file_status(file_id: str, status: str, thumbnail_key: str | None) -> None:
    engine = _get_sync_engine()
    with engine.begin() as conn:
        if thumbnail_key is not None:
            conn.execute(
                text(
                    "UPDATE files SET status = :status, thumbnail_key = :thumbnail_key, "
                    "updated_at = now() WHERE id = :file_id"
                ),
                {"status": status, "thumbnail_key": thumbnail_key, "file_id": file_id},
            )
        else:
            conn.execute(
                text("UPDATE files SET status = :status, updated_at = now() WHERE id = :file_id"),
                {"status": status, "file_id": file_id},
            )
