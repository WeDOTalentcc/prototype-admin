"""Add evaluation_criteria table for WDT-016.

Revision ID: 008_add_evaluation_criteria
Revises: 007_learning_loop_import
Create Date: 2026-02-08

Phase 3 of André's methodology: Evaluation criteria with positive/negative
evidence examples per criterion type for LLM prompt enhancement.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = '008_add_evaluation_criteria'
down_revision = '007_learning_loop_import'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'evaluation_criteria',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(300), nullable=False, index=True),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('positive_evidences', JSONB, nullable=False, server_default='[]'),
        sa.Column('negative_evidences', JSONB, nullable=False, server_default='[]'),
        sa.Column('evaluation_guidelines', sa.Text, nullable=True),
        sa.Column('effectiveness_score', sa.Float, nullable=False, server_default='0.5'),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('feedback_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('source', sa.String(50), nullable=False, server_default="'seed'"),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('evaluation_criteria')
