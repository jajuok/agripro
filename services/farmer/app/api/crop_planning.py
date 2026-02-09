"""Crop Planning API endpoints (Phase 3.1)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.crop_planning import (
    # Template schemas
    CropCalendarTemplateCreate,
    CropCalendarTemplateUpdate,
    CropCalendarTemplateResponse,
    CropCalendarTemplateListResponse,
    TemplateRecommendation,
    # Plan schemas
    CropPlanCreate,
    CropPlanUpdate,
    CropPlanActivate,
    CropPlanAdvanceStage,
    CropPlanComplete,
    CropPlanResponse,
    CropPlanSummary,
    CropPlanListResponse,
    CropPlanStatistics,
    CropPlanningDashboard,
    # Activity schemas
    PlannedActivityCreate,
    PlannedActivityUpdate,
    PlannedActivityResponse,
    PlannedActivityListResponse,
    ActivityCompletion,
    ActivitySkip,
    UpcomingActivitiesResponse,
    # Input schemas
    InputRequirementCreate,
    InputRequirementUpdate,
    InputRequirementResponse,
    InputRequirementListResponse,
    InputCalculation,
    QrCodeVerification,
    QrCodeVerificationResult,
    # Irrigation schemas
    IrrigationScheduleCreate,
    IrrigationScheduleUpdate,
    IrrigationScheduleResponse,
    IrrigationScheduleListResponse,
    IrrigationCompletion,
    IrrigationGenerateRequest,
    # Alert schemas
    CropPlanAlertResponse,
    CropPlanAlertListResponse,
    # Enums
    Season,
    CropPlanStatus,
    ActivityStatus,
)
from app.services.crop_planning_service import CropPlanningService

router = APIRouter()


# Dependency to get crop planning service
async def get_crop_planning_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> CropPlanningService:
    return CropPlanningService(db)


# =============================================================================
# Crop Calendar Templates
# =============================================================================


@router.post(
    "/templates",
    response_model=CropCalendarTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Templates"],
)
async def create_template(
    data: CropCalendarTemplateCreate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Create a new crop calendar template (Admin only)."""
    template = await service.create_template(data)
    return CropCalendarTemplateResponse.model_validate(template)


