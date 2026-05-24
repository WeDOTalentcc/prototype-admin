"use client"

import React, { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

interface Policy {
  id?: string
  policy_id?: string
  name: string
  description?: string
  type?: string
  policy_type?: string
  scope?: string
  enabled?: boolean
  active?: boolean
  is_active?: boolean
  version?: string | number
}

interface BackendRule {
  id?: string
  name: string
  description?: string
  rule_type?: string
  trigger_type?: string
  target_type?: string
  is_active?: boolean
  version?: string | number
}

interface PolicyListResponse {
  business_rules?: BackendRule[]
  rate_limit_rules?: BackendRule[]
  escalation_rules?: BackendRule[]
  total_business_rules?: number
  total_rate_limit_rules?: number
  total_escalation_rules?: number
}

function flattenPolicyList(data: PolicyListResponse | unknown): Policy[] {
  if (!data || typeof data !== "object") return []
  const d = data as PolicyListResponse
  const merge = (rules: BackendRule[] | undefined, kind: string): Policy[] =>
    (rules ?? []).map((r) => ({
      id: r.id,
      name: r.name,
      description: r.description,
      type: kind,
      policy_type: r.rule_type ?? r.trigger_type ?? r.target_type ?? kind,
      enabled: r.is_active,
      is_active: r.is_active,
      version: r.version,
    }))
  return [
    ...merge(d.business_rules, "business"),
    ...merge(d.rate_limit_rules, "rate_limit"),
    ...merge(d.escalation_rules, "escalation"),
  ]
}

// WT-2022 P3.3: sector list MUST match backend canonical (lia-agent-system/app/api/v1/policy_engine.py:407)
// Backend valid_sectors = {"tech", "varejo", "logistica", "financeiro", "saude", "rpo"}
const SECTORS = ["tech", "varejo", "logistica", "financeiro", "saude", "rpo"] as const

const SECTOR_LABELS: Record<typeof SECTORS[number], string> = {
  tech: "Tecnologia",
  varejo: "Varejo",
  logistica: "Logistica",
  financeiro: "Financeiro",
  saude: "Saude",
  rpo: "RPO",
}

export function PolicyEnginePanel() {
  const t = useTranslations("settings.governanca.policyEngine")
  const { companyId } = useCompanyId()
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sector, setSector] = useState<typeof SECTORS[number]>("tech")
  const [applyMsg, setApplyMsg] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    if (!companyId) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await apiFetch("/api/backend-proxy/policy-engine")
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (cancelled) return
        const items: Policy[] = Array.isArray(data)
          ? (data as Policy[])
          : flattenPolicyList(data)
        setPolicies(items)
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : t("errorLoad"))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [companyId, t])

  const applySector = async () => {
    if (!companyId) return
    setApplying(true)
    setApplyMsg(null)
    try {
      const url = `/api/backend-proxy/policy-engine/apply-sector?companyId=${companyId}&sector=${sector}`
      const res = await apiFetch(url, {
        method: "POST",
      })
      notifyChatOfSettingsUpdate({ actionId: "manage_policy", section: "governance" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setApplyMsg(t("applySuccess"))
    } catch (err) {
      setApplyMsg(err instanceof Error ? err.message : t("applyError"))
    } finally {
      setApplying(false)
    }
  }

  if (loading) return <Loading variant="spinner" text={t("loading")} />
  if (error) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-status-error")}>
        {t("errorLoad")}: {error}
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="policy-engine-panel">
      <p className={textStyles.description}>{t("description")}</p>

      <div className={cn(cardStyles.default, "space-y-3 p-4")}>
        <h3 className={textStyles.h3}>{t("applySector")}</h3>
        <p className="text-xs text-lia-text-secondary">{t("applySectorHelp")}</p>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={sector}
            onValueChange={(value) => setSector(value as typeof SECTORS[number])}
          >
            <SelectTrigger
              className="h-8 w-[180px] text-xs"
              data-testid="policy-engine-sector-select"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SECTORS.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            type="button"
            size="sm"
            onClick={applySector}
            disabled={applying}
            data-testid="policy-engine-apply-sector"
            className="text-xs"
          >
            {applying ? t("applying") : t("apply")}
          </Button>
          {applyMsg && (
            <span className="text-xs text-lia-text-secondary">{applyMsg}</span>
          )}
        </div>
      </div>

      <h2 className={textStyles.h2}>{t("policies")}</h2>

      <div className={cn(cardStyles.default, "overflow-x-auto")}>
        <table className="min-w-full text-xs">
          <thead className="bg-lia-bg-secondary">
            <tr className="text-left text-lia-text-secondary">
              <th className="px-3 py-2 font-medium">{t("colName")}</th>
              <th className="px-3 py-2 font-medium">{t("colType")}</th>
              <th className="px-3 py-2 font-medium">{t("colScope")}</th>
              <th className="px-3 py-2 font-medium">{t("colVersion")}</th>
              <th className="px-3 py-2 font-medium">{t("colStatus")}</th>
            </tr>
          </thead>
          <tbody>
            {policies.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-lia-text-secondary">
                  {t("empty")}
                </td>
              </tr>
            )}
            {policies.map((policy, i) => {
              const id = policy.id ?? policy.policy_id ?? String(i)
              const isActive = policy.enabled ?? policy.active ?? true
              return (
                <tr key={id} className="border-t border-lia-border-subtle">
                  <td className="px-3 py-2">
                    <div className="font-medium text-lia-text-primary">{policy.name}</div>
                    {policy.description && (
                      <div className="text-[11px] text-lia-text-secondary">{policy.description}</div>
                    )}
                  </td>
                  <td className="px-3 py-2">{policy.type ?? policy.policy_type ?? "-"}</td>
                  <td className="px-3 py-2">{policy.scope ?? "-"}</td>
                  <td className="px-3 py-2 font-mono">{policy.version ?? "-"}</td>
                  <td className="px-3 py-2">
                    <Chip variant={isActive ? "success" : "neutral"} density="compact">
                      {isActive ? t("statusActive") : t("statusInactive")}
                    </Chip>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PolicyEnginePanel
