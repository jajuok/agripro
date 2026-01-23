"""Add eligibility assessment tables (Phase 2.3)

Revision ID: d9e4f6g7h8i9
Revises: c8a2f5e3d1b4
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd9e4f6g7h8i9'
down_revision: Union[str, None] = 'c8a2f5e3d1b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create eligibility_schemes table
    op.create_table(
        'eligibility_schemes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('scheme_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('application_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_beneficiaries', sa.Integer, nullable=True),
        sa.Column('current_beneficiaries', sa.Integer, nullable=False, server_default='0'),
        sa.Column('budget_amount', sa.Float, nullable=True),
        sa.Column('disbursed_amount', sa.Float, nullable=False, server_default='0'),
        sa.Column('benefit_type', sa.String(50), nullable=True),
        sa.Column('benefit_amount', sa.Float, nullable=True),
        sa.Column('benefit_description', sa.Text, nullable=True),
        sa.Column('auto_approve_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('min_score_for_auto_approve', sa.Float, nullable=True),
        sa.Column('max_risk_for_auto_approve', sa.String(20), nullable=True),
        sa.Column('waitlist_enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('waitlist_capacity', sa.Integer, nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create eligibility_rule_groups table
    op.create_table(
        'eligibility_rule_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scheme_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_schemes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('logic_operator', sa.String(10), nullable=False, server_default='AND'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('weight', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create eligibility_rules table
    op.create_table(
        'eligibility_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scheme_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_schemes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_rule_groups.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('field_type', sa.String(20), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('field_path', sa.String(200), nullable=True),
        sa.Column('operator', sa.String(30), nullable=False),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('value_type', sa.String(20), nullable=False, server_default='string'),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_exclusion', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('weight', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='1'),
        sa.Column('pass_message', sa.String(500), nullable=True),
        sa.Column('fail_message', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create eligibility_assessments table
    op.create_table(
        'eligibility_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('scheme_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_schemes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farm_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('assessment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('eligibility_score', sa.Float, nullable=True),
        sa.Column('risk_score', sa.Float, nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('credit_score', sa.Float, nullable=True),
        sa.Column('rules_passed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rules_failed', sa.Integer, nullable=False, server_default='0'),
        sa.Column('mandatory_rules_passed', sa.Boolean, nullable=True),
        sa.Column('rule_results', postgresql.JSONB, nullable=True),
        sa.Column('workflow_decision', sa.String(20), nullable=True),
        sa.Column('final_decision', sa.String(20), nullable=True),
        sa.Column('decision_reason', sa.Text, nullable=True),
        sa.Column('decision_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('waitlist_position', sa.Integer, nullable=True),
        sa.Column('waitlisted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create credit_bureau_providers table
    op.create_table(
        'credit_bureau_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('api_base_url', sa.String(500), nullable=True),
        sa.Column('api_key_encrypted', sa.Text, nullable=True),
        sa.Column('api_config', postgresql.JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='1'),
        sa.Column('timeout_seconds', sa.Integer, nullable=False, server_default='30'),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='3'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create credit_checks table
    op.create_table(
        'credit_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_assessments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('credit_bureau_providers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True, unique=True),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('consent_given', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('credit_score', sa.Integer, nullable=True),
        sa.Column('score_band', sa.String(20), nullable=True),
        sa.Column('total_accounts', sa.Integer, nullable=True),
        sa.Column('active_accounts', sa.Integer, nullable=True),
        sa.Column('total_debt', sa.Float, nullable=True),
        sa.Column('monthly_obligations', sa.Float, nullable=True),
        sa.Column('delinquent_accounts', sa.Integer, nullable=True),
        sa.Column('defaults_count', sa.Integer, nullable=True),
        sa.Column('declared_income', sa.Float, nullable=True),
        sa.Column('debt_to_income_ratio', sa.Float, nullable=True),
        sa.Column('response_data', postgresql.JSONB, nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
    )

    # Create risk_factors table
    op.create_table(
        'risk_factors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('data_source', sa.String(50), nullable=False),
        sa.Column('field_path', sa.String(200), nullable=True),
        sa.Column('calculation_method', sa.String(50), nullable=False),
        sa.Column('scoring_config', postgresql.JSONB, nullable=True),
        sa.Column('weight', sa.Float, nullable=False, server_default='1.0'),
        sa.Column('max_score', sa.Float, nullable=False, server_default='100.0'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_assessments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('assessed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('total_risk_score', sa.Float, nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('credit_risk_score', sa.Float, nullable=True),
        sa.Column('performance_risk_score', sa.Float, nullable=True),
        sa.Column('external_risk_score', sa.Float, nullable=True),
        sa.Column('fraud_risk_score', sa.Float, nullable=True),
        sa.Column('factor_scores', postgresql.JSONB, nullable=True),
        sa.Column('fraud_indicators', postgresql.JSONB, nullable=True),
        sa.Column('risk_flags', postgresql.JSONB, nullable=True),
        sa.Column('recommendations', postgresql.JSONB, nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('model_type', sa.String(50), nullable=False, server_default='rule_based'),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
    )

    # Create eligibility_review_queue table
    op.create_table(
        'eligibility_review_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_assessments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('queue_reason', sa.String(200), nullable=False),
        sa.Column('queue_category', sa.String(50), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('decision', sa.String(20), nullable=True),
        sa.Column('decision_notes', sa.Text, nullable=True),
        sa.Column('sla_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_overdue', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create scheme_waitlists table
    op.create_table(
        'scheme_waitlists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scheme_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_schemes.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('original_position', sa.Integer, nullable=False),
        sa.Column('eligibility_score', sa.Float, nullable=False),
        sa.Column('risk_score', sa.Float, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='waiting'),
        sa.Column('offered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('offer_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create eligibility_notifications table
    op.create_table(
        'eligibility_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('eligibility_assessments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('data', postgresql.JSONB, nullable=True),
        sa.Column('channels', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes for performance
    op.create_index('ix_eligibility_assessments_status', 'eligibility_assessments', ['status'])
    op.create_index('ix_eligibility_assessments_farmer_scheme', 'eligibility_assessments', ['farmer_id', 'scheme_id'])
    op.create_index('ix_credit_checks_farmer_status', 'credit_checks', ['farmer_id', 'status'])
    op.create_index('ix_risk_assessments_farmer', 'risk_assessments', ['farmer_id'])
    op.create_index('ix_scheme_waitlists_scheme_status', 'scheme_waitlists', ['scheme_id', 'status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_scheme_waitlists_scheme_status')
    op.drop_index('ix_risk_assessments_farmer')
    op.drop_index('ix_credit_checks_farmer_status')
    op.drop_index('ix_eligibility_assessments_farmer_scheme')
    op.drop_index('ix_eligibility_assessments_status')

    # Drop tables in reverse order
    op.drop_table('eligibility_notifications')
    op.drop_table('scheme_waitlists')
    op.drop_table('eligibility_review_queue')
    op.drop_table('risk_assessments')
    op.drop_table('risk_factors')
    op.drop_table('credit_checks')
    op.drop_table('credit_bureau_providers')
    op.drop_table('eligibility_assessments')
    op.drop_table('eligibility_rules')
    op.drop_table('eligibility_rule_groups')
    op.drop_table('eligibility_schemes')
