-- Migration: Add extended candidate fields for full column configuration support
-- Date: 2024-11-29

-- Basic Information - Additional contacts and avatar
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS secondary_email VARCHAR(255);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS mobile_phone VARCHAR(50);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS secondary_phone VARCHAR(50);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);

-- Personal Information
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS gender VARCHAR(50);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS nationality VARCHAR(100);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS marital_status VARCHAR(50);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS cpf VARCHAR(14);

-- Professional Profile - Additional
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS self_introduction TEXT;

-- Skills & Competencies - Additional
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS interests TEXT[] DEFAULT '{}';

-- Location - Full Address
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS address_street VARCHAR(255);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS address_number VARCHAR(20);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS address_district VARCHAR(100);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS address_zip VARCHAR(20);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS address_complement VARCHAR(255);

-- Work Preferences - Additional
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS mobility BOOLEAN DEFAULT FALSE;

-- Salary - Current and Expectations by contract type
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS current_salary FLOAT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS salary_expectation_clt FLOAT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS salary_expectation_pj FLOAT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS salary_expectation_freelance FLOAT;

-- Registration status
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS completed_register BOOLEAN DEFAULT FALSE;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS accept_terms BOOLEAN DEFAULT FALSE;

-- Create indexes for common search fields
CREATE INDEX IF NOT EXISTS idx_candidates_cpf ON candidates(cpf);
CREATE INDEX IF NOT EXISTS idx_candidates_gender ON candidates(gender);
CREATE INDEX IF NOT EXISTS idx_candidates_nationality ON candidates(nationality);
