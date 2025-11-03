# SmartPDF Shrinker - Architecture Design

## System Architecture Overview

This document describes the technical architecture of the SmartPDF Shrinker platform.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Nginx (Port 80)                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Location Rules:                                     │    │
│  │  / → frontend:3000 (Next.js)                       │    │
│  │  /api → backend:8000 (FastAPI)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────┬────────────────────────────┬────────────────────┘
            │                            │
            ▼                            ▼
    ┌───────────────┐         ┌──────────────────┐
    │   Frontend    │         │     Backend      │
    │   Next.js     │         │    FastAPI       │
    │  TypeScript   │         │   Python 3.11    │
    │   Tailwind    │         │                  │
    │     SWR       │         │  API Routes      │
    └───────────────┘         │  Task Queue      │
                              │  Storage         │
                              │  Database        │
                              └────────┬─────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌───────────────┐  ┌─────────────┐  ┌──────────────┐
            │ Celery Worker │  │   Redis     │  │   Storage    │
            │               │  │             │  │              │
            │ PDF Compress  │  │  Task Queue │  │ Local/MinIO  │
            │               │  │             │  │              │
            └───────┬───────┘  └─────────────┘  └──────────────┘
                    │
                    ▼
            ┌───────────────┐
            │   Database    │
            │               │
            │ SQLite/Postgres│
            │               │
            └───────────────┘
```

## Technology Stack

### Frontend Layer

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 3.x
- **Data Fetching**: SWR (stale-while-revalidate)
- **HTTP Client**: Axios
- **Build Tool**: Turbopack (Next.js built-in)

### Backend Layer

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11
- **ASGI Server**: Uvicorn
- **API Documentation**: OpenAPI/Swagger (auto-generated)
- **Validation**: Pydantic V2

### Task Queue Layer

- **Queue**: Celery 5.x
- **Broker**: Redis 7.x
- **Result Backend**: Redis
- **Concurrency**: Prefork/Gevent

### Storage Layer

**Option 1: Local Storage**
- Direct filesystem access
- Path: `/data/files`

**Option 2: MinIO**
- S3-compatible object storage
- Bucket-based organization
- Pre-signed URLs for downloads

### Database Layer

**Option 1: SQLite** (Development)
- File-based database
- Zero configuration
- Path: `/data/db.sqlite3`

**Option 2: PostgreSQL 15** (Production)
- ACID compliance
- Concurrent access
- Connection pooling

### Infrastructure Layer

- **Reverse Proxy**: Nginx latest
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Networking**: Docker bridge network

## Data Flow

### Upload & Compression Flow

```
1. User uploads PDF via browser
   ↓
2. Next.js sends multipart/form-data to /api/v1/compress
   ↓
3. FastAPI validates file and creates task
   ↓
4. Task queued in Redis via Celery
   ↓
5. Database record created (status: queued)
   ↓
6. API returns task_id to frontend
   ↓
7. Frontend polls /api/v1/tasks/{task_id}
   ↓
8. Celery worker picks up task
   ↓
9. Worker downloads file from storage
   ↓
10. PDF compression executed
   ↓
11. Compressed file uploaded to storage
   ↓
12. Database updated (status: completed)
   ↓
13. Frontend receives completion status
   ↓
14. User downloads compressed file
```

### Status Polling Flow

```
Frontend → GET /api/v1/tasks/{task_id}
            ↓
         FastAPI queries database
            ↓
         Returns current status:
         - queued
         - running
         - completed
         - failed
```

## Database Schema

### Table: `tasks`

| Column              | Type      | Description                |
|---------------------|-----------|----------------------------|
| id                  | UUID      | Primary key                |
| created_at          | DateTime  | Task creation time         |
| updated_at          | DateTime  | Last update time           |
| status              | String    | queued/running/completed   |
| original_filename   | String    | Uploaded file name         |
| original_size_bytes | Integer   | Original file size         |
| target_size_mb      | Float     | Desired output size        |
| compressed_size_bytes| Integer  | Actual output size         |
| original_file_path  | String    | Storage path (original)    |
| compressed_file_path| String    | Storage path (compressed)  |
| error_message       | String    | Error details (if failed)  |
| min_quality         | Integer   | Compression parameter      |
| max_iterations      | Integer   | Compression parameter      |
| preserve_metadata   | Boolean   | Compression parameter      |

### Indexes

- `idx_tasks_status` on `status`
- `idx_tasks_created_at` on `created_at`

## API Specification

### POST /api/v1/compress

**Request**:
```http
POST /api/v1/compress
Content-Type: multipart/form-data

file: <binary>
target_size_mb: 2.0
min_quality: 20 (optional, default: 20)
max_iterations: 10 (optional, default: 10)
preserve_metadata: false (optional, default: false)
```

**Response** (201 Created):
```json
{
  "task_id": "uuid-string",
  "status": "queued"
}
```

**Error Responses**:
- 400: Invalid file type or parameters
- 413: File too large
- 500: Internal server error

### GET /api/v1/tasks/{task_id}

**Response** (200 OK):
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "original_filename": "document.pdf",
  "original_size_mb": 8.5,
  "compressed_size_mb": 2.1,
  "target_size_mb": 2.0,
  "created_at": "2024-01-01T10:00:00Z",
  "completed_at": "2024-01-01T10:00:25Z",
  "result_download_url": "/api/v1/download/uuid-string"
}
```

**Status Values**:
- `queued`: Waiting in queue
- `running`: Currently processing
- `completed`: Successfully compressed
- `failed`: Error occurred

### GET /api/v1/download/{file_id}

