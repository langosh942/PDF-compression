"""
Celery worker entry point.

This module provides the celery application instance for the worker.
Run with: celery -A celery_worker worker --loglevel=info
"""
from app.worker.celery_app import celery_app

# Expose celery_app at module level for the Celery CLI
celery = celery_app

__all__ = ["celery", "celery_app"]
