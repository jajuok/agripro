"""Farmer schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class FarmerBase(BaseModel):
    """Base farmer schema."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    email: EmailStr | None = None
    national_id: str | None = None
    date_of_birth: datetime | None = None
    gender: str | None = None


class FarmerCreate(FarmerBase):
    """Farmer creation schema."""

    user_id: UUID
    tenant_id: UUID
    address: str | None = None
    county: str | None = None
    sub_county: str | None = None
    ward: str | None = None
    village: str | None = None


class FarmerUpdate(BaseModel):
    """Farmer update schema."""

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    mobile_money_number: str | None = None


class FarmerResponse(BaseModel):
    """Farmer response schema."""

    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    phone_number: str
    email: str | None
    national_id: str | None
    kyc_status: str
    county: str | None
    sub_county: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FarmerListResponse(BaseModel):
    """Paginated farmer list."""

    items: list[FarmerResponse]
    total: int
    page: int
    page_size: int
