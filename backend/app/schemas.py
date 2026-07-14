import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---- Auth ----

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Files: upload ----

class UploadRequestIn(BaseModel):
    filename: str = Field(min_length=1, max_length=512)
    content_type: str
    size_bytes: int = Field(gt=0)

    @field_validator("content_type")
    @classmethod
    def _validate_content_type(cls, v: str) -> str:
        if not (v.startswith("image/") or v.startswith("video/")):
            raise ValueError("content_type must be image/* or video/*")
        return v


class UploadRequestOut(BaseModel):
    file_id: uuid.UUID | None = None
    upload_method: str
    upload_url: str | None = None
    expires_in: int | None = None
    upload_id: str | None = None
    part_size_bytes: int | None = None


class ConfirmOut(BaseModel):
    file_id: uuid.UUID
    status: str


class MultipartInitiateOut(BaseModel):
    file_id: uuid.UUID
    upload_id: str
    part_size_bytes: int


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


class FileListOut(BaseModel):
    items: list[FileOut]
    page: int
    page_size: int
    total: int


class DownloadUrlOut(BaseModel):
    url: str
    expires_in: int
