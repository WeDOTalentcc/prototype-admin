-- WSI (WeDoTalent Skill Index) Database Schema
-- Complete schema for scientific candidate assessment

-- ============================================================================
-- CORE WSI TABLES
-- ============================================================================

-- WSI Screening Sessions
CREATE TABLE IF NOT EXISTS wsi_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id VARCHAR NOT NULL,
    job_vacancy_id VARCHAR NOT NULL,
    screening_type VARCHAR NOT NULL CHECK (screening_type IN ('voice', 'chat', 'hybrid')),
    mode VARCHAR NOT NULL CHECK (mode IN ('compact', 'compact_plus')) DEFAULT 'compact',
    status VARCHAR NOT NULL CHECK (status IN ('in_progress', 'completed', 'cancelled')) DEFAULT 'in_progress',
    call_id VARCHAR(255),  -- OpenMic.ai call ID for voice screening
    agent_id VARCHAR(255),  -- OpenMic.ai agent ID for voice screening
    question_set_version INTEGER,
    question_set_id VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WSI Questions Generated
CREATE TABLE IF NOT EXISTS wsi_questions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR NOT NULL REFERENCES wsi_sessions(id) ON DELETE CASCADE,
    competency VARCHAR NOT NULL,
    framework VARCHAR NOT NULL CHECK (framework IN ('CBI', 'Bloom', 'Dreyfus', 'BigFive')),
    question_type VARCHAR NOT NULL CHECK (question_type IN ('autodeclaration', 'contextual', 'microcase', 'situational')),
    question_text TEXT NOT NULL,
    weight DECIMAL(3,2) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    expected_signals JSONB,
    scoring_criteria JSONB,
    sequence_order INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WSI Response Analyses
