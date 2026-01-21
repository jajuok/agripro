"""Farmer and KYC models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.db_types import JSONBCompatible

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


class FarmDocumentType(str, Enum):
    """Farm-specific document types."""
    LAND_TITLE = "land_title"
    LEASE_AGREEMENT = "lease_agreement"
    SURVEY_MAP = "survey_map"
    OWNERSHIP_LETTER = "ownership_letter"
    FARM_PHOTO = "farm_photo"
    BOUNDARY_PHOTO = "boundary_photo"
    GPS_TAGGED_PHOTO = "gps_tagged_photo"
    SOIL_TEST_REPORT = "soil_test_report"
    OTHER = "other"


class AssetCategory(str, Enum):
    """Farm asset categories."""
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    INFRASTRUCTURE = "infrastructure"
    STORAGE = "storage"
    IRRIGATION = "irrigation"
    LIVESTOCK_EQUIPMENT = "livestock_equipment"
    OTHER = "other"


class CropStatus(str, Enum):
    """Crop record status."""
    PLANNED = "planned"
    PLANTED = "planted"
    GROWING = "growing"
    HARVESTED = "harvested"
    FAILED = "failed"


class FieldVisitStatus(str, Enum):
    """Field visit status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class FarmRegistrationStep(str, Enum):
    """Farm registration workflow steps."""
    LOCATION = "location"
    BOUNDARY = "boundary"
    LAND_DETAILS = "land_details"
    DOCUMENTS = "documents"
    SOIL_WATER = "soil_water"
    ASSETS = "assets"
    CROP_HISTORY = "crop_history"
    REVIEW = "review"
    COMPLETE = "complete"


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
    boundary_geojson: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Administrative boundaries
    county: Mapped[str | None] = mapped_column(String(100))
    sub_county: Mapped[str | None] = mapped_column(String(100))
    ward: Mapped[str | None] = mapped_column(String(100))
    village: Mapped[str | None] = mapped_column(String(100))

    # Enhanced location data
    altitude: Mapped[float | None] = mapped_column(Float)  # meters above sea level
    address_description: Mapped[str | None] = mapped_column(Text)  # Written directions

    # Land details
    total_acreage: Mapped[float | None] = mapped_column(Float)
    cultivable_acreage: Mapped[float | None] = mapped_column(Float)
    ownership_type: Mapped[str | None] = mapped_column(String(50))  # owned, leased, communal, family

    # Boundary validation
    boundary_area_calculated: Mapped[float | None] = mapped_column(Float)  # Area from GeoJSON in acres
    boundary_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    boundary_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Plot ID metadata
    plot_id_source: Mapped[str | None] = mapped_column(String(50))  # manual, land_registry, auto_generated
    land_reference_number: Mapped[str | None] = mapped_column(String(100))  # Official LR number

    # Soil profile
    soil_type: Mapped[str | None] = mapped_column(String(100))
    soil_ph: Mapped[float | None] = mapped_column(Float)
    soil_nutrients: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Water
    water_source: Mapped[str | None] = mapped_column(String(100))
    irrigation_type: Mapped[str | None] = mapped_column(String(100))
    has_year_round_water: Mapped[bool | None] = mapped_column(Boolean)
    water_reliability: Mapped[str | None] = mapped_column(String(50))  # reliable, seasonal, unreliable

    # Legacy JSON fields (kept for backward compatibility)
    crop_history: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Registration workflow tracking
    registration_step: Mapped[str] = mapped_column(String(50), default=FarmRegistrationStep.LOCATION.value)
    registration_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="farms")
    documents: Mapped[list["FarmDocument"]] = relationship(
        "FarmDocument", back_populates="farm", cascade="all, delete-orphan"
    )
    assets: Mapped[list["FarmAsset"]] = relationship(
        "FarmAsset", back_populates="farm", cascade="all, delete-orphan"
    )
    crop_records: Mapped[list["CropRecord"]] = relationship(
        "CropRecord", back_populates="farm", cascade="all, delete-orphan"
    )
    soil_tests: Mapped[list["SoilTestReport"]] = relationship(
        "SoilTestReport", back_populates="farm", cascade="all, delete-orphan"
    )
    field_visits: Mapped[list["FieldVisit"]] = relationship(
        "FieldVisit", back_populates="farm", cascade="all, delete-orphan"
    )


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
    extracted_data: Mapped[dict | None] = mapped_column(JSONBCompatible)

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
    capture_location: Mapped[dict | None] = mapped_column(JSONBCompatible)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="biometrics")


