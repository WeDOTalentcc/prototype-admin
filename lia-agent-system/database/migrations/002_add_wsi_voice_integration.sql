-- Migration: Add voice integration columns to wsi_sessions
-- Links WSI sessions with OpenMic.ai calls

-- Add call_id column (OpenMic.ai call identifier)
ALTER TABLE wsi_sessions
ADD COLUMN IF NOT EXISTS call_id VARCHAR(255);

-- Add agent_id column (OpenMic.ai agent identifier)
ALTER TABLE wsi_sessions
ADD COLUMN IF NOT EXISTS agent_id VARCHAR(255);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_wsi_sessions_call_id ON wsi_sessions(call_id);
CREATE INDEX IF NOT EXISTS idx_wsi_sessions_agent_id ON wsi_sessions(agent_id);

-- Add comment
COMMENT ON COLUMN wsi_sessions.call_id IS 'OpenMic.ai call ID for voice screening sessions';
COMMENT ON COLUMN wsi_sessions.agent_id IS 'OpenMic.ai agent ID used for the voice screening';
