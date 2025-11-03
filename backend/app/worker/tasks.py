from __future__ import annotations

from datetime import datetime
from pathlib import Path

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import CompressionTask, TaskStatus
from app.services.compress import compress_pdf


@shared_task(name="app.worker.tasks.compress_pdf_task")
def compress_pdf_task(task_id: str) -> None:
    session: Session = SessionLocal()
    try:
        task: CompressionTask | None = session.get(CompressionTask, task_id)
        if task is None:
            return

        if not task.original_file_path:
            task.status = TaskStatus.FAILED
            task.error_message = "Original file path missing"
            task.updated_at = datetime.utcnow()
            session.commit()
            return

        source_path = Path(task.original_file_path)
        if not source_path.exists():
            task.status = TaskStatus.FAILED
            task.error_message = "Original file not found"
            task.updated_at = datetime.utcnow()
            session.commit()
            return

        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(task)

        storage_root = Path(settings.STORAGE_PATH)
        compressed_dir = storage_root / "compressed"
        compressed_dir.mkdir(parents=True, exist_ok=True)
        output_path = compressed_dir / f"{task.id}.pdf"

        result = compress_pdf(
            source_path,
            output_path,
            task.target_size_mb,
            min_quality=task.min_quality,
            max_iterations=task.max_iterations,
            preserve_metadata=task.preserve_metadata,
        )

        task.status = TaskStatus.COMPLETED
        task.compressed_file_path = str(result.output_path)
        task.compressed_size_bytes = result.size_bytes
        task.updated_at = datetime.utcnow()
        task.completed_at = datetime.utcnow()
        session.commit()
    except Exception as exc:  # pragma: no cover - defensive path
        task = session.get(CompressionTask, task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            task.updated_at = datetime.utcnow()
            session.commit()
        raise
    finally:
        session.close()
