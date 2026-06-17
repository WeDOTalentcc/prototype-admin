// Onda 4 F1 (2026-05-28) — types canonical do endpoint GET /ai-consumption/by-agent/drilldown.
// Schema espelha `ConsumptionDrilldownResponse` em lia-agent-system/app/api/v1/ai_consumption.py (Onda 4 B2).

export interface ConsumptionExecutionItem {
  consumption_id: string
  agent_type: string
  studio_agent_id: string | null
  operation: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost_cents: number
  candidate_id: string | null
  vacancy_id: string | null
  created_at: string
}

export interface ConsumptionDrilldownResponse {
  items: ConsumptionExecutionItem[]
  total_count: number
  total_cost_cents: number
  total_tokens: number
}

export interface ConsumptionDrilldownParams {
  agent_type?: string
  studio_agent_id?: string
  since_days?: number
  limit?: number
  offset?: number
}
