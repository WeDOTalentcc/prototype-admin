-- Migration: 006_approval_workflow_fields.sql
-- Description: Add approval workflow fields to job_vacancies table
-- Created: 2025-12-01

-- Add approval workflow columns
ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS approval_requested_at TIMESTAMP;
ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS approval_requested_by VARCHAR(255);
ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255);
ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE job_vacancies ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Create index for approval status queries
CREATE INDEX IF NOT EXISTS idx_job_vacancies_approval_status ON job_vacancies(approval_status);
CREATE INDEX IF NOT EXISTS idx_job_vacancies_approval_requested_at ON job_vacancies(approval_requested_at);
