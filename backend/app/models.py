import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("media_type in ('image','video')", name="ck_media_type"),
        CheckConstraint("status in ('pending','uploaded','processing','ready','failed')", name="ck_status"),
        Index("idx_files_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    storage_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    media_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    thumbnail_key: Mapped[str | None] = mapped_column(String, nullable=True)
    upload_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # SHA-256 hex digest of the anonymous uploader's delete token. The raw
    # token is returned to the browser exactly once, at upload time, and
    # never stored — only its hash. Deleting requires presenting a token
    # whose hash matches, and only within DELETE_WINDOW_DAYS of upload.
    delete_token_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
