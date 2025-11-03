"""Celery application entrypoint for the SmartPDF backend."""
from app.worker.celery_app import celery_app

celery = celery_app

__all__ = ["celery", "celery_app"]
