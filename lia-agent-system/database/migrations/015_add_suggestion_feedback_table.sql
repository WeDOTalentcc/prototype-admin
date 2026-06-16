-- Create suggestion_feedback table for recording user feedback on suggestions

CREATE TABLE IF NOT EXISTS suggestion_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    suggested_value JSONB,
    actual_value JSONB,
    accepted INTEGER NOT NULL DEFAULT 0,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    
    -- Indexes for common queries
    CONSTRAINT fk_company_id_sf FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE INDEX idx_suggestion_feedback_company_id ON suggestion_feedback(company_id);
CREATE INDEX idx_suggestion_feedback_field_name ON suggestion_feedback(field_name);
CREATE INDEX idx_suggestion_feedback_created_at ON suggestion_feedback(created_at);
