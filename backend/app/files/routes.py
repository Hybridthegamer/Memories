import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.database import get_db
from app.files import storage_service
from app.files.jobs import enqueue_process_file
from app.models import File
from app.rate_limit import rate_limit_by_ip
from app.schemas import (
    ConfirmOut,
    DownloadUrlOut,
    FileListOut,
    FileOut,
    FolderListOut,
    FolderOut,
    MultipartCompleteIn,
    MultipartInitiateOut,
    PartUrlIn,
    PartUrlOut,
    UploadRequestIn,
    UploadRequestOut,
)

router = APIRouter()

_upload_rate_limit = rate_limit_by_ip(
    "upload", count=settings.UPLOAD_RATE_LIMIT_COUNT, window_seconds=settings.UPLOAD_RATE_LIMIT_WINDOW_SECONDS
)
_part_url_rate_limit = rate_limit_by_ip("upload-part", count=600, window_seconds=60)
_read_rate_limit = rate_limit_by_ip(
    "read", count=settings.READ_RATE_LIMIT_COUNT, window_seconds=settings.READ_RATE_LIMIT_WINDOW_SECONDS
)
_download_rate_limit = rate_limit_by_ip(
    "download", count=settings.DOWNLOAD_RATE_LIMIT_COUNT, window_seconds=settings.DOWNLOAD_RATE_LIMIT_WINDOW_SECONDS
)
_delete_rate_limit = rate_limit_by_ip(
    "delete", count=settings.DELETE_RATE_LIMIT_COUNT, window_seconds=settings.DELETE_RATE_LIMIT_WINDOW_SECONDS
)

# Arbitrary constant identifying the global-quota mutex to Postgres advisory
# locks. It has no meaning beyond being a stable, shared identity that every
# concurrent request serializes on for the duration of its transaction.
_QUOTA_LOCK_KEY = 875321


def _media_type_from_content_type(content_type: str) -> str:
    return "image" if content_type.startswith("image/") else "video"


