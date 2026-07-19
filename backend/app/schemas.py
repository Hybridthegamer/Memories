import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ---- Files: upload ----

class UploadRequestIn(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str
    size_bytes: int = Field(gt=0)
    folder: str | None = Field(default=None, max_length=60)

    @field_validator("content_type")
    @classmethod
    def _validate_content_type(cls, v: str) -> str:
        if not (v.startswith("image/") or v.startswith("video/")):
            raise ValueError("content_type must be image/* or video/*")
        return v

    @field_validator("folder")
    @classmethod
    def _normalize_folder(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None


class UploadRequestOut(BaseModel):
    file_id: uuid.UUID | None = None
    upload_method: str
    upload_url: str | None = None
    expires_in: int | None = None
    upload_id: str | None = None
    part_size_bytes: int | None = None
    # Returned exactly once. The browser must hold onto this (e.g. localStorage)
    # to be able to delete this file later — the server never stores it raw.
    delete_token: str | None = None


class ConfirmOut(BaseModel):
    file_id: uuid.UUID
    status: str


class MultipartInitiateOut(BaseModel):
    file_id: uuid.UUID
    upload_id: str
    part_size_bytes: int
    delete_token: str


class PartUrlIn(BaseModel):
    part_number: int = Field(gt=0, le=10000)


class PartUrlOut(BaseModel):
    url: str


class CompletedPart(BaseModel):
    part_number: int = Field(gt=0, le=10000)
    etag: str


class MultipartCompleteIn(BaseModel):
    parts: list[CompletedPart] = Field(min_length=1)


# ---- Files: retrieval ----

class FileOut(BaseModel):
    id: uuid.UUID
    original_name: str
    media_type: str
    size_bytes: int
    status: str
    thumbnail_url: str | None = None
    created_at: datetime
    delete_deadline: datetime
    folder: str | None = None


class FileListOut(BaseModel):
    items: list[FileOut]
    page: int
    page_size: int
    total: int


class DownloadUrlOut(BaseModel):
    url: str
    expires_in: int


class FolderOut(BaseModel):
    name: str
    file_count: int


class FolderListOut(BaseModel):
    folders: list[FolderOut]
