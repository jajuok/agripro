"""Document management service."""

from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Document
from app.schemas.document import DocumentResponse


class DocumentService:
    """Service for document operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_document(
        self,
        farmer_id: UUID,
        document_type: str,
        file: UploadFile,
        document_number: str | None = None,
    ) -> DocumentResponse:
        """Upload and store a document."""
        # TODO: Implement S3 upload
        file_path = f"documents/{farmer_id}/{document_type}/{file.filename}"

        doc = Document(
            farmer_id=farmer_id,
            document_type=document_type,
            document_number=document_number,
            file_path=file_path,
            file_name=file.filename or "unknown",
            mime_type=file.content_type or "application/octet-stream",
            file_size=file.size,
        )
        self.db.add(doc)
        await self.db.flush()
        return DocumentResponse.model_validate(doc)

    async def get_document(self, document_id: UUID) -> DocumentResponse | None:
        """Get document by ID."""
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        return DocumentResponse.model_validate(doc) if doc else None

    async def list_farmer_documents(self, farmer_id: UUID) -> list[DocumentResponse]:
        """List all documents for a farmer."""
        result = await self.db.execute(
            select(Document).where(Document.farmer_id == farmer_id)
        )
        docs = result.scalars().all()
        return [DocumentResponse.model_validate(d) for d in docs]

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document."""
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc:
            # TODO: Delete from S3
            await self.db.delete(doc)
