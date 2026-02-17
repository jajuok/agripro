"""Eligibility Assessment API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.eligibility import (
    AssessmentDecisionRequest,
    AssessmentStatus,
    BatchAssessmentRequest,
    BatchAssessmentResponse,
    # Credit schemas
    CreditCheckRequest,
    CreditCheckResponse,
    EligibilityAssessmentListResponse,
    # Assessment schemas
    EligibilityAssessmentRequest,
    EligibilityAssessmentResponse,
    # Rule schemas
    EligibilityRuleCreate,
    EligibilityRuleGroupCreate,
    EligibilityRuleGroupResponse,
    EligibilityRuleResponse,
    # Scheme schemas
    EligibilitySchemeCreate,
    EligibilitySchemeListResponse,
    EligibilitySchemeResponse,
    EligibilitySchemeUpdate,
    ReviewQueueItemResponse,
    ReviewQueueListResponse,
    # Risk schemas
    RiskAssessmentResponse,
    SchemeEligibilitySummary,
    SchemeStatus,
    WaitlistEntryResponse,
    # Other schemas
    WaitlistResponse,
)
from app.services.credit_service import CreditBureauService
from app.services.eligibility_service import EligibilityService
from app.services.risk_scoring import RiskScoringService

router = APIRouter(prefix="/eligibility", tags=["Eligibility"])


# Dependency to get eligibility service
async def get_eligibility_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EligibilityService:
    return EligibilityService(db)


# =============================================================================
# Scheme Endpoints
# =============================================================================


@router.post(
    "/schemes", response_model=EligibilitySchemeResponse, status_code=status.HTTP_201_CREATED
)
async def create_scheme(
    data: EligibilitySchemeCreate,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Create a new eligibility scheme."""
    # Check for duplicate code
    existing = await service.get_scheme_by_code(data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scheme with code '{data.code}' already exists",
        )

    scheme = await service.create_scheme(data)
    return scheme


