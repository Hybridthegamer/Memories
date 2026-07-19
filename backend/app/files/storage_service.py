import re
import uuid

import boto3
from botocore.config import Config

from app.config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            config=Config(
                signature_version="s3v4",
                max_pool_connections=50,
                # A hung B2 connection would otherwise tie up a threadpool
                # worker (and, transitively, whatever request or job is
                # waiting on it) indefinitely under load.
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 2, "mode": "standard"},
            ),
        )
    return _s3_client


def build_storage_key(file_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    # Strip anything not alphanumeric to keep the key safe regardless of client input.
    ext = "".join(c for c in ext if c.isalnum()) or "bin"
    return f"f/{file_id}/original.{ext}"


def build_thumbnail_key(storage_key: str) -> str:
    return storage_key.rsplit("/", 1)[0] + "/thumb.jpg"


def _thumbnail_bucket() -> str:
    # Thumbnails can live in a separate, publicly-readable bucket fronted by
    # a CDN — they're already shown to everyone in the gallery, so making
    # them public isn't a new exposure, and it means the edge can cache them
    # instead of every viewer re-hitting the origin. Falls back to the main
    # (private) bucket if no public bucket is configured.
    return settings.S3_THUMBNAIL_BUCKET_NAME or settings.S3_BUCKET_NAME


def _safe_header_filename(filename: str) -> str:
    # original_name is user-controlled and gets embedded in a quoted
    # Content-Disposition header value. Strip characters that could break
    # out of the quotes or inject CRLF/additional header directives.
    cleaned = re.sub(r'["\r\n]', "", filename).strip()
    return cleaned[:255] or "download"


def generate_presigned_upload_url(storage_key: str, content_type: str) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": storage_key, "ContentType": content_type},
        ExpiresIn=settings.UPLOAD_URL_EXPIRY_SECONDS,
    )


def generate_presigned_download_url(storage_key: str, filename: str | None = None, bucket: str | None = None) -> str:
    client = get_s3_client()
    params = {"Bucket": bucket or settings.S3_BUCKET_NAME, "Key": storage_key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{_safe_header_filename(filename)}"'
    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=settings.DOWNLOAD_URL_EXPIRY_SECONDS,
    )


def build_thumbnail_url(thumbnail_key: str) -> str:
    """Direct CDN URL if a thumbnail CDN is configured, else a presigned URL
    against wherever thumbnails actually live (public bucket or the main one)."""
    if settings.THUMBNAIL_CDN_BASE_URL:
        return f"{settings.THUMBNAIL_CDN_BASE_URL.rstrip('/')}/{thumbnail_key}"
    return generate_presigned_download_url(thumbnail_key, bucket=_thumbnail_bucket())


def upload_thumbnail(local_path: str, thumbnail_key: str) -> None:
    client = get_s3_client()
    client.upload_file(
        local_path,
        _thumbnail_bucket(),
        thumbnail_key,
        ExtraArgs={"ContentType": "image/jpeg", "CacheControl": "public, max-age=31536000, immutable"},
    )


def initiate_multipart_upload(storage_key: str, content_type: str) -> str:
    client = get_s3_client()
    resp = client.create_multipart_upload(Bucket=settings.S3_BUCKET_NAME, Key=storage_key, ContentType=content_type)
    return resp["UploadId"]


def generate_presigned_part_url(storage_key: str, upload_id: str, part_number: int) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        ClientMethod="upload_part",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": storage_key,
            "UploadId": upload_id,
            "PartNumber": part_number,
        },
        ExpiresIn=settings.UPLOAD_URL_EXPIRY_SECONDS,
    )


def complete_multipart_upload(storage_key: str, upload_id: str, parts: list[dict]) -> None:
    client = get_s3_client()
    client.complete_multipart_upload(
        Bucket=settings.S3_BUCKET_NAME,
        Key=storage_key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )


def abort_multipart_upload(storage_key: str, upload_id: str) -> None:
    client = get_s3_client()
    client.abort_multipart_upload(Bucket=settings.S3_BUCKET_NAME, Key=storage_key, UploadId=upload_id)


def delete_object(storage_key: str, bucket: str | None = None) -> None:
    client = get_s3_client()
    client.delete_object(Bucket=bucket or settings.S3_BUCKET_NAME, Key=storage_key)


def head_object_size(storage_key: str) -> int | None:
    """Real size of an already-uploaded object, straight from B2 — used to
    correct/verify a client's declared size_bytes rather than trusting it
    blindly (a client could otherwise under-report size to dodge the quota
    check, then upload something much larger)."""
    client = get_s3_client()
    try:
        resp = client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key)
        return resp["ContentLength"]
    except Exception:
        return None


def new_file_id() -> uuid.UUID:
    return uuid.uuid4()
