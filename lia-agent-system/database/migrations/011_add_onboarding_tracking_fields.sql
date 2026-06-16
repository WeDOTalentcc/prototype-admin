-- Migration: Add onboarding tracking fields to client_accounts
-- Date: 2026-01-12
-- Description: Adds fields to track onboarding progress for each client

-- Add welcome email tracking fields
ALTER TABLE client_accounts 
ADD COLUMN IF NOT EXISTS welcome_email_sent BOOLEAN DEFAULT FALSE;

ALTER TABLE client_accounts 
ADD COLUMN IF NOT EXISTS welcome_email_sent_at TIMESTAMP;

-- Add WorkOS organization tracking fields
ALTER TABLE client_accounts 
ADD COLUMN IF NOT EXISTS workos_organization_created BOOLEAN DEFAULT FALSE;

ALTER TABLE client_accounts 
ADD COLUMN IF NOT EXISTS workos_organization_created_at TIMESTAMP;

-- Add SSO configuration tracking fields
ALTER TABLE client_accounts 
ADD COLUMN IF NOT EXISTS sso_configured BOOLEAN DEFAULT FALSE;

ALTER TABLE client_accounts 
ADD COLUMN IF NOT EXISTS sso_configured_at TIMESTAMP;

-- Create index for filtering by onboarding status
CREATE INDEX IF NOT EXISTS idx_client_onboarding_status 
ON client_accounts (welcome_email_sent, workos_organization_created, sso_configured);
