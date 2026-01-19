"""Farmer and KYC models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    """Base class for models."""
    pass


class KYCStatus(str, Enum):
    """KYC verification status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DocumentType(str, Enum):
    """Document types for KYC."""
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    LAND_TITLE = "land_title"
    LEASE_AGREEMENT = "lease_agreement"
    TAX_ID = "tax_id"
    BANK_STATEMENT = "bank_statement"
    SOIL_TEST = "soil_test"
    OTHER = "other"


class Farmer(Base):
    """Farmer profile model."""

    __tablename__ = "farmers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    # Personal info
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime)
    gender: Mapped[str | None] = mapped_column(String(20))
    national_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)

    # Contact
    phone_number: Mapped[str] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)

    # Location
    county: Mapped[str | None] = mapped_column(String(100))
    sub_county: Mapped[str | None] = mapped_column(String(100))
    ward: Mapped[str | None] = mapped_column(String(100))
    village: Mapped[str | None] = mapped_column(String(100))

    # KYC Status
    kyc_status: Mapped[str] = mapped_column(String(20), default=KYCStatus.PENDING.value)
    kyc_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kyc_verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Bank info
    bank_name: Mapped[str | None] = mapped_column(String(100))
    bank_account: Mapped[str | None] = mapped_column(String(50))
    bank_branch: Mapped[str | None] = mapped_column(String(100))
    mobile_money_number: Mapped[str | None] = mapped_column(String(20))

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farms: Mapped[list["FarmProfile"]] = relationship("FarmProfile", back_populates="farmer")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="farmer")
    biometrics: Mapped[list["BiometricData"]] = relationship("BiometricData", back_populates="farmer")


class FarmProfile(Base):
    """Farm/plot profile model."""

    __tablename__ = "farm_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE")
    )
    plot_id: Mapped[str | None] = mapped_column(String(50), unique=True)

    # Location
    name: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    boundary_geojson: Mapped[dict | None] = mapped_column(JSONB)

    # Land details
    total_acreage: Mapped[float | None] = mapped_column(Float)
    cultivable_acreage: Mapped[float | None] = mapped_column(Float)
    ownership_type: Mapped[str | None] = mapped_column(String(50))  # owned, leased, communal

    # Soil profile
    soil_type: Mapped[str | None] = mapped_column(String(100))
    soil_ph: Mapped[float | None] = mapped_column(Float)
    soil_nutrients: Mapped[dict | None] = mapped_column(JSONB)

    # Water
    water_source: Mapped[str | None] = mapped_column(String(100))
    irrigation_type: Mapped[str | None] = mapped_column(String(100))

    # Crop history
    crop_history: Mapped[dict | None] = mapped_column(JSONB)

    # Assets
    assets: Mapped[dict | None] = mapped_column(JSONB)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="farms")


class Document(Base):
    """KYC document model."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE")
    )

    document_type: Mapped[str] = mapped_column(String(50))
    document_number: Mapped[str | None] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column()

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    verification_notes: Mapped[str | None] = mapped_column(Text)

    # OCR/extracted data
    extracted_data: Mapped[dict | None] = mapped_column(JSONB)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="documents")


class BiometricData(Base):
    """Biometric data model."""

    __tablename__ = "biometric_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE")
    )

    biometric_type: Mapped[str] = mapped_column(String(50))  # fingerprint, face, voice
    template_hash: Mapped[str] = mapped_column(String(255))  # encrypted template reference
    quality_score: Mapped[float | None] = mapped_column(Float)

    # Capture metadata
    capture_device: Mapped[str | None] = mapped_column(String(100))
    capture_location: Mapped[dict | None] = mapped_column(JSONB)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="biometrics")
