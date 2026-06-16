// Onda 2 F1 (2026-05-27) — types canonical do endpoint
// GET /agent-monitoring/candidate/{candidate_id}/touches.
// Schema espelha `CandidateTouchesResponse` em
// lia-agent-system/app/api/v1/agent_monitoring.py (Onda 2 B3).

export interface CandidateTouch {
  execution_id: string
  agent_id: string
  agent_name: string
  action_type: string
  timestamp: string
  outcome: string | null
}

export interface CandidateTouchesResponse {
  candidate_id: string
  touch_count: number
  last_touch_at: string | null
  touches: CandidateTouch[]
}
