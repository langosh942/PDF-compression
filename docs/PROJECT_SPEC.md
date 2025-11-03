# 🧭 SmartPDF Shrinker 项目开发文档


## 1. 项目总览

### 📌 项目名称

**SmartPDF Shrinker – 在线 PDF 智能压缩平台**

### 📘 项目描述

SmartPDF Shrinker 是一个基于 Web 的 PDF 压缩系统。
用户上传 PDF 并指定目标压缩后文件大小（例如压缩至 2MB），系统通过分析 PDF 内容并自动调整图像质量、分辨率、字体与对象流等参数，在尽量保持可读性的情况下，输出接近目标大小的 PDF 文件。

系统支持多种部署模式与可扩展配置，适用于云端与本地部署环境。

---

## 2. 项目目标

| 目标类型 | 内容                            |
| ---- | ----------------------------- |
| 功能目标 | 用户可上传 PDF、设定目标大小并获取压缩结果       |
| 技术目标 | 采用现代前后端分离架构，支持容器化一键部署         |
| 性能目标 | 对 10MB 以内的 PDF，平均压缩时间不超过 30 秒 |
| 可扩展性 | 模块化设计，支持本地或云存储、支持多数据库类型       |
| 自动化  | 所有组件均可由 AI Agent 自动生成、配置与部署   |

---

## 3. 系统架构设计

### 🧩 架构总览

**主要组件：**

* 前端：Next.js (TypeScript + Tailwind)
* 后端：FastAPI (Python 3.11)
* 异步任务：Celery + Redis
* 文件存储：可配置为本地或 MinIO (S3 兼容)
* 数据库：可配置为 SQLite（开发）或 PostgreSQL（生产）
* 网关：Nginx（反向代理 + 静态资源服务）
* 容器：Docker Compose 一键部署

---

### 🔧 架构图

```
[ Browser ]
   │
   ▼
[ Nginx Proxy ]
   ├─ /api → [ FastAPI Backend ]
   │            └─ Celery Worker (PDF 压缩任务)
   │                 ├─ Redis (队列)
   │                 ├─ MinIO / 本地存储
   │                 └─ SQLite / PostgreSQL
   └─ / → [ Next.js Frontend (Web UI) ]
```

---

## 4. 核心功能模块

| 模块            | 描述                                                    |
| ------------- | ----------------------------------------------------- |
| **文件上传**      | 用户上传 PDF 文件，校验类型与大小                                   |
| **目标压缩控制**    | 输入期望大小（MB），系统自动调整压缩参数                                 |
| **压缩引擎**      | 使用 Ghostscript、pikepdf、Pillow 等库逐步压缩                  |
| **任务队列**      | Celery 异步执行压缩，支持并发处理                                  |
| **文件下载**      | 压缩完成后生成下载链接（支持临时授权URL）                                |
| **配置化存储与数据库** | 通过环境变量切换本地/MinIO、SQLite/PostgreSQL                    |
| **容器部署**      | Nginx + Next.js + FastAPI + Redis + MinIO + DB 全栈容器部署 |

---

## 5. 核心算法设计（PDF 智能压缩逻辑）

1. **文件分析阶段**

   * 解析 PDF 对象树，统计图片资源占比；
   * 检查字体嵌入、流压缩状态。

2. **初步优化**

   * 使用 `qpdf` 或 `pikepdf` 去除未引用对象；
   * 重写对象流（Flate 压缩）。

3. **目标匹配压缩**

   * 对图片进行二分搜索压缩：

     * 调整 JPEG 质量 (20~95)
     * 调整分辨率 (72~300 DPI)
   * 逐步测试压缩结果大小；
   * 当文件接近目标大小时停止。

4. **最终输出**

   * 清理元数据；
   * 重新线性化 PDF；
   * 输出最终版本。

5. **误差容忍**

   * 允许 ±10% 大小误差；
   * 若无法达到目标大小 → 返回最小可压缩结果并提示。

---

## 6. 接口设计（FastAPI）

### `POST /api/v1/compress`

创建压缩任务
**请求参数**：

* `file`: PDF 文件
* `target_size_mb`: 目标大小 (float)
* 可选参数：`min_quality`, `max_iterations`, `preserve_metadata`

**返回示例**：

```json
{
  "task_id": "3b92a2b7-f830-4f3a-9f12-fc9dce21b45b",
  "status": "queued"
}
```

---

### `GET /api/v1/tasks/{task_id}`

查询任务状态

```json
{
  "task_id": "3b92a2b7-f830-4f3a-9f12-fc9dce21b45b",
  "status": "running",
  "original_size_mb": 8.5,
  "current_size_mb": 3.2,
  "target_size_mb": 2.0,
  "result_download_url": "https://example.com/download/3b92a2b7.pdf"
}
```

---

### `GET /api/v1/download/{file_id}`

获取最终压缩文件（由存储层返回实际文件内容）

---

## 7. 前端（Next.js）设计

### 页面结构

| 页面                   | 功能                   |
| -------------------- | -------------------- |
| `/`                  | 上传 PDF，输入目标大小，发起压缩任务 |
| `/progress/[taskId]` | 显示压缩进度、实时状态          |
| `/result/[taskId]`   | 展示下载链接与任务结果          |

### 前端组件

* `UploadForm.tsx`：文件选择与参数输入；
* `ProgressCard.tsx`：轮询任务状态；
* `DownloadCard.tsx`：展示结果文件；
* 全局状态管理使用 React Query / SWR。

