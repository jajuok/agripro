"""API Integration tests for Crop Planning (Phase 3.1)."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crop_planning import (
    CropCalendarTemplate,
    CropPlan,
    PlannedActivity,
    InputRequirement,
    IrrigationSchedule,
    CropPlanAlert,
    CropPlanStatus,
    ActivityStatus,
    AlertSeverity,
)
from app.models.farmer import Farmer, FarmProfile, KYCStatus


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def cp_tenant_id():
    """Create a test tenant ID."""
    return uuid.uuid4()


@pytest_asyncio.fixture
async def cp_farmer(db_session: AsyncSession, cp_tenant_id):
    """Create a test farmer for crop planning tests."""
    farmer = Farmer(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=cp_tenant_id,
        first_name="Crop",
        last_name="Planner",
        phone_number="+254712345600",
        email="crop.planner@example.com",
        national_id="CP123456",
        kyc_status=KYCStatus.APPROVED.value,
        kyc_verified_at=datetime.now(timezone.utc),
        county="Nakuru",
        is_active=True,
    )
    db_session.add(farmer)
    await db_session.commit()
    await db_session.refresh(farmer)
    return farmer


@pytest_asyncio.fixture
async def cp_farm(db_session: AsyncSession, cp_farmer):
    """Create a test farm for crop planning tests."""
    farm = FarmProfile(
        id=uuid.uuid4(),
        farmer_id=cp_farmer.id,
        name="Test Farm",
        total_acreage=10.0,
        cultivable_acreage=8.0,
        ownership_type="owned",
        latitude=-0.3031,
        longitude=36.0800,
        county="Nakuru",
        is_verified=True,
        registration_complete=True,
        water_source="borehole",
        irrigation_type="drip",
    )
    db_session.add(farm)
    await db_session.commit()
    await db_session.refresh(farm)
    return farm


@pytest_asyncio.fixture
async def cp_template(db_session: AsyncSession, cp_tenant_id):
    """Create a test crop calendar template."""
    template = CropCalendarTemplate(
        id=uuid.uuid4(),
        tenant_id=cp_tenant_id,
        crop_name="Maize",
        variety="H614D",
        region_type="national",
        region_value=None,
        season="long_rains",
        recommended_planting_start_month=3,
        recommended_planting_end_month=4,
        total_days_to_harvest=140,
        seed_rate_kg_per_acre=10,
        expected_yield_kg_per_acre_min=1500,
        expected_yield_kg_per_acre_max=2500,
        water_requirements_mm=600,
        source="KALRO",
        growth_stages=[
            {
                "name": "Germination",
                "start_day": 0,
                "end_day": 10,
                "activities": [
                    {"activity_type": "planting", "title": "Plant maize seeds", "day_offset": 0}
                ],
            },
            {
                "name": "Vegetative Growth",
                "start_day": 11,
                "end_day": 45,
                "activities": [
                    {"activity_type": "weeding", "title": "First weeding", "day_offset": 10},
                    {"activity_type": "fertilizer_application", "title": "Apply fertilizer", "day_offset": 21},
                ],
            },
            {
                "name": "Tasseling",
                "start_day": 46,
                "end_day": 70,
                "critical_for_yield": True,
                "activities": [],
            },
            {
                "name": "Grain Filling",
                "start_day": 71,
                "end_day": 110,
                "activities": [],
            },
            {
                "name": "Maturation",
                "start_day": 111,
                "end_day": 140,
                "activities": [
                    {"activity_type": "harvesting", "title": "Harvest maize", "day_offset": 25}
                ],
            },
        ],
        fertilizer_requirements={
            "basal": {"type": "DAP", "rate_kg_per_acre": 50},
            "topdress": {"type": "CAN", "rate_kg_per_acre": 50},
        },
        is_active=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest_asyncio.fixture
async def cp_plan(db_session: AsyncSession, cp_farmer, cp_farm, cp_template):
    """Create a test crop plan."""
    plan = CropPlan(
        id=uuid.uuid4(),
        farmer_id=cp_farmer.id,
        farm_id=cp_farm.id,
        template_id=cp_template.id,
        name="Maize Season 2026",
        crop_name="Maize",
        variety="H614D",
        season="long_rains",
        year=2026,
        planned_planting_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
        expected_harvest_date=datetime(2026, 8, 3, tzinfo=timezone.utc),
        planned_acreage=5.0,
        expected_yield_kg=10000,
        status=CropPlanStatus.DRAFT.value,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest_asyncio.fixture
async def cp_activity(db_session: AsyncSession, cp_plan):
    """Create a test planned activity."""
    activity = PlannedActivity(
        id=uuid.uuid4(),
        crop_plan_id=cp_plan.id,
        activity_type="planting",
        title="Plant maize seeds",
        description="Plant maize seeds in prepared rows",
        growth_stage="Germination",
        scheduled_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
        duration_hours=8,
        is_weather_dependent=True,
        weather_conditions_required={"no_rain": True},
        status=ActivityStatus.SCHEDULED.value,
        priority=1,
    )
    db_session.add(activity)
    await db_session.commit()
    await db_session.refresh(activity)
    return activity


# =============================================================================
# Template API Tests
# =============================================================================


class TestCropCalendarTemplatesAPI:
    """Test crop calendar template endpoints."""

    @pytest.mark.asyncio
    async def test_create_template(self, client: AsyncClient, cp_tenant_id):
        """Test creating a new crop calendar template."""
        response = await client.post(
            "/api/v1/crop-planning/templates",
            json={
                "tenant_id": str(cp_tenant_id),
                "crop_name": "Beans",
                "variety": "Rose Coco",
                "region_type": "national",
                "season": "long_rains",
                "recommended_planting_start_month": 3,
                "recommended_planting_end_month": 4,
                "total_days_to_harvest": 90,
                "seed_rate_kg_per_acre": 25,
                "expected_yield_kg_per_acre_min": 400,
                "expected_yield_kg_per_acre_max": 800,
                "source": "KALRO",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["crop_name"] == "Beans"
        assert data["variety"] == "Rose Coco"
        assert data["total_days_to_harvest"] == 90

    @pytest.mark.asyncio
    async def test_list_templates(self, client: AsyncClient, cp_tenant_id, cp_template):
        """Test listing crop calendar templates."""
        response = await client.get(
            "/api/v1/crop-planning/templates",
            params={"tenant_id": str(cp_tenant_id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, client: AsyncClient, cp_tenant_id, cp_template):
        """Test listing templates with crop name filter."""
        response = await client.get(
            "/api/v1/crop-planning/templates",
            params={
                "tenant_id": str(cp_tenant_id),
                "crop_name": "Maize",
                "season": "long_rains",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["crop_name"] == "Maize" for item in data["items"])

    @pytest.mark.asyncio
    async def test_get_template(self, client: AsyncClient, cp_template):
        """Test getting a single template by ID."""
        response = await client.get(f"/api/v1/crop-planning/templates/{cp_template.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(cp_template.id)
        assert data["crop_name"] == "Maize"
        assert data["growth_stages"] is not None
        assert len(data["growth_stages"]) == 5


# =============================================================================
# Crop Plan API Tests
# =============================================================================


class TestCropPlanAPI:
    """Test crop plan endpoints."""

    @pytest.mark.asyncio
    async def test_create_plan(self, client: AsyncClient, cp_farmer, cp_farm, cp_template):
        """Test creating a new crop plan."""
        response = await client.post(
            "/api/v1/crop-planning/plans",
            json={
                "farmer_id": str(cp_farmer.id),
                "farm_id": str(cp_farm.id),
                "template_id": str(cp_template.id),
                "name": "Test Maize Plan",
                "crop_name": "Maize",
                "variety": "H614D",
                "season": "long_rains",
                "year": 2026,
                "planned_planting_date": "2026-03-20T00:00:00Z",
                "planned_acreage": 3.0,
                "generate_activities": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Maize Plan"
        assert data["status"] == "draft"
        assert data["planned_acreage"] == 3.0

    @pytest.mark.asyncio
    async def test_list_plans(self, client: AsyncClient, cp_farmer, cp_plan):
        """Test listing crop plans."""
        response = await client.get(
            "/api/v1/crop-planning/plans",
            params={"farmer_id": str(cp_farmer.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_plan(self, client: AsyncClient, cp_plan):
        """Test getting a crop plan by ID."""
        response = await client.get(f"/api/v1/crop-planning/plans/{cp_plan.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(cp_plan.id)
        assert data["crop_name"] == "Maize"

    @pytest.mark.asyncio
    async def test_update_plan(self, client: AsyncClient, cp_plan):
        """Test updating a crop plan."""
        response = await client.patch(
            f"/api/v1/crop-planning/plans/{cp_plan.id}",
            json={"notes": "Updated notes for the plan"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Updated notes" in data["notes"]

    @pytest.mark.asyncio
    async def test_activate_plan(self, client: AsyncClient, cp_plan):
        """Test activating a crop plan."""
        response = await client.post(
            f"/api/v1/crop-planning/plans/{cp_plan.id}/activate",
            json={
                "actual_planting_date": "2026-03-18T08:00:00Z",
                "actual_planted_acreage": 4.8,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["actual_planted_acreage"] == 4.8

    @pytest.mark.asyncio
    async def test_delete_draft_plan(self, client: AsyncClient, db_session, cp_farmer, cp_farm):
        """Test deleting a draft crop plan."""
        # Create a new draft plan to delete
        plan = CropPlan(
            id=uuid.uuid4(),
            farmer_id=cp_farmer.id,
            farm_id=cp_farm.id,
            name="Plan to Delete",
            crop_name="Wheat",
            season="long_rains",
            year=2026,
            planned_planting_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
            planned_acreage=2.0,
            status=CropPlanStatus.DRAFT.value,
        )
        db_session.add(plan)
        await db_session.commit()

        response = await client.delete(f"/api/v1/crop-planning/plans/{plan.id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_get_plan_statistics(self, client: AsyncClient, cp_plan, cp_activity):
        """Test getting plan statistics."""
        response = await client.get(f"/api/v1/crop-planning/plans/{cp_plan.id}/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == str(cp_plan.id)
        assert data["activities_total"] >= 1


# =============================================================================
# Activity API Tests
# =============================================================================


class TestPlannedActivityAPI:
    """Test planned activity endpoints."""

    @pytest.mark.asyncio
    async def test_create_activity(self, client: AsyncClient, cp_plan):
        """Test creating a new activity."""
        response = await client.post(
            f"/api/v1/crop-planning/plans/{cp_plan.id}/activities",
            json={
                "crop_plan_id": str(cp_plan.id),
                "activity_type": "weeding",
                "title": "First weeding",
                "description": "Remove weeds from the field",
                "scheduled_date": "2026-03-25T08:00:00Z",
                "duration_hours": 6,
                "priority": 2,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "First weeding"
        assert data["activity_type"] == "weeding"

    @pytest.mark.asyncio
    async def test_list_activities(self, client: AsyncClient, cp_plan, cp_activity):
        """Test listing activities for a plan."""
        response = await client.get(f"/api/v1/crop-planning/plans/{cp_plan.id}/activities")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_complete_activity(self, client: AsyncClient, cp_activity):
        """Test completing an activity."""
        response = await client.post(
            f"/api/v1/crop-planning/activities/{cp_activity.id}/complete",
            json={
                "completion_notes": "Completed planting successfully",
                "gps_latitude": -0.3031,
                "gps_longitude": 36.0800,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completion_notes"] is not None

    @pytest.mark.asyncio
    async def test_skip_activity(self, client: AsyncClient, db_session, cp_plan):
        """Test skipping an activity."""
        # Create activity to skip
        activity = PlannedActivity(
            id=uuid.uuid4(),
            crop_plan_id=cp_plan.id,
            activity_type="pesticide_application",
            title="Apply pesticide",
            scheduled_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
            status=ActivityStatus.SCHEDULED.value,
        )
        db_session.add(activity)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/crop-planning/activities/{activity.id}/skip",
            json={"reason": "No pest infestation observed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_get_upcoming_activities(self, client: AsyncClient, cp_farmer, cp_plan, cp_activity):
        """Test getting upcoming activities."""
        response = await client.get(
            "/api/v1/crop-planning/activities/upcoming",
            params={"farmer_id": str(cp_farmer.id), "days_ahead": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


# =============================================================================
# Input Requirements API Tests
# =============================================================================


class TestInputRequirementsAPI:
    """Test input requirement endpoints."""

    @pytest.mark.asyncio
    async def test_create_input(self, client: AsyncClient, cp_plan):
        """Test creating an input requirement."""
        response = await client.post(
            f"/api/v1/crop-planning/plans/{cp_plan.id}/inputs",
            json={
                "crop_plan_id": str(cp_plan.id),
                "category": "seed",
                "name": "H614D Maize Seeds",
                "quantity_required": 50,
                "unit": "kg",
                "is_certified": True,
                "unit_price": 500,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "H614D Maize Seeds"
        assert data["quantity_required"] == 50

    @pytest.mark.asyncio
    async def test_list_inputs(self, client: AsyncClient, db_session, cp_plan):
        """Test listing inputs for a plan."""
        # Create some inputs
        input1 = InputRequirement(
            id=uuid.uuid4(),
            crop_plan_id=cp_plan.id,
            category="seed",
            name="Maize Seeds",
            quantity_required=50,
            unit="kg",
            unit_price=500,
            total_estimated_cost=25000,
        )
        input2 = InputRequirement(
            id=uuid.uuid4(),
            crop_plan_id=cp_plan.id,
            category="fertilizer",
            name="DAP Fertilizer",
            quantity_required=100,
            unit="kg",
            unit_price=100,
            total_estimated_cost=10000,
        )
        db_session.add_all([input1, input2])
        await db_session.commit()

        response = await client.get(f"/api/v1/crop-planning/plans/{cp_plan.id}/inputs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["total_estimated_cost"] == 35000

    @pytest.mark.asyncio
    async def test_calculate_inputs(self, client: AsyncClient, cp_tenant_id, cp_template):
        """Test calculating input requirements."""
        response = await client.get(
            "/api/v1/crop-planning/calculate-inputs",
            params={
                "tenant_id": str(cp_tenant_id),
                "crop_name": "Maize",
                "acreage": 5.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["crop_name"] == "Maize"
        assert data["acreage"] == 5.0
        assert len(data["recommendations"]) > 0


# =============================================================================
# Irrigation API Tests
# =============================================================================


class TestIrrigationAPI:
    """Test irrigation schedule endpoints."""

    @pytest.mark.asyncio
    async def test_create_irrigation(self, client: AsyncClient, cp_plan):
        """Test creating an irrigation schedule."""
        response = await client.post(
            f"/api/v1/crop-planning/plans/{cp_plan.id}/irrigation",
            json={
                "crop_plan_id": str(cp_plan.id),
                "method": "drip",
                "scheduled_date": "2026-03-20T06:00:00Z",
                "scheduled_duration_minutes": 60,
                "water_amount_liters": 5000,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["method"] == "drip"
        assert data["water_amount_liters"] == 5000

    @pytest.mark.asyncio
    async def test_list_irrigation(self, client: AsyncClient, db_session, cp_plan):
        """Test listing irrigation schedules."""
        # Create some schedules
        schedule1 = IrrigationSchedule(
            id=uuid.uuid4(),
            crop_plan_id=cp_plan.id,
            method="drip",
            scheduled_date=datetime(2026, 3, 20, 6, tzinfo=timezone.utc),
            water_amount_liters=5000,
        )
        schedule2 = IrrigationSchedule(
            id=uuid.uuid4(),
            crop_plan_id=cp_plan.id,
            method="drip",
            scheduled_date=datetime(2026, 3, 27, 6, tzinfo=timezone.utc),
            water_amount_liters=5000,
        )
        db_session.add_all([schedule1, schedule2])
        await db_session.commit()

        response = await client.get(f"/api/v1/crop-planning/plans/{cp_plan.id}/irrigation")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["total_water_planned_liters"] == 10000

    @pytest.mark.asyncio
    async def test_generate_irrigation(self, client: AsyncClient, cp_plan):
        """Test generating irrigation schedules."""
        response = await client.post(
            f"/api/v1/crop-planning/plans/{cp_plan.id}/irrigation/generate",
            json={
                "start_date": "2026-03-15T00:00:00Z",
                "end_date": "2026-04-15T00:00:00Z",
                "method": "drip",
                "frequency_days": 7,
                "water_amount_per_event_liters": 5000,
            },
        )
        assert response.status_code == 201
        data = response.json()
        # Should generate ~4-5 schedules for 30 days with 7-day frequency
        assert len(data) >= 4


# =============================================================================
# Alert API Tests
# =============================================================================


class TestAlertAPI:
    """Test alert endpoints."""

    @pytest.mark.asyncio
    async def test_list_alerts(self, client: AsyncClient, db_session, cp_farmer, cp_plan):
        """Test listing alerts for a farmer."""
        # Create some alerts
        alert1 = CropPlanAlert(
            id=uuid.uuid4(),
            farmer_id=cp_farmer.id,
            crop_plan_id=cp_plan.id,
            alert_type="activity_reminder",
            title="Activity Due Tomorrow",
            message="Don't forget to plant maize seeds tomorrow",
            severity=AlertSeverity.INFO.value,
            channels=["in_app"],
        )
        alert2 = CropPlanAlert(
            id=uuid.uuid4(),
            farmer_id=cp_farmer.id,
            crop_plan_id=cp_plan.id,
            alert_type="weather_warning",
            title="Heavy Rain Expected",
            message="Heavy rainfall expected, consider postponing spraying",
            severity=AlertSeverity.WARNING.value,
            channels=["in_app", "push"],
        )
        db_session.add_all([alert1, alert2])
        await db_session.commit()

        response = await client.get(
            "/api/v1/crop-planning/alerts",
            params={"farmer_id": str(cp_farmer.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["unread_count"] == 2

    @pytest.mark.asyncio
    async def test_mark_alert_read(self, client: AsyncClient, db_session, cp_farmer):
        """Test marking an alert as read."""
        alert = CropPlanAlert(
            id=uuid.uuid4(),
            farmer_id=cp_farmer.id,
            alert_type="activity_reminder",
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.INFO.value,
            channels=["in_app"],
        )
        db_session.add(alert)
        await db_session.commit()

        response = await client.post(f"/api/v1/crop-planning/alerts/{alert.id}/read")
        assert response.status_code == 200
        data = response.json()
        assert data["read_at"] is not None


# =============================================================================
# Dashboard API Tests
# =============================================================================


class TestDashboardAPI:
    """Test dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard(self, client: AsyncClient, cp_farmer, cp_plan, cp_activity):
        """Test getting the crop planning dashboard."""
        response = await client.get(
            "/api/v1/crop-planning/dashboard",
            params={"farmer_id": str(cp_farmer.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["farmer_id"] == str(cp_farmer.id)
        assert "active_plans_count" in data
        assert "draft_plans_count" in data
        assert "upcoming_activities" in data
