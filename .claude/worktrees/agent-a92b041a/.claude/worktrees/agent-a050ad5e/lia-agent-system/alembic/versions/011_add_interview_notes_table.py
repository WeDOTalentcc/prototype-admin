"""Add interview_notes table for persistent WSI Score Card storage.

Revision ID: 011_add_interview_notes_table
Revises: 010_add_human_review_gate
Create Date: 2026-02-28

A4 — Interview Notes Persistence:
Replaces the in-memory dict `interview_notes_db` in interview_notes.py
with a proper PostgreSQL table. Mirrors the frontend InterviewNote type
(WSI Score Card, questions, answers, LIA parecer, recommendation).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = '011_add_interview_notes_table'
down_revision = '010_add_human_review_gate'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'interview_notes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_name', sa.String(255), nullable=True),
        sa.Column('job_id', UUID(as_uuid=True), nullable=True),
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.Column('scheduled_interview_id', sa.String(255), nullable=True),
        sa.Column('interviewer_id', sa.String(255), nullable=True),
        sa.Column('recruiter_name', sa.String(255), nullable=True),
        sa.Column('interview_date', sa.DateTime(), nullable=True),
        sa.Column('interview_type', sa.String(50), server_default='structured'),
        sa.Column('questions', JSON, server_default='[]'),
        sa.Column('blocks', JSON, server_default='[]'),
        sa.Column('general_notes', sa.Text(), nullable=True),
        sa.Column('transcription', sa.Text(), nullable=True),
        sa.Column('transcription_source', sa.String(50), nullable=True),
        sa.Column('lia_parecer', sa.Text(), nullable=True),
        sa.Column('lia_parecer_editado', sa.Boolean(), server_default='false'),
        sa.Column('wsi_score', JSON, nullable=True),
        sa.Column('recommendation', sa.String(50), nullable=True),
        sa.Column('next_stage', sa.String(100), nullable=True),
        sa.Column('feedback_sent', sa.Boolean(), server_default='false'),
        sa.Column('feedback_scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('created_by', sa.String(255), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index('idx_interview_notes_company', 'interview_notes', ['company_id'])
    op.create_index('idx_interview_notes_candidate', 'interview_notes', ['candidate_id'])
    op.create_index('idx_interview_notes_job', 'interview_notes', ['job_id'],
                    postgresql_where=sa.text('job_id IS NOT NULL'))
    op.create_index('idx_interview_notes_status', 'interview_notes', ['status'])
    op.create_index('idx_interview_notes_created', 'interview_notes', ['created_at'])


def downgrade():
    op.drop_index('idx_interview_notes_created', table_name='interview_notes')
    op.drop_index('idx_interview_notes_status', table_name='interview_notes')
    op.drop_index('idx_interview_notes_job', table_name='interview_notes')
    op.drop_index('idx_interview_notes_candidate', table_name='interview_notes')
    op.drop_index('idx_interview_notes_company', table_name='interview_notes')
    op.drop_table('interview_notes')
