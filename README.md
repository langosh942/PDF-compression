# SmartPDF Shrinker

**SmartPDF Shrinker** is an intelligent online PDF compression platform that automatically reduces PDF file sizes while maintaining readability.

## Features

- 🎯 **Target-based compression**: Specify desired output size (e.g., compress to 2MB)
- 🤖 **Smart optimization**: Automatically adjusts image quality, resolution, and PDF structure
- ⚡ **Async processing**: Background task queue for efficient compression
- 📦 **Flexible storage**: Configurable local or MinIO (S3-compatible) storage
- 🗄️ **Multiple databases**: Support for SQLite (dev) or PostgreSQL (prod)
- 🐳 **One-click deployment**: Full Docker Compose setup

## Architecture

```
Browser → Nginx → Frontend (Next.js) | Backend (FastAPI)
                      ↓
                  Celery Worker
                      ↓
         Redis + Storage + Database
```

## Tech Stack

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- SWR for data fetching

### Backend
- FastAPI (Python 3.11)
- Celery + Redis
- SQLAlchemy
- pikepdf, Pillow for PDF processing

### Infrastructure
- Docker & Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (production)
- MinIO (S3-compatible storage)

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Launch

```bash
docker-compose up --build
```

### Access

- **Web UI**: http://localhost
- **API**: http://localhost/api
- **MinIO Console**: http://localhost:9000

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Configuration
│   │   ├── services/    # Business logic
│   │   ├── worker/      # Celery tasks
│   │   ├── main.py      # Entry point
│   │   └── models.py    # Database models
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # Pages
│   │   └── components/ # React components
│   ├── Dockerfile
│   └── package.json
├── nginx.conf           # Nginx configuration
├── docker-compose.yml   # Full stack deployment
└── docs/               # Documentation
```

## API Endpoints

### POST /api/v1/compress

Create compression task

**Request**:
```bash
curl -X POST http://localhost/api/v1/compress \
  -F "file=@document.pdf" \
  -F "target_size_mb=2.0"
```

**Response**:
```json
{
  "task_id": "3b92a2b7-f830-4f3a-9f12-fc9dce21b45b",
  "status": "queued"
}
```

### GET /api/v1/tasks/{task_id}

Query task status

**Response**:
```json
{
  "task_id": "3b92a2b7-f830-4f3a-9f12-fc9dce21b45b",
  "status": "completed",
  "original_size_mb": 8.5,
  "compressed_size_mb": 2.1,
  "target_size_mb": 2.0,
  "result_download_url": "/api/v1/download/3b92a2b7"
}
```

### GET /api/v1/download/{file_id}

Download compressed file

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Storage
STORAGE_BACKEND=local  # or 'minio'
STORAGE_PATH=/data/files

# MinIO (if using)
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password
MINIO_BUCKET=pdf-files

# Database
DATABASE_URL=sqlite:///./data/db.sqlite3
# DATABASE_URL=postgresql://pdfadmin:pdfpass@db:5432/pdfdb

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Run Celery Worker

```bash
cd backend
celery -A app.worker worker --loglevel=info
```

## Compression Algorithm

1. **Analysis**: Parse PDF structure, identify images and embedded fonts
2. **Optimization**: Remove unreferenced objects, compress streams
3. **Target matching**: Binary search compression levels to approach target size
   - Adjust JPEG quality (20-95)
   - Adjust resolution (72-300 DPI)
4. **Finalization**: Clean metadata, linearize PDF
5. **Tolerance**: ±10% size variance allowed

## Performance

- **Target**: 10MB PDFs compressed in ≤30 seconds
- **Concurrent tasks**: Scalable with multiple Celery workers
- **File size limits**: Configurable (default: 50MB)

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

For questions or issues, please check the [documentation](./docs/) or open an issue.
