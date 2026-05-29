// Onda C4.2 (2026-05-29) — types canonical do endpoint GET /agent-monitoring/daily-digest.
// Schema espelha `DailyDigestResponse` em lia-agent-system/app/api/v1/agent_monitoring.py (Onda C4.2).
//
// REGRA: drift TS <-> Python = quebra runtime. Mudar campo aqui exige mudar
// no backend canonical e vice-versa.

export type DigestKind =
  | "decision_approved"
  | "candidates_surfaced"
  | "agent_error"
  | "pending_approval"
  | "high_cost"

export type DigestSeverity = "info" | "attention" | "celebration"

export interface DigestItem {
  kind: DigestKind
  agent_id: string
  agent_name: string
  summary: string
  target_type: string | null
  target_name: string | null
  count: number | null
  severity: DigestSeverity
  execution_id: string | null
  timestamp: string
}

export interface DailyDigestResponse {
  period_hours: number
  generated_at: string
  items: DigestItem[]
  total_runs: number
  total_candidates_processed: number
}
