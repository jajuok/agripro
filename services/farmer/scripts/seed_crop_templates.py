"""Seed crop calendar templates for common Kenyan crops.

Run with: python -m scripts.seed_crop_templates
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.crop_planning import CropCalendarTemplate


# Default tenant ID for seeding (replace with actual tenant in production)
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


CROP_TEMPLATES = [
    # ==========================================================================
    # MAIZE TEMPLATES
    # ==========================================================================
    {
        "crop_name": "Maize",
        "variety": "H614D",
        "region_type": "national",
        "region_value": None,
        "season": "long_rains",
        "recommended_planting_start_month": 3,
        "recommended_planting_end_month": 4,
        "total_days_to_harvest": 140,
        "seed_rate_kg_per_acre": 10,
        "expected_yield_kg_per_acre_min": 1500,
        "expected_yield_kg_per_acre_max": 2500,
        "water_requirements_mm": 600,
        "source": "KALRO",
        "growth_stages": [
            {
                "name": "Germination",
                "start_day": 0,
                "end_day": 10,
                "description": "Seed emergence and early root development",
                "water_requirement_mm_per_day": 3,
                "activities": [
                    {"activity_type": "planting", "title": "Plant maize seeds", "day_offset": 0, "duration_hours": 8},
                ]
            },
            {
                "name": "Vegetative Growth",
                "start_day": 11,
                "end_day": 45,
                "description": "Leaf development and stem elongation",
                "water_requirement_mm_per_day": 5,
                "critical_for_yield": True,
                "activities": [
                    {"activity_type": "weeding", "title": "First weeding", "day_offset": 10, "duration_hours": 6},
                    {"activity_type": "fertilizer_application", "title": "Apply top-dress fertilizer (CAN)", "day_offset": 21, "duration_hours": 4},
                    {"activity_type": "weeding", "title": "Second weeding", "day_offset": 30, "duration_hours": 6},
                ]
            },
            {
                "name": "Tasseling & Silking",
                "start_day": 46,
                "end_day": 70,
                "description": "Flowering stage - most critical for water",
                "water_requirement_mm_per_day": 8,
                "critical_for_yield": True,
                "activities": [
                    {"activity_type": "scouting", "title": "Scout for pests (stalk borer)", "day_offset": 5, "duration_hours": 2},
                    {"activity_type": "pesticide_application", "title": "Apply pesticide if needed", "day_offset": 7, "duration_hours": 3, "is_weather_dependent": True},
                ]
            },
            {
                "name": "Grain Filling",
                "start_day": 71,
                "end_day": 110,
                "description": "Kernel development and starch accumulation",
                "water_requirement_mm_per_day": 6,
                "activities": [
                    {"activity_type": "scouting", "title": "Monitor for ear damage", "day_offset": 15, "duration_hours": 2},
                ]
            },
            {
                "name": "Maturation",
                "start_day": 111,
                "end_day": 140,
                "description": "Drying and hardening of grain",
                "water_requirement_mm_per_day": 2,
                "activities": [
                    {"activity_type": "harvesting", "title": "Harvest maize", "day_offset": 25, "duration_hours": 10},
                    {"activity_type": "post_harvest", "title": "Dry and store maize", "day_offset": 28, "duration_hours": 8},
                ]
            },
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 50, "timing": "At planting"},
            "topdress": {"type": "CAN", "rate_kg_per_acre": 50, "timing": "21 days after planting"},
        },
    },
    {
        "crop_name": "Maize",
        "variety": "DH04",
        "region_type": "county",
        "region_value": "Nakuru",
        "season": "long_rains",
        "recommended_planting_start_month": 3,
        "recommended_planting_end_month": 4,
        "total_days_to_harvest": 120,
        "seed_rate_kg_per_acre": 10,
        "expected_yield_kg_per_acre_min": 1200,
        "expected_yield_kg_per_acre_max": 2000,
        "water_requirements_mm": 500,
        "source": "KALRO",
        "growth_stages": [
            {"name": "Germination", "start_day": 0, "end_day": 10, "activities": []},
            {"name": "Vegetative Growth", "start_day": 11, "end_day": 40, "activities": []},
            {"name": "Tasseling & Silking", "start_day": 41, "end_day": 60, "critical_for_yield": True, "activities": []},
            {"name": "Grain Filling", "start_day": 61, "end_day": 95, "activities": []},
            {"name": "Maturation", "start_day": 96, "end_day": 120, "activities": []},
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 50, "timing": "At planting"},
            "topdress": {"type": "CAN", "rate_kg_per_acre": 50, "timing": "21 days after planting"},
        },
    },
    # ==========================================================================
    # BEANS TEMPLATES
    # ==========================================================================
    {
        "crop_name": "Beans",
        "variety": "Rose Coco",
        "region_type": "national",
        "region_value": None,
        "season": "long_rains",
        "recommended_planting_start_month": 3,
        "recommended_planting_end_month": 4,
        "total_days_to_harvest": 90,
        "seed_rate_kg_per_acre": 25,
        "expected_yield_kg_per_acre_min": 400,
        "expected_yield_kg_per_acre_max": 800,
        "water_requirements_mm": 400,
        "source": "KALRO",
        "growth_stages": [
            {
                "name": "Germination",
                "start_day": 0,
                "end_day": 7,
                "activities": [
                    {"activity_type": "planting", "title": "Plant bean seeds", "day_offset": 0, "duration_hours": 6},
                ]
            },
            {
                "name": "Vegetative",
                "start_day": 8,
                "end_day": 35,
                "activities": [
                    {"activity_type": "weeding", "title": "First weeding", "day_offset": 10, "duration_hours": 5},
                    {"activity_type": "weeding", "title": "Second weeding", "day_offset": 20, "duration_hours": 5},
                ]
            },
            {
                "name": "Flowering",
                "start_day": 36,
                "end_day": 50,
                "critical_for_yield": True,
                "activities": [
                    {"activity_type": "scouting", "title": "Scout for aphids", "day_offset": 5, "duration_hours": 2},
                ]
            },
            {
                "name": "Pod Development",
                "start_day": 51,
                "end_day": 75,
                "activities": []
            },
            {
                "name": "Maturation",
                "start_day": 76,
                "end_day": 90,
                "activities": [
                    {"activity_type": "harvesting", "title": "Harvest beans", "day_offset": 10, "duration_hours": 6},
                ]
            },
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 40, "timing": "At planting"},
        },
    },
    {
        "crop_name": "Beans",
        "variety": "KAT B1",
        "region_type": "agro_ecological_zone",
        "region_value": "Highland",
        "season": "short_rains",
        "recommended_planting_start_month": 10,
        "recommended_planting_end_month": 11,
        "total_days_to_harvest": 85,
        "seed_rate_kg_per_acre": 25,
        "expected_yield_kg_per_acre_min": 350,
        "expected_yield_kg_per_acre_max": 700,
        "water_requirements_mm": 350,
        "source": "KALRO",
        "growth_stages": [
            {"name": "Germination", "start_day": 0, "end_day": 7, "activities": []},
            {"name": "Vegetative", "start_day": 8, "end_day": 30, "activities": []},
            {"name": "Flowering", "start_day": 31, "end_day": 45, "critical_for_yield": True, "activities": []},
            {"name": "Pod Development", "start_day": 46, "end_day": 70, "activities": []},
            {"name": "Maturation", "start_day": 71, "end_day": 85, "activities": []},
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 40, "timing": "At planting"},
        },
    },
    # ==========================================================================
    # WHEAT TEMPLATES
    # ==========================================================================
    {
        "crop_name": "Wheat",
        "variety": "Kenya Fahari",
        "region_type": "county",
        "region_value": "Narok",
        "season": "long_rains",
        "recommended_planting_start_month": 3,
        "recommended_planting_end_month": 4,
        "total_days_to_harvest": 120,
        "seed_rate_kg_per_acre": 40,
        "expected_yield_kg_per_acre_min": 800,
        "expected_yield_kg_per_acre_max": 1500,
        "water_requirements_mm": 450,
        "source": "KALRO",
        "growth_stages": [
            {"name": "Germination", "start_day": 0, "end_day": 10, "activities": []},
            {"name": "Tillering", "start_day": 11, "end_day": 40, "activities": []},
            {"name": "Stem Extension", "start_day": 41, "end_day": 60, "activities": []},
            {"name": "Heading", "start_day": 61, "end_day": 80, "critical_for_yield": True, "activities": []},
            {"name": "Grain Filling", "start_day": 81, "end_day": 100, "activities": []},
            {"name": "Maturation", "start_day": 101, "end_day": 120, "activities": []},
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 50, "timing": "At planting"},
            "topdress": {"type": "CAN", "rate_kg_per_acre": 50, "timing": "30 days after planting"},
        },
    },
    # ==========================================================================
    # SORGHUM TEMPLATES
    # ==========================================================================
    {
        "crop_name": "Sorghum",
        "variety": "Gadam",
        "region_type": "national",
        "region_value": None,
        "season": "short_rains",
        "recommended_planting_start_month": 10,
        "recommended_planting_end_month": 11,
        "total_days_to_harvest": 110,
        "seed_rate_kg_per_acre": 4,
        "expected_yield_kg_per_acre_min": 600,
        "expected_yield_kg_per_acre_max": 1200,
        "water_requirements_mm": 400,
        "source": "KALRO",
        "growth_stages": [
            {"name": "Germination", "start_day": 0, "end_day": 10, "activities": []},
            {"name": "Vegetative", "start_day": 11, "end_day": 45, "activities": []},
            {"name": "Booting", "start_day": 46, "end_day": 60, "activities": []},
            {"name": "Flowering", "start_day": 61, "end_day": 75, "critical_for_yield": True, "activities": []},
            {"name": "Grain Filling", "start_day": 76, "end_day": 95, "activities": []},
            {"name": "Maturation", "start_day": 96, "end_day": 110, "activities": []},
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 40, "timing": "At planting"},
            "topdress": {"type": "CAN", "rate_kg_per_acre": 40, "timing": "30 days after planting"},
        },
    },
    # ==========================================================================
    # POTATO TEMPLATES
    # ==========================================================================
    {
        "crop_name": "Potato",
        "variety": "Shangi",
        "region_type": "county",
        "region_value": "Nyandarua",
        "season": "long_rains",
        "recommended_planting_start_month": 3,
        "recommended_planting_end_month": 4,
        "total_days_to_harvest": 100,
        "seed_rate_kg_per_acre": 600,  # Tubers, not seed
        "expected_yield_kg_per_acre_min": 4000,
        "expected_yield_kg_per_acre_max": 8000,
        "water_requirements_mm": 500,
        "source": "KALRO",
        "growth_stages": [
            {
                "name": "Sprouting",
                "start_day": 0,
                "end_day": 15,
                "activities": [
                    {"activity_type": "planting", "title": "Plant potato tubers", "day_offset": 0, "duration_hours": 8},
                ]
            },
            {
                "name": "Vegetative Growth",
                "start_day": 16,
                "end_day": 40,
                "activities": [
                    {"activity_type": "weeding", "title": "First weeding", "day_offset": 10, "duration_hours": 6},
                    {"activity_type": "fertilizer_application", "title": "First earthing up with fertilizer", "day_offset": 15, "duration_hours": 6},
                ]
            },
            {
                "name": "Tuber Initiation",
                "start_day": 41,
                "end_day": 55,
                "critical_for_yield": True,
                "activities": [
                    {"activity_type": "fertilizer_application", "title": "Second earthing up", "day_offset": 7, "duration_hours": 5},
                ]
            },
            {
                "name": "Tuber Bulking",
                "start_day": 56,
                "end_day": 85,
                "critical_for_yield": True,
                "activities": [
                    {"activity_type": "scouting", "title": "Scout for late blight", "day_offset": 10, "duration_hours": 2},
                    {"activity_type": "pesticide_application", "title": "Apply fungicide if needed", "day_offset": 12, "duration_hours": 3, "is_weather_dependent": True},
                ]
            },
            {
                "name": "Maturation",
                "start_day": 86,
                "end_day": 100,
                "activities": [
                    {"activity_type": "harvesting", "title": "Harvest potatoes", "day_offset": 10, "duration_hours": 10},
                ]
            },
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 80, "timing": "At planting"},
            "topdress_1": {"type": "CAN", "rate_kg_per_acre": 60, "timing": "First earthing up"},
            "topdress_2": {"type": "NPK 17:17:17", "rate_kg_per_acre": 40, "timing": "Second earthing up"},
        },
    },
    # ==========================================================================
    # TOMATO TEMPLATES (Irrigated)
    # ==========================================================================
    {
        "crop_name": "Tomato",
        "variety": "Rio Grande",
        "region_type": "national",
        "region_value": None,
        "season": "irrigated",
        "recommended_planting_start_month": 1,
        "recommended_planting_end_month": 12,
        "total_days_to_harvest": 90,
        "seed_rate_kg_per_acre": 0.1,  # Transplants
        "expected_yield_kg_per_acre_min": 8000,
        "expected_yield_kg_per_acre_max": 15000,
        "water_requirements_mm": 600,
        "source": "Ministry of Agriculture",
        "growth_stages": [
            {
                "name": "Transplanting",
                "start_day": 0,
                "end_day": 14,
                "activities": [
                    {"activity_type": "planting", "title": "Transplant tomato seedlings", "day_offset": 0, "duration_hours": 6},
                    {"activity_type": "irrigation", "title": "Initial irrigation", "day_offset": 0, "duration_hours": 2},
                ]
            },
            {
                "name": "Vegetative Growth",
                "start_day": 15,
                "end_day": 35,
                "activities": [
                    {"activity_type": "staking", "title": "Stake tomato plants", "day_offset": 5, "duration_hours": 4},
                    {"activity_type": "pruning", "title": "First pruning of suckers", "day_offset": 10, "duration_hours": 3},
                    {"activity_type": "fertilizer_application", "title": "Apply foliar fertilizer", "day_offset": 15, "duration_hours": 2},
                ]
            },
            {
                "name": "Flowering",
                "start_day": 36,
                "end_day": 50,
                "critical_for_yield": True,
                "activities": [
                    {"activity_type": "scouting", "title": "Scout for pests and diseases", "day_offset": 7, "duration_hours": 2},
                ]
            },
            {
                "name": "Fruit Development",
                "start_day": 51,
                "end_day": 75,
                "activities": [
                    {"activity_type": "fertilizer_application", "title": "Apply potassium-rich fertilizer", "day_offset": 10, "duration_hours": 2},
                ]
            },
            {
                "name": "Harvesting",
                "start_day": 76,
                "end_day": 90,
                "activities": [
                    {"activity_type": "harvesting", "title": "First harvest", "day_offset": 0, "duration_hours": 4},
                    {"activity_type": "harvesting", "title": "Continue harvesting", "day_offset": 7, "duration_hours": 4},
                ]
            },
        ],
        "fertilizer_requirements": {
            "basal": {"type": "DAP", "rate_kg_per_acre": 100, "timing": "At transplanting"},
            "topdress_1": {"type": "CAN", "rate_kg_per_acre": 50, "timing": "21 days after transplanting"},
            "topdress_2": {"type": "NPK 0:0:60", "rate_kg_per_acre": 40, "timing": "At fruit set"},
        },
    },
]


async def seed_templates(db: AsyncSession) -> None:
    """Seed crop calendar templates into the database."""
    print(f"Seeding {len(CROP_TEMPLATES)} crop calendar templates...")

    for template_data in CROP_TEMPLATES:
        template = CropCalendarTemplate(
            id=uuid.uuid4(),
            tenant_id=DEFAULT_TENANT_ID,
            crop_name=template_data["crop_name"],
            variety=template_data.get("variety"),
            region_type=template_data["region_type"],
            region_value=template_data.get("region_value"),
            season=template_data["season"],
            recommended_planting_start_month=template_data["recommended_planting_start_month"],
            recommended_planting_end_month=template_data["recommended_planting_end_month"],
            total_days_to_harvest=template_data["total_days_to_harvest"],
            growth_stages=template_data.get("growth_stages"),
            seed_rate_kg_per_acre=template_data.get("seed_rate_kg_per_acre"),
            fertilizer_requirements=template_data.get("fertilizer_requirements"),
            expected_yield_kg_per_acre_min=template_data.get("expected_yield_kg_per_acre_min"),
            expected_yield_kg_per_acre_max=template_data.get("expected_yield_kg_per_acre_max"),
            water_requirements_mm=template_data.get("water_requirements_mm"),
            source=template_data.get("source"),
            is_active=True,
        )
        db.add(template)
        print(f"  + {template.crop_name} ({template.variety or 'Generic'}) - {template.season}")

    await db.commit()
    print("Seeding complete!")


async def main():
    """Main entry point for seeding."""
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )

    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        await seed_templates(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
