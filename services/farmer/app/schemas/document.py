"""Document schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: UUID
    farmer_id: UUID
    document_type: str
    document_number: str | None
    file_name: str
    mime_type: str
    is_verified: bool
    verified_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
