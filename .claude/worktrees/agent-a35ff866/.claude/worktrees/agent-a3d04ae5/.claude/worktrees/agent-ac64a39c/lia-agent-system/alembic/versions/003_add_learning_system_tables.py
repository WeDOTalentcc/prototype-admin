"""Add learning system tables (FeatureFlag, StageFeedback, LearningAnalytics).

Revision ID: 003_add_learning_system
Revises: 002_add_comment
Create Date: 2026-01-28

This migration creates tables for:
- feature_flags: Granular control of platform functionality with rollout support
- stage_feedback: Capture feedback from wizard stages 2-7
- learning_analytics: Pre-computed metrics for dashboard
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '003_add_learning_system'
down_revision = '002_add_comment'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feature_flags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('flag_key', sa.String(100), nullable=False, index=True),
        sa.Column('company_id', sa.String(255), nullable=True, index=True),
        sa.Column('is_enabled', sa.Boolean(), default=False),
        sa.Column('rollout_percentage', sa.Integer(), default=100),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), default='general'),
        sa.Column('flag_metadata', sa.JSON(), default=dict),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.UniqueConstraint('flag_key', 'company_id', name='uq_feature_flag_company'),
    )
    
    op.create_index(
        'ix_feature_flags_key_enabled',
        'feature_flags',
        ['flag_key', 'is_enabled']
    )
    
    op.execute('''
        CREATE UNIQUE INDEX ix_feature_flags_global_unique 
        ON feature_flags (flag_key) 
        WHERE company_id IS NULL
    ''')
    
    op.create_table(
        'stage_feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.String(255), nullable=False, index=True),
        sa.Column('job_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('stage_number', sa.Integer(), nullable=False, index=True),
        sa.Column('stage_name', sa.String(100), nullable=True),
        sa.Column('field_name', sa.String(100), nullable=False, index=True),
        sa.Column('suggested_value', sa.JSON(), nullable=True),
        sa.Column('accepted_value', sa.JSON(), nullable=True),
        sa.Column('was_accepted', sa.Boolean(), default=True),
        sa.Column('was_modified', sa.Boolean(), default=False),
        sa.Column('role', sa.String(255), nullable=True, index=True),
        sa.Column('seniority', sa.String(50), nullable=True),
        sa.Column('confidence_before', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(255), nullable=True),
    )
    
    op.create_index(
        'ix_stage_feedback_company_stage',
        'stage_feedback',
        ['company_id', 'stage_number']
    )
    
    op.create_index(
        'ix_stage_feedback_field',
        'stage_feedback',
        ['company_id', 'field_name']
    )
    
    op.create_table(
        'learning_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.String(255), nullable=False, index=True),
        sa.Column('metric_type', sa.String(100), nullable=False, index=True),
        sa.Column('metric_key', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.JSON(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('sample_size', sa.Integer(), default=0),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    
    op.create_index(
        'ix_learning_analytics_company_type',
        'learning_analytics',
        ['company_id', 'metric_type']
    )


def downgrade():
    op.drop_table('learning_analytics')
    op.drop_table('stage_feedback')
    op.drop_index('ix_feature_flags_global_unique', 'feature_flags')
    op.drop_index('ix_feature_flags_key_enabled', 'feature_flags')
    op.drop_table('feature_flags')