class KYCApplication(Base):
    """KYC application tracking model for step-by-step registration."""

    __tablename__ = "kyc_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE"), unique=True
    )

    # Current step in the workflow
    current_step: Mapped[str] = mapped_column(String(50), default="personal_info")
    # Steps: personal_info -> documents -> biometrics -> bank_info -> review -> complete

    # Step completion tracking
    personal_info_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    documents_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    biometrics_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    bank_info_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    # Required documents checklist (stored as JSON)
    required_documents: Mapped[dict | None] = mapped_column(JSONBCompatible, default=dict)
    submitted_documents: Mapped[dict | None] = mapped_column(JSONBCompatible, default=dict)

    # Required biometrics checklist
    required_biometrics: Mapped[list | None] = mapped_column(JSONBCompatible, default=list)
    captured_biometrics: Mapped[list | None] = mapped_column(JSONBCompatible, default=list)

    # External verification results
    id_verification_result: Mapped[dict | None] = mapped_column(JSONBCompatible)
    credit_check_result: Mapped[dict | None] = mapped_column(JSONBCompatible)
    sanctions_check_result: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Review tracking
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    review_notes: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(String(500))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    farmer: Mapped["Farmer"] = relationship("Farmer", backref="kyc_application")


class ExternalVerification(Base):
    """External verification results (ID verification, credit bureau, sanctions)."""

    __tablename__ = "external_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE")
    )

    verification_type: Mapped[str] = mapped_column(String(50))  # id_iprs, id_nin, credit_bureau, sanctions
    provider: Mapped[str] = mapped_column(String(100))
    reference_number: Mapped[str | None] = mapped_column(String(100))

    # Request/Response
    request_data: Mapped[dict | None] = mapped_column(JSONBCompatible)
    response_data: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Result
    status: Mapped[str] = mapped_column(String(20))  # pending, success, failed, error
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    farmer: Mapped["Farmer"] = relationship("Farmer", backref="external_verifications")


class KYCReviewQueue(Base):
    """Queue for KYC applications pending manual review."""

    __tablename__ = "kyc_review_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farmers.id", ondelete="CASCADE")
    )

    priority: Mapped[int] = mapped_column(default=5)  # 1=highest, 10=lowest
    reason: Mapped[str] = mapped_column(String(200))  # Why manual review is needed
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, in_progress, completed
    decision: Mapped[str | None] = mapped_column(String(20))  # approved, rejected, escalated

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    farmer: Mapped["Farmer"] = relationship("Farmer", backref="review_queue_entries")


# =============================================================================
# Farm Registration Models (Phase 2.2)
# =============================================================================


class FarmDocument(Base):
    """Farm-specific document model for land titles, photos, etc."""

    __tablename__ = "farm_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="CASCADE")
    )

    document_type: Mapped[str] = mapped_column(String(50))
    document_number: Mapped[str | None] = mapped_column(String(100))
    file_url: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column()

    # GPS metadata for tagged photos
    gps_latitude: Mapped[float | None] = mapped_column(Float)
    gps_longitude: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Description/notes
    description: Mapped[str | None] = mapped_column(Text)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    verification_notes: Mapped[str | None] = mapped_column(Text)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm: Mapped["FarmProfile"] = relationship("FarmProfile", back_populates="documents")


class FarmAsset(Base):
    """Farm asset/equipment model."""

    __tablename__ = "farm_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="CASCADE")
    )

    asset_type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    # Ownership
    ownership_type: Mapped[str] = mapped_column(String(50), default="owned")  # owned, leased, rented, shared
    acquisition_date: Mapped[datetime | None] = mapped_column(DateTime)
    estimated_value: Mapped[float | None] = mapped_column(Float)

    # For equipment
    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    condition: Mapped[str | None] = mapped_column(String(50))  # excellent, good, fair, poor

    # Quantity for countable items
    quantity: Mapped[int] = mapped_column(default=1)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_photo_path: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm: Mapped["FarmProfile"] = relationship("FarmProfile", back_populates="assets")


