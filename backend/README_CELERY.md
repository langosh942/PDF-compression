# Running Celery Worker

To start the Celery worker for the PDF compression backend, use one of the following commands:

## From the backend directory:

```bash
# Using the celery_worker module
celery -A celery_worker worker --loglevel=info

# Or using app.celery
celery -A app.celery worker --loglevel=info

# Or using app.worker
celery -A app.worker worker --loglevel=info
```

## Windows-specific instructions

On Windows, Celery has known issues with the default multiprocessing pool. The application automatically detects Windows and configures the worker to use the `solo` pool to avoid WinError 5 (Access Denied) permission issues.

Simply run the worker normally on Windows:

```bash
celery -A celery_worker worker --loglevel=info
```

The application will automatically use the `solo` pool on Windows. No additional flags are needed.

## Prerequisites

Make sure you have:
1. Redis running (default: redis://localhost:6379/0)
2. Backend dependencies installed: `pip install -r requirements.txt`
3. Environment variables configured (see .env.example)

## Flower (optional)

To monitor Celery tasks with Flower:

```bash
celery -A celery_worker flower --port=5555
```

Then visit http://localhost:5555 in your browser.
