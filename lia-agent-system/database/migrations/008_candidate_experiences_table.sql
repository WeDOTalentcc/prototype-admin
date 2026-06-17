-- Migration 008: Create candidate_experiences table for rich company data and sector-based search
-- Date: December 2025
-- Purpose: Store detailed professional experiences with industries for deep search capabilities

-- Create candidate_experiences table
CREATE TABLE IF NOT EXISTS candidate_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    
    -- Company Information
    company_name VARCHAR(255) NOT NULL,
    company_linkedin_url VARCHAR(500),
    company_domain VARCHAR(255),
    
    -- Role Information
    title VARCHAR(255),
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    duration_years FLOAT,
    is_current BOOLEAN DEFAULT FALSE,
    
    -- Description
    description TEXT,
    location VARCHAR(255),
    
    -- Rich Company Data (for sector-based search)
    industries VARCHAR(255)[] DEFAULT '{}',
    company_size VARCHAR(50),
    company_size_range VARCHAR(50),
    technologies VARCHAR(255)[] DEFAULT '{}',
    is_startup BOOLEAN,
    company_founded_year INTEGER,
    company_annual_revenue FLOAT,
    
    -- Ordering
    sequence_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_candidate_experiences_candidate_id ON candidate_experiences(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_experiences_company_name ON candidate_experiences(company_name);
CREATE INDEX IF NOT EXISTS idx_candidate_experiences_industries ON candidate_experiences USING GIN(industries);
CREATE INDEX IF NOT EXISTS idx_candidate_experiences_technologies ON candidate_experiences USING GIN(technologies);
CREATE INDEX IF NOT EXISTS idx_candidate_experiences_is_startup ON candidate_experiences(is_startup) WHERE is_startup = TRUE;

-- Add comment for documentation
COMMENT ON TABLE candidate_experiences IS 'Detailed professional experiences with rich company data for sector-based search';
COMMENT ON COLUMN candidate_experiences.industries IS 'Array of industry sectors (e.g., Technology, Fintech, Healthcare) - indexed for search';
COMMENT ON COLUMN candidate_experiences.technologies IS 'Array of technologies/stack used at the company';
