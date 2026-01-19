"""S3 Storage service for document and media storage."""

import hashlib
import io
import os
from datetime import datetime, timedelta, timezone
from typing import BinaryIO
from uuid import UUID, uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings


class StorageService:
    """Service for S3-compatible object storage."""

    def __init__(self) -> None:
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.s3_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket)

    async def upload_file(
        self,
        file: UploadFile,
        folder: str,
        farmer_id: UUID,
        encrypt: bool = True,
    ) -> dict:
        """Upload a file to S3.

        Returns dict with file_path, file_hash, file_size, mime_type.
        """
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Calculate hash for integrity
        file_hash = hashlib.sha256(content).hexdigest()

        # Generate unique file path
        ext = os.path.splitext(file.filename or "file")[1]
        unique_id = uuid4().hex[:12]
        file_path = f"{folder}/{farmer_id}/{unique_id}{ext}"

        # Upload to S3
        extra_args = {
            "ContentType": file.content_type or "application/octet-stream",
        }
        if encrypt:
            extra_args["ServerSideEncryption"] = "AES256"

        self.s3_client.upload_fileobj(
            io.BytesIO(content),
            self.bucket,
            file_path,
            ExtraArgs=extra_args,
        )

        return {
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "mime_type": file.content_type or "application/octet-stream",
            "original_name": file.filename,
        }

    async def upload_bytes(
        self,
        content: bytes,
        file_path: str,
        content_type: str = "application/octet-stream",
        encrypt: bool = True,
    ) -> dict:
        """Upload raw bytes to S3."""
        file_hash = hashlib.sha256(content).hexdigest()

        extra_args = {"ContentType": content_type}
        if encrypt:
            extra_args["ServerSideEncryption"] = "AES256"

        self.s3_client.upload_fileobj(
            io.BytesIO(content),
            self.bucket,
            file_path,
            ExtraArgs=extra_args,
        )

        return {
            "file_path": file_path,
            "file_hash": file_hash,
            "file_size": len(content),
        }

    async def download_file(self, file_path: str) -> bytes:
        """Download a file from S3."""
        response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
        return response["Body"].read()

    async def get_presigned_url(
        self,
        file_path: str,
        expiration_minutes: int = 60,
        for_upload: bool = False,
    ) -> str:
        """Generate a presigned URL for file access or upload."""
        client_method = "put_object" if for_upload else "get_object"

        url = self.s3_client.generate_presigned_url(
            ClientMethod=client_method,
            Params={"Bucket": self.bucket, "Key": file_path},
            ExpiresIn=expiration_minutes * 60,
        )
        return url

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError:
            return False

    async def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError:
            return False


# Singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
