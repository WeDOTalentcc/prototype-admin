-- Migration 009: Add new filter fields to candidate tables
-- Date: December 2025
-- Purpose: Add fields for advanced filtering: funding stage, company HQ location,
--          institution details, timezone, and location history

-- =============================================================================
-- CANDIDATE_EXPERIENCES TABLE: Add company metadata fields
-- =============================================================================

-- Funding stage of the company (e.g., Seed, Series A, Series B, etc.)
ALTER TABLE candidate_experiences 
ADD COLUMN IF NOT EXISTS funding_stage VARCHAR(50);

-- Company tags/keywords for additional categorization
ALTER TABLE candidate_experiences 
ADD COLUMN IF NOT EXISTS company_tags VARCHAR(255)[] DEFAULT '{}';

-- Company headquarters location
ALTER TABLE candidate_experiences 
ADD COLUMN IF NOT EXISTS company_hq_city VARCHAR(100);

ALTER TABLE candidate_experiences 
ADD COLUMN IF NOT EXISTS company_hq_state VARCHAR(100);

ALTER TABLE candidate_experiences 
ADD COLUMN IF NOT EXISTS company_hq_country VARCHAR(100);

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_candidate_experiences_funding_stage 
ON candidate_experiences(funding_stage) WHERE funding_stage IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_candidate_experiences_company_hq_country 
ON candidate_experiences(company_hq_country) WHERE company_hq_country IS NOT NULL;

-- =============================================================================
-- CANDIDATE_EDUCATION TABLE: Add institution metadata fields
-- =============================================================================

-- Institution location details
ALTER TABLE candidate_education 
ADD COLUMN IF NOT EXISTS institution_city VARCHAR(100);

ALTER TABLE candidate_education 
ADD COLUMN IF NOT EXISTS institution_state VARCHAR(100);

ALTER TABLE candidate_education 
ADD COLUMN IF NOT EXISTS institution_country VARCHAR(100);

-- Institution ranking (e.g., QS World Ranking, national ranking)
ALTER TABLE candidate_education 
ADD COLUMN IF NOT EXISTS institution_ranking INTEGER;

-- Institution tier classification (e.g., Tier 1, Tier 2, Top 10, Top 50)
ALTER TABLE candidate_education 
ADD COLUMN IF NOT EXISTS institution_tier VARCHAR(50);

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_candidate_education_institution_country 
ON candidate_education(institution_country) WHERE institution_country IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_candidate_education_institution_tier 
ON candidate_education(institution_tier) WHERE institution_tier IS NOT NULL;

-- =============================================================================
-- CANDIDATES TABLE: Add timezone and location history
-- =============================================================================

-- Candidate's timezone (e.g., America/Sao_Paulo, Europe/London)
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50);

-- Past locations as JSON array of location objects
-- Format: [{"city": "...", "state": "...", "country": "...", "from": "...", "to": "..."}]
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS past_locations JSONB DEFAULT '[]'::jsonb;

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_candidates_timezone 
ON candidates(timezone) WHERE timezone IS NOT NULL;

-- Comments for documentation
COMMENT ON COLUMN candidate_experiences.funding_stage IS 'Company funding stage: Seed, Series A, Series B, Series C+, IPO, Bootstrapped, etc.';
COMMENT ON COLUMN candidate_experiences.company_tags IS 'Additional company tags/keywords for categorization';
COMMENT ON COLUMN candidate_experiences.company_hq_city IS 'Company headquarters city';
COMMENT ON COLUMN candidate_experiences.company_hq_state IS 'Company headquarters state/province';
COMMENT ON COLUMN candidate_experiences.company_hq_country IS 'Company headquarters country';
COMMENT ON COLUMN candidate_education.institution_city IS 'Educational institution city';
COMMENT ON COLUMN candidate_education.institution_state IS 'Educational institution state/province';
COMMENT ON COLUMN candidate_education.institution_country IS 'Educational institution country';
COMMENT ON COLUMN candidate_education.institution_ranking IS 'Institution ranking (e.g., QS World Ranking number)';
COMMENT ON COLUMN candidate_education.institution_tier IS 'Institution tier classification: Tier 1, Tier 2, Top 10, Top 50';
COMMENT ON COLUMN candidates.timezone IS 'Candidate timezone identifier (e.g., America/Sao_Paulo)';
COMMENT ON COLUMN candidates.past_locations IS 'JSON array of past locations with dates';
