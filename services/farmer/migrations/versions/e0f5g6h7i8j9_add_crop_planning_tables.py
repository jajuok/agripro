"""Add crop planning tables (Phase 3.1)

Revision ID: e0f5g6h7i8j9
Revises: d9e4f6g7h8i9
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e0f5g6h7i8j9'
down_revision: Union[str, None] = 'd9e4f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create crop_calendar_templates table
    op.create_table(
        'crop_calendar_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('crop_name', sa.String(100), nullable=False, index=True),
        sa.Column('variety', sa.String(100), nullable=True),
        sa.Column('region_type', sa.String(50), nullable=False),
        sa.Column('region_value', sa.String(100), nullable=True),
        sa.Column('season', sa.String(50), nullable=False),
        sa.Column('recommended_planting_start_month', sa.Integer, nullable=False),
        sa.Column('recommended_planting_end_month', sa.Integer, nullable=False),
        sa.Column('total_days_to_harvest', sa.Integer, nullable=False),
        sa.Column('growth_stages', postgresql.JSONB, nullable=True),
        sa.Column('seed_rate_kg_per_acre', sa.Float, nullable=True),
        sa.Column('fertilizer_requirements', postgresql.JSONB, nullable=True),
        sa.Column('expected_yield_kg_per_acre_min', sa.Float, nullable=True),
        sa.Column('expected_yield_kg_per_acre_max', sa.Float, nullable=True),
        sa.Column('water_requirements_mm', sa.Float, nullable=True),
        sa.Column('critical_water_stages', postgresql.JSONB, nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create crop_plans table
    op.create_table(
        'crop_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farm_profiles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_calendar_templates.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('crop_name', sa.String(100), nullable=False, index=True),
        sa.Column('variety', sa.String(100), nullable=True),
        sa.Column('season', sa.String(50), nullable=False),
        sa.Column('year', sa.Integer, nullable=False, index=True),
        sa.Column('planned_planting_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expected_harvest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_planting_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_harvest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('optimal_planting_window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('optimal_planting_window_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_acreage', sa.Float, nullable=False),
        sa.Column('actual_planted_acreage', sa.Float, nullable=True),
        sa.Column('expected_yield_kg', sa.Float, nullable=True),
        sa.Column('actual_yield_kg', sa.Float, nullable=True),
        sa.Column('current_growth_stage', sa.String(100), nullable=True),
        sa.Column('current_growth_stage_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('growth_stage_history', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('estimated_total_cost', sa.Float, nullable=True),
        sa.Column('actual_total_cost', sa.Float, nullable=True),
        sa.Column('weather_data_snapshot', postgresql.JSONB, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create planned_activities table
    op.create_table(
        'planned_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_plans.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('growth_stage', sa.String(100), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('scheduled_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_hours', sa.Float, nullable=True),
        sa.Column('earliest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('latest_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_weather_dependent', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('weather_conditions_required', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='scheduled'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_notes', sa.Text, nullable=True),
        sa.Column('completion_photos', postgresql.JSONB, nullable=True),
        sa.Column('gps_latitude', sa.Float, nullable=True),
        sa.Column('gps_longitude', sa.Float, nullable=True),
        sa.Column('inputs_used', postgresql.JSONB, nullable=True),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        sa.Column('actual_cost', sa.Float, nullable=True),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('reminder_days_before', sa.Integer, nullable=False, server_default='1'),
        sa.Column('alert_sent', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create input_requirements table
    op.create_table(
        'input_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_plans.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('is_certified', sa.Boolean, nullable=True),
        sa.Column('certification_number', sa.String(100), nullable=True),
        sa.Column('qr_code_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('qr_code_data', postgresql.JSONB, nullable=True),
        sa.Column('qr_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quantity_required', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('quantity_per_acre', sa.Float, nullable=True),
        sa.Column('application_stage', sa.String(100), nullable=True),
        sa.Column('application_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('application_method', sa.String(100), nullable=True),
        sa.Column('unit_price', sa.Float, nullable=True),
        sa.Column('total_estimated_cost', sa.Float, nullable=True),
        sa.Column('actual_cost', sa.Float, nullable=True),
        sa.Column('procurement_status', sa.String(20), nullable=False, server_default='planned'),
        sa.Column('supplier_name', sa.String(200), nullable=True),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('purchase_location', sa.String(200), nullable=True),
        sa.Column('quantity_used', sa.Float, nullable=True),
        sa.Column('quantity_remaining', sa.Float, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create irrigation_schedules table
    op.create_table(
        'irrigation_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('crop_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_plans.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('scheduled_duration_minutes', sa.Integer, nullable=True),
        sa.Column('water_amount_liters', sa.Float, nullable=True),
        sa.Column('water_amount_mm', sa.Float, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='scheduled'),
        sa.Column('actual_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer, nullable=True),
        sa.Column('actual_water_used_liters', sa.Float, nullable=True),
        sa.Column('soil_moisture_before', sa.Float, nullable=True),
        sa.Column('soil_moisture_after', sa.Float, nullable=True),
        sa.Column('rainfall_mm_last_24h', sa.Float, nullable=True),
        sa.Column('temperature_celsius', sa.Float, nullable=True),
        sa.Column('evapotranspiration_mm', sa.Float, nullable=True),
        sa.Column('is_deficit_irrigation', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('deficit_percentage', sa.Float, nullable=True),
        sa.Column('growth_stage', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create crop_plan_alerts table
    op.create_table(
        'crop_plan_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('crop_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('crop_plans.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('planned_activities.id', ondelete='CASCADE'), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='info'),
        sa.Column('data', postgresql.JSONB, nullable=True),
        sa.Column('channels', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes for performance
    op.create_index('ix_crop_plans_farmer_status', 'crop_plans', ['farmer_id', 'status'])
    op.create_index('ix_crop_plans_farm_year', 'crop_plans', ['farm_id', 'year'])
    op.create_index('ix_planned_activities_plan_status', 'planned_activities', ['crop_plan_id', 'status'])
    op.create_index('ix_planned_activities_scheduled', 'planned_activities', ['scheduled_date', 'status'])
    op.create_index('ix_irrigation_schedules_plan_status', 'irrigation_schedules', ['crop_plan_id', 'status'])
    op.create_index('ix_crop_plan_alerts_farmer_unread', 'crop_plan_alerts', ['farmer_id', 'read_at'])
    op.create_index('ix_crop_calendar_templates_crop_season', 'crop_calendar_templates', ['crop_name', 'season'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_crop_calendar_templates_crop_season')
    op.drop_index('ix_crop_plan_alerts_farmer_unread')
    op.drop_index('ix_irrigation_schedules_plan_status')
    op.drop_index('ix_planned_activities_scheduled')
    op.drop_index('ix_planned_activities_plan_status')
    op.drop_index('ix_crop_plans_farm_year')
    op.drop_index('ix_crop_plans_farmer_status')

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('crop_plan_alerts')
    op.drop_table('irrigation_schedules')
    op.drop_table('input_requirements')
    op.drop_table('planned_activities')
    op.drop_table('crop_plans')
    op.drop_table('crop_calendar_templates')
