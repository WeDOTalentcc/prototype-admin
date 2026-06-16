// Onda 4 F1 (2026-05-28) — types canonical do endpoint GET /custom-agents/{id}/kpis.
// Schema espelha `AgentKpiResponse` em lia-agent-system/app/api/v1/custom_agents.py (Onda 4 B1).
//
// REGRA: drift TS <-> Python = quebra runtime. Mudar campo aqui exige mudar
// no backend canonical e vice-versa.

export type AgentKpiPeriod = "7d" | "30d" | "90d" | "all"

export interface AgentKpiBucket {
  period: string
  candidates_processed: number
  candidates_approved: number
  candidates_rejected: number
  candidates_pending: number
  avg_execution_seconds: number
  p95_execution_seconds: number
  total_executions: number
  error_count: number
  total_cost_usd: number
  total_tokens_input: number
  total_tokens_output: number
}

export interface AgentKpiHourHeatmap {
  hour_of_day: number
  executions_count: number
}

export interface AgentKpiToolBreakdown {
  tool_name: string
  count: number
  success_rate: number
}

export interface AgentKpiResponse {
  agent_id: string
  agent_name: string
  agent_category: string
  period: string
  bucket: AgentKpiBucket
  hour_heatmap: AgentKpiHourHeatmap[]
  tool_breakdown: AgentKpiToolBreakdown[]
  last_run_at: string | null
  is_learning: boolean
}