class CropRecord(Base):
    """Crop cultivation record model."""

    __tablename__ = "crop_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="CASCADE")
    )

    # Crop details
    crop_name: Mapped[str] = mapped_column(String(100))
    variety: Mapped[str | None] = mapped_column(String(100))

    # Season and year
    season: Mapped[str] = mapped_column(String(50))  # long_rains, short_rains, irrigated
    year: Mapped[int] = mapped_column()
    planting_date: Mapped[datetime | None] = mapped_column(DateTime)
    harvest_date: Mapped[datetime | None] = mapped_column(DateTime)

    # Area
    planted_acreage: Mapped[float | None] = mapped_column(Float)

    # Yield
    expected_yield_kg: Mapped[float | None] = mapped_column(Float)
    actual_yield_kg: Mapped[float | None] = mapped_column(Float)

    # Is this the current crop?
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    # Inputs used
    inputs_used: Mapped[dict | None] = mapped_column(JSONBCompatible)  # seeds, fertilizer, pesticides
    notes: Mapped[str | None] = mapped_column(Text)

    # Verification by extension officer
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm: Mapped["FarmProfile"] = relationship("FarmProfile", back_populates="crop_records")


class SoilTestReport(Base):
    """Soil test report model."""

    __tablename__ = "soil_test_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="CASCADE")
    )

    # Test metadata
    test_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tested_by: Mapped[str | None] = mapped_column(String(200))
    lab_name: Mapped[str | None] = mapped_column(String(200))
    sample_id: Mapped[str | None] = mapped_column(String(100))

    # Sample location
    sample_latitude: Mapped[float | None] = mapped_column(Float)
    sample_longitude: Mapped[float | None] = mapped_column(Float)
    sample_depth_cm: Mapped[float | None] = mapped_column(Float)

    # Core results
    texture: Mapped[str | None] = mapped_column(String(100))
    ph_level: Mapped[float | None] = mapped_column(Float)
    organic_matter_percent: Mapped[float | None] = mapped_column(Float)

    # Macronutrients (in ppm)
    nitrogen_ppm: Mapped[float | None] = mapped_column(Float)
    phosphorus_ppm: Mapped[float | None] = mapped_column(Float)
    potassium_ppm: Mapped[float | None] = mapped_column(Float)

    # Secondary nutrients
    calcium: Mapped[float | None] = mapped_column(Float)
    magnesium: Mapped[float | None] = mapped_column(Float)
    sulfur: Mapped[float | None] = mapped_column(Float)

    # Micronutrients and other data
    micronutrients: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Full parsed report data
    full_report_data: Mapped[dict | None] = mapped_column(JSONBCompatible)

    # Document reference
    report_file_url: Mapped[str | None] = mapped_column(String(500))

    # Recommendations
    recommendations: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm: Mapped["FarmProfile"] = relationship("FarmProfile", back_populates="soil_tests")


class FieldVisit(Base):
    """Field visit verification model."""

    __tablename__ = "field_visits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm_profiles.id", ondelete="CASCADE")
    )

    # Visit details
    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    purpose: Mapped[str] = mapped_column(String(50))  # verification, inspection, extension, follow_up

    # Visitor info
    visitor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))  # Extension officer/verifier user ID
    visitor_name: Mapped[str] = mapped_column(String(200))

    # Visit location verification
    gps_latitude: Mapped[float | None] = mapped_column(Float)
    gps_longitude: Mapped[float | None] = mapped_column(Float)

    # Status
    verification_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, verified, rejected

    # Findings
    findings: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)
    photos: Mapped[list | None] = mapped_column(JSONBCompatible)  # List of photo paths

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm: Mapped["FarmProfile"] = relationship("FarmProfile", back_populates="field_visits")
