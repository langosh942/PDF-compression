from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String, Text

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CompressionTask(Base):
    __tablename__ = "tasks"

    id: str = Column(String(64), primary_key=True, index=True)
    status: TaskStatus = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.QUEUED)
    original_filename: str = Column(String(255), nullable=False)
    original_file_path: str = Column(String(500), nullable=False)
    compressed_file_path: Optional[str] = Column(String(500), nullable=True)
    original_size_bytes: int = Column(Integer, nullable=False)
    compressed_size_bytes: Optional[int] = Column(Integer, nullable=True)
    target_size_mb: float = Column(Float, nullable=False)
    min_quality: int = Column(Integer, nullable=False, default=20)
    max_iterations: int = Column(Integer, nullable=False, default=6)
    preserve_metadata: bool = Column(Boolean, nullable=False, default=False)
    error_message: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
