-- Migration: Add multi-tenancy constraints for company_id columns
-- Date: 2024-12-01
-- Description: Ensures all tenant-scoped tables have proper NOT NULL constraints
--              with default values for company isolation

-- Step 1: Update any NULL company_id values to 'default' before adding constraints

-- job_vacancies table
UPDATE job_vacancies SET company_id = 'default' WHERE company_id IS NULL;

-- vacancy_candidates table  
UPDATE vacancy_candidates SET company_id = 'default' WHERE company_id IS NULL;

-- archetypes table (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'archetypes') THEN
        UPDATE archetypes SET company_id = 'default' WHERE company_id IS NULL;
    END IF;
END $$;

-- ats_integrations table (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ats_integrations') THEN
        UPDATE ats_integrations SET company_id = 'default' WHERE company_id IS NULL;
    END IF;
END $$;

-- Step 2: Add NOT NULL constraints with default values

-- job_vacancies: Alter column to NOT NULL with default
ALTER TABLE job_vacancies 
    ALTER COLUMN company_id SET NOT NULL,
    ALTER COLUMN company_id SET DEFAULT 'default';

-- vacancy_candidates: Alter column to NOT NULL with default
ALTER TABLE vacancy_candidates 
    ALTER COLUMN company_id SET NOT NULL,
    ALTER COLUMN company_id SET DEFAULT 'default';

-- archetypes: Alter column to NOT NULL with default (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'archetypes') THEN
        ALTER TABLE archetypes 
            ALTER COLUMN company_id SET NOT NULL,
            ALTER COLUMN company_id SET DEFAULT 'default';
    END IF;
END $$;

-- ats_integrations: Alter column to NOT NULL with default (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ats_integrations') THEN
        ALTER TABLE ats_integrations 
            ALTER COLUMN company_id SET NOT NULL,
            ALTER COLUMN company_id SET DEFAULT 'default';
    END IF;
END $$;

-- Step 3: Create indexes for efficient tenant queries (if not exist)
CREATE INDEX IF NOT EXISTS idx_job_vacancies_company_id ON job_vacancies(company_id);
CREATE INDEX IF NOT EXISTS idx_vacancy_candidates_company_id ON vacancy_candidates(company_id);

-- Step 4: Add audit comment
COMMENT ON COLUMN job_vacancies.company_id IS 'Tenant identifier for multi-tenancy. Required for all records. Default is "default" for legacy data.';
COMMENT ON COLUMN vacancy_candidates.company_id IS 'Tenant identifier for multi-tenancy. Required for all records. Inherits from parent job_vacancy.';
