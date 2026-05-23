"use client"

/**
 * usePolicyEngineCRUD — hook canonical para CRUD do Policy Engine.
 *
 * Consumidor de:
 *   - GET    /api/backend-proxy/policy-engine (lista canonical via PolicyListResponse)
 *   - POST   /api/backend-proxy/policy-engine/business-rules
 *   - PUT    /api/backend-proxy/policy-engine/business-rules/:ruleId
 *   - DELETE /api/backend-proxy/policy-engine/business-rules/:ruleId
 *   - POST   /api/backend-proxy/policy-engine/rate-limit-rules
 *   - PUT    /api/backend-proxy/policy-engine/rate-limit-rules/:ruleId
 *   - POST   /api/backend-proxy/policy-engine/escalation-rules
 *   - PUT    /api/backend-proxy/policy-engine/escalation-rules/:ruleId
 *
 * Backend: lia-agent-system/app/api/v1/policy_engine.py
 * Multi-tenancy: company_id vem do JWT via get_verified_company_id; nunca enviar no payload.
 *
 * NOTE: backend NÃO expõe DELETE para rate_limit_rules e escalation_rules. Use is_active=false
 * via PUT para "desativar" como soft-delete.
 */
import useSWR from "swr"
import { useCallback } from "react"
import { apiFetch } from "@/lib/api/api-fetch"
import { useCompanyId } from "@/hooks/company/useCompanyId"

// ============ Types alinhados ao backend Pydantic schemas ============

export type RuleTypeValue = "allow" | "deny" | "require_approval"
export type TargetTypeValue = "company" | "user" | "agent" | "action"
export type TriggerTypeValue =
  | "timeout"
  | "failure"
  | "failure_count"
  | "threshold"
  | "sla_breach"
export type EscalationActionValue =
  | "notify_manager"
  | "notify_admin"
  | "pause_workflow"
  | "require_review"
  | "send_alert"
  | "create_task"

export interface BusinessRule {
  id: string
  company_id?: string | null
  name: string
  description?: string | null
  rule_type: RuleTypeValue
  conditions: Record<string, unknown>
  actions: string[]
  priority: number
  approval_config?: Record<string, unknown> | null
  is_active: boolean
  rule_metadata?: Record<string, unknown> | null
  version?: string | number
}

export interface BusinessRuleInput {
  name: string
  description?: string | null
  rule_type: RuleTypeValue
  conditions?: Record<string, unknown>
  actions?: string[]
  priority?: number
  approval_config?: Record<string, unknown> | null
  is_active?: boolean
  rule_metadata?: Record<string, unknown> | null
}

export interface RateLimitRule {
  id: string
  company_id?: string | null
  name: string
  description?: string | null
  target_type: TargetTypeValue
  target_id?: string | null
  action_pattern?: string | null
  limit_value: number
  window_seconds: number
  burst_limit?: number | null
  is_active: boolean
  version?: string | number
}

export interface RateLimitRuleInput {
  name: string
  description?: string | null
  target_type: TargetTypeValue
  target_id?: string | null
  action_pattern?: string | null
  limit_value: number
  window_seconds: number
  burst_limit?: number | null
  is_active?: boolean
}

export interface EscalationRule {
  id: string
  company_id?: string | null
  name: string
  description?: string | null
  trigger_type: TriggerTypeValue
  condition: Record<string, unknown>
  escalate_to: string[]
  escalation_action: EscalationActionValue
  notification_template?: string | null
  cooldown_seconds: number
  priority: number
  is_active: boolean
  version?: string | number
}

export interface EscalationRuleInput {
  name: string
  description?: string | null
  trigger_type: TriggerTypeValue
  condition?: Record<string, unknown>
  escalate_to?: string[]
  escalation_action?: EscalationActionValue
  notification_template?: string | null
  cooldown_seconds?: number
  priority?: number
  is_active?: boolean
}

interface PolicyListResponse {
  business_rules?: BusinessRule[]
  rate_limit_rules?: RateLimitRule[]
  escalation_rules?: EscalationRule[]
  total_business_rules?: number
  total_rate_limit_rules?: number
  total_escalation_rules?: number
}

// ============ Fetcher canonical ============

