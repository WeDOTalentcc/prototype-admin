-- Migration 010: Add company_id to alert_preferences for multi-tenant isolation
-- This is a CRITICAL security fix to prevent cross-tenant access

-- Add company_id column to alert_preferences
ALTER TABLE alert_preferences
ADD COLUMN IF NOT EXISTS company_id VARCHAR(255);

-- Create index on company_id for performance
CREATE INDEX IF NOT EXISTS idx_alert_preferences_company_id ON alert_preferences(company_id);

-- Create composite index for efficient multi-tenant queries
CREATE INDEX IF NOT EXISTS idx_alert_preferences_company_user ON alert_preferences(company_id, user_id);

-- For existing records without company_id, they will be orphaned
-- and should be deleted or migrated by a data migration script
-- UPDATE alert_preferences SET company_id = 'legacy' WHERE company_id IS NULL;

-- After data migration, make the column NOT NULL
-- ALTER TABLE alert_preferences ALTER COLUMN company_id SET NOT NULL;