def _new_delete_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hex_hash). Only the hash is ever persisted."""
    raw = secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, digest


def _delete_deadline(created_at: datetime) -> datetime:
    return created_at + timedelta(days=settings.DELETE_WINDOW_DAYS)


async def _get_file_or_404(db: AsyncSession, file_id: uuid.UUID) -> File:
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file


async def _get_file_for_update_or_404(db: AsyncSession, file_id: uuid.UUID) -> File:
    """Same as _get_file_or_404, but locks the row (SELECT ... FOR UPDATE)
    for the rest of the transaction. Without this, two concurrent deletes
    for the same file both pass the token/deadline check against the same
    still-present row before either commits, and both report success even
    though only one delete is real — a locked read makes the second
    request block until the first commits, then see the row already gone.
    """
    result = await db.execute(select(File).where(File.id == file_id).with_for_update())
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file


async def _check_global_quota(db: AsyncSession, incoming_bytes: int) -> None:
    # Without this lock, two requests can both read the same used_bytes,
    # both see room for their own upload, and both commit — overshooting the
    # quota (classic check-then-act race). The lock is transaction-scoped
    # and releases automatically at commit/rollback, so it only serializes
    # the check+reserve, not the whole request.
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _QUOTA_LOCK_KEY})

    stale_cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.PENDING_UPLOAD_STALE_SECONDS)
    # Rows stuck in "pending" past the abandonment cutoff were never
    # followed through — sweep them so they stop occupying quota forever.
    # Otherwise spamming upload-requests without uploading anything would
    # let anyone exhaust the whole platform quota for free.
    await db.execute(delete(File).where(File.status == "pending", File.created_at < stale_cutoff))

    result = await db.execute(select(func.coalesce(func.sum(File.size_bytes), 0)).where(File.status != "failed"))
    used_bytes = result.scalar_one()
    if used_bytes + incoming_bytes > settings.GLOBAL_STORAGE_QUOTA_BYTES:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="The platform's storage is full. Please try again later.",
        )


def _to_file_out(f: File, thumbnail_url: str | None) -> FileOut:
    return FileOut(
        id=f.id,
        original_name=f.original_name,
        media_type=f.media_type,
        size_bytes=f.size_bytes,
        status=f.status,
        thumbnail_url=thumbnail_url,
        created_at=f.created_at,
        delete_deadline=_delete_deadline(f.created_at),
        folder=f.folder,
    )


# ---- Single upload ----

@router.post("/upload-request", response_model=UploadRequestOut)
async def upload_request(
    payload: UploadRequestIn,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_upload_rate_limit),
):
    await _check_global_quota(db, payload.size_bytes)

    if payload.size_bytes > settings.SINGLE_UPLOAD_THRESHOLD_BYTES:
        return UploadRequestOut(upload_method="multipart")

    file_id = storage_service.new_file_id()
    storage_key = storage_service.build_storage_key(str(file_id), payload.filename)
    media_type = _media_type_from_content_type(payload.content_type)
    raw_token, token_hash = _new_delete_token()

    file = File(
        id=file_id,
        storage_key=storage_key,
        original_name=payload.filename,
        mime_type=payload.content_type,
        size_bytes=payload.size_bytes,
        media_type=media_type,
        status="pending",
        delete_token_hash=token_hash,
        folder=payload.folder,
    )
    db.add(file)
    await db.commit()

    upload_url = storage_service.generate_presigned_upload_url(storage_key, payload.content_type)
    return UploadRequestOut(
        file_id=file_id,
        upload_method="single",
        upload_url=upload_url,
        expires_in=settings.UPLOAD_URL_EXPIRY_SECONDS,
        delete_token=raw_token,
    )


@router.post("/{file_id}/confirm", response_model=ConfirmOut)
async def confirm_upload(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    file = await _get_file_or_404(db, file_id)
    if file.status not in ("pending", "processing"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"File is already {file.status}")

    # The client's declared size_bytes was only ever a claim used for the
    # pre-upload quota check — verify it against what actually landed in B2
    # before it's trusted for real quota accounting, otherwise a client
    # could under-report size to dodge the check and then upload far more.
    real_size = await run_in_threadpool(storage_service.head_object_size, file.storage_key)
    if real_size is not None:
        file.size_bytes = real_size

    file.status = "processing"
    await db.commit()

    enqueue_process_file(str(file.id), file.storage_key, file.media_type)
    return ConfirmOut(file_id=file.id, status=file.status)


# ---- Multipart upload ----

@router.post("/upload-request/multipart/initiate", response_model=MultipartInitiateOut)
async def multipart_initiate(
    payload: UploadRequestIn,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_upload_rate_limit),
):
    await _check_global_quota(db, payload.size_bytes)

    file_id = storage_service.new_file_id()
    storage_key = storage_service.build_storage_key(str(file_id), payload.filename)
    media_type = _media_type_from_content_type(payload.content_type)
    raw_token, token_hash = _new_delete_token()

    upload_id = await run_in_threadpool(
        storage_service.initiate_multipart_upload, storage_key, payload.content_type
    )

    file = File(
        id=file_id,
        storage_key=storage_key,
        original_name=payload.filename,
        mime_type=payload.content_type,
        size_bytes=payload.size_bytes,
        media_type=media_type,
        status="pending",
        upload_id=upload_id,
        delete_token_hash=token_hash,
        folder=payload.folder,
    )
    db.add(file)
    await db.commit()

    return MultipartInitiateOut(
        file_id=file_id,
        upload_id=upload_id,
        part_size_bytes=settings.MULTIPART_PART_SIZE_BYTES,
        delete_token=raw_token,
    )


@router.post("/{file_id}/multipart/part-url", response_model=PartUrlOut)
async def multipart_part_url(
    file_id: uuid.UUID,
    payload: PartUrlIn,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_part_url_rate_limit),
):
    file = await _get_file_or_404(db, file_id)
    if not file.upload_id or file.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not awaiting multipart upload")

    url = storage_service.generate_presigned_part_url(file.storage_key, file.upload_id, payload.part_number)
    return PartUrlOut(url=url)


@router.post("/{file_id}/multipart/complete", response_model=ConfirmOut)
async def multipart_complete(
    file_id: uuid.UUID,
    payload: MultipartCompleteIn,
    db: AsyncSession = Depends(get_db),
):
    file = await _get_file_or_404(db, file_id)
    if not file.upload_id or file.status not in ("pending", "processing"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not awaiting multipart upload")

    parts = [{"PartNumber": p.part_number, "ETag": p.etag} for p in payload.parts]
    try:
        await run_in_threadpool(
            storage_service.complete_multipart_upload, file.storage_key, file.upload_id, parts
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to complete upload") from exc

    real_size = await run_in_threadpool(storage_service.head_object_size, file.storage_key)
    if real_size is not None:
        file.size_bytes = real_size

    file.status = "processing"
    await db.commit()

    enqueue_process_file(str(file.id), file.storage_key, file.media_type)
    return ConfirmOut(file_id=file.id, status=file.status)


@router.post("/{file_id}/multipart/abort", status_code=status.HTTP_204_NO_CONTENT)
async def multipart_abort(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    file = await _get_file_or_404(db, file_id)
    if file.upload_id:
        try:
            await run_in_threadpool(storage_service.abort_multipart_upload, file.storage_key, file.upload_id)
        except Exception:
            pass  # best-effort cleanup; the file row is still marked failed below

    file.status = "failed"
    await db.commit()


# ---- Retrieval ----

@router.get("/folders", response_model=FolderListOut)
async def list_folders(db: AsyncSession = Depends(get_db), _rl: None = Depends(_read_rate_limit)):
    result = await db.execute(
        select(File.folder, func.count(File.id))
        .where(File.folder.is_not(None), File.status != "pending", File.status != "failed")
        .group_by(File.folder)
        .order_by(func.count(File.id).desc())
    )
    return FolderListOut(folders=[FolderOut(name=name, file_count=count) for name, count in result.all()])


@router.get("", response_model=FileListOut)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    media_type: str | None = Query(None, pattern="^(image|video)$"),
    folder: str | None = Query(None, max_length=60),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_read_rate_limit),
):
    # Global gallery: every ready/processing file from every uploader, newest first.
    filters = [File.status != "pending", File.status != "failed"]
    if media_type:
        filters.append(File.media_type == media_type)
    if folder:
        filters.append(File.folder == folder)

    count_result = await db.execute(select(func.count(File.id)).where(*filters))
    total = count_result.scalar_one()

    result = await db.execute(
        select(File)
        .where(*filters)
        .order_by(File.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    files = result.scalars().all()

    items = []
    for f in files:
        thumbnail_url = None
        if f.thumbnail_key and f.status == "ready":
            thumbnail_url = storage_service.build_thumbnail_url(f.thumbnail_key)
        items.append(_to_file_out(f, thumbnail_url))

    return FileListOut(items=items, page=page, page_size=page_size, total=total)


@router.get("/{file_id}/download-url", response_model=DownloadUrlOut)
async def get_download_url(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_download_rate_limit),
):
    file = await _get_file_or_404(db, file_id)
    if file.status not in ("uploaded", "processing", "ready"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not available for download yet")

    url = storage_service.generate_presigned_download_url(file.storage_key, filename=file.original_name)
    return DownloadUrlOut(url=url, expires_in=settings.DOWNLOAD_URL_EXPIRY_SECONDS)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_delete_token: str | None = Header(default=None),
    _rl: None = Depends(_delete_rate_limit),
):
    file = await _get_file_for_update_or_404(db, file_id)

    if not x_delete_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing delete token")

    provided_hash = hashlib.sha256(x_delete_token.encode("utf-8")).hexdigest()
    if not secrets.compare_digest(provided_hash, file.delete_token_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid delete token")

    if datetime.now(timezone.utc) > _delete_deadline(file.created_at):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This file's 3-day delete window has passed — it's permanent now.",
        )

    try:
        await run_in_threadpool(_sync_delete, file.storage_key, file.thumbnail_key)
    except Exception:
        pass  # storage object may already be gone; don't block metadata cleanup

    await db.delete(file)
    await db.commit()


def _sync_delete(storage_key: str, thumbnail_key: str | None) -> None:
    storage_service.delete_object(storage_key)
    if thumbnail_key:
        storage_service.delete_object(thumbnail_key)