async function fetcher(url: string, companyId: string): Promise<PolicyListResponse> {
  const res = await apiFetch(url, {
    headers: { "X-Company-ID": companyId },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return (await res.json()) as PolicyListResponse
}

// ============ Hook ============

export function usePolicyEngineCRUD() {
  const { companyId } = useCompanyId()
  const key = companyId
    ? (["/api/backend-proxy/policy-engine", companyId] as const)
    : null
  const { data, error, isLoading, mutate } = useSWR<PolicyListResponse>(
    key,
    ([url, cid]) => fetcher(url as string, cid as string),
  )

  const headers = useCallback((): HeadersInit => {
    const h: Record<string, string> = { "Content-Type": "application/json" }
    if (companyId) h["X-Company-ID"] = companyId
    return h
  }, [companyId])

  // -------- Business Rules --------

  const createBusinessRule = useCallback(
    async (payload: BusinessRuleInput): Promise<BusinessRule> => {
      const res = await apiFetch("/api/backend-proxy/policy-engine/business-rules", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as BusinessRule
      await mutate()
      return json
    },
    [headers, mutate],
  )

  const updateBusinessRule = useCallback(
    async (ruleId: string, payload: Partial<BusinessRuleInput>): Promise<BusinessRule> => {
      const res = await apiFetch(
        `/api/backend-proxy/policy-engine/business-rules/${encodeURIComponent(ruleId)}`,
        {
          method: "PUT",
          headers: headers(),
          body: JSON.stringify(payload),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as BusinessRule
      await mutate()
      return json
    },
    [headers, mutate],
  )

  const deleteBusinessRule = useCallback(
    async (ruleId: string): Promise<void> => {
      const res = await apiFetch(
        `/api/backend-proxy/policy-engine/business-rules/${encodeURIComponent(ruleId)}`,
        {
          method: "DELETE",
          headers: headers(),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await mutate()
    },
    [headers, mutate],
  )

  // -------- Rate Limit Rules (sem DELETE no backend) --------

  const createRateLimitRule = useCallback(
    async (payload: RateLimitRuleInput): Promise<RateLimitRule> => {
      const res = await apiFetch(
        "/api/backend-proxy/policy-engine/rate-limit-rules",
        {
          method: "POST",
          headers: headers(),
          body: JSON.stringify(payload),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as RateLimitRule
      await mutate()
      return json
    },
    [headers, mutate],
  )

  const updateRateLimitRule = useCallback(
    async (
      ruleId: string,
      payload: Partial<RateLimitRuleInput>,
    ): Promise<RateLimitRule> => {
      const res = await apiFetch(
        `/api/backend-proxy/policy-engine/rate-limit-rules/${encodeURIComponent(ruleId)}`,
        {
          method: "PUT",
          headers: headers(),
          body: JSON.stringify(payload),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as RateLimitRule
      await mutate()
      return json
    },
    [headers, mutate],
  )

  // -------- Escalation Rules (sem DELETE no backend) --------

  const createEscalationRule = useCallback(
    async (payload: EscalationRuleInput): Promise<EscalationRule> => {
      const res = await apiFetch(
        "/api/backend-proxy/policy-engine/escalation-rules",
        {
          method: "POST",
          headers: headers(),
          body: JSON.stringify(payload),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as EscalationRule
      await mutate()
      return json
    },
    [headers, mutate],
  )

  const updateEscalationRule = useCallback(
    async (
      ruleId: string,
      payload: Partial<EscalationRuleInput>,
    ): Promise<EscalationRule> => {
      const res = await apiFetch(
        `/api/backend-proxy/policy-engine/escalation-rules/${encodeURIComponent(ruleId)}`,
        {
          method: "PUT",
          headers: headers(),
          body: JSON.stringify(payload),
        },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = (await res.json()) as EscalationRule
      await mutate()
      return json
    },
    [headers, mutate],
  )

  return {
    businessRules: data?.business_rules ?? [],
    rateLimitRules: data?.rate_limit_rules ?? [],
    escalationRules: data?.escalation_rules ?? [],
    isLoading,
    error,
    refresh: mutate,
    // Business Rules
    createBusinessRule,
    updateBusinessRule,
    deleteBusinessRule,
    // Rate Limit Rules
    createRateLimitRule,
    updateRateLimitRule,
    // Escalation Rules
    createEscalationRule,
    updateEscalationRule,
  }
}
