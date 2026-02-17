"""Crop Planning Service (Phase 3.1)."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.crop_planning import (
    ActivityStatus,
    AlertSeverity,
    AlertType,
    CropCalendarTemplate,
    CropPlan,
    CropPlanAlert,
    CropPlanStatus,
    InputRequirement,
    IrrigationSchedule,
    IrrigationStatus,
    PlannedActivity,
    ProcurementStatus,
)
from app.models.farmer import Farmer, FarmProfile
from app.schemas.crop_planning import (
    ActivityCompletion,
    ActivitySkip,
    ActivityType,
    CropCalendarTemplateCreate,
    CropCalendarTemplateUpdate,
    CropPlanActivate,
    CropPlanAdvanceStage,
    CropPlanAlertResponse,
    CropPlanComplete,
    CropPlanCreate,
    CropPlanningDashboard,
    CropPlanStatistics,
    CropPlanUpdate,
    InputCalculation,
    InputCategory,
    InputRequirementCreate,
    InputRequirementUpdate,
    IrrigationCompletion,
    IrrigationGenerateRequest,
    IrrigationScheduleCreate,
    IrrigationScheduleUpdate,
    PlannedActivityCreate,
    PlannedActivityResponse,
    PlannedActivityUpdate,
    QrCodeVerification,
    QrCodeVerificationResult,
    Season,
    UpcomingActivity,
)


class CropPlanningService:
    """Service for crop planning operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Crop Calendar Templates
    # =========================================================================

    async def create_template(self, data: CropCalendarTemplateCreate) -> CropCalendarTemplate:
        """Create a new crop calendar template."""
        template = CropCalendarTemplate(
            tenant_id=data.tenant_id,
            crop_name=data.crop_name,
            variety=data.variety,
            region_type=data.region_type,
            region_value=data.region_value,
            season=data.season.value,
            recommended_planting_start_month=data.recommended_planting_start_month,
            recommended_planting_end_month=data.recommended_planting_end_month,
            total_days_to_harvest=data.total_days_to_harvest,
            growth_stages=[s.model_dump() for s in data.growth_stages]
            if data.growth_stages
            else None,
            seed_rate_kg_per_acre=data.seed_rate_kg_per_acre,
            fertilizer_requirements=data.fertilizer_requirements,
            expected_yield_kg_per_acre_min=data.expected_yield_kg_per_acre_min,
            expected_yield_kg_per_acre_max=data.expected_yield_kg_per_acre_max,
            water_requirements_mm=data.water_requirements_mm,
            critical_water_stages=data.critical_water_stages,
            source=data.source,
            source_url=data.source_url,
        )
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def get_template(self, template_id: uuid.UUID) -> CropCalendarTemplate | None:
        """Get template by ID."""
        query = select(CropCalendarTemplate).where(CropCalendarTemplate.id == template_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_templates(
        self,
        tenant_id: uuid.UUID,
        crop_name: str | None = None,
        region: str | None = None,
        season: Season | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CropCalendarTemplate], int]:
        """List templates with filters."""
        query = select(CropCalendarTemplate).where(
            and_(
                CropCalendarTemplate.tenant_id == tenant_id,
                CropCalendarTemplate.is_active == True,
            )
        )

        if crop_name:
            query = query.where(CropCalendarTemplate.crop_name.ilike(f"%{crop_name}%"))
        if region:
            query = query.where(CropCalendarTemplate.region_value == region)
        if season:
            query = query.where(CropCalendarTemplate.season == season.value)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(CropCalendarTemplate.crop_name)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def recommend_template(
        self,
        tenant_id: uuid.UUID,
        farm_id: uuid.UUID,
        crop_name: str,
        planned_date: datetime,
    ) -> list[CropCalendarTemplate]:
        """Recommend templates based on farm location and timing."""
        # Get farm details
        farm = await self._get_farm(farm_id)
        if not farm:
            return []

        # Determine season from planned date
        month = planned_date.month
        if 3 <= month <= 5:
            season = Season.LONG_RAINS
        elif 10 <= month <= 12:
            season = Season.SHORT_RAINS
        else:
            season = Season.IRRIGATED

        # Find matching templates
        query = select(CropCalendarTemplate).where(
            and_(
                CropCalendarTemplate.tenant_id == tenant_id,
                CropCalendarTemplate.is_active == True,
                CropCalendarTemplate.crop_name.ilike(f"%{crop_name}%"),
                or_(
                    CropCalendarTemplate.season == season.value,
                    CropCalendarTemplate.season == Season.IRRIGATED.value,
                ),
            )
        )

        # Prioritize templates matching farm's region
        if farm.county:
            query = query.order_by(
                # Templates with matching county first
                (CropCalendarTemplate.region_value == farm.county).desc(),
                CropCalendarTemplate.crop_name,
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_template(
        self, template_id: uuid.UUID, data: CropCalendarTemplateUpdate
    ) -> CropCalendarTemplate | None:
        """Update a template."""
        template = await self.get_template(template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(template, field):
                if field == "season" and value:
                    value = value.value
                elif field == "growth_stages" and value:
                    value = [s.model_dump() for s in value]
                setattr(template, field, value)

        await self.db.flush()
        await self.db.refresh(template)
        return template

    # =========================================================================
    # Crop Plans
    # =========================================================================

    async def create_plan(self, data: CropPlanCreate) -> CropPlan:
        """Create a new crop plan."""
        # Calculate expected harvest date if template provided
        expected_harvest = data.expected_harvest_date
        template = None
        if data.template_id:
            template = await self.get_template(data.template_id)
            if template and not expected_harvest:
                expected_harvest = data.planned_planting_date + timedelta(
                    days=template.total_days_to_harvest
                )

        plan = CropPlan(
            farmer_id=data.farmer_id,
            farm_id=data.farm_id,
            template_id=data.template_id,
            name=data.name,
            crop_name=data.crop_name,
            variety=data.variety,
            season=data.season.value,
            year=data.year,
            planned_planting_date=data.planned_planting_date,
            expected_harvest_date=expected_harvest,
            planned_acreage=data.planned_acreage,
            expected_yield_kg=data.expected_yield_kg,
            notes=data.notes,
            status=CropPlanStatus.DRAFT.value,
        )
        self.db.add(plan)
        await self.db.flush()

        # Auto-generate activities from template if requested
        if data.generate_activities and template:
            await self._generate_activities_from_template(plan, template)

        # Calculate estimated input costs
        if template:
            await self._calculate_input_requirements(plan, template)

        await self.db.refresh(plan)
        return plan

    async def _generate_activities_from_template(
        self, plan: CropPlan, template: CropCalendarTemplate
    ) -> None:
        """Generate planned activities from template growth stages."""
        if not template.growth_stages:
            return

        for stage in template.growth_stages:
            stage_start_day = stage.get("start_day", 0)
            stage_name = stage.get("name", "Unknown")

            for activity_def in stage.get("activities", []):
                day_offset = stage_start_day + activity_def.get("day_offset", 0)
                scheduled_date = plan.planned_planting_date + timedelta(days=day_offset)

                activity = PlannedActivity(
                    crop_plan_id=plan.id,
                    activity_type=activity_def.get("activity_type", ActivityType.OTHER.value),
                    title=activity_def.get("title", "Activity"),
                    description=activity_def.get("description"),
                    growth_stage=stage_name,
                    scheduled_date=scheduled_date,
                    duration_hours=activity_def.get("duration_hours"),
                    is_weather_dependent=activity_def.get("is_weather_dependent", False),
                    weather_conditions_required=activity_def.get("weather_conditions"),
                )
                self.db.add(activity)

    async def _calculate_input_requirements(
        self, plan: CropPlan, template: CropCalendarTemplate
    ) -> None:
        """Calculate and create input requirements from template."""
        total_cost = 0.0

        # Seeds
        if template.seed_rate_kg_per_acre:
            seed_qty = template.seed_rate_kg_per_acre * plan.planned_acreage
            seed_input = InputRequirement(
                crop_plan_id=plan.id,
                category=InputCategory.SEED.value,
                name=f"{plan.crop_name} Seeds",
                quantity_required=seed_qty,
                unit="kg",
                quantity_per_acre=template.seed_rate_kg_per_acre,
                application_stage="Planting",
            )
            self.db.add(seed_input)

        # Fertilizers
        if template.fertilizer_requirements:
            for fert_type, fert_data in template.fertilizer_requirements.items():
                if isinstance(fert_data, dict):
                    rate = fert_data.get("rate_kg_per_acre", 0)
                    fert_qty = rate * plan.planned_acreage
                    fert_input = InputRequirement(
                        crop_plan_id=plan.id,
                        category=InputCategory.FERTILIZER.value,
                        name=fert_data.get("type", fert_type),
                        quantity_required=fert_qty,
                        unit="kg",
                        quantity_per_acre=rate,
                        application_stage=fert_type.replace("_", " ").title(),
                    )
                    self.db.add(fert_input)

    async def get_plan(self, plan_id: uuid.UUID) -> CropPlan | None:
        """Get crop plan by ID with relationships."""
        query = (
            select(CropPlan)
            .options(
                selectinload(CropPlan.activities),
                selectinload(CropPlan.input_requirements),
                selectinload(CropPlan.irrigation_schedules),
            )
            .where(CropPlan.id == plan_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_plans(
        self,
        farmer_id: uuid.UUID | None = None,
        farm_id: uuid.UUID | None = None,
        status: CropPlanStatus | None = None,
        season: Season | None = None,
        year: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CropPlan], int]:
        """List crop plans with filters."""
        query = select(CropPlan).options(selectinload(CropPlan.activities))

        conditions = []
        if farmer_id:
            conditions.append(CropPlan.farmer_id == farmer_id)
        if farm_id:
            conditions.append(CropPlan.farm_id == farm_id)
        if status:
            conditions.append(CropPlan.status == status.value)
        if season:
            conditions.append(CropPlan.season == season.value)
        if year:
            conditions.append(CropPlan.year == year)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total (without eager loading for efficiency)
        count_base = select(CropPlan)
        if conditions:
            count_base = count_base.where(and_(*conditions))
        count_query = select(func.count()).select_from(count_base.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(CropPlan.created_at.desc())

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_plan(self, plan_id: uuid.UUID, data: CropPlanUpdate) -> CropPlan | None:
        """Update a crop plan."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(plan, field):
                if field == "status" and value:
                    value = value.value
                setattr(plan, field, value)

        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def activate_plan(self, plan_id: uuid.UUID, data: CropPlanActivate) -> CropPlan | None:
        """Activate a crop plan (start planting)."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        if plan.status != CropPlanStatus.DRAFT.value:
            raise ValueError(f"Can only activate draft plans, current status: {plan.status}")

        plan.status = CropPlanStatus.ACTIVE.value
        plan.actual_planting_date = data.actual_planting_date or datetime.now(UTC)
        if data.actual_planted_acreage:
            plan.actual_planted_acreage = data.actual_planted_acreage

        # Set initial growth stage
        template = await self.get_template(plan.template_id) if plan.template_id else None
        if template and template.growth_stages:
            first_stage = template.growth_stages[0]
            plan.current_growth_stage = first_stage.get("name")
            plan.current_growth_stage_start = datetime.now(UTC)
            plan.growth_stage_history = [
                {
                    "stage": first_stage.get("name"),
                    "started_at": datetime.now(UTC).isoformat(),
                }
            ]

        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def advance_stage(
        self, plan_id: uuid.UUID, data: CropPlanAdvanceStage
    ) -> CropPlan | None:
        """Advance crop plan to next growth stage."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        if plan.status != CropPlanStatus.ACTIVE.value:
            raise ValueError("Can only advance active plans")

        # Update growth stage history
        history = plan.growth_stage_history or []
        if history and plan.current_growth_stage:
            history[-1]["ended_at"] = datetime.now(UTC).isoformat()

        history.append(
            {
                "stage": data.new_stage,
                "started_at": datetime.now(UTC).isoformat(),
                "notes": data.notes,
            }
        )

        plan.current_growth_stage = data.new_stage
        plan.current_growth_stage_start = datetime.now(UTC)
        plan.growth_stage_history = history

        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def complete_plan(self, plan_id: uuid.UUID, data: CropPlanComplete) -> CropPlan | None:
        """Complete a crop plan (harvest done)."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return None

        plan.status = CropPlanStatus.COMPLETED.value
        plan.actual_harvest_date = data.actual_harvest_date
        plan.actual_yield_kg = data.actual_yield_kg
        if data.notes:
            plan.notes = (plan.notes or "") + f"\n\nCompletion notes: {data.notes}"

        # Calculate actual total cost from inputs
        cost_query = select(func.sum(InputRequirement.actual_cost)).where(
            InputRequirement.crop_plan_id == plan_id
        )
        result = await self.db.execute(cost_query)
        plan.actual_total_cost = result.scalar()

        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def delete_plan(self, plan_id: uuid.UUID) -> bool:
        """Delete a crop plan (only drafts)."""
        plan = await self.get_plan(plan_id)
        if not plan:
            return False

        if plan.status != CropPlanStatus.DRAFT.value:
            raise ValueError("Can only delete draft plans")

        await self.db.delete(plan)
        await self.db.flush()
        return True

    # =========================================================================
    # Planned Activities
    # =========================================================================

    async def create_activity(self, data: PlannedActivityCreate) -> PlannedActivity:
        """Create a new planned activity."""
        activity = PlannedActivity(
            crop_plan_id=data.crop_plan_id,
            activity_type=data.activity_type.value,
            title=data.title,
            description=data.description,
            growth_stage=data.growth_stage,
            scheduled_date=data.scheduled_date,
            scheduled_end_date=data.scheduled_end_date,
            duration_hours=data.duration_hours,
            earliest_date=data.earliest_date,
            latest_date=data.latest_date,
            is_weather_dependent=data.is_weather_dependent,
            weather_conditions_required=data.weather_conditions_required,
            estimated_cost=data.estimated_cost,
            priority=data.priority,
            reminder_days_before=data.reminder_days_before,
        )
        self.db.add(activity)
        await self.db.flush()
        await self.db.refresh(activity)
        return activity

    async def get_activity(self, activity_id: uuid.UUID) -> PlannedActivity | None:
        """Get activity by ID."""
        query = select(PlannedActivity).where(PlannedActivity.id == activity_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_activities(
        self,
        crop_plan_id: uuid.UUID,
        status: ActivityStatus | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PlannedActivity], int]:
        """List activities for a crop plan."""
        query = select(PlannedActivity).where(PlannedActivity.crop_plan_id == crop_plan_id)

        if status:
            query = query.where(PlannedActivity.status == status.value)
        if from_date:
            query = query.where(PlannedActivity.scheduled_date >= from_date)
        if to_date:
            query = query.where(PlannedActivity.scheduled_date <= to_date)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(PlannedActivity.scheduled_date)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_activity(
        self, activity_id: uuid.UUID, data: PlannedActivityUpdate
    ) -> PlannedActivity | None:
        """Update an activity."""
        activity = await self.get_activity(activity_id)
        if not activity:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(activity, field):
                if field == "status" and value:
                    value = value.value
                setattr(activity, field, value)

        await self.db.flush()
        await self.db.refresh(activity)
        return activity

    async def complete_activity(
        self, activity_id: uuid.UUID, data: ActivityCompletion
    ) -> PlannedActivity | None:
        """Mark activity as completed."""
        activity = await self.get_activity(activity_id)
        if not activity:
            return None

        activity.status = ActivityStatus.COMPLETED.value
        activity.completed_at = datetime.now(UTC)
        activity.actual_date = data.actual_date or datetime.now(UTC)
        activity.completion_notes = data.completion_notes
        activity.completion_photos = data.completion_photos
        activity.gps_latitude = data.gps_latitude
        activity.gps_longitude = data.gps_longitude
        activity.inputs_used = data.inputs_used
        activity.actual_cost = data.actual_cost

        await self.db.flush()
        await self.db.refresh(activity)
        return activity

    async def skip_activity(
        self, activity_id: uuid.UUID, data: ActivitySkip
    ) -> PlannedActivity | None:
        """Skip an activity with reason."""
        activity = await self.get_activity(activity_id)
        if not activity:
            return None

        activity.status = ActivityStatus.SKIPPED.value
        activity.completion_notes = f"Skipped: {data.reason}"
        activity.completed_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(activity)
        return activity

    async def get_upcoming_activities(
        self, farmer_id: uuid.UUID, days_ahead: int = 7
    ) -> list[UpcomingActivity]:
        """Get upcoming activities for a farmer."""
        now = datetime.now(UTC)
        end_date = now + timedelta(days=days_ahead)

        # Get active plans for farmer
        plans_query = select(CropPlan).where(
            and_(
                CropPlan.farmer_id == farmer_id,
                CropPlan.status == CropPlanStatus.ACTIVE.value,
            )
        )
        plans_result = await self.db.execute(plans_query)
        plans = {p.id: p for p in plans_result.scalars().all()}

        if not plans:
            return []

        # Get upcoming activities
        query = (
            select(PlannedActivity)
            .where(
                and_(
                    PlannedActivity.crop_plan_id.in_(plans.keys()),
                    PlannedActivity.status.in_(
                        [
                            ActivityStatus.SCHEDULED.value,
                            ActivityStatus.OVERDUE.value,
                        ]
                    ),
                    PlannedActivity.scheduled_date <= end_date,
                )
            )
            .order_by(PlannedActivity.scheduled_date)
            .limit(20)
        )
        result = await self.db.execute(query)
        activities = result.scalars().all()

        # Build response with context
        upcoming = []
        for activity in activities:
            plan = plans.get(activity.crop_plan_id)
            if not plan:
                continue

            farm = await self._get_farm(plan.farm_id)
            days_until = (activity.scheduled_date.date() - now.date()).days
            is_overdue = days_until < 0

            upcoming.append(
                UpcomingActivity(
                    activity=PlannedActivityResponse.model_validate(activity),
                    plan_id=plan.id,
                    plan_name=plan.name,
                    crop_name=plan.crop_name,
                    farm_name=farm.name if farm else "Unknown",
                    days_until=days_until,
                    is_overdue=is_overdue,
                )
            )

        return upcoming

    # =========================================================================
    # Input Requirements
    # =========================================================================

    async def create_input(self, data: InputRequirementCreate) -> InputRequirement:
        """Create input requirement."""
        total_cost = None
        if data.unit_price and data.quantity_required:
            total_cost = data.unit_price * data.quantity_required

        input_req = InputRequirement(
            crop_plan_id=data.crop_plan_id,
            category=data.category.value,
            name=data.name,
            brand=data.brand,
            is_certified=data.is_certified,
            certification_number=data.certification_number,
            quantity_required=data.quantity_required,
            unit=data.unit,
            quantity_per_acre=data.quantity_per_acre,
            application_stage=data.application_stage,
            application_date=data.application_date,
            application_method=data.application_method,
            unit_price=data.unit_price,
            total_estimated_cost=total_cost,
            supplier_name=data.supplier_name,
            notes=data.notes,
        )
        self.db.add(input_req)
        await self.db.flush()
        await self.db.refresh(input_req)
        return input_req

    async def get_input(self, input_id: uuid.UUID) -> InputRequirement | None:
        """Get input by ID."""
        query = select(InputRequirement).where(InputRequirement.id == input_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_inputs(
        self, crop_plan_id: uuid.UUID
    ) -> tuple[list[InputRequirement], float | None, float | None]:
        """List inputs for a crop plan with totals."""
        query = (
            select(InputRequirement)
            .where(InputRequirement.crop_plan_id == crop_plan_id)
            .order_by(InputRequirement.category, InputRequirement.name)
        )

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Calculate totals
        total_estimated = sum(i.total_estimated_cost or 0 for i in items)
        total_actual = sum(i.actual_cost or 0 for i in items)

        return (
            items,
            total_estimated if total_estimated > 0 else None,
            total_actual if total_actual > 0 else None,
        )

    async def update_input(
        self, input_id: uuid.UUID, data: InputRequirementUpdate
    ) -> InputRequirement | None:
        """Update input requirement."""
        input_req = await self.get_input(input_id)
        if not input_req:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(input_req, field):
                if field == "procurement_status" and value:
                    value = value.value
                setattr(input_req, field, value)

        # Recalculate total if prices changed
        if input_req.unit_price and input_req.quantity_required:
            input_req.total_estimated_cost = input_req.unit_price * input_req.quantity_required

        # Calculate remaining
        if input_req.quantity_used is not None:
            input_req.quantity_remaining = input_req.quantity_required - input_req.quantity_used

        await self.db.flush()
        await self.db.refresh(input_req)
        return input_req

    async def verify_input_qr(
        self, input_id: uuid.UUID, data: QrCodeVerification
    ) -> QrCodeVerificationResult:
        """Verify input product via QR code."""
        input_req = await self.get_input(input_id)
        if not input_req:
            raise ValueError(f"Input not found: {input_id}")

        # In a real implementation, this would call an external verification API
        # For now, we'll simulate verification based on QR data
        qr_data = data.qr_code_data

        # Simulate verification (in production, call actual verification service)
        verified = qr_data.get("valid", True)
        result = QrCodeVerificationResult(
            verified=verified,
            product_name=qr_data.get("product_name"),
            manufacturer=qr_data.get("manufacturer"),
            batch_number=qr_data.get("batch_number"),
            expiry_date=qr_data.get("expiry_date"),
            certification_status="certified" if verified else "unknown",
            warnings=qr_data.get("warnings"),
        )

        # Update input record
        input_req.qr_code_verified = verified
        input_req.qr_code_data = qr_data
        input_req.qr_verified_at = datetime.now(UTC)

        await self.db.flush()
        return result

    async def calculate_inputs(
        self, crop_name: str, variety: str | None, acreage: float, tenant_id: uuid.UUID
    ) -> InputCalculation:
        """Calculate input requirements based on crop and acreage."""
        # Find matching template
        templates, _ = await self.list_templates(
            tenant_id=tenant_id,
            crop_name=crop_name,
            page_size=1,
        )

        recommendations = []
        total_cost = 0.0
        source = None

        if templates:
            template = templates[0]
            source = template.source

            # Seed calculation
            if template.seed_rate_kg_per_acre:
                seed_qty = template.seed_rate_kg_per_acre * acreage
                recommendations.append(
                    InputRequirementBase(
                        category=InputCategory.SEED,
                        name=f"{crop_name} Seeds",
                        quantity_required=seed_qty,
                        unit="kg",
                    )
                )

            # Fertilizer calculations
            if template.fertilizer_requirements:
                for fert_type, fert_data in template.fertilizer_requirements.items():
                    if isinstance(fert_data, dict):
                        rate = fert_data.get("rate_kg_per_acre", 0)
                        fert_qty = rate * acreage
                        recommendations.append(
                            InputRequirementBase(
                                category=InputCategory.FERTILIZER,
                                name=fert_data.get("type", fert_type),
                                quantity_required=fert_qty,
                                unit="kg",
                            )
                        )

        return InputCalculation(
            crop_name=crop_name,
            variety=variety,
            acreage=acreage,
            recommendations=recommendations,
            total_estimated_cost=total_cost if total_cost > 0 else None,
            source=source,
        )

    # =========================================================================
    # Irrigation Schedules
    # =========================================================================

    async def create_irrigation(self, data: IrrigationScheduleCreate) -> IrrigationSchedule:
        """Create irrigation schedule."""
        schedule = IrrigationSchedule(
            crop_plan_id=data.crop_plan_id,
            method=data.method.value,
            scheduled_date=data.scheduled_date,
            scheduled_duration_minutes=data.scheduled_duration_minutes,
            water_amount_liters=data.water_amount_liters,
            water_amount_mm=data.water_amount_mm,
            growth_stage=data.growth_stage,
            is_deficit_irrigation=data.is_deficit_irrigation,
            deficit_percentage=data.deficit_percentage,
            notes=data.notes,
        )
        self.db.add(schedule)
        await self.db.flush()
        await self.db.refresh(schedule)
        return schedule

    async def get_irrigation(self, schedule_id: uuid.UUID) -> IrrigationSchedule | None:
        """Get irrigation schedule by ID."""
        query = select(IrrigationSchedule).where(IrrigationSchedule.id == schedule_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_irrigation(
        self, crop_plan_id: uuid.UUID
    ) -> tuple[list[IrrigationSchedule], float | None, float | None]:
        """List irrigation schedules for a crop plan."""
        query = (
            select(IrrigationSchedule)
            .where(IrrigationSchedule.crop_plan_id == crop_plan_id)
            .order_by(IrrigationSchedule.scheduled_date)
        )

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # Calculate totals
        total_planned = sum(i.water_amount_liters or 0 for i in items)
        total_used = sum(
            i.actual_water_used_liters or 0
            for i in items
            if i.status == IrrigationStatus.COMPLETED.value
        )

        return (
            items,
            total_planned if total_planned > 0 else None,
            total_used if total_used > 0 else None,
        )

    async def update_irrigation(
        self, schedule_id: uuid.UUID, data: IrrigationScheduleUpdate
    ) -> IrrigationSchedule | None:
        """Update irrigation schedule."""
        schedule = await self.get_irrigation(schedule_id)
        if not schedule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(schedule, field):
                if field in ("method", "status") and value:
                    value = value.value
                setattr(schedule, field, value)

        await self.db.flush()
        await self.db.refresh(schedule)
        return schedule

    async def complete_irrigation(
        self, schedule_id: uuid.UUID, data: IrrigationCompletion
    ) -> IrrigationSchedule | None:
        """Mark irrigation as completed."""
        schedule = await self.get_irrigation(schedule_id)
        if not schedule:
            return None

        schedule.status = IrrigationStatus.COMPLETED.value
        schedule.actual_date = data.actual_date or datetime.now(UTC)
        schedule.actual_duration_minutes = data.actual_duration_minutes
        schedule.actual_water_used_liters = data.actual_water_used_liters
        schedule.soil_moisture_before = data.soil_moisture_before
        schedule.soil_moisture_after = data.soil_moisture_after
        if data.notes:
            schedule.notes = data.notes

        await self.db.flush()
        await self.db.refresh(schedule)
        return schedule

    async def generate_irrigation_schedule(
        self, crop_plan_id: uuid.UUID, data: IrrigationGenerateRequest
    ) -> list[IrrigationSchedule]:
        """Auto-generate irrigation schedules."""
        plan = await self.get_plan(crop_plan_id)
        if not plan:
            raise ValueError(f"Crop plan not found: {crop_plan_id}")

        schedules = []
        current_date = data.start_date

        while current_date <= data.end_date:
            schedule = IrrigationSchedule(
                crop_plan_id=crop_plan_id,
                method=data.method.value,
                scheduled_date=current_date,
                water_amount_liters=data.water_amount_per_event_liters,
            )
            self.db.add(schedule)
            schedules.append(schedule)
            current_date += timedelta(days=data.frequency_days)

        await self.db.flush()
        for s in schedules:
            await self.db.refresh(s)
        return schedules

    # =========================================================================
    # Alerts
    # =========================================================================

    async def create_alert(
        self,
        farmer_id: uuid.UUID,
        alert_type: AlertType,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        crop_plan_id: uuid.UUID | None = None,
        activity_id: uuid.UUID | None = None,
        data: dict | None = None,
    ) -> CropPlanAlert:
        """Create a crop plan alert."""
        alert = CropPlanAlert(
            farmer_id=farmer_id,
            crop_plan_id=crop_plan_id,
            activity_id=activity_id,
            alert_type=alert_type.value,
            title=title,
            message=message,
            severity=severity.value,
            data=data,
            channels=["in_app", "push"],
        )
        self.db.add(alert)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def list_alerts(
        self, farmer_id: uuid.UUID, unread_only: bool = False, page: int = 1, page_size: int = 20
    ) -> tuple[list[CropPlanAlert], int, int]:
        """List alerts for a farmer."""
        query = select(CropPlanAlert).where(CropPlanAlert.farmer_id == farmer_id)

        if unread_only:
            query = query.where(CropPlanAlert.read_at == None)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Count unread
        unread_query = select(func.count()).where(
            and_(
                CropPlanAlert.farmer_id == farmer_id,
                CropPlanAlert.read_at == None,
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread = unread_result.scalar() or 0

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.order_by(CropPlanAlert.created_at.desc())

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total, unread

    async def mark_alert_read(self, alert_id: uuid.UUID) -> CropPlanAlert | None:
        """Mark alert as read."""
        query = select(CropPlanAlert).where(CropPlanAlert.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalars().first()

        if alert:
            alert.read_at = datetime.now(UTC)
            await self.db.flush()

        return alert

    async def dismiss_alert(self, alert_id: uuid.UUID) -> CropPlanAlert | None:
        """Dismiss an alert."""
        query = select(CropPlanAlert).where(CropPlanAlert.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalars().first()

        if alert:
            alert.dismissed_at = datetime.now(UTC)
            await self.db.flush()

        return alert

    # =========================================================================
    # Dashboard & Statistics
    # =========================================================================

    async def get_plan_statistics(self, plan_id: uuid.UUID) -> CropPlanStatistics:
        """Get statistics for a crop plan."""
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        # Activity counts
        activities = plan.activities or []
        total = len(activities)
        completed = sum(1 for a in activities if a.status == ActivityStatus.COMPLETED.value)
        pending = sum(1 for a in activities if a.status == ActivityStatus.SCHEDULED.value)
        overdue = sum(1 for a in activities if a.status == ActivityStatus.OVERDUE.value)

        # Days calculation
        days_since_planting = None
        days_to_harvest = None
        now = datetime.now(UTC)

        if plan.actual_planting_date:
            planting = plan.actual_planting_date
            if planting.tzinfo is None:
                planting = planting.replace(tzinfo=UTC)
            days_since_planting = (now - planting).days

        if plan.expected_harvest_date:
            harvest = plan.expected_harvest_date
            if harvest.tzinfo is None:
                harvest = harvest.replace(tzinfo=UTC)
            days_to_harvest = (harvest - now).days

        # Cost calculation
        inputs, estimated_cost, actual_cost = await self.list_inputs(plan_id)
        cost_variance = None
        if estimated_cost and actual_cost:
            cost_variance = actual_cost - estimated_cost

        # Procurement percentage
        inputs_procured = sum(
            1
            for i in inputs
            if i.procurement_status
            in [ProcurementStatus.RECEIVED.value, ProcurementStatus.APPLIED.value]
        )
        inputs_procured_pct = (inputs_procured / len(inputs) * 100) if inputs else None

        return CropPlanStatistics(
            plan_id=plan_id,
            days_since_planting=days_since_planting,
            days_to_harvest=days_to_harvest,
            activities_total=total,
            activities_completed=completed,
            activities_pending=pending,
            activities_overdue=overdue,
            completion_percentage=(completed / total * 100) if total > 0 else 0,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost,
            cost_variance=cost_variance,
            inputs_procured_percentage=inputs_procured_pct,
        )

    async def get_dashboard(self, farmer_id: uuid.UUID) -> CropPlanningDashboard:
        """Get crop planning dashboard for a farmer."""
        now = datetime.now(UTC)

        # Count plans by status
        plans, _ = await self.list_plans(farmer_id=farmer_id, page_size=100)

        active_count = sum(1 for p in plans if p.status == CropPlanStatus.ACTIVE.value)
        draft_count = sum(1 for p in plans if p.status == CropPlanStatus.DRAFT.value)
        completed_count = sum(1 for p in plans if p.status == CropPlanStatus.COMPLETED.value)

        # Calculate total acreage
        total_acreage = sum(
            p.planned_acreage for p in plans if p.status == CropPlanStatus.ACTIVE.value
        )

        # Get upcoming activities
        upcoming = await self.get_upcoming_activities(farmer_id, days_ahead=7)

        # Count activities
        activities_today = sum(1 for a in upcoming if a.days_until == 0)
        activities_overdue = sum(1 for a in upcoming if a.is_overdue)
        activities_this_week = len(upcoming)

        # Get alerts
        alerts, _, unread = await self.list_alerts(farmer_id, page_size=5)

        return CropPlanningDashboard(
            farmer_id=farmer_id,
            active_plans_count=active_count,
            draft_plans_count=draft_count,
            completed_plans_count=completed_count,
            total_planned_acreage=total_acreage,
            activities_today=activities_today,
            activities_overdue=activities_overdue,
            activities_this_week=activities_this_week,
            upcoming_activities=upcoming[:5],
            alerts_unread=unread,
            recent_alerts=[CropPlanAlertResponse.model_validate(a) for a in alerts],
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_farmer(self, farmer_id: uuid.UUID) -> Farmer | None:
        """Get farmer by ID."""
        query = select(Farmer).where(Farmer.id == farmer_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def _get_farm(self, farm_id: uuid.UUID) -> FarmProfile | None:
        """Get farm by ID."""
        query = select(FarmProfile).where(FarmProfile.id == farm_id)
        result = await self.db.execute(query)
        return result.scalars().first()


# Import the base schema for input calculations
from app.schemas.crop_planning import InputRequirementBase
