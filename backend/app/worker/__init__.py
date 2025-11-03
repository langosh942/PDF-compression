"""Celery worker package."""
from .celery_app import celery_app

celery = celery_app

__all__ = ["celery", "celery_app"]
