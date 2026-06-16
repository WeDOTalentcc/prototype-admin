// Onda 4 F1 (2026-05-28) — types canonical do endpoint GET /ai-consumption/budget-alerts.
// Schema espelha `BudgetAlertsResponse` em lia-agent-system/app/api/v1/ai_consumption.py (Onda 4 B3).
//
// CF-B B2 (2026-05-29): o valor do limite e em TOKENS, nao cents. O backend
// historicamente expoe o field como `limit_cents` (gap de naming). A migracao
// canonical renomeia para `limit_tokens`. Enquanto o backend nao renomeia,
// mantemos AMBOS os fields opcionais para forward-compat e lemos via
// `resolveBudgetLimitTokens` (le limit_tokens com fallback para limit_cents).

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
   * Naming canonical (migracao em curso). Valor em TOKENS.
   */
  limit_tokens?: number
  /**
   * Legacy field name (valor em tokens, apesar do sufixo "_cents").
   * Mantido para compat enquanto o backend nao renomeia para limit_tokens.
   * @deprecated usar limit_tokens via resolveBudgetLimitTokens.
   */
  limit_cents?: number
  days_in_period: number
  days_remaining: number
  projected_to_exceed: boolean
}

export interface BudgetAlertsResponse {
  alerts: BudgetAlert[]
  period_start: string
  period_end: string
}

/**
 * Le o limite (em tokens) de forma resiliente ao naming do backend.
 * Prefere o canonical `limit_tokens`; faz fallback para o legacy `limit_cents`.
 */
export function resolveBudgetLimitTokens(alert: BudgetAlert): number {
  return alert.limit_tokens ?? alert.limit_cents ?? 0
}