@router.get("/schemes", response_model=EligibilitySchemeListResponse)
async def list_schemes(
    tenant_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
    scheme_status: SchemeStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List eligibility schemes for a tenant."""
    items, total = await service.list_schemes(
        tenant_id=tenant_id,
        status=scheme_status,
        page=page,
        page_size=page_size,
    )
    return EligibilitySchemeListResponse(
        items=[EligibilitySchemeResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/schemes/{scheme_id}", response_model=EligibilitySchemeResponse)
async def get_scheme(
    scheme_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Get a scheme by ID."""
    scheme = await service.get_scheme(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )
    return scheme


@router.patch("/schemes/{scheme_id}", response_model=EligibilitySchemeResponse)
async def update_scheme(
    scheme_id: UUID,
    data: EligibilitySchemeUpdate,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Update a scheme."""
    scheme = await service.update_scheme(scheme_id, data)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )
    return scheme


@router.post("/schemes/{scheme_id}/activate", response_model=EligibilitySchemeResponse)
async def activate_scheme(
    scheme_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Activate a scheme to start accepting applications."""
    scheme = await service.activate_scheme(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )
    return scheme


# =============================================================================
# Rule Endpoints
# =============================================================================


@router.post("/rules", response_model=EligibilityRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: EligibilityRuleCreate,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Create a new eligibility rule."""
    # Verify scheme exists
    scheme = await service.get_scheme(data.scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )

    rule = await service.create_rule(data)
    return rule


@router.get("/schemes/{scheme_id}/rules", response_model=list[EligibilityRuleResponse])
async def list_scheme_rules(
    scheme_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """List all rules for a scheme."""
    rules = await service.get_scheme_rules(scheme_id)
    return [EligibilityRuleResponse.model_validate(rule) for rule in rules]


@router.post(
    "/rule-groups", response_model=EligibilityRuleGroupResponse, status_code=status.HTTP_201_CREATED
)
async def create_rule_group(
    data: EligibilityRuleGroupCreate,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Create a new rule group."""
    # Verify scheme exists
    scheme = await service.get_scheme(data.scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )

    group = await service.create_rule_group(data)
    return group


# =============================================================================
# Assessment Endpoints
# =============================================================================


@router.post(
    "/assessments",
    response_model=EligibilityAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assess_eligibility(
    request: EligibilityAssessmentRequest,
    tenant_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Assess farmer eligibility for a scheme."""
    try:
        assessment = await service.assess_eligibility(request, tenant_id)
        return EligibilityAssessmentResponse.model_validate(assessment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/assessments/{assessment_id}", response_model=EligibilityAssessmentResponse)
async def get_assessment(
    assessment_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Get an assessment by ID."""
    assessment = await service.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    return EligibilityAssessmentResponse.model_validate(assessment)


@router.get("/farmers/{farmer_id}/assessments", response_model=EligibilityAssessmentListResponse)
async def list_farmer_assessments(
    farmer_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List assessments for a farmer."""
    items, total = await service.list_farmer_assessments(
        farmer_id=farmer_id,
        page=page,
        page_size=page_size,
    )
    return EligibilityAssessmentListResponse(
        items=[EligibilityAssessmentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/schemes/{scheme_id}/assessments", response_model=EligibilityAssessmentListResponse)
async def list_scheme_assessments(
    scheme_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
    assessment_status: AssessmentStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List assessments for a scheme."""
    items, total = await service.list_scheme_assessments(
        scheme_id=scheme_id,
        status=assessment_status,
        page=page,
        page_size=page_size,
    )
    return EligibilityAssessmentListResponse(
        items=[EligibilityAssessmentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/assessments/{assessment_id}/decision", response_model=EligibilityAssessmentResponse)
async def make_assessment_decision(
    assessment_id: UUID,
    decision: AssessmentDecisionRequest,
    reviewer_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Make a manual decision on an assessment."""
    try:
        assessment = await service.make_decision(assessment_id, decision, reviewer_id)
        return EligibilityAssessmentResponse.model_validate(assessment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =============================================================================
# Review Queue Endpoints
# =============================================================================


@router.get("/review-queue", response_model=ReviewQueueListResponse)
async def get_review_queue(
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
    queue_status: str = Query("pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get the manual review queue."""
    items, total = await service.get_review_queue(
        status=queue_status,
        page=page,
        page_size=page_size,
    )

    # Count pending and overdue
    pending_count = sum(1 for item in items if item.status == "pending")
    overdue_count = sum(1 for item in items if item.is_overdue)

    return ReviewQueueListResponse(
        items=[
            ReviewQueueItemResponse(
                id=item.id,
                assessment_id=item.assessment_id,
                farmer_id=item.assessment.farmer_id,
                farmer_name="",  # Would need to join farmer table
                scheme_id=item.assessment.scheme_id,
                scheme_name="",  # Would need to join scheme table
                priority=item.priority,
                queue_reason=item.queue_reason,
                queue_category=item.queue_category,
                status=item.status,
                assigned_to=item.assigned_to,
                sla_due_at=item.sla_due_at,
                is_overdue=item.is_overdue,
                queued_at=item.queued_at,
            )
            for item in items
        ],
        total=total,
        pending_count=pending_count,
        overdue_count=overdue_count,
    )


# =============================================================================
# Waitlist Endpoints
# =============================================================================


@router.get("/schemes/{scheme_id}/waitlist", response_model=WaitlistResponse)
async def get_scheme_waitlist(
    scheme_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get the waitlist for a scheme."""
    scheme = await service.get_scheme(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )

    items, total = await service.get_scheme_waitlist(
        scheme_id=scheme_id,
        page=page,
        page_size=page_size,
    )

    return WaitlistResponse(
        items=[WaitlistEntryResponse.model_validate(item) for item in items],
        total=total,
        scheme_id=scheme_id,
        scheme_name=scheme.name,
    )


# =============================================================================
# Credit Check Endpoints
# =============================================================================


@router.post(
    "/credit-checks", response_model=CreditCheckResponse, status_code=status.HTTP_201_CREATED
)
async def request_credit_check(
    request: CreditCheckRequest,
    tenant_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request a credit check for a farmer."""
    # Get farmer
    from sqlalchemy import select

    from app.models.farmer import Farmer

    query = select(Farmer).where(Farmer.id == request.farmer_id)
    result = await db.execute(query)
    farmer = result.scalars().first()

    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        )

    credit_service = CreditBureauService(db)
    credit_check = await credit_service.request_credit_check(request, farmer, tenant_id)
    return CreditCheckResponse.model_validate(credit_check)


@router.get("/farmers/{farmer_id}/credit-checks", response_model=list[CreditCheckResponse])
async def get_farmer_credit_history(
    farmer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    """Get credit check history for a farmer."""
    credit_service = CreditBureauService(db)
    checks = await credit_service.get_farmer_credit_history(farmer_id, limit)
    return [CreditCheckResponse.model_validate(check) for check in checks]


# =============================================================================
# Risk Assessment Endpoints
# =============================================================================


@router.get("/farmers/{farmer_id}/risk-assessment", response_model=RiskAssessmentResponse)
async def get_farmer_risk_assessment(
    farmer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the most recent risk assessment for a farmer."""
    risk_service = RiskScoringService(db)
    assessment = await risk_service.get_recent_risk_assessment(farmer_id)

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent risk assessment found",
        )

    return RiskAssessmentResponse.model_validate(assessment)


@router.get("/farmers/{farmer_id}/risk-history", response_model=list[RiskAssessmentResponse])
async def get_farmer_risk_history(
    farmer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    """Get risk assessment history for a farmer."""
    risk_service = RiskScoringService(db)
    assessments = await risk_service.get_farmer_risk_history(farmer_id, limit)
    return [RiskAssessmentResponse.model_validate(a) for a in assessments]


# =============================================================================
# Analytics Endpoints
# =============================================================================


@router.get("/schemes/{scheme_id}/summary", response_model=SchemeEligibilitySummary)
async def get_scheme_eligibility_summary(
    scheme_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """Get eligibility statistics summary for a scheme."""
    try:
        summary = await service.get_scheme_summary(scheme_id)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# Batch Operations
# =============================================================================


@router.post("/assessments/batch", response_model=BatchAssessmentResponse)
async def batch_assess_eligibility(
    request: BatchAssessmentRequest,
    tenant_id: UUID,
    service: Annotated[EligibilityService, Depends(get_eligibility_service)],
):
    """
    Batch assess multiple farmers for a scheme.

    This endpoint processes farmers either by explicit IDs or by filter criteria.
    """
    if not request.farmer_ids and not request.filters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either farmer_ids or filters",
        )

    # This would be implemented with background task processing
    # For now, return a placeholder response
    return BatchAssessmentResponse(
        total_processed=0,
        eligible_count=0,
        not_eligible_count=0,
        error_count=0,
        assessment_ids=[],
    )
