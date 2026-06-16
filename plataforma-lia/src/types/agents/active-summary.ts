// Onda 2 F1 (2026-05-27) — types canonical do endpoint GET /agent-monitoring/active-summary.
// Schema espelha `ActiveSummaryResponse` em lia-agent-system/app/api/v1/agent_monitoring.py (Onda 2 B1).
//
// REGRA: drift TS <-> Python = quebra runtime. Mudar campo aqui exige mudar
// no backend canonical e vice-versa.

export type ActiveAgentSurface = "decidir" | "pool" | "job" | "funil" | "all"

export type ActiveAgentStatus = "running" | "idle" | "pending_approval"

export type ActiveAgentTargetType =
  | "job"
  | "talent_pool"
  | "pipeline_stage"
  | "candidate_list"
  | string

export interface ActiveAgentSummaryItem {
  agent_id: string
  agent_name: string
  agent_category: string
  status: ActiveAgentStatus
  target_type: ActiveAgentTargetType | null
  target_id: string | null
  target_name: string | null
  last_action_label: string | null
  last_execution_id: string | null
  pending_approvals_count: number
  last_activity_at: string | null
}

export interface ActiveSummaryResponse {
  running_count: number
  items: ActiveAgentSummaryItem[]
}
