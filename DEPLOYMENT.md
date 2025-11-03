# SmartPDF Shrinker - Deployment Guide

## MVP Implementation Completed

This MVP includes all core components:

### ✅ Backend (FastAPI)
- REST API endpoints for upload, status check, and download
- Celery worker for async PDF compression
- SQLAlchemy models with support for SQLite/PostgreSQL
- Configurable storage (local/MinIO)
- PDF compression engine using pikepdf and Pillow

### ✅ Frontend (Next.js)
- Upload page with file selection and target size input
- Real-time progress tracking with SWR polling
- Download result page
- Responsive UI with Tailwind CSS

### ✅ Infrastructure
- Docker Compose with all services
- Nginx reverse proxy
- Redis for Celery queue
- PostgreSQL database (optional)
- MinIO object storage (optional)

## Quick Deploy

```bash
# 1. Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version

# 2. Clone/navigate to project directory
cd /path/to/smartpdf-shrinker

# 3. Create environment configuration (already created)
# The .env file is pre-configured with local storage and SQLite

# 4. Start all services
docker-compose up --build

# 5. Access the application
# Web UI: http://localhost
# API: http://localhost/api/v1
# MinIO Console: http://localhost:9001
```

## Service Architecture

```
┌─────────────┐
│   Browser   │
└─────┬───────┘
      │
┌─────▼────────────────────────┐
│  Nginx (Port 80)             │
│  ├─ / → frontend:3000        │
│  └─ /api → backend:8000      │
└─────┬────────────┬───────────┘
      │            │
┌─────▼──────┐ ┌──▼──────────┐
│  Frontend  │ │   Backend   │
│  (Next.js) │ │  (FastAPI)  │
└────────────┘ └──┬──────────┘
                  │
      ┌───────────┼────────────┐
      │           │            │
┌─────▼──────┐ ┌─▼─────┐ ┌───▼──────┐
│   Worker   │ │ Redis │ │ Database │
│  (Celery)  │ │       │ │ (SQLite) │
└────────────┘ └───────┘ └──────────┘
```

## Environment Variables

Key configuration in `.env`:

- `STORAGE_BACKEND=local` - Use local filesystem (or `minio` for S3)
- `DATABASE_URL=sqlite:///./data/db.sqlite3` - SQLite for development
- `REDIS_URL=redis://redis:6379/0` - Redis connection

## Development Mode

Run services individually for development:

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Celery Worker
```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testing the System

1. **Upload a PDF**: Navigate to http://localhost, select a PDF file
2. **Set target size**: Enter desired compression size (e.g., 2.0 MB)
3. **Monitor progress**: Watch real-time compression status
4. **Download result**: Get the compressed PDF when complete

## Troubleshooting

### Services not starting
```bash
docker-compose down
docker-compose up --build
```

### Check logs
```bash
docker-compose logs backend
docker-compose logs worker
docker-compose logs frontend
```

### Permission issues
```bash
sudo chown -R $USER:$USER data/
```

## Production Recommendations

1. **Use PostgreSQL**: Update `DATABASE_URL` to PostgreSQL connection string
2. **Use MinIO/S3**: Set `STORAGE_BACKEND=minio` for scalable storage
3. **Add HTTPS**: Configure SSL certificates in Nginx
4. **Scale workers**: Add more Celery worker instances
5. **Add monitoring**: Implement logging aggregation and metrics

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: http://localhost/api/docs
- ReDoc: http://localhost/api/redoc
