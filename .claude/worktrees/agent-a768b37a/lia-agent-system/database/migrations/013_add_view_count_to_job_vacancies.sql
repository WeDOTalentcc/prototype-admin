-- Migration: Add view_count column to job_vacancies table
-- Date: 2026-01-19
-- Purpose: Track public page views for job vacancies

ALTER TABLE job_vacancies 
ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
