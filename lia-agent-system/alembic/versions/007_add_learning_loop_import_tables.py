"""Add Learning Loop import tables (ImportedJobDescription, ImportBatch, ClientSkillCatalog).

Revision ID: 007_learning_loop_import
Revises: 006_add_conversation_memory_tables
Create Date: 2026-02-02

Phase 1B of Learning Loop: Import JDs from ATS/HRIS to enable company-specific
suggestions in the wizard. Implements data priority tiers:
- Imported JDs from ATS (85% precision)
- Client skill catalogs built from imports
- Batch tracking for large imports
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY


revision = '007_learning_loop_import'
down_revision = '006_add_conversation_memory'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'imported_job_descriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('external_id', sa.String(255), nullable=True, index=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual_upload'),
        sa.Column('import_batch_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('job_title_original', sa.String(500), nullable=False),
        sa.Column('job_title_normalized', sa.String(255), nullable=True, index=True),
        sa.Column('department', sa.String(100), nullable=True, index=True),
        sa.Column('area', sa.String(100), nullable=True),
        sa.Column('team', sa.String(100), nullable=True),
        sa.Column('seniority', sa.String(50), nullable=True, index=True),
        sa.Column('seniority_confidence', sa.Float(), server_default='0.0'),
        sa.Column('employment_type', sa.String(50), nullable=True),
        sa.Column('work_model', sa.String(50), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('description_raw', sa.Text(), nullable=True),
        sa.Column('description_parsed', sa.Text(), nullable=True),
        sa.Column('responsibilities', ARRAY(sa.String()), server_default='{}'),
        sa.Column('responsibilities_raw', sa.Text(), nullable=True),
        sa.Column('technical_skills', sa.JSON(), server_default='[]'),
        sa.Column('behavioral_competencies', sa.JSON(), server_default='[]'),
        sa.Column('requirements_mandatory', ARRAY(sa.String()), server_default='{}'),
        sa.Column('requirements_desirable', ARRAY(sa.String()), server_default='{}'),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('salary_currency', sa.String(10), server_default='BRL'),
        sa.Column('salary_period', sa.String(20), server_default='monthly'),
        sa.Column('salary_confidential', sa.Boolean(), server_default='false'),
        sa.Column('benefits', ARRAY(sa.String()), server_default='{}'),
        sa.Column('benefits_details', sa.JSON(), server_default='{}'),
        sa.Column('hiring_manager', sa.String(255), nullable=True),
        sa.Column('hiring_manager_email', sa.String(255), nullable=True),
        sa.Column('recruiter', sa.String(255), nullable=True),
        sa.Column('headcount', sa.Integer(), server_default='1'),
        sa.Column('job_status', sa.String(50), nullable=True),
        sa.Column('was_filled', sa.Boolean(), nullable=True),
        sa.Column('candidates_count', sa.Integer(), nullable=True),
        sa.Column('time_to_fill_days', sa.Integer(), nullable=True),
        sa.Column('hired_candidate_id', sa.String(255), nullable=True),
        sa.Column('created_date_original', sa.DateTime(), nullable=True),
        sa.Column('closed_date_original', sa.DateTime(), nullable=True),
        sa.Column('processing_status', sa.String(50), server_default='raw'),
        sa.Column('parsing_confidence', sa.Float(), server_default='0.0'),
        sa.Column('parsing_errors', sa.JSON(), server_default='[]'),
        sa.Column('metadata_raw', sa.JSON(), server_default='{}'),
        sa.Column('is_used_for_learning', sa.Boolean(), server_default='true'),
        sa.Column('times_used_as_template', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )
    
    op.create_index('idx_imported_jd_company_title', 'imported_job_descriptions', ['company_id', 'job_title_normalized'])
    op.create_index('idx_imported_jd_company_dept', 'imported_job_descriptions', ['company_id', 'department'])
    op.create_index('idx_imported_jd_company_source', 'imported_job_descriptions', ['company_id', 'source'])
    op.create_index('idx_imported_jd_batch', 'imported_job_descriptions', ['import_batch_id'])
    op.create_index('idx_imported_jd_learning', 'imported_job_descriptions', ['company_id', 'is_used_for_learning'])
    
    op.create_table(
        'import_batches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('source_connection_id', UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('total_records', sa.Integer(), server_default='0'),
        sa.Column('processed_records', sa.Integer(), server_default='0'),
        sa.Column('successful_records', sa.Integer(), server_default='0'),
        sa.Column('failed_records', sa.Integer(), server_default='0'),
        sa.Column('skipped_records', sa.Integer(), server_default='0'),
        sa.Column('import_config', sa.JSON(), server_default='{}'),
        sa.Column('errors', sa.JSON(), server_default='[]'),
        sa.Column('warnings', sa.JSON(), server_default='[]'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), index=True),
    )
    
    op.create_index('idx_import_batch_company', 'import_batches', ['company_id', 'status'])
    
    op.create_table(
        'client_skill_catalogs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('skill_name', sa.String(255), nullable=False),
        sa.Column('skill_name_normalized', sa.String(255), nullable=False, index=True),
        sa.Column('skill_type', sa.String(50), server_default='technical'),
        sa.Column('frequency', sa.Integer(), server_default='1'),
        sa.Column('associated_titles', ARRAY(sa.String()), server_default='{}'),
        sa.Column('associated_departments', ARRAY(sa.String()), server_default='{}'),
        sa.Column('associated_seniorities', ARRAY(sa.String()), server_default='{}'),
        sa.Column('typical_level', sa.String(50), nullable=True),
        sa.Column('source_jds', ARRAY(sa.String()), server_default='{}'),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    
    op.create_index('idx_client_skill_lookup', 'client_skill_catalogs', ['company_id', 'skill_name_normalized'])
    op.create_index('idx_client_skill_type', 'client_skill_catalogs', ['company_id', 'skill_type', 'is_active'])


def downgrade():
    op.drop_table('client_skill_catalogs')
    op.drop_table('import_batches')
    op.drop_table('imported_job_descriptions')
