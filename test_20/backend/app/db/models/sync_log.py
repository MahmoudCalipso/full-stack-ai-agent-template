"""SyncLog model — tracks document synchronization history."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.db.base import TimestampMixin


class SyncLog(TimestampMixin, SQLModel, table=True):
    """Tracks document sync operations (local, GDrive, S3, upload)."""

    __tablename__ = "sync_logs"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    source: str = Field(sa_column=Column(String(20), nullable=False))  # local, gdrive, s3, upload
    collection_name: str = Field(sa_column=Column(String(255), nullable=False, index=True))
    status: str = Field(default="running", sa_column=Column(String(20), nullable=False, default="running"))  # running, done, error
    mode: str = Field(default="full", sa_column=Column(String(20), nullable=False, default="full"))  # full, new_only, update_only
    total_files: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    ingested: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    updated: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    skipped: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    failed: int = Field(default=0, sa_column=Column(Integer, nullable=False, default=0))
    error_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    started_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, source={self.source}, status={self.status})>"