CREATE TABLE IF NOT EXISTS wsi_response_analyses (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR NOT NULL REFERENCES wsi_sessions(id) ON DELETE CASCADE,
    question_id VARCHAR NOT NULL REFERENCES wsi_questions(id) ON DELETE CASCADE,
    competency VARCHAR NOT NULL,
    response_text TEXT NOT NULL,
    response_audio_url VARCHAR,  -- OpenMic.ai recording URL
    autodeclaration_score DECIMAL(3,2) CHECK (autodeclaration_score BETWEEN 1 AND 5),
    context_score DECIMAL(3,2) CHECK (context_score BETWEEN 1 AND 5),
    bloom_level INT CHECK (bloom_level BETWEEN 1 AND 5),
    dreyfus_level INT CHECK (dreyfus_level BETWEEN 1 AND 5),
    evidences JSONB,
    red_flags JSONB,
    consistency_penalty DECIMAL(3,2) DEFAULT 0,
    final_score DECIMAL(3,2) NOT NULL CHECK (final_score BETWEEN 1 AND 5),
    justification TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WSI Results (Final Scores)
CREATE TABLE IF NOT EXISTS wsi_results (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR NOT NULL UNIQUE REFERENCES wsi_sessions(id) ON DELETE CASCADE,
    candidate_id VARCHAR NOT NULL,
    job_vacancy_id VARCHAR NOT NULL,
    technical_wsi DECIMAL(3,2) NOT NULL CHECK (technical_wsi BETWEEN 1 AND 5),
    behavioral_wsi DECIMAL(3,2) NOT NULL CHECK (behavioral_wsi BETWEEN 1 AND 5),
    overall_wsi DECIMAL(3,2) NOT NULL CHECK (overall_wsi BETWEEN 1 AND 5),
    classification VARCHAR NOT NULL CHECK (classification IN ('excelente', 'alto', 'medio', 'regular', 'baixo')),
    percentile INT CHECK (percentile BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WSI Structured Reports (for recruiters)
CREATE TABLE IF NOT EXISTS wsi_reports (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    wsi_result_id VARCHAR NOT NULL UNIQUE REFERENCES wsi_results(id) ON DELETE CASCADE,
    candidate_id VARCHAR NOT NULL,
    executive_summary TEXT NOT NULL,
    technical_analysis JSONB NOT NULL,  -- {pontos_fortes, gaps, evidencias}
    behavioral_analysis JSONB NOT NULL,  -- {colaboracao, inovacao, organizacao, resiliencia}
    cultural_fit JSONB NOT NULL,  -- {score, valores_alinhados, atencoes}
    recommendation JSONB NOT NULL,  -- {decisao, justificativa, proximos_passos}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WSI Candidate Feedbacks
CREATE TABLE IF NOT EXISTS wsi_feedbacks (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    wsi_result_id VARCHAR NOT NULL UNIQUE REFERENCES wsi_results(id) ON DELETE CASCADE,
    candidate_id VARCHAR NOT NULL,
    decision VARCHAR NOT NULL CHECK (decision IN ('aprovado', 'aguardando', 'nao_aprovado')),
    main_message TEXT NOT NULL,
    technical_strengths JSONB,
    development_opportunities JSONB,
    behavioral_strengths JSONB,
    next_steps TEXT,
    personalized_tip TEXT,
    development_plan JSONB,  -- {curto_prazo, medio_prazo}
    recommended_resources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_wsi_sessions_candidate ON wsi_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_wsi_sessions_job ON wsi_sessions(job_vacancy_id);
CREATE INDEX IF NOT EXISTS idx_wsi_sessions_status ON wsi_sessions(status);
CREATE INDEX IF NOT EXISTS idx_wsi_sessions_call_id ON wsi_sessions(call_id);
CREATE INDEX IF NOT EXISTS idx_wsi_sessions_agent_id ON wsi_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_wsi_questions_session ON wsi_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_wsi_responses_session ON wsi_response_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_wsi_responses_question ON wsi_response_analyses(question_id);
CREATE INDEX IF NOT EXISTS idx_wsi_results_candidate ON wsi_results(candidate_id);
CREATE INDEX IF NOT EXISTS idx_wsi_results_job ON wsi_results(job_vacancy_id);
CREATE INDEX IF NOT EXISTS idx_wsi_reports_candidate ON wsi_reports(candidate_id);
CREATE INDEX IF NOT EXISTS idx_wsi_feedbacks_candidate ON wsi_feedbacks(candidate_id);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: WSI Scores Overview
CREATE OR REPLACE VIEW wsi_scores_overview AS
SELECT 
    r.id as result_id,
    r.candidate_id,
    r.job_vacancy_id,
    r.overall_wsi,
    r.technical_wsi,
    r.behavioral_wsi,
    r.classification,
    r.percentile,
    s.screening_type,
    s.completed_at,
    COUNT(ra.id) as total_questions_answered,
    AVG(ra.final_score) as avg_response_score
FROM wsi_results r
JOIN wsi_sessions s ON r.session_id = s.id
LEFT JOIN wsi_response_analyses ra ON ra.session_id = s.id
WHERE s.status = 'completed'
GROUP BY r.id, r.candidate_id, r.job_vacancy_id, r.overall_wsi, r.technical_wsi, 
         r.behavioral_wsi, r.classification, r.percentile, s.screening_type, s.completed_at;

-- View: Red Flags Summary
CREATE OR REPLACE VIEW wsi_red_flags_summary AS
SELECT 
    ra.session_id,
    ra.candidate_id,
    ra.competency,
    JSONB_ARRAY_LENGTH(ra.red_flags) as red_flags_count,
    ra.red_flags,
    ra.final_score,
    ra.created_at
FROM wsi_response_analyses ra
WHERE JSONB_ARRAY_LENGTH(ra.red_flags) > 0
ORDER BY JSONB_ARRAY_LENGTH(ra.red_flags) DESC, ra.created_at DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger: Auto-update updated_at for wsi_sessions
CREATE TRIGGER update_wsi_sessions_updated_at BEFORE UPDATE ON wsi_sessions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE wsi_sessions IS 'WSI screening sessions (voice, chat, hybrid)';
COMMENT ON TABLE wsi_questions IS 'Generated WSI questions per session';
COMMENT ON TABLE wsi_response_analyses IS 'Analyzed candidate responses with scores 1-5';
COMMENT ON TABLE wsi_results IS 'Final WSI scores (technical, behavioral, overall)';
COMMENT ON TABLE wsi_reports IS 'Structured reports for recruiters';
COMMENT ON TABLE wsi_feedbacks IS 'Constructive feedbacks for candidates';