**Response** (200 OK):
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="compressed_document.pdf"

<binary data>
```

## PDF Compression Algorithm

### Phase 1: Analysis

```python
def analyze_pdf(file_path):
    with pikepdf.open(file_path) as pdf:
        # Count pages
        num_pages = len(pdf.pages)
        
        # Identify images
        images = extract_images(pdf)
        
        # Calculate image contribution
        image_size = sum(img.size for img in images)
        
        # Check fonts
        fonts = extract_fonts(pdf)
        
        return {
            'num_pages': num_pages,
            'num_images': len(images),
            'image_size_bytes': image_size,
            'embedded_fonts': len(fonts)
        }
```

### Phase 2: Initial Optimization

```python
def initial_optimize(input_path, output_path):
    with pikepdf.open(input_path) as pdf:
        # Remove unreferenced objects
        pdf.remove_unreferenced_resources()
        
        # Compress object streams
        pdf.save(output_path, 
                 compress_streams=True,
                 stream_decode_level=StreamDecodeLevel.generalized)
```

### Phase 3: Image Compression (Binary Search)

```python
def compress_to_target(input_path, target_bytes, max_iterations=10):
    min_quality = 20
    max_quality = 95
    
    for iteration in range(max_iterations):
        quality = (min_quality + max_quality) // 2
        
        # Compress with current quality
        compressed_path = compress_images(input_path, quality)
        compressed_size = os.path.getsize(compressed_path)
        
        # Check if within tolerance (±10%)
        if abs(compressed_size - target_bytes) / target_bytes <= 0.1:
            return compressed_path
        
        # Adjust quality range
        if compressed_size > target_bytes:
            max_quality = quality - 1
        else:
            min_quality = quality + 1
    
    return compressed_path  # Return best attempt
```

### Phase 4: Finalization

```python
def finalize_pdf(input_path, output_path, preserve_metadata=False):
    with pikepdf.open(input_path) as pdf:
        if not preserve_metadata:
            # Remove metadata
            with pdf.open_metadata() as meta:
                meta.clear()
        
        # Linearize for fast web viewing
        pdf.save(output_path, linearize=True)
```

## Configuration Management

### Environment Variables

```python
# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SmartPDF Shrinker"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ALLOWED_HOSTS: list[str] = ["*"]
    
    # Storage
    STORAGE_BACKEND: str = "local"  # or "minio"
    STORAGE_PATH: str = "/data/files"
    
    # MinIO
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password"
    MINIO_BUCKET: str = "pdf-files"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/db.sqlite3"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]
    
    class Config:
        env_file = ".env"
```

## Security Considerations

### Input Validation

- File type validation (MIME type + magic bytes)
- File size limits
- Filename sanitization
- Parameter validation with Pydantic

### Storage Security

- Unique file IDs (UUIDs)
- Temporary download URLs
- File isolation per task
- Automatic cleanup of old files

### Network Security

- Nginx as security boundary
- CORS configuration
- Rate limiting (future)
- HTTPS in production (recommended)

## Scalability

### Horizontal Scaling

- **Frontend**: Multiple Next.js instances behind load balancer
- **Backend**: Multiple FastAPI instances
- **Workers**: Multiple Celery workers
- **Redis**: Redis Cluster for high availability
- **Database**: PostgreSQL with connection pooling

### Vertical Scaling

- Increase worker processes per container
- Allocate more CPU/memory to containers
- Optimize PDF processing algorithms

## Monitoring & Observability

### Logs

- **Backend**: Structured JSON logs to stdout
- **Celery**: Task execution logs
- **Nginx**: Access and error logs

### Metrics (Future Enhancement)

- Task processing time
- Success/failure rates
- Queue depth
- Storage usage
- API response times

## Deployment

### Docker Compose Services

1. **nginx**: Reverse proxy (port 80)
2. **frontend**: Next.js app
3. **backend**: FastAPI app
4. **worker**: Celery worker
5. **redis**: Message broker
6. **db**: PostgreSQL database
7. **minio**: S3-compatible storage

### Volume Mounts

- `./data/db`: PostgreSQL data
- `./data/minio`: MinIO data
- `./data/files`: Local file storage (if not using MinIO)

### Networking

- All services on same Docker bridge network
- Only nginx exposes ports to host
- Inter-service communication via service names

## Development Workflow

### Local Development (without Docker)

1. Start Redis: `docker run -p 6379:6379 redis:7`
2. Start backend: `cd backend && uvicorn app.main:app --reload`
3. Start worker: `cd backend && celery -A app.worker worker --loglevel=info`
4. Start frontend: `cd frontend && npm run dev`

### Full Docker Deployment

1. Configure `.env` file
2. Run: `docker-compose up --build`
3. Access: http://localhost

## Testing Strategy

### Unit Tests

- Backend: pytest
- Frontend: Jest + React Testing Library

### Integration Tests

- API endpoint tests
- Celery task tests
- Storage integration tests

### End-to-End Tests

- Upload → Compress → Download flow
- Error handling scenarios
- Performance benchmarks

## Future Enhancements

1. **Authentication & Authorization**
   - User accounts
   - API keys
   - Usage quotas

2. **Advanced Compression**
   - OCR optimization
   - Font subsetting
   - Page deduplication

3. **Batch Processing**
   - Multiple file upload
   - ZIP archive support

4. **Analytics Dashboard**
   - Compression statistics
   - Storage usage
   - Popular settings

5. **API Enhancements**
   - Webhooks for completion
   - WebSocket for real-time updates
   - RESTful task cancellation
