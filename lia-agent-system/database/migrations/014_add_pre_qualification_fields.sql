-- Migration: Add pre-qualification fields to whatsapp_conversations
-- Date: 2026-01-23
-- Purpose: Support intelligent pre-qualification workflow with humanized messages

-- Add pre-qualification fields
ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS pre_qualification_score INTEGER;

ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS pre_qualification_result VARCHAR(50);

ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS pre_qualification_matched JSONB;

ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS pre_qualification_missing JSONB;

ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS pre_qualification_decision VARCHAR(50);

ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS pre_qualification_at TIMESTAMP WITH TIME ZONE;

-- Add existing candidate tracking fields
ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS is_existing_candidate BOOLEAN DEFAULT FALSE;

ALTER TABLE whatsapp_conversations 
ADD COLUMN IF NOT EXISTS existing_candidate_since TIMESTAMP WITH TIME ZONE;

-- Add new conversation state value to enum if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'pre_qualification' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'conversation_state_enum')
    ) THEN
        ALTER TYPE conversation_state_enum ADD VALUE IF NOT EXISTS 'pre_qualification' AFTER 'confirming_cv';
    END IF;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Create index for analytics on pre-qualification results
CREATE INDEX IF NOT EXISTS idx_whatsapp_conv_pre_qual_result 
ON whatsapp_conversations(pre_qualification_result) 
WHERE pre_qualification_result IS NOT NULL;

-- Create index for existing candidate lookups
CREATE INDEX IF NOT EXISTS idx_whatsapp_conv_existing_candidate 
ON whatsapp_conversations(is_existing_candidate) 
WHERE is_existing_candidate = TRUE;

COMMENT ON COLUMN whatsapp_conversations.pre_qualification_score IS 'Internal adherence score (0-100), not shown to candidate';
COMMENT ON COLUMN whatsapp_conversations.pre_qualification_result IS 'Result category: aligned, partial, distant, very_distant';
COMMENT ON COLUMN whatsapp_conversations.pre_qualification_decision IS 'Candidate decision: continue, view_other_jobs, talent_pool, declined, auto_advanced';
COMMENT ON COLUMN whatsapp_conversations.is_existing_candidate IS 'Whether candidate already existed in database before this application';
