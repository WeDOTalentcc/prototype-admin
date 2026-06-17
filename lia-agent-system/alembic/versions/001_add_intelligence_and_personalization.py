"""Add intelligence layer and recruiter personalization tables

Revision ID: 001_intelligence
Revises: 
Create Date: 2026-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_intelligence'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('intelligence_insights',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('recruiter_id', sa.String(length=255), nullable=True),
        sa.Column('insight_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('insight_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('was_applied', sa.Boolean(), nullable=True, default=False),
        sa.Column('was_dismissed', sa.Boolean(), nullable=True, default=False),
        sa.Column('user_feedback', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intelligence_insights_company_id'), 'intelligence_insights', ['company_id'], unique=False)
    op.create_index(op.f('ix_intelligence_insights_insight_type'), 'intelligence_insights', ['insight_type'], unique=False)

    op.create_table('pattern_cache',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('pattern_type', sa.String(length=100), nullable=False),
        sa.Column('cache_key', sa.String(length=500), nullable=False),
        sa.Column('cached_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pattern_cache_company_id'), 'pattern_cache', ['company_id'], unique=False)
    op.create_index(op.f('ix_pattern_cache_pattern_type'), 'pattern_cache', ['pattern_type'], unique=False)
    op.create_index(op.f('ix_pattern_cache_cache_key'), 'pattern_cache', ['cache_key'], unique=False)

    op.create_table('correction_patterns',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('field', sa.String(length=100), nullable=False),
        sa.Column('pattern_type', sa.String(length=50), nullable=False),
        sa.Column('seniority', sa.String(length=50), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('original_value_pattern', sa.String(length=500), nullable=True),
        sa.Column('corrected_value_pattern', sa.String(length=500), nullable=True),
        sa.Column('adjustment_direction', sa.String(length=20), nullable=True),
        sa.Column('adjustment_magnitude', sa.Float(), nullable=True),
        sa.Column('occurrence_count', sa.Integer(), nullable=True, default=0),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('sample_size', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_correction_patterns_company_id'), 'correction_patterns', ['company_id'], unique=False)
    op.create_index(op.f('ix_correction_patterns_field'), 'correction_patterns', ['field'], unique=False)

    op.create_table('success_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('seniority', sa.String(length=50), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('role_family', sa.String(length=100), nullable=True),
        sa.Column('avg_time_to_fill_days', sa.Float(), nullable=True),
        sa.Column('avg_salary', sa.Float(), nullable=True),
        sa.Column('salary_range_min', sa.Float(), nullable=True),
        sa.Column('salary_range_max', sa.Float(), nullable=True),
        sa.Column('common_skills', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('common_requirements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_work_model', sa.String(length=50), nullable=True),
        sa.Column('avg_satisfaction_score', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_success_profiles_company_id'), 'success_profiles', ['company_id'], unique=False)
    op.create_index(op.f('ix_success_profiles_seniority'), 'success_profiles', ['seniority'], unique=False)

    op.create_table('outcome_correlations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('factor_field', sa.String(length=100), nullable=False),
        sa.Column('outcome_type', sa.String(length=100), nullable=False),
        sa.Column('correlation_coefficient', sa.Float(), nullable=False),
        sa.Column('p_value', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True, default=0),
        sa.Column('is_significant', sa.Boolean(), nullable=True, default=False),
        sa.Column('direction', sa.String(length=20), nullable=True),
        sa.Column('insight_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outcome_correlations_company_id'), 'outcome_correlations', ['company_id'], unique=False)
    op.create_index(op.f('ix_outcome_correlations_factor_field'), 'outcome_correlations', ['factor_field'], unique=False)

    op.create_table('recruiter_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_id', sa.String(length=255), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('total_jobs_created', sa.Integer(), nullable=True, default=0),
        sa.Column('total_corrections_made', sa.Integer(), nullable=True, default=0),
        sa.Column('avg_completion_time_seconds', sa.Float(), nullable=True),
        sa.Column('preferred_seniorities', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_departments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('correction_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_threshold_adjustment', sa.Float(), nullable=True, default=0.0),
        sa.Column('wizard_mode', sa.String(length=50), nullable=True, default='standard'),
        sa.Column('experience_level', sa.String(length=50), nullable=True, default='beginner'),
        sa.Column('profile_version', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recruiter_profiles_recruiter_id'), 'recruiter_profiles', ['recruiter_id'], unique=True)
    op.create_index(op.f('ix_recruiter_profiles_company_id'), 'recruiter_profiles', ['company_id'], unique=False)

    op.create_table('recruiter_field_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_profile_id', sa.UUID(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('correction_count', sa.Integer(), nullable=True, default=0),
        sa.Column('correction_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('typical_value', sa.String(length=500), nullable=True),
        sa.Column('value_frequency', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('avg_time_on_field_seconds', sa.Float(), nullable=True),
        sa.Column('skip_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recruiter_profile_id'], ['recruiter_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recruiter_field_preferences_recruiter_profile_id'), 'recruiter_field_preferences', ['recruiter_profile_id'], unique=False)
    op.create_index(op.f('ix_recruiter_field_preferences_field_name'), 'recruiter_field_preferences', ['field_name'], unique=False)

    op.create_table('personalization_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_id', sa.String(length=255), nullable=False),
        sa.Column('company_id', sa.String(length=255), nullable=False),
        sa.Column('job_draft_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('original_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('event_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personalization_events_recruiter_id'), 'personalization_events', ['recruiter_id'], unique=False)
    op.create_index(op.f('ix_personalization_events_event_type'), 'personalization_events', ['event_type'], unique=False)

    op.create_table('personalization_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_id', sa.String(length=255), nullable=False),
        sa.Column('personalization_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('data_collection_consent', sa.Boolean(), nullable=True, default=True),
        sa.Column('show_personalization_indicators', sa.Boolean(), nullable=True, default=True),
        sa.Column('allow_behavior_learning', sa.Boolean(), nullable=True, default=True),
        sa.Column('preferred_language', sa.String(length=10), nullable=True, default='pt-BR'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_personalization_settings_recruiter_id'), 'personalization_settings', ['recruiter_id'], unique=True)

    op.create_table('profile_calculation_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('recruiter_profile_id', sa.UUID(), nullable=False),
        sa.Column('calculation_type', sa.String(length=100), nullable=False),
        sa.Column('old_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('trigger_event', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['recruiter_profile_id'], ['recruiter_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profile_calculation_logs_recruiter_profile_id'), 'profile_calculation_logs', ['recruiter_profile_id'], unique=False)


def downgrade() -> None:
    op.drop_table('profile_calculation_logs')
    op.drop_table('personalization_settings')
    op.drop_table('personalization_events')
    op.drop_table('recruiter_field_preferences')
    op.drop_table('recruiter_profiles')
    op.drop_table('outcome_correlations')
    op.drop_table('success_profiles')
    op.drop_table('correction_patterns')
    op.drop_table('pattern_cache')
    op.drop_table('intelligence_insights')
