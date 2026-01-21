"""Farm Registration Workflow Engine - orchestrates the farm registration process."""

import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.farmer import (
    CropRecord,
    Farmer,
    FarmAsset,
    FarmDocument,
    FarmProfile,
    FieldVisit,
    SoilTestReport,
)
from app.schemas.farm_registration import (
    BoundaryInput,
    CropRecordCreate,
    FarmAssetCreate,
    FarmDocumentCreate,
    FarmRegistrationStatus,
    FarmRegistrationStep,
    FieldVisitCreate,
    LandDetailsInput,
    LocationInput,
    SoilTestReportCreate,
    SoilWaterInput,
)


class FarmRegistrationWorkflowService:
    """Service for managing farm registration workflow.

    This service orchestrates:
    1. Step-by-step registration wizard
    2. Location and GPS capture
    3. Boundary mapping and validation
    4. Land documentation
    5. Soil and water profile
    6. Asset registration
    7. Crop history
    """

    # GIS service URL (configure via settings in production)
    GIS_SERVICE_URL = "http://localhost:9003/api/v1"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start_registration(
        self,
        farmer_id: UUID,
        data: LocationInput,
    ) -> FarmProfile:
        """Start a new farm registration for a farmer.

        Args:
            farmer_id: The farmer's UUID
            data: Initial location data

        Returns:
            The created farm profile
        """
        # Verify farmer exists
        farmer = await self._get_farmer(farmer_id)
        if not farmer:
            raise ValueError("Farmer not found")

        # Generate unique plot ID
        plot_id = await self._generate_plot_id()

        # Get administrative location from GIS service
        admin_location = await self._reverse_geocode(data.latitude, data.longitude)

        # Create farm profile
        farm = FarmProfile(
            farmer_id=farmer_id,
            plot_id=plot_id,
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
            altitude=data.altitude,
            address_description=data.address_description,
            county=admin_location.get("county"),
            sub_county=admin_location.get("sub_county"),
            ward=admin_location.get("ward"),
            registration_step=FarmRegistrationStep.LOCATION.value,
            registration_complete=False,
        )
        self.db.add(farm)
        await self.db.flush()
        return farm

    async def get_registration_status(self, farm_id: UUID) -> FarmRegistrationStatus | None:
        """Get the current registration status for a farm."""
        farm = await self._get_farm_with_relations(farm_id)
        if not farm:
            return None

        # Calculate progress
        steps_completed = self._count_completed_steps(farm)
        total_steps = 7  # location, boundary, land_details, documents, soil_water, assets, crop_history
        progress = int((steps_completed / total_steps) * 100)

        return FarmRegistrationStatus(
            farm_id=farm.id,
            farmer_id=farm.farmer_id,
            farm_name=farm.name,
            current_step=farm.registration_step or FarmRegistrationStep.LOCATION.value,
            registration_complete=farm.registration_complete,
            progress_percentage=progress,
            steps=self._build_steps_status(farm),
            county=farm.county,
            sub_county=farm.sub_county,
            ward=farm.ward,
            boundary_area_acres=farm.boundary_area_calculated,
            boundary_validated=farm.boundary_validated,
            created_at=farm.created_at,
            updated_at=farm.updated_at,
        )

    async def update_location(
        self,
        farm_id: UUID,
        latitude: float,
        longitude: float,
        altitude: float | None = None,
    ) -> FarmProfile:
        """Update farm location and re-geocode."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        farm.latitude = latitude
        farm.longitude = longitude
        if altitude is not None:
            farm.altitude = altitude

        # Re-geocode
        admin_location = await self._reverse_geocode(latitude, longitude)
        farm.county = admin_location.get("county")
        farm.sub_county = admin_location.get("sub_county")
        farm.ward = admin_location.get("ward")

        farm.updated_at = datetime.now(timezone.utc)
        return farm

    async def set_boundary(
        self,
        farm_id: UUID,
        data: BoundaryInput,
    ) -> FarmProfile:
        """Set farm boundary from GeoJSON polygon."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        # Validate polygon via GIS service
        validation = await self._validate_polygon(data.boundary_geojson)
        if not validation.get("is_valid"):
            raise ValueError(f"Invalid boundary polygon: {validation.get('validation_errors', [])}")

        # Calculate area
        area_result = await self._calculate_area(data.boundary_geojson)

        # Store boundary and calculated values
        farm.boundary_geojson = data.boundary_geojson
        farm.boundary_area_calculated = area_result.get("area_acres")
        farm.total_acreage = area_result.get("area_acres")  # Auto-fill total acreage
        farm.boundary_validated = True

        # Advance to next step
        if farm.registration_step == FarmRegistrationStep.LOCATION.value:
            farm.registration_step = FarmRegistrationStep.BOUNDARY.value

        farm.updated_at = datetime.now(timezone.utc)
        return farm

    async def update_land_details(
        self,
        farm_id: UUID,
        data: LandDetailsInput,
    ) -> FarmProfile:
        """Update land ownership and details."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        farm.total_acreage = data.total_acreage
        if data.cultivable_acreage:
            farm.cultivable_acreage = data.cultivable_acreage
        farm.ownership_type = data.ownership_type
        farm.land_reference_number = data.land_reference_number
        farm.plot_id_source = data.plot_id_source

        # Advance step if needed
        if farm.registration_step in [
            FarmRegistrationStep.LOCATION.value,
            FarmRegistrationStep.BOUNDARY.value,
        ]:
            farm.registration_step = FarmRegistrationStep.LAND_DETAILS.value

        farm.updated_at = datetime.now(timezone.utc)
        return farm

    async def update_soil_water(
        self,
        farm_id: UUID,
        data: SoilWaterInput,
    ) -> FarmProfile:
        """Update soil and water profile."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        farm.soil_type = data.soil_type
        farm.soil_ph = data.soil_ph
        farm.water_source = data.water_source
        farm.irrigation_type = data.irrigation_type

        # Advance step if needed
        if farm.registration_step in [
            FarmRegistrationStep.LOCATION.value,
            FarmRegistrationStep.BOUNDARY.value,
            FarmRegistrationStep.LAND_DETAILS.value,
            FarmRegistrationStep.DOCUMENTS.value,
        ]:
            farm.registration_step = FarmRegistrationStep.SOIL_WATER.value

        farm.updated_at = datetime.now(timezone.utc)
        return farm

    async def complete_step(
        self,
        farm_id: UUID,
        step: FarmRegistrationStep,
    ) -> FarmRegistrationStatus:
        """Mark a registration step as complete and advance to next."""
        farm = await self._get_farm_with_relations(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        # Validate step order
        current_step_index = self._get_step_index(farm.registration_step)
        requested_step_index = self._get_step_index(step.value)

        if requested_step_index > current_step_index + 1:
            raise ValueError(f"Cannot skip to step {step.value}. Complete previous steps first.")

        # Validate step requirements
        self._validate_step_requirements(farm, step)

        # Advance to next step
        next_step = self._get_next_step(step)
        if next_step:
            farm.registration_step = next_step.value
        else:
            farm.registration_step = FarmRegistrationStep.COMPLETE.value
            farm.registration_complete = True
            farm.is_verified = False  # Requires field verification

        farm.updated_at = datetime.now(timezone.utc)
        return await self.get_registration_status(farm_id)  # type: ignore

    async def complete_registration(self, farm_id: UUID) -> FarmRegistrationStatus:
        """Complete the farm registration."""
        farm = await self._get_farm_with_relations(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        # Validate minimum requirements
        if not farm.latitude or not farm.longitude:
            raise ValueError("Farm location is required")
        if not farm.total_acreage:
            raise ValueError("Farm acreage is required")
        if not farm.ownership_type:
            raise ValueError("Ownership type is required")

        farm.registration_step = FarmRegistrationStep.COMPLETE.value
        farm.registration_complete = True
        farm.updated_at = datetime.now(timezone.utc)

        return await self.get_registration_status(farm_id)  # type: ignore

    # Document management
    async def add_document(
        self,
        farm_id: UUID,
        data: FarmDocumentCreate,
    ) -> FarmDocument:
        """Add a document to the farm."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        document = FarmDocument(
            farm_id=farm_id,
            document_type=data.document_type,
            document_number=data.document_number,
            file_url=data.file_url,
            file_name=data.file_name,
            file_size=data.file_size,
            mime_type=data.mime_type,
            gps_latitude=data.gps_latitude,
            gps_longitude=data.gps_longitude,
        )
        self.db.add(document)
        await self.db.flush()

        # Advance step if needed
        if farm.registration_step in [
            FarmRegistrationStep.LOCATION.value,
            FarmRegistrationStep.BOUNDARY.value,
            FarmRegistrationStep.LAND_DETAILS.value,
        ]:
            farm.registration_step = FarmRegistrationStep.DOCUMENTS.value
            farm.updated_at = datetime.now(timezone.utc)

        return document

    async def get_documents(self, farm_id: UUID) -> list[FarmDocument]:
        """Get all documents for a farm."""
        result = await self.db.execute(
            select(FarmDocument).where(FarmDocument.farm_id == farm_id)
        )
        return list(result.scalars().all())

    # Asset management
    async def add_asset(
        self,
        farm_id: UUID,
        data: FarmAssetCreate,
    ) -> FarmAsset:
        """Add an asset to the farm."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        asset = FarmAsset(
            farm_id=farm_id,
            asset_type=data.asset_type,
            name=data.name,
            description=data.description,
            quantity=data.quantity,
            estimated_value=data.estimated_value,
            acquisition_date=data.acquisition_date,
            condition=data.condition,
        )
        self.db.add(asset)
        await self.db.flush()

        # Advance step if needed
        if farm.registration_step == FarmRegistrationStep.SOIL_WATER.value:
            farm.registration_step = FarmRegistrationStep.ASSETS.value
            farm.updated_at = datetime.now(timezone.utc)

        return asset

    async def get_assets(self, farm_id: UUID) -> list[FarmAsset]:
        """Get all assets for a farm."""
        result = await self.db.execute(
            select(FarmAsset).where(FarmAsset.farm_id == farm_id)
        )
        return list(result.scalars().all())

    # Crop records management
    async def add_crop_record(
        self,
        farm_id: UUID,
        data: CropRecordCreate,
    ) -> CropRecord:
        """Add a crop record to the farm."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        # If this is current crop, mark others as not current
        if data.is_current:
            result = await self.db.execute(
                select(CropRecord).where(
                    CropRecord.farm_id == farm_id,
                    CropRecord.is_current == True,
                )
            )
            for record in result.scalars().all():
                record.is_current = False

        crop_record = CropRecord(
            farm_id=farm_id,
            crop_name=data.crop_name,
            variety=data.variety,
            season=data.season,
            year=data.year,
            planted_acreage=data.planted_acreage,
            expected_yield_kg=data.expected_yield_kg,
            actual_yield_kg=data.actual_yield_kg,
            planting_date=data.planting_date,
            harvest_date=data.harvest_date,
            is_current=data.is_current,
        )
        self.db.add(crop_record)
        await self.db.flush()

        # Advance step if needed
        if farm.registration_step in [
            FarmRegistrationStep.SOIL_WATER.value,
            FarmRegistrationStep.ASSETS.value,
        ]:
            farm.registration_step = FarmRegistrationStep.CROP_HISTORY.value
            farm.updated_at = datetime.now(timezone.utc)

        return crop_record

    async def get_crop_records(self, farm_id: UUID) -> list[CropRecord]:
        """Get all crop records for a farm."""
        result = await self.db.execute(
            select(CropRecord)
            .where(CropRecord.farm_id == farm_id)
            .order_by(CropRecord.year.desc(), CropRecord.season)
        )
        return list(result.scalars().all())

    # Soil test reports
    async def add_soil_test(
        self,
        farm_id: UUID,
        data: SoilTestReportCreate,
    ) -> SoilTestReport:
        """Add a soil test report to the farm."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        report = SoilTestReport(
            farm_id=farm_id,
            test_date=data.test_date,
            tested_by=data.tested_by,
            lab_name=data.lab_name,
            ph_level=data.ph_level,
            nitrogen_ppm=data.nitrogen_ppm,
            phosphorus_ppm=data.phosphorus_ppm,
            potassium_ppm=data.potassium_ppm,
            organic_matter_percent=data.organic_matter_percent,
            texture=data.texture,
            recommendations=data.recommendations,
            report_file_url=data.report_file_url,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def get_soil_tests(self, farm_id: UUID) -> list[SoilTestReport]:
        """Get all soil test reports for a farm."""
        result = await self.db.execute(
            select(SoilTestReport)
            .where(SoilTestReport.farm_id == farm_id)
            .order_by(SoilTestReport.test_date.desc())
        )
        return list(result.scalars().all())

    # Field visits
    async def add_field_visit(
        self,
        farm_id: UUID,
        data: FieldVisitCreate,
    ) -> FieldVisit:
        """Add a field visit record."""
        farm = await self._get_farm(farm_id)
        if not farm:
            raise ValueError("Farm not found")

        visit = FieldVisit(
            farm_id=farm_id,
            visit_date=data.visit_date,
            visitor_id=data.visitor_id,
            visitor_name=data.visitor_name,
            purpose=data.purpose,
            findings=data.findings,
            recommendations=data.recommendations,
            gps_latitude=data.gps_latitude,
            gps_longitude=data.gps_longitude,
            photos=data.photos,
        )
        self.db.add(visit)
        await self.db.flush()

        # If verification visit, update farm status
        if data.purpose == "verification":
            farm.is_verified = True
            farm.verification_date = datetime.now(timezone.utc)

        return visit

    async def get_field_visits(self, farm_id: UUID) -> list[FieldVisit]:
        """Get all field visits for a farm."""
        result = await self.db.execute(
            select(FieldVisit)
            .where(FieldVisit.farm_id == farm_id)
            .order_by(FieldVisit.visit_date.desc())
        )
        return list(result.scalars().all())

    # Private helper methods

    async def _get_farmer(self, farmer_id: UUID) -> Farmer | None:
        """Get farmer by ID."""
        result = await self.db.execute(
            select(Farmer).where(Farmer.id == farmer_id)
        )
        return result.scalar_one_or_none()

    async def _get_farm(self, farm_id: UUID) -> FarmProfile | None:
        """Get farm by ID."""
        result = await self.db.execute(
            select(FarmProfile).where(FarmProfile.id == farm_id)
        )
        return result.scalar_one_or_none()

    async def _get_farm_with_relations(self, farm_id: UUID) -> FarmProfile | None:
        """Get farm with all relations loaded."""
        result = await self.db.execute(
            select(FarmProfile)
            .options(
                selectinload(FarmProfile.documents),
                selectinload(FarmProfile.assets),
                selectinload(FarmProfile.crop_records),
                selectinload(FarmProfile.soil_tests),
                selectinload(FarmProfile.field_visits),
            )
            .where(FarmProfile.id == farm_id)
        )
        return result.scalar_one_or_none()

    async def _generate_plot_id(self) -> str:
        """Generate unique plot ID."""
        # Format: PLT-YYYYMMDD-XXXX
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = secrets.token_hex(2).upper()
        return f"PLT-{date_part}-{random_part}"

    async def _reverse_geocode(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Get administrative location from coordinates via GIS service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.GIS_SERVICE_URL}/gis/reverse-geocode",
                    json={"latitude": latitude, "longitude": longitude},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        # Return empty dict if GIS service unavailable
        return {}

    async def _validate_polygon(self, geojson: dict) -> dict[str, Any]:
        """Validate polygon via GIS service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.GIS_SERVICE_URL}/gis/validate-polygon",
                    json={"geojson": geojson},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        # Return valid if GIS service unavailable (for offline mode)
        return {"is_valid": True}

    async def _calculate_area(self, geojson: dict) -> dict[str, Any]:
        """Calculate polygon area via GIS service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.GIS_SERVICE_URL}/gis/calculate-area",
                    json={"geojson": geojson},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return {"area_acres": None}

    def _count_completed_steps(self, farm: FarmProfile) -> int:
        """Count completed registration steps."""
        count = 0
        if farm.latitude and farm.longitude:
            count += 1  # location
        if farm.boundary_geojson:
            count += 1  # boundary
        if farm.total_acreage and farm.ownership_type:
            count += 1  # land_details
        if farm.documents and len(farm.documents) > 0:
            count += 1  # documents
        if farm.soil_type or farm.water_source:
            count += 1  # soil_water
        if farm.assets and len(farm.assets) > 0:
            count += 1  # assets
        if farm.crop_records and len(farm.crop_records) > 0:
            count += 1  # crop_history
        return count

    def _build_steps_status(self, farm: FarmProfile) -> dict[str, dict[str, Any]]:
        """Build status dict for all steps."""
        return {
            FarmRegistrationStep.LOCATION.value: {
                "complete": bool(farm.latitude and farm.longitude),
                "required": True,
            },
            FarmRegistrationStep.BOUNDARY.value: {
                "complete": bool(farm.boundary_geojson),
                "required": False,
            },
            FarmRegistrationStep.LAND_DETAILS.value: {
                "complete": bool(farm.total_acreage and farm.ownership_type),
                "required": True,
            },
            FarmRegistrationStep.DOCUMENTS.value: {
                "complete": bool(farm.documents and len(farm.documents) > 0),
                "required": False,
                "count": len(farm.documents) if farm.documents else 0,
            },
            FarmRegistrationStep.SOIL_WATER.value: {
                "complete": bool(farm.soil_type or farm.water_source),
                "required": False,
            },
            FarmRegistrationStep.ASSETS.value: {
                "complete": bool(farm.assets and len(farm.assets) > 0),
                "required": False,
                "count": len(farm.assets) if farm.assets else 0,
            },
            FarmRegistrationStep.CROP_HISTORY.value: {
                "complete": bool(farm.crop_records and len(farm.crop_records) > 0),
                "required": False,
                "count": len(farm.crop_records) if farm.crop_records else 0,
            },
        }

    def _get_step_index(self, step: str | None) -> int:
        """Get numeric index for a step."""
        steps = [
            FarmRegistrationStep.LOCATION.value,
            FarmRegistrationStep.BOUNDARY.value,
            FarmRegistrationStep.LAND_DETAILS.value,
            FarmRegistrationStep.DOCUMENTS.value,
            FarmRegistrationStep.SOIL_WATER.value,
            FarmRegistrationStep.ASSETS.value,
            FarmRegistrationStep.CROP_HISTORY.value,
            FarmRegistrationStep.REVIEW.value,
            FarmRegistrationStep.COMPLETE.value,
        ]
        if step and step in steps:
            return steps.index(step)
        return 0

    def _get_next_step(self, current: FarmRegistrationStep) -> FarmRegistrationStep | None:
        """Get next step after current."""
        step_order = [
            FarmRegistrationStep.LOCATION,
            FarmRegistrationStep.BOUNDARY,
            FarmRegistrationStep.LAND_DETAILS,
            FarmRegistrationStep.DOCUMENTS,
            FarmRegistrationStep.SOIL_WATER,
            FarmRegistrationStep.ASSETS,
            FarmRegistrationStep.CROP_HISTORY,
            FarmRegistrationStep.REVIEW,
            FarmRegistrationStep.COMPLETE,
        ]
        try:
            idx = step_order.index(current)
            if idx < len(step_order) - 1:
                return step_order[idx + 1]
        except ValueError:
            pass
        return None

    def _validate_step_requirements(self, farm: FarmProfile, step: FarmRegistrationStep) -> None:
        """Validate requirements for completing a step."""
        if step == FarmRegistrationStep.LOCATION:
            if not farm.latitude or not farm.longitude:
                raise ValueError("Location coordinates are required")

        elif step == FarmRegistrationStep.LAND_DETAILS:
            if not farm.total_acreage:
                raise ValueError("Total acreage is required")
            if not farm.ownership_type:
                raise ValueError("Ownership type is required")
