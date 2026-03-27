-- Migration: 007_data_hygiene_company_ids.sql
-- Description: Data hygiene migration to replace "default" company_id with real company IDs
-- Created: 2025-12-01
-- Purpose: Ensure all tenant-scoped records have proper company associations for multi-tenancy
--
-- This migration:
-- 1. Creates a simple 'companies' table for tenant management if it doesn't exist
-- 2. Creates a "demo_company" entry for demonstration/development purposes
-- 3. Updates all existing records with company_id='default' to use 'demo_company'
-- 4. Updates the default value constraints for future records

-- Start transaction for atomicity
BEGIN;

-- ============================================================================
-- Step 1: Create the companies table if it doesn't exist
-- ============================================================================
-- This table serves as the source of truth for valid company/tenant identifiers
-- The company_id fields in other tables reference this table's id column

CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add comment to explain the table purpose
COMMENT ON TABLE companies IS 'Simple tenant table for multi-tenancy. Stores valid company identifiers that are referenced by other tables (users, job_vacancies, vacancy_candidates, etc.)';

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active);

-- ============================================================================
-- Step 2: Create the demo_company entry
-- ============================================================================
-- This is the default company for demonstration and development purposes
-- All legacy "default" company_id values will be migrated to this company

INSERT INTO companies (id, name, display_name, is_active, is_demo, created_at, updated_at)
VALUES (
    'demo_company',
    'Demo Company',
    'Demo Company - Development/Testing',
    TRUE,
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- Step 3: Update existing records with company_id='default'
-- ============================================================================
-- Migrate all legacy 'default' values to the new 'demo_company' identifier

-- Update users table
UPDATE users 
SET company_id = 'demo_company', 
    updated_at = CURRENT_TIMESTAMP
WHERE company_id = 'default';

-- Update job_vacancies table
UPDATE job_vacancies 
SET company_id = 'demo_company',
    updated_at = CURRENT_TIMESTAMP
WHERE company_id = 'default';

-- Update vacancy_candidates table
UPDATE vacancy_candidates 
SET company_id = 'demo_company',
    updated_at = CURRENT_TIMESTAMP
WHERE company_id = 'default';

-- Update archetypes table if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'archetypes') THEN
        UPDATE archetypes 
        SET company_id = 'demo_company'
        WHERE company_id = 'default';
    END IF;
END $$;

-- Update ats_integrations table if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ats_integrations') THEN
        UPDATE ats_integrations 
        SET company_id = 'demo_company'
        WHERE company_id = 'default';
    END IF;
END $$;

-- Update notifications table if it exists and has company_id
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notifications' AND column_name = 'company_id'
    ) THEN
        UPDATE notifications 
        SET company_id = 'demo_company'
        WHERE company_id = 'default';
    END IF;
END $$;

-- ============================================================================
-- Step 4: Update default constraints for future records
-- ============================================================================
-- Change the default value from 'default' to 'demo_company' for new records

ALTER TABLE users 
    ALTER COLUMN company_id SET DEFAULT 'demo_company';

ALTER TABLE job_vacancies 
    ALTER COLUMN company_id SET DEFAULT 'demo_company';

ALTER TABLE vacancy_candidates 
    ALTER COLUMN company_id SET DEFAULT 'demo_company';

-- Update archetypes if exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'archetypes') THEN
        ALTER TABLE archetypes 
            ALTER COLUMN company_id SET DEFAULT 'demo_company';
    END IF;
END $$;

-- Update ats_integrations if exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ats_integrations') THEN
        ALTER TABLE ats_integrations 
            ALTER COLUMN company_id SET DEFAULT 'demo_company';
    END IF;
END $$;

-- ============================================================================
-- Step 5: Add audit comments
-- ============================================================================

COMMENT ON COLUMN users.company_id IS 'Tenant identifier for multi-tenancy. References companies.id. Default is "demo_company" for new users.';
COMMENT ON COLUMN job_vacancies.company_id IS 'Tenant identifier for multi-tenancy. References companies.id. Default is "demo_company" for development.';
COMMENT ON COLUMN vacancy_candidates.company_id IS 'Tenant identifier for multi-tenancy. References companies.id. Inherits from parent job_vacancy.';

-- Commit the transaction
COMMIT;

-- ============================================================================
-- Verification queries (run manually to verify migration)
-- ============================================================================
-- SELECT COUNT(*) FROM companies WHERE id = 'demo_company';
-- SELECT COUNT(*) FROM users WHERE company_id = 'default';
-- SELECT COUNT(*) FROM job_vacancies WHERE company_id = 'default';
-- SELECT COUNT(*) FROM vacancy_candidates WHERE company_id = 'default';
