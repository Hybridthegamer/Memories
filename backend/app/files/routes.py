import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.files import storage_service
from app.files.jobs import enqueue_process_file
from app.models import File, User
from app.rate_limit import rate_limit_by_user
from app.schemas import (
    ConfirmOut,
    DownloadUrlOut,
    FileListOut,
    FileOut,
    MultipartCompleteIn,
    MultipartInitiateOut,
    PartUrlIn,
    PartUrlOut,
    UploadRequestIn,
    UploadRequestOut,
)

router = APIRouter()

_upload_rate_limit = rate_limit_by_user(
    "upload", count=settings.UPLOAD_RATE_LIMIT_COUNT, window_seconds=settings.UPLOAD_RATE_LIMIT_WINDOW_SECONDS
)
_part_url_rate_limit = rate_limit_by_user("upload-part", count=600, window_seconds=60)


def _media_type_from_content_type(content_type: str) -> str:
    return "image" if content_type.startswith("image/") else "video"


async def _get_owned_file_or_404(db: AsyncSession, user: User, file_id: uuid.UUID) -> File:
    result = await db.execute(select(File).where(File.id == file_id, File.owner_id == user.id))
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file


async def _check_quota(db: AsyncSession, user: User, incoming_bytes: int) -> None:
    result = await db.execute(
        select(func.coalesce(func.sum(File.size_bytes), 0)).where(
            File.owner_id == user.id, File.status != "failed"
        )
    )
    used_bytes = result.scalar_one()
    if used_bytes + incoming_bytes > settings.USER_STORAGE_QUOTA_BYTES:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Storage quota exceeded",
        )


# ---- Single upload ----

@router.post("/upload-request", response_model=UploadRequestOut)
async def upload_request(
    payload: UploadRequestIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_upload_rate_limit),
):
    await _check_quota(db, user, payload.size_bytes)

    if payload.size_bytes > settings.SINGLE_UPLOAD_THRESHOLD_BYTES:
        return UploadRequestOut(upload_method="multipart")

    file_id = storage_service.new_file_id()
    storage_key = storage_service.build_storage_key(str(user.id), str(file_id), payload.filename)
    media_type = _media_type_from_content_type(payload.content_type)

    file = File(
        id=file_id,
        owner_id=user.id,
        storage_key=storage_key,
        original_name=payload.filename,
        mime_type=payload.content_type,
        size_bytes=payload.size_bytes,
        media_type=media_type,
        status="pending",
    )
    db.add(file)
    await db.commit()

    upload_url = storage_service.generate_presigned_upload_url(storage_key, payload.content_type)
    return UploadRequestOut(
        file_id=file_id,
        upload_method="single",
        upload_url=upload_url,
        expires_in=settings.UPLOAD_URL_EXPIRY_SECONDS,
    )


@router.post("/{file_id}/confirm", response_model=ConfirmOut)
async def confirm_upload(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = await _get_owned_file_or_404(db, user, file_id)
    if file.status not in ("pending", "processing"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"File is already {file.status}")

    file.status = "processing"
    await db.commit()

    enqueue_process_file(str(file.id), file.storage_key, file.media_type)
    return ConfirmOut(file_id=file.id, status=file.status)


# ---- Multipart upload ----

@router.post("/upload-request/multipart/initiate", response_model=MultipartInitiateOut)
async def multipart_initiate(
    payload: UploadRequestIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_upload_rate_limit),
):
    await _check_quota(db, user, payload.size_bytes)

    file_id = storage_service.new_file_id()
    storage_key = storage_service.build_storage_key(str(user.id), str(file_id), payload.filename)
    media_type = _media_type_from_content_type(payload.content_type)

    upload_id = await run_in_threadpool(
        storage_service.initiate_multipart_upload, storage_key, payload.content_type
    )

    file = File(
        id=file_id,
        owner_id=user.id,
        storage_key=storage_key,
        original_name=payload.filename,
        mime_type=payload.content_type,
        size_bytes=payload.size_bytes,
        media_type=media_type,
        status="pending",
        upload_id=upload_id,
    )
    db.add(file)
    await db.commit()

    return MultipartInitiateOut(
        file_id=file_id, upload_id=upload_id, part_size_bytes=settings.MULTIPART_PART_SIZE_BYTES
    )


@router.post("/{file_id}/multipart/part-url", response_model=PartUrlOut)
async def multipart_part_url(
    file_id: uuid.UUID,
    payload: PartUrlIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_part_url_rate_limit),
):
    file = await _get_owned_file_or_404(db, user, file_id)
    if not file.upload_id or file.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not awaiting multipart upload")

    url = storage_service.generate_presigned_part_url(file.storage_key, file.upload_id, payload.part_number)
    return PartUrlOut(url=url)


@router.post("/{file_id}/multipart/complete", response_model=ConfirmOut)
async def multipart_complete(
    file_id: uuid.UUID,
    payload: MultipartCompleteIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = await _get_owned_file_or_404(db, user, file_id)
    if not file.upload_id or file.status not in ("pending", "processing"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not awaiting multipart upload")

    parts = [{"PartNumber": p.part_number, "ETag": p.etag} for p in payload.parts]
    try:
        await run_in_threadpool(
            storage_service.complete_multipart_upload, file.storage_key, file.upload_id, parts
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to complete upload") from exc

    file.status = "processing"
    await db.commit()

    enqueue_process_file(str(file.id), file.storage_key, file.media_type)
    return ConfirmOut(file_id=file.id, status=file.status)


@router.post("/{file_id}/multipart/abort", status_code=status.HTTP_204_NO_CONTENT)
async def multipart_abort(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = await _get_owned_file_or_404(db, user, file_id)
    if file.upload_id:
        try:
            await run_in_threadpool(storage_service.abort_multipart_upload, file.storage_key, file.upload_id)
        except Exception:
            pass  # best-effort cleanup; the file row is still marked failed below

    file.status = "failed"
    await db.commit()


# ---- Retrieval ----

@router.get("", response_model=FileListOut)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    media_type: str | None = Query(None, pattern="^(image|video)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = [File.owner_id == user.id]
    if media_type:
        filters.append(File.media_type == media_type)

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
            thumbnail_url = storage_service.generate_presigned_download_url(f.thumbnail_key)
        items.append(
            FileOut(
                id=f.id,
                original_name=f.original_name,
                media_type=f.media_type,
                size_bytes=f.size_bytes,
                status=f.status,
                thumbnail_url=thumbnail_url,
                created_at=f.created_at,
            )
        )

    return FileListOut(items=items, page=page, page_size=page_size, total=total)


@router.get("/{file_id}/download-url", response_model=DownloadUrlOut)
async def get_download_url(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = await _get_owned_file_or_404(db, user, file_id)
    if file.status not in ("uploaded", "processing", "ready"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="File is not available for download yet")

    url = storage_service.generate_presigned_download_url(file.storage_key, filename=file.original_name)
    return DownloadUrlOut(url=url, expires_in=settings.DOWNLOAD_URL_EXPIRY_SECONDS)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    file = await _get_owned_file_or_404(db, user, file_id)

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
