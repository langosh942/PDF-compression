from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import CompressionTask, TaskStatus
from app.services.compress import compress_pdf
from app.services.storage import get_storage


@shared_task(name="app.worker.tasks.compress_pdf_task")
def compress_pdf_task(task_id: str) -> None:
    session: Session = SessionLocal()
    storage = get_storage()
    temp_source_path: Path | None = None
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

        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(task)

        storage_root = Path(settings.STORAGE_PATH)
        storage_root.mkdir(parents=True, exist_ok=True)

        if settings.STORAGE_BACKEND == "local":
            source_path = Path(task.original_file_path)
            if not source_path.exists():
                source_path = Path(storage.get_path(task.original_file_path))
            if not source_path.exists():
                task.status = TaskStatus.FAILED
                task.error_message = "Original file not found"
                task.updated_at = datetime.utcnow()
                session.commit()
                return
        else:
            reference = task.original_file_path
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
            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error_message = f"Failed to retrieve original file: {exc}"
                task.updated_at = datetime.utcnow()
                session.commit()
                return

            temp_dir = storage_root / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_source_path = temp_dir / f"{task.id}_input.pdf"
            with open(temp_source_path, "wb") as tmp_file:
                tmp_file.write(file_data)
            source_path = temp_source_path

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

        compressed_file_key = f"compressed/{task.id}.pdf"
        if settings.STORAGE_BACKEND != "local":
            with open(output_path, "rb") as tmp_output:
                storage.save(compressed_file_key, tmp_output)
            output_path.unlink(missing_ok=True)

        stored_reference = (
            str(output_path) if settings.STORAGE_BACKEND == "local" else compressed_file_key
        )

        task.status = TaskStatus.COMPLETED
        task.compressed_file_path = stored_reference
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
        if temp_source_path and temp_source_path.exists():
            temp_source_path.unlink(missing_ok=True)
        session.close()
