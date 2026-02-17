"""Farm registration workflow API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.schemas.farm_registration import (
    BoundaryInput,
    CropRecordCreate,
    CropRecordResponse,
    FarmAssetCreate,
    FarmAssetResponse,
    FarmDocumentCreate,
    FarmDocumentResponse,
    FarmRegistrationResponse,
    FarmRegistrationStatus,
    FarmRegistrationStep,
    FieldVisitCreate,
    FieldVisitResponse,
    LandDetailsInput,
    LocationInput,
    RegistrationStartInput,
    SoilTestReportCreate,
    SoilTestReportResponse,
    SoilWaterInput,
)
from app.services.farm_registration_workflow_service import FarmRegistrationWorkflowService

router = APIRouter()


# Registration workflow endpoints


@router.post("/start", response_model=FarmRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def start_registration(
    data: RegistrationStartInput,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationResponse:
    """Start a new farm registration for a farmer."""
    service = FarmRegistrationWorkflowService(db)
    try:
        location_data = LocationInput(
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
        )
        farm = await service.start_registration(data.farmer_id, location_data)
        await db.commit()
        return FarmRegistrationResponse(
            farm_id=farm.id,
            status="started",
            message="Farm registration started successfully",
            current_step=FarmRegistrationStep.LOCATION.value,
            next_step=FarmRegistrationStep.BOUNDARY.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Failed to start farm registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start registration: {type(e).__name__}: {str(e)}",
        )


@router.get("/{farm_id}/status", response_model=FarmRegistrationStatus)
async def get_registration_status(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationStatus:
    """Get current registration status for a farm."""
    service = FarmRegistrationWorkflowService(db)
    status_result = await service.get_registration_status(farm_id)
    if not status_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return status_result


@router.patch("/{farm_id}/location", response_model=FarmRegistrationResponse)
async def update_location(
    farm_id: UUID,
    latitude: float,
    longitude: float,
    altitude: float | None = None,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationResponse:
    """Update farm location."""
    service = FarmRegistrationWorkflowService(db)
    try:
        farm = await service.update_location(farm_id, latitude, longitude, altitude)
        await db.commit()
        return FarmRegistrationResponse(
            farm_id=farm.id,
            status="updated",
            message="Location updated successfully",
            current_step=farm.registration_step or FarmRegistrationStep.LOCATION.value,
            next_step=FarmRegistrationStep.BOUNDARY.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{farm_id}/boundary", response_model=FarmRegistrationResponse)
async def set_boundary(
    farm_id: UUID,
    data: BoundaryInput,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationResponse:
    """Set farm boundary from GeoJSON polygon."""
    service = FarmRegistrationWorkflowService(db)
    try:
        farm = await service.set_boundary(farm_id, data)
        await db.commit()
        area_msg = (
            f" Calculated area: {farm.boundary_area_calculated:.2f} acres"
            if farm.boundary_area_calculated
            else ""
        )
        return FarmRegistrationResponse(
            farm_id=farm.id,
            status="updated",
            message=f"Boundary set successfully.{area_msg}",
            current_step=farm.registration_step or FarmRegistrationStep.BOUNDARY.value,
            next_step=FarmRegistrationStep.LAND_DETAILS.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{farm_id}/land-details", response_model=FarmRegistrationResponse)
async def update_land_details(
    farm_id: UUID,
    data: LandDetailsInput,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationResponse:
    """Update land ownership and details."""
    service = FarmRegistrationWorkflowService(db)
    try:
        farm = await service.update_land_details(farm_id, data)
        await db.commit()
        return FarmRegistrationResponse(
            farm_id=farm.id,
            status="updated",
            message="Land details updated successfully",
            current_step=farm.registration_step or FarmRegistrationStep.LAND_DETAILS.value,
            next_step=FarmRegistrationStep.DOCUMENTS.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{farm_id}/soil-water", response_model=FarmRegistrationResponse)
async def update_soil_water(
    farm_id: UUID,
    data: SoilWaterInput,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationResponse:
    """Update soil and water profile."""
    service = FarmRegistrationWorkflowService(db)
    try:
        farm = await service.update_soil_water(farm_id, data)
        await db.commit()
        return FarmRegistrationResponse(
            farm_id=farm.id,
            status="updated",
            message="Soil and water profile updated successfully",
            current_step=farm.registration_step or FarmRegistrationStep.SOIL_WATER.value,
            next_step=FarmRegistrationStep.ASSETS.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{farm_id}/complete-step", response_model=FarmRegistrationStatus)
async def complete_step(
    farm_id: UUID,
    step: FarmRegistrationStep,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationStatus:
    """Mark a registration step as complete."""
    service = FarmRegistrationWorkflowService(db)
    try:
        result = await service.complete_step(farm_id, step)
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{farm_id}/complete", response_model=FarmRegistrationStatus)
async def complete_registration(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FarmRegistrationStatus:
    """Complete the farm registration."""
    service = FarmRegistrationWorkflowService(db)
    try:
        result = await service.complete_registration(farm_id)
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Document endpoints


@router.post(
    "/{farm_id}/documents", response_model=FarmDocumentResponse, status_code=status.HTTP_201_CREATED
)
async def add_document(
    farm_id: UUID,
    data: FarmDocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> FarmDocumentResponse:
    """Add a document to the farm."""
    service = FarmRegistrationWorkflowService(db)
    try:
        document = await service.add_document(farm_id, data)
        await db.commit()
        return FarmDocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{farm_id}/documents", response_model=list[FarmDocumentResponse])
async def list_documents(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FarmDocumentResponse]:
    """List all documents for a farm."""
    service = FarmRegistrationWorkflowService(db)
    documents = await service.get_documents(farm_id)
    return [FarmDocumentResponse.model_validate(d) for d in documents]


# Asset endpoints


@router.post(
    "/{farm_id}/assets", response_model=FarmAssetResponse, status_code=status.HTTP_201_CREATED
)
async def add_asset(
    farm_id: UUID,
    data: FarmAssetCreate,
    db: AsyncSession = Depends(get_db),
) -> FarmAssetResponse:
    """Add an asset to the farm."""
    service = FarmRegistrationWorkflowService(db)
    try:
        asset = await service.add_asset(farm_id, data)
        await db.commit()
        return FarmAssetResponse.model_validate(asset)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{farm_id}/assets", response_model=list[FarmAssetResponse])
async def list_assets(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FarmAssetResponse]:
    """List all assets for a farm."""
    service = FarmRegistrationWorkflowService(db)
    assets = await service.get_assets(farm_id)
    return [FarmAssetResponse.model_validate(a) for a in assets]


# Crop record endpoints


@router.post(
    "/{farm_id}/crops", response_model=CropRecordResponse, status_code=status.HTTP_201_CREATED
)
async def add_crop_record(
    farm_id: UUID,
    data: CropRecordCreate,
    db: AsyncSession = Depends(get_db),
) -> CropRecordResponse:
    """Add a crop record to the farm."""
    service = FarmRegistrationWorkflowService(db)
    try:
        record = await service.add_crop_record(farm_id, data)
        await db.commit()
        return CropRecordResponse.model_validate(record)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{farm_id}/crops", response_model=list[CropRecordResponse])
async def list_crop_records(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CropRecordResponse]:
    """List all crop records for a farm."""
    service = FarmRegistrationWorkflowService(db)
    records = await service.get_crop_records(farm_id)
    return [CropRecordResponse.model_validate(r) for r in records]


# Soil test endpoints


@router.post(
    "/{farm_id}/soil-tests",
    response_model=SoilTestReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_soil_test(
    farm_id: UUID,
    data: SoilTestReportCreate,
    db: AsyncSession = Depends(get_db),
) -> SoilTestReportResponse:
    """Add a soil test report to the farm."""
    service = FarmRegistrationWorkflowService(db)
    try:
        report = await service.add_soil_test(farm_id, data)
        await db.commit()
        return SoilTestReportResponse.model_validate(report)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{farm_id}/soil-tests", response_model=list[SoilTestReportResponse])
async def list_soil_tests(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SoilTestReportResponse]:
    """List all soil test reports for a farm."""
    service = FarmRegistrationWorkflowService(db)
    reports = await service.get_soil_tests(farm_id)
    return [SoilTestReportResponse.model_validate(r) for r in reports]


# Field visit endpoints


@router.post(
    "/{farm_id}/visits", response_model=FieldVisitResponse, status_code=status.HTTP_201_CREATED
)
async def add_field_visit(
    farm_id: UUID,
    data: FieldVisitCreate,
    db: AsyncSession = Depends(get_db),
) -> FieldVisitResponse:
    """Add a field visit record."""
    service = FarmRegistrationWorkflowService(db)
    try:
        visit = await service.add_field_visit(farm_id, data)
        await db.commit()
        return FieldVisitResponse.model_validate(visit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{farm_id}/visits", response_model=list[FieldVisitResponse])
async def list_field_visits(
    farm_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FieldVisitResponse]:
    """List all field visits for a farm."""
    service = FarmRegistrationWorkflowService(db)
    visits = await service.get_field_visits(farm_id)
    return [FieldVisitResponse.model_validate(v) for v in visits]