---

## 8. 后端（FastAPI）结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 主入口
│   ├── api/
│   │   ├── routes.py        # API 路由定义
│   ├── core/
│   │   ├── config.py        # 环境变量 & 设置
│   ├── services/
│   │   ├── compress.py      # PDF 压缩核心逻辑
│   │   ├── storage.py       # 本地/MinIO 存储模块
│   ├── worker/
│   │   ├── tasks.py         # Celery 任务定义
│   └── models.py            # SQLAlchemy ORM 模型
├── Dockerfile
└── requirements.txt
```

---

## 9. 存储与数据库配置

### 本地存储

```
STORAGE_BACKEND=local
STORAGE_PATH=/data/files
```

### MinIO 存储

```
STORAGE_BACKEND=minio
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password
MINIO_BUCKET=pdf-files
```

### 数据库选择

* SQLite：`sqlite:///./data/db.sqlite3`
* PostgreSQL：`postgresql://pdfadmin:pdfpass@db:5432/pdfdb`

---

## 10. Nginx 配置

**`nginx.conf`**

```nginx
events { }

http {
  server {
    listen 80;

    location / {
      proxy_pass http://frontend:3000;
    }

    location /api/ {
      proxy_pass http://backend:8000/;
    }

    location /static/ {
      alias /usr/share/nginx/html/static/;
    }
  }
}
```

---

## 11. Docker Compose 一键部署

**`docker-compose.yml`**

```yaml
version: "3.9"

services:
  nginx:
    image: nginx:latest
    container_name: nginx
    depends_on:
      - frontend
      - backend
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: frontend
    environment:
      - NEXT_PUBLIC_API_BASE=/api
    restart: unless-stopped

  backend:
    build: ./backend
    container_name: backend
    env_file: .env
    depends_on:
      - redis
      - db
      - minio
    restart: unless-stopped

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    env_file: .env
    depends_on:
      - backend
      - redis
    restart: unless-stopped

  redis:
    image: redis:7
    container_name: redis
    restart: unless-stopped

  db:
    image: postgres:15
    container_name: db
    environment:
      POSTGRES_USER: pdfadmin
      POSTGRES_PASSWORD: pdfpass
      POSTGRES_DB: pdfdb
    volumes:
      - ./data/db:/var/lib/postgresql/data
    restart: unless-stopped

  minio:
    image: minio/minio
    container_name: minio
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password
    command: server /data
    ports:
      - "9000:9000"
    volumes:
      - ./data/minio:/data
    restart: unless-stopped
```

---

## 12. 运行方式

### 本地运行

```bash
docker-compose up --build
```

访问：

* Web UI：[http://localhost](http://localhost)
* API：[http://localhost/api](http://localhost/api)
* MinIO 控制台：[http://localhost:9000](http://localhost:9000)

---

## 13. 日志与监控

| 类型   | 工具                             | 内容            |
| ---- | ------------------------------ | ------------- |
| 后端日志 | stdout / JSON                  | API 请求、压缩任务状态 |
| 队列监控 | Celery logs                    | Worker 执行结果   |
| 存储日志 | MinIO Console                  | 文件上传/下载统计     |
| 系统监控 | Docker stats / Prometheus (可选) | CPU、内存、任务速率   |

---

## 14. 测试与验收标准

| 测试项    | 预期结果                     |
| ------ | ------------------------ |
| 上传 PDF | 成功，返回任务 ID               |
| 查询任务状态 | 正确显示进度与文件大小              |
| 下载结果   | 文件有效，大小接近目标（误差 ≤10%）     |
| 一键部署   | `docker-compose up` 启动成功 |
| 性能     | 10MB 文件压缩 ≤30 秒          |
| 安全     | 无恶意脚本执行，上传限制有效           |

---

## 15. 扩展与自动化开发指令

### 🔹 可由 AI 自动执行的开发任务模板

| 任务名称                       | 说明                                  |
| -------------------------- | ----------------------------------- |
| `init_project_structure`   | 生成 `frontend` 与 `backend` 目录及基础文件   |
| `generate_api_routes`      | 根据接口规范自动生成 FastAPI 路由               |
| `generate_frontend_ui`     | 根据页面描述生成 Next.js 页面与组件              |
| `generate_docker_compose`  | 输出包含所有服务的 Docker Compose 文件         |
| `configure_env`            | 生成 `.env` 文件，设定默认本地运行配置             |
| `implement_pdf_compressor` | 实现核心压缩逻辑（pikepdf + Ghostscript）     |
| `deploy_local`             | 执行 `docker-compose up --build` 启动项目 |
| `run_tests`                | 自动执行端到端测试脚本验证流程正确性                  |

---

## ✅ 16. 验收条件

* [x] 用户能上传并压缩 PDF；
* [x] 压缩后大小接近目标（误差 ≤10%）；
* [x] 文档可阅读、未被破坏；
* [x] API 返回结构正确；
* [x] Docker Compose 启动全部服务成功；
* [x] 环境变量可切换存储与数据库类型。

---

## 17. 附录

### 推荐 Python 库

* `pikepdf`：PDF 结构优化
* `Pillow`：图像压缩
* `Ghostscript`：流式压缩引擎
* `fastapi`：后端框架
* `celery`：任务队列
* `redis`：消息中间件
* `sqlalchemy`：ORM 数据库管理

### 推荐 Node 库

* `next`, `react`, `axios`, `tailwindcss`, `swr`

---
