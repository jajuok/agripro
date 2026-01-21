"""add_farm_registration_tables

Revision ID: c8a2f5e3d1b4
Revises: bf6af1710f97
Create Date: 2026-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8a2f5e3d1b4'
down_revision: Union[str, Sequence[str], None] = 'bf6af1710f97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to farm_profiles table
    op.add_column('farm_profiles', sa.Column('county', sa.String(length=100), nullable=True))
    op.add_column('farm_profiles', sa.Column('sub_county', sa.String(length=100), nullable=True))
    op.add_column('farm_profiles', sa.Column('ward', sa.String(length=100), nullable=True))
    op.add_column('farm_profiles', sa.Column('village', sa.String(length=100), nullable=True))
    op.add_column('farm_profiles', sa.Column('altitude', sa.Float(), nullable=True))
    op.add_column('farm_profiles', sa.Column('address_description', sa.Text(), nullable=True))
    op.add_column('farm_profiles', sa.Column('boundary_area_calculated', sa.Float(), nullable=True))
    op.add_column('farm_profiles', sa.Column('boundary_validated', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('farm_profiles', sa.Column('boundary_validated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('farm_profiles', sa.Column('plot_id_source', sa.String(length=50), nullable=True))
    op.add_column('farm_profiles', sa.Column('land_reference_number', sa.String(length=100), nullable=True))
    op.add_column('farm_profiles', sa.Column('has_year_round_water', sa.Boolean(), nullable=True))
    op.add_column('farm_profiles', sa.Column('water_reliability', sa.String(length=50), nullable=True))
    op.add_column('farm_profiles', sa.Column('verified_by', sa.UUID(), nullable=True))
    op.add_column('farm_profiles', sa.Column('registration_step', sa.String(length=50), nullable=False, server_default='location'))
    op.add_column('farm_profiles', sa.Column('registration_complete', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('farm_profiles', sa.Column('registration_completed_at', sa.DateTime(timezone=True), nullable=True))

    # Create indexes for farm_profiles new columns
    op.create_index('ix_farm_profiles_county', 'farm_profiles', ['county'])
    op.create_index('ix_farm_profiles_registration_step', 'farm_profiles', ['registration_step'])
    op.create_index('ix_farm_profiles_registration_complete', 'farm_profiles', ['registration_complete'])

    # Create farm_documents table
    op.create_table('farm_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farm_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.UUID(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_farm_documents_farm_id', 'farm_documents', ['farm_id'])
    op.create_index('ix_farm_documents_document_type', 'farm_documents', ['document_type'])

    # Create farm_assets table
    op.create_table('farm_assets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farm_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ownership_type', sa.String(length=50), nullable=False, server_default='owned'),
        sa.Column('acquisition_date', sa.DateTime(), nullable=True),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('make', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('condition', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_photo_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_farm_assets_farm_id', 'farm_assets', ['farm_id'])
    op.create_index('ix_farm_assets_category', 'farm_assets', ['category'])

    # Create crop_records table
    op.create_table('crop_records',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farm_id', sa.UUID(), nullable=False),
        sa.Column('crop_name', sa.String(length=100), nullable=False),
        sa.Column('crop_variety', sa.String(length=100), nullable=True),
        sa.Column('season', sa.String(length=50), nullable=False),
        sa.Column('planting_date', sa.DateTime(), nullable=True),
        sa.Column('harvest_date', sa.DateTime(), nullable=True),
        sa.Column('area_planted', sa.Float(), nullable=True),
        sa.Column('area_unit', sa.String(length=20), nullable=False, server_default='acres'),
        sa.Column('expected_yield', sa.Float(), nullable=True),
        sa.Column('actual_yield', sa.Float(), nullable=True),
        sa.Column('yield_unit', sa.String(length=50), nullable=True),
        sa.Column('inputs_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', sa.UUID(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crop_records_farm_id', 'crop_records', ['farm_id'])
    op.create_index('ix_crop_records_season', 'crop_records', ['season'])
    op.create_index('ix_crop_records_crop_name', 'crop_records', ['crop_name'])
    op.create_index('ix_crop_records_status', 'crop_records', ['status'])

    # Create soil_test_reports table
    op.create_table('soil_test_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farm_id', sa.UUID(), nullable=False),
        sa.Column('test_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('laboratory_name', sa.String(length=200), nullable=True),
        sa.Column('sample_id', sa.String(length=100), nullable=True),
        sa.Column('sample_latitude', sa.Float(), nullable=True),
        sa.Column('sample_longitude', sa.Float(), nullable=True),
        sa.Column('sample_depth_cm', sa.Float(), nullable=True),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('soil_texture', sa.String(length=100), nullable=True),
        sa.Column('ph_value', sa.Float(), nullable=True),
        sa.Column('organic_matter_percent', sa.Float(), nullable=True),
        sa.Column('nitrogen', sa.Float(), nullable=True),
        sa.Column('phosphorus', sa.Float(), nullable=True),
        sa.Column('potassium', sa.Float(), nullable=True),
        sa.Column('calcium', sa.Float(), nullable=True),
        sa.Column('magnesium', sa.Float(), nullable=True),
        sa.Column('sulfur', sa.Float(), nullable=True),
        sa.Column('micronutrients', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('full_report_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('report_file_path', sa.String(length=500), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_soil_test_reports_farm_id', 'soil_test_reports', ['farm_id'])
    op.create_index('ix_soil_test_reports_test_date', 'soil_test_reports', ['test_date'])

    # Create field_visits table
    op.create_table('field_visits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('farm_id', sa.UUID(), nullable=False),
        sa.Column('visit_type', sa.String(length=50), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('visitor_id', sa.UUID(), nullable=False),
        sa.Column('visitor_name', sa.String(length=200), nullable=False),
        sa.Column('visitor_role', sa.String(length=100), nullable=False),
        sa.Column('check_in_latitude', sa.Float(), nullable=True),
        sa.Column('check_in_longitude', sa.Float(), nullable=True),
        sa.Column('check_in_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_out_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='scheduled'),
        sa.Column('verification_checklist', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('photos', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('verification_result', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farm_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_field_visits_farm_id', 'field_visits', ['farm_id'])
    op.create_index('ix_field_visits_visitor_id', 'field_visits', ['visitor_id'])
    op.create_index('ix_field_visits_status', 'field_visits', ['status'])
    op.create_index('ix_field_visits_scheduled_date', 'field_visits', ['scheduled_date'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop field_visits table
    op.drop_index('ix_field_visits_scheduled_date', table_name='field_visits')
    op.drop_index('ix_field_visits_status', table_name='field_visits')
    op.drop_index('ix_field_visits_visitor_id', table_name='field_visits')
    op.drop_index('ix_field_visits_farm_id', table_name='field_visits')
    op.drop_table('field_visits')

    # Drop soil_test_reports table
    op.drop_index('ix_soil_test_reports_test_date', table_name='soil_test_reports')
    op.drop_index('ix_soil_test_reports_farm_id', table_name='soil_test_reports')
    op.drop_table('soil_test_reports')

    # Drop crop_records table
    op.drop_index('ix_crop_records_status', table_name='crop_records')
    op.drop_index('ix_crop_records_crop_name', table_name='crop_records')
    op.drop_index('ix_crop_records_season', table_name='crop_records')
    op.drop_index('ix_crop_records_farm_id', table_name='crop_records')
    op.drop_table('crop_records')

    # Drop farm_assets table
    op.drop_index('ix_farm_assets_category', table_name='farm_assets')
    op.drop_index('ix_farm_assets_farm_id', table_name='farm_assets')
    op.drop_table('farm_assets')

    # Drop farm_documents table
    op.drop_index('ix_farm_documents_document_type', table_name='farm_documents')
    op.drop_index('ix_farm_documents_farm_id', table_name='farm_documents')
    op.drop_table('farm_documents')

    # Drop indexes from farm_profiles
    op.drop_index('ix_farm_profiles_registration_complete', table_name='farm_profiles')
    op.drop_index('ix_farm_profiles_registration_step', table_name='farm_profiles')
    op.drop_index('ix_farm_profiles_county', table_name='farm_profiles')

    # Drop columns from farm_profiles
    op.drop_column('farm_profiles', 'registration_completed_at')
    op.drop_column('farm_profiles', 'registration_complete')
    op.drop_column('farm_profiles', 'registration_step')
    op.drop_column('farm_profiles', 'verified_by')
    op.drop_column('farm_profiles', 'water_reliability')
    op.drop_column('farm_profiles', 'has_year_round_water')
    op.drop_column('farm_profiles', 'land_reference_number')
    op.drop_column('farm_profiles', 'plot_id_source')
    op.drop_column('farm_profiles', 'boundary_validated_at')
    op.drop_column('farm_profiles', 'boundary_validated')
    op.drop_column('farm_profiles', 'boundary_area_calculated')
    op.drop_column('farm_profiles', 'address_description')
    op.drop_column('farm_profiles', 'altitude')
    op.drop_column('farm_profiles', 'village')
    op.drop_column('farm_profiles', 'ward')
    op.drop_column('farm_profiles', 'sub_county')
    op.drop_column('farm_profiles', 'county')
