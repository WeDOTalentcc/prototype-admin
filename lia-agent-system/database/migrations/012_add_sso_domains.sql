-- Migration: Add sso_domains column to company_workos_config
-- Date: 2026-01-12
-- Description: Adds sso_domains array to enable automatic SSO detection by email domain

ALTER TABLE company_workos_config 
ADD COLUMN IF NOT EXISTS sso_domains TEXT[] DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_company_workos_config_sso_domains 
ON company_workos_config USING GIN (sso_domains);

COMMENT ON COLUMN company_workos_config.sso_domains IS 'List of email domains that should trigger SSO login (e.g., ["company.com", "subsidiary.com"])';
