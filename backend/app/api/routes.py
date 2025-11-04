from __future__ import annotations

import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import CompressionTask, TaskStatus
from app.services.storage import get_storage
from app.worker.tasks import compress_pdf_task

router = APIRouter(prefix="/api/v1")


class CompressResponse(BaseModel):
    task_id: str
    status: str


class TaskResponse(BaseModel):
    task_id: str
    status: str
    original_filename: str
    original_size_mb: float
    compressed_size_mb: Optional[float] = None
    target_size_mb: float
    created_at: str
    completed_at: Optional[str] = None
    result_download_url: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/compress", response_model=CompressResponse, status_code=201)
async def create_compression_task(
    file: UploadFile = File(..., description="PDF file to compress"),
    target_size_mb: float = Form(..., description="Target output size in MB", gt=0),
    min_quality: int = Form(20, ge=1, le=100),
    max_iterations: int = Form(6, ge=1, le=20),
    preserve_metadata: bool = Form(False),
    db: Session = Depends(get_db),
) -> CompressResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    task_id = str(uuid.uuid4())
    original_file_key = f"original/{task_id}.pdf"

    storage = get_storage()
    storage.save(original_file_key, BytesIO(content))
    stored_path = storage.get_path(original_file_key)
    if not stored_path:
        raise HTTPException(status_code=500, detail="Failed to store uploaded file")

    original_size_bytes = len(content)
    if settings.STORAGE_BACKEND == "local":
        try:
            path_obj = Path(stored_path)
            if path_obj.exists():
                original_size_bytes = path_obj.stat().st_size
        except OSError:
            pass

    task = CompressionTask(
        id=task_id,
        status=TaskStatus.QUEUED,
        original_filename=file.filename or "unknown.pdf",
        original_file_path=original_file_key,
        original_size_bytes=original_size_bytes,
        target_size_mb=target_size_mb,
        min_quality=min_quality,
        max_iterations=max_iterations,
        preserve_metadata=preserve_metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(task)
    db.commit()

    compress_pdf_task.delay(task_id)

    return CompressResponse(task_id=task_id, status=task.status.value)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)) -> TaskResponse:
    task: CompressionTask | None = db.get(CompressionTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result_download_url = None
    if task.status == TaskStatus.COMPLETED and task.compressed_file_path:
        result_download_url = f"/api/v1/download/{task_id}"

    compressed_size_mb = None
    if task.compressed_size_bytes is not None:
        compressed_size_mb = task.compressed_size_bytes / (1024 * 1024)

    return TaskResponse(
        task_id=task.id,
        status=task.status.value,
        original_filename=task.original_filename,
        original_size_mb=task.original_size_bytes / (1024 * 1024),
        compressed_size_mb=compressed_size_mb,
        target_size_mb=task.target_size_mb,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        result_download_url=result_download_url,
        error_message=task.error_message,
    )


@router.get("/download/{task_id}")
def download_compressed_file(task_id: str, db: Session = Depends(get_db)):
    task: CompressionTask | None = db.get(CompressionTask, task_id)
    if task is None or task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="File not found")

    if not task.compressed_file_path:
        raise HTTPException(status_code=404, detail="Compressed file not available")

    filename = f"compressed_{task.original_filename}"

    if settings.STORAGE_BACKEND == "local":
        compressed_path = Path(task.compressed_file_path)
        if not compressed_path.exists():
            compressed_path = Path(settings.STORAGE_PATH) / task.compressed_file_path
        if not compressed_path.exists():
            raise HTTPException(status_code=404, detail="File does not exist")

        return FileResponse(
            path=compressed_path,
            media_type="application/pdf",
            filename=filename,
        )
    else:
        storage = get_storage()
        reference = task.compressed_file_path
        key = reference
        if reference.startswith("http"):
            parsed = urlparse(reference)
            path = parsed.path.lstrip("/")
            if path:
                parts = path.split("/", 1)
                if len(parts) == 2:
                    key = parts[1]
                else:
                    key = parts[0]

        try:
            file_data = storage.get(key)
            return StreamingResponse(
                BytesIO(file_data),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception:
            raise HTTPException(status_code=404, detail="File does not exist in storage")
