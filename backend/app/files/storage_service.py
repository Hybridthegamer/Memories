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
            config=Config(signature_version="s3v4", max_pool_connections=50),
        )
    return _s3_client


def build_storage_key(file_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    # Strip anything not alphanumeric to keep the key safe regardless of client input.
    ext = "".join(c for c in ext if c.isalnum()) or "bin"
    return f"f/{file_id}/original.{ext}"


def build_thumbnail_key(storage_key: str) -> str:
    return storage_key.rsplit("/", 1)[0] + "/thumb.jpg"


def generate_presigned_upload_url(storage_key: str, content_type: str) -> str:
    client = get_s3_client()
    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": storage_key, "ContentType": content_type},
        ExpiresIn=settings.UPLOAD_URL_EXPIRY_SECONDS,
    )


def generate_presigned_download_url(storage_key: str, filename: str | None = None) -> str:
    client = get_s3_client()
    params = {"Bucket": settings.S3_BUCKET_NAME, "Key": storage_key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=settings.DOWNLOAD_URL_EXPIRY_SECONDS,
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


def delete_object(storage_key: str) -> None:
    client = get_s3_client()
    client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key)


def new_file_id() -> uuid.UUID:
    return uuid.uuid4()
