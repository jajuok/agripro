"""Document management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter()


@router.post(
    "/upload/{farmer_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    farmer_id: UUID,
    document_type: str,
    file: UploadFile = File(...),
    document_number: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a KYC document."""
    service = DocumentService(db)
    return await service.upload_document(
        farmer_id=farmer_id,
        document_type=document_type,
        file=file,
        document_number=document_number,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get document by ID."""
    service = DocumentService(db)
    doc = await service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get("/farmer/{farmer_id}", response_model=list[DocumentResponse])
async def list_farmer_documents(
    farmer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    """List all documents for a farmer."""
    service = DocumentService(db)
    return await service.list_farmer_documents(farmer_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document."""
    service = DocumentService(db)
    await service.delete_document(document_id)
