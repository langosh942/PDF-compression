from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from minio import Minio

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_path: str, content: BinaryIO) -> str:
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        pass

    @abstractmethod
    def get_path(self, file_path: str) -> str:
        pass

    @abstractmethod
    def delete(self, file_path: str) -> None:
        pass


class LocalStorage(StorageBackend):
    def __init__(self, base_path: Path = settings.STORAGE_PATH):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, file_path: str, content: BinaryIO) -> str:
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            while chunk := content.read(8192):
                f.write(chunk)

        return str(full_path)

    def get(self, file_path: str) -> bytes:
        full_path = self.base_path / file_path
        with open(full_path, "rb") as f:
            return f.read()

    def get_path(self, file_path: str) -> str:
        return str(self.base_path / file_path)

    def delete(self, file_path: str) -> None:
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()


class MinIOStorage(StorageBackend):
    def __init__(self):
        endpoint = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        self.client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save(self, file_path: str, content: BinaryIO) -> str:
        data = content.read()
        self.client.put_object(
            self.bucket,
            file_path,
            BytesIO(data),
            length=len(data),
            content_type="application/pdf",
        )
        return file_path

    def get(self, file_path: str) -> bytes:
        response = self.client.get_object(self.bucket, file_path)
        data = response.read()
        response.close()
        response.release_conn()
        return data

    def get_path(self, file_path: str) -> str:
        return self.client.presigned_get_object(self.bucket, file_path)

    def delete(self, file_path: str) -> None:
        self.client.remove_object(self.bucket, file_path)


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "minio":
        return MinIOStorage()
    return LocalStorage()
