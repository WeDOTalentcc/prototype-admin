// Onda 4 F1 (2026-05-28) — types canonical do endpoint GET /ai-consumption/budget-alerts.
// Schema espelha `BudgetAlertsResponse` em lia-agent-system/app/api/v1/ai_consumption.py (Onda 4 B3).
//
// IMPORTANTE: Backend retorna `limit_cents` mas o valor é em TOKENS, não cents
// (gap documentado em DECISIONS Onda 4). UI deve renomear no display para
// "limit_tokens". Mantemos o field name TS espelhando o backend para evitar
// drift; o helper `formatBudgetLimit` no consumidor faz a normalização.

export type BudgetAlertSeverity = "info" | "warning" | "critical"
export type BudgetAlertScope = "global" | "agent"

export interface BudgetAlert {
  severity: BudgetAlertSeverity
  scope: BudgetAlertScope
  studio_agent_id: string | null
  agent_name: string | null
  used_pct: number
  used_cents: number
  /**
   * Nome do field espelha backend, mas o valor é em TOKENS (gap conhecido).
   * Renderizar como "tokens" no UI via helper formatBudgetLimit.
   */
  limit_cents: number
  days_in_period: number
  days_remaining: number
  projected_to_exceed: boolean
}

export interface BudgetAlertsResponse {
  alerts: BudgetAlert[]
  period_start: string
  period_end: string
}