@router.get("/templates", response_model=CropCalendarTemplateListResponse, tags=["Templates"])
async def list_templates(
    tenant_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
    crop_name: str | None = None,
    region: str | None = None,
    season: Season | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List crop calendar templates with filters."""
    items, total = await service.list_templates(
        tenant_id=tenant_id,
        crop_name=crop_name,
        region=region,
        season=season,
        page=page,
        page_size=page_size,
    )
    return CropCalendarTemplateListResponse(
        items=[CropCalendarTemplateResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/templates/{template_id}", response_model=CropCalendarTemplateResponse, tags=["Templates"])
async def get_template(
    template_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get a crop calendar template by ID."""
    template = await service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return CropCalendarTemplateResponse.model_validate(template)


@router.get("/templates/recommend", response_model=list[TemplateRecommendation], tags=["Templates"])
async def recommend_templates(
    tenant_id: UUID,
    farm_id: UUID,
    crop_name: str,
    planned_date: datetime,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get template recommendations based on farm location and timing."""
    templates = await service.recommend_template(
        tenant_id=tenant_id,
        farm_id=farm_id,
        crop_name=crop_name,
        planned_date=planned_date,
    )
    # Build recommendations with match scores
    recommendations = []
    for i, template in enumerate(templates):
        recommendations.append(
            TemplateRecommendation(
                template=CropCalendarTemplateResponse.model_validate(template),
                match_score=100 - (i * 10),  # Simple scoring based on order
                match_reasons=["Matching crop and season"],
                warnings=None,
            )
        )
    return recommendations


@router.patch("/templates/{template_id}", response_model=CropCalendarTemplateResponse, tags=["Templates"])
async def update_template(
    template_id: UUID,
    data: CropCalendarTemplateUpdate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Update a crop calendar template (Admin only)."""
    template = await service.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return CropCalendarTemplateResponse.model_validate(template)


# =============================================================================
# Crop Plans
# =============================================================================


@router.post(
    "/plans",
    response_model=CropPlanResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Plans"],
)
async def create_plan(
    data: CropPlanCreate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Create a new crop plan."""
    plan = await service.create_plan(data)
    return CropPlanResponse.model_validate(plan)


@router.get("/plans", response_model=CropPlanListResponse, tags=["Plans"])
async def list_plans(
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
    farmer_id: UUID | None = None,
    farm_id: UUID | None = None,
    plan_status: CropPlanStatus | None = None,
    season: Season | None = None,
    year: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List crop plans with filters."""
    items, total = await service.list_plans(
        farmer_id=farmer_id,
        farm_id=farm_id,
        status=plan_status,
        season=season,
        year=year,
        page=page,
        page_size=page_size,
    )

    # Build summaries with activity counts
    summaries = []
    for plan in items:
        activities = plan.activities if hasattr(plan, "activities") else []
        summaries.append(
            CropPlanSummary(
                id=plan.id,
                name=plan.name,
                crop_name=plan.crop_name,
                variety=plan.variety,
                season=plan.season,
                year=plan.year,
                status=plan.status,
                farm_id=plan.farm_id,
                farm_name="",  # Would need to join with farm
                planned_planting_date=plan.planned_planting_date,
                planned_acreage=plan.planned_acreage,
                current_growth_stage=plan.current_growth_stage,
                activities_total=len(activities),
                activities_completed=sum(1 for a in activities if a.status == "completed"),
                activities_overdue=sum(1 for a in activities if a.status == "overdue"),
                created_at=plan.created_at,
            )
        )

    return CropPlanListResponse(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/plans/{plan_id}", response_model=CropPlanResponse, tags=["Plans"])
async def get_plan(
    plan_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get a crop plan by ID with all details."""
    plan = await service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop plan not found")

    response = CropPlanResponse.model_validate(plan)
    response.activities_total = len(plan.activities) if plan.activities else 0
    response.activities_completed = sum(
        1 for a in (plan.activities or []) if a.status == "completed"
    )
    return response


@router.patch("/plans/{plan_id}", response_model=CropPlanResponse, tags=["Plans"])
async def update_plan(
    plan_id: UUID,
    data: CropPlanUpdate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Update a crop plan."""
    plan = await service.update_plan(plan_id, data)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop plan not found")
    return CropPlanResponse.model_validate(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Plans"])
async def delete_plan(
    plan_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Delete a draft crop plan."""
    try:
        deleted = await service.delete_plan(plan_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop plan not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/plans/{plan_id}/activate", response_model=CropPlanResponse, tags=["Plans"])
async def activate_plan(
    plan_id: UUID,
    data: CropPlanActivate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Activate a crop plan (start planting)."""
    try:
        plan = await service.activate_plan(plan_id, data)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop plan not found")
        return CropPlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/plans/{plan_id}/advance-stage", response_model=CropPlanResponse, tags=["Plans"])
async def advance_stage(
    plan_id: UUID,
    data: CropPlanAdvanceStage,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Advance crop plan to next growth stage."""
    try:
        plan = await service.advance_stage(plan_id, data)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop plan not found")
        return CropPlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/plans/{plan_id}/complete", response_model=CropPlanResponse, tags=["Plans"])
async def complete_plan(
    plan_id: UUID,
    data: CropPlanComplete,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Complete a crop plan (harvest done)."""
    plan = await service.complete_plan(plan_id, data)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop plan not found")
    return CropPlanResponse.model_validate(plan)


@router.get("/plans/{plan_id}/statistics", response_model=CropPlanStatistics, tags=["Plans"])
async def get_plan_statistics(
    plan_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get statistics for a crop plan."""
    try:
        return await service.get_plan_statistics(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# Planned Activities
# =============================================================================


@router.post(
    "/plans/{plan_id}/activities",
    response_model=PlannedActivityResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Activities"],
)
async def create_activity(
    plan_id: UUID,
    data: PlannedActivityCreate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Add a new activity to a crop plan."""
    # Verify plan_id matches
    if data.crop_plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan ID in path doesn't match body",
        )

    activity = await service.create_activity(data)
    return PlannedActivityResponse.model_validate(activity)


@router.get("/plans/{plan_id}/activities", response_model=PlannedActivityListResponse, tags=["Activities"])
async def list_activities(
    plan_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
    activity_status: ActivityStatus | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """List activities for a crop plan."""
    items, total = await service.list_activities(
        crop_plan_id=plan_id,
        status=activity_status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return PlannedActivityListResponse(
        items=[PlannedActivityResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/activities/upcoming", response_model=UpcomingActivitiesResponse, tags=["Activities"])
async def get_upcoming_activities(
    farmer_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
    days_ahead: int = Query(7, ge=1, le=30),
):
    """Get upcoming activities for a farmer."""
    activities = await service.get_upcoming_activities(farmer_id, days_ahead)
    return UpcomingActivitiesResponse(
        items=activities,
        total=len(activities),
    )


@router.get("/activities/{activity_id}", response_model=PlannedActivityResponse, tags=["Activities"])
async def get_activity(
    activity_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get an activity by ID."""
    activity = await service.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return PlannedActivityResponse.model_validate(activity)


@router.patch("/activities/{activity_id}", response_model=PlannedActivityResponse, tags=["Activities"])
async def update_activity(
    activity_id: UUID,
    data: PlannedActivityUpdate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Update an activity."""
    activity = await service.update_activity(activity_id, data)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return PlannedActivityResponse.model_validate(activity)


@router.post("/activities/{activity_id}/complete", response_model=PlannedActivityResponse, tags=["Activities"])
async def complete_activity(
    activity_id: UUID,
    data: ActivityCompletion,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Mark an activity as completed."""
    activity = await service.complete_activity(activity_id, data)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return PlannedActivityResponse.model_validate(activity)


@router.post("/activities/{activity_id}/skip", response_model=PlannedActivityResponse, tags=["Activities"])
async def skip_activity(
    activity_id: UUID,
    data: ActivitySkip,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Skip an activity with reason."""
    activity = await service.skip_activity(activity_id, data)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return PlannedActivityResponse.model_validate(activity)


# =============================================================================
# Input Requirements
# =============================================================================


@router.post(
    "/plans/{plan_id}/inputs",
    response_model=InputRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Inputs"],
)
async def create_input(
    plan_id: UUID,
    data: InputRequirementCreate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Add input requirement to a crop plan."""
    if data.crop_plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan ID in path doesn't match body",
        )

    input_req = await service.create_input(data)
    return InputRequirementResponse.model_validate(input_req)


@router.get("/plans/{plan_id}/inputs", response_model=InputRequirementListResponse, tags=["Inputs"])
async def list_inputs(
    plan_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """List input requirements for a crop plan."""
    items, total_estimated, total_actual = await service.list_inputs(plan_id)
    return InputRequirementListResponse(
        items=[InputRequirementResponse.model_validate(i) for i in items],
        total=len(items),
        total_estimated_cost=total_estimated,
        total_actual_cost=total_actual,
    )


@router.get("/inputs/{input_id}", response_model=InputRequirementResponse, tags=["Inputs"])
async def get_input(
    input_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get input requirement by ID."""
    input_req = await service.get_input(input_id)
    if not input_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Input not found")
    return InputRequirementResponse.model_validate(input_req)


@router.patch("/inputs/{input_id}", response_model=InputRequirementResponse, tags=["Inputs"])
async def update_input(
    input_id: UUID,
    data: InputRequirementUpdate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Update input requirement."""
    input_req = await service.update_input(input_id, data)
    if not input_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Input not found")
    return InputRequirementResponse.model_validate(input_req)


@router.post("/inputs/{input_id}/verify-qr", response_model=QrCodeVerificationResult, tags=["Inputs"])
async def verify_input_qr(
    input_id: UUID,
    data: QrCodeVerification,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Verify input product via QR code."""
    try:
        return await service.verify_input_qr(input_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/calculate-inputs", response_model=InputCalculation, tags=["Inputs"])
async def calculate_inputs(
    tenant_id: UUID,
    crop_name: str,
    acreage: float,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
    variety: str | None = None,
):
    """Calculate input requirements based on crop and acreage."""
    return await service.calculate_inputs(crop_name, variety, acreage, tenant_id)


# =============================================================================
# Irrigation Schedules
# =============================================================================


@router.post(
    "/plans/{plan_id}/irrigation",
    response_model=IrrigationScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Irrigation"],
)
async def create_irrigation(
    plan_id: UUID,
    data: IrrigationScheduleCreate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Add irrigation schedule to a crop plan."""
    if data.crop_plan_id != plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan ID in path doesn't match body",
        )

    schedule = await service.create_irrigation(data)
    return IrrigationScheduleResponse.model_validate(schedule)


@router.get("/plans/{plan_id}/irrigation", response_model=IrrigationScheduleListResponse, tags=["Irrigation"])
async def list_irrigation(
    plan_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """List irrigation schedules for a crop plan."""
    items, total_planned, total_used = await service.list_irrigation(plan_id)
    return IrrigationScheduleListResponse(
        items=[IrrigationScheduleResponse.model_validate(i) for i in items],
        total=len(items),
        total_water_planned_liters=total_planned,
        total_water_used_liters=total_used,
    )


@router.post(
    "/plans/{plan_id}/irrigation/generate",
    response_model=list[IrrigationScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["Irrigation"],
)
async def generate_irrigation(
    plan_id: UUID,
    data: IrrigationGenerateRequest,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Auto-generate irrigation schedule for a crop plan."""
    try:
        schedules = await service.generate_irrigation_schedule(plan_id, data)
        return [IrrigationScheduleResponse.model_validate(s) for s in schedules]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/irrigation/{schedule_id}", response_model=IrrigationScheduleResponse, tags=["Irrigation"])
async def get_irrigation(
    schedule_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get irrigation schedule by ID."""
    schedule = await service.get_irrigation(schedule_id)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Irrigation schedule not found")
    return IrrigationScheduleResponse.model_validate(schedule)


@router.patch("/irrigation/{schedule_id}", response_model=IrrigationScheduleResponse, tags=["Irrigation"])
async def update_irrigation(
    schedule_id: UUID,
    data: IrrigationScheduleUpdate,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Update irrigation schedule."""
    schedule = await service.update_irrigation(schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Irrigation schedule not found")
    return IrrigationScheduleResponse.model_validate(schedule)


@router.post("/irrigation/{schedule_id}/complete", response_model=IrrigationScheduleResponse, tags=["Irrigation"])
async def complete_irrigation(
    schedule_id: UUID,
    data: IrrigationCompletion,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Mark irrigation as completed."""
    schedule = await service.complete_irrigation(schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Irrigation schedule not found")
    return IrrigationScheduleResponse.model_validate(schedule)


# =============================================================================
# Alerts
# =============================================================================


@router.get("/alerts", response_model=CropPlanAlertListResponse, tags=["Alerts"])
async def list_alerts(
    farmer_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List alerts for a farmer."""
    items, total, unread = await service.list_alerts(
        farmer_id=farmer_id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return CropPlanAlertListResponse(
        items=[CropPlanAlertResponse.model_validate(a) for a in items],
        total=total,
        unread_count=unread,
    )


@router.post("/alerts/{alert_id}/read", response_model=CropPlanAlertResponse, tags=["Alerts"])
async def mark_alert_read(
    alert_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Mark alert as read."""
    alert = await service.mark_alert_read(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return CropPlanAlertResponse.model_validate(alert)


@router.post("/alerts/{alert_id}/dismiss", response_model=CropPlanAlertResponse, tags=["Alerts"])
async def dismiss_alert(
    alert_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Dismiss an alert."""
    alert = await service.dismiss_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return CropPlanAlertResponse.model_validate(alert)


# =============================================================================
# Dashboard
# =============================================================================


@router.get("/dashboard", response_model=CropPlanningDashboard, tags=["Dashboard"])
async def get_dashboard(
    farmer_id: UUID,
    service: Annotated[CropPlanningService, Depends(get_crop_planning_service)],
):
    """Get crop planning dashboard for a farmer."""
    return await service.get_dashboard(farmer_id)
