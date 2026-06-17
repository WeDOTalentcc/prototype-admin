-- Migration: 005_communication_system.sql
-- Description: Communication system tables for approval workflow, audit logging, LGPD compliance, and quarantine
-- Created: 2025-12-01

-- Note: These tables are created automatically by SQLAlchemy create_all
-- This migration file serves as documentation and can be used for manual setup if needed

-- Pending Approvals Table (Human-in-the-Loop)
CREATE TABLE IF NOT EXISTS pending_approvals (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    candidate_id VARCHAR NOT NULL,
    candidate_name VARCHAR(255),
    candidate_email VARCHAR(255),
    candidate_phone VARCHAR(50),
    job_id VARCHAR,
    job_title VARCHAR(255),
    message_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    ai_personalization TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    requested_by VARCHAR NOT NULL,
    reviewed_by VARCHAR,
    review_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    extra_data JSON DEFAULT '{}'::json
);

CREATE INDEX IF NOT EXISTS idx_pending_approvals_company ON pending_approvals(company_id);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_candidate ON pending_approvals(candidate_id);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_job ON pending_approvals(job_id);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_status ON pending_approvals(status);

-- Communication Log Table (Audit Trail)
CREATE TABLE IF NOT EXISTS communication_logs (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    candidate_id VARCHAR NOT NULL,
    candidate_email VARCHAR(255),
    candidate_phone VARCHAR(50),
    job_id VARCHAR,
    message_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    subject VARCHAR(500),
    body TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    provider VARCHAR(50),
    provider_message_id VARCHAR(255),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSON DEFAULT '{}'::json
);

CREATE INDEX IF NOT EXISTS idx_communication_logs_company ON communication_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_communication_logs_candidate ON communication_logs(candidate_id);
CREATE INDEX IF NOT EXISTS idx_communication_logs_status ON communication_logs(status);
CREATE INDEX IF NOT EXISTS idx_communication_logs_created_at ON communication_logs(created_at);

-- Candidate Opt-Outs Table (LGPD Compliance)
CREATE TABLE IF NOT EXISTS candidate_opt_outs (
    id VARCHAR PRIMARY KEY,
    candidate_id VARCHAR NOT NULL UNIQUE,
    candidate_email VARCHAR(255),
    candidate_phone VARCHAR(50),
    opt_out_reason TEXT,
    channels JSON DEFAULT '["email", "whatsapp", "sms"]'::json,
    opted_out_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opted_in_at TIMESTAMP,
    consent_ip VARCHAR(50),
    consent_user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidate_opt_outs_candidate ON candidate_opt_outs(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_opt_outs_email ON candidate_opt_outs(candidate_email);

-- Candidate Quarantine Table (Post-Rejection Period)
CREATE TABLE IF NOT EXISTS candidate_quarantines (
    id VARCHAR PRIMARY KEY,
    candidate_id VARCHAR NOT NULL,
    company_id VARCHAR NOT NULL,
    job_id VARCHAR,
    reason VARCHAR(50) NOT NULL,
    quarantine_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quarantine_end TIMESTAMP NOT NULL,
    lifted_at TIMESTAMP,
    lifted_by VARCHAR,
    lift_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidate_quarantines_candidate ON candidate_quarantines(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_quarantines_company ON candidate_quarantines(company_id);
CREATE INDEX IF NOT EXISTS idx_candidate_quarantines_end ON candidate_quarantines(quarantine_end);

-- Personalized Feedback Records Table
CREATE TABLE IF NOT EXISTS personalized_feedback_records (
    id VARCHAR PRIMARY KEY,
    company_id VARCHAR NOT NULL,
    candidate_id VARCHAR NOT NULL,
    candidate_name VARCHAR(255),
    job_id VARCHAR,
    job_title VARCHAR(255),
    feedback_type VARCHAR(50) DEFAULT 'rejection',
    tone VARCHAR(20) DEFAULT 'warm',
    channel VARCHAR(20) DEFAULT 'email',
    subject VARCHAR(500),
    body TEXT,
    whatsapp_version TEXT,
    personalization_data JSON DEFAULT '{}'::json,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by VARCHAR,
    approved_at TIMESTAMP,
    edited_subject VARCHAR(500),
    edited_body TEXT,
    editor_notes TEXT,
    sent_at TIMESTAMP,
    sent_channel VARCHAR(20),
    send_result JSON,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    extra_data JSON DEFAULT '{}'::json,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_personalized_feedback_company ON personalized_feedback_records(company_id);
CREATE INDEX IF NOT EXISTS idx_personalized_feedback_candidate ON personalized_feedback_records(candidate_id);
CREATE INDEX IF NOT EXISTS idx_personalized_feedback_status ON personalized_feedback_records(status);
CREATE INDEX IF NOT EXISTS idx_personalized_feedback_created ON personalized_feedback_records(created_at);
