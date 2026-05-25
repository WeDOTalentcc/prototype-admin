"use client"

import React, { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

interface AutomationRule {
  id: string
  rule_id?: string
  name: string
  description?: string
  trigger_type?: string
  trigger?: string
  enabled?: boolean
  active?: boolean
  priority?: number
  execution_count?: number
  executions_count?: number
  last_executed_at?: string
  last_execution_at?: string
  last_execution_status?: string
  last_run?: string
  created_at?: string
  updated_at?: string
}

export function AutomationRulesPanel() {
  const t = useTranslations("settings.governanca.automationRules")
  const { companyId } = useCompanyId()
  const [rules, setRules] = useState<AutomationRule[]>([])
  // Auditoria 2026-05-22: initial=false. Antes (true) + 
  // no useEffect deixava spinner eterno se useCompanyId nao resolvesse o JWT.
  // Agora loading so vira true quando o fetch realmente arranca.
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (!companyId) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await apiFetch(`/api/backend-proxy/automation-rules/company/${companyId}`,
        )
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (cancelled) return
        const items: AutomationRule[] = Array.isArray(data)
          ? data
          : data.rules ?? data.items ?? data.data ?? []
        setRules(items)
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

  const toggleRule = async (rule: AutomationRule) => {
    const id = rule.id ?? rule.rule_id
    if (!id || !companyId) return
    setPending((p) => ({ ...p, [id]: true }))
    try {
      const res = await apiFetch(`/api/backend-proxy/automation-rules/${id}/toggle`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json" } })
      notifyChatOfSettingsUpdate({ actionId: "configure_automation", section: "governance" })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setRules((curr) =>
        curr.map((r) => {
          const rid = r.id ?? r.rule_id
          if (rid !== id) return r
          const next = !(r.enabled ?? r.active ?? false)
          return { ...r, enabled: next, active: next }
        }),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorToggle"))
    } finally {
      setPending((p) => ({ ...p, [id]: false }))
    }
  }

  if (loading) return <Loading variant="spinner" text={t("loading")} />

  // WT-2022 P3.2: stage_automation_rules eh DEPRECATED. Engine real usa
  // communication_automations (path quente em stage_automation_engine.py:198).
  // Toggles aqui NAO TEM EFEITO ate migration ser completada (Sprint pendente).
  // Decisao Paulo 2026-05-21: matar stage_automation_rules em favor de
  // communication_automations.
  // P1-W4-09: migration banner agora renderiza SEMPRE (fora do bloco de erro),
  // pois o aviso deve ser visivel independentemente do estado do fetch.
  const migrationBanner = (
    <div className="rounded-md border border-status-warning/40 bg-status-warning/10 p-3 mb-3">
      <p className="text-xs font-medium text-status-warning">
        ⚠ Aviso de migracao pendente
      </p>
      <p className="text-[11px] text-lia-text-secondary mt-1">
        Esta tela manipula <code>stage_automation_rules</code> mas o engine de
        automacao real usa <code>communication_automations</code>. Toggles aqui
        NAO afetam comportamento de agentes ate migracao ser completada.
        Tracking: WT-2022 P3.2.
      </p>
    </div>
  )

  if (error) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-status-error")}>
        {migrationBanner}
        {t("errorLoad")}: {error}
      </div>
    )
  }

  const total = rules.length
  const active = rules.filter((r) => r.enabled ?? r.active ?? false).length
  const totalExecs = rules.reduce(
    (sum, r) => sum + (r.execution_count ?? r.executions_count ?? 0),
    0,
  )

  return (
    <div className="space-y-4" data-testid="automation-rules-panel">
      {migrationBanner}
      <p className={textStyles.description}>{t("description")}</p>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <SummaryCard label={t("totalRules")} value={total} />
        <SummaryCard label={t("activeRules")} value={active} />
        <SummaryCard label={t("inactiveRules")} value={Math.max(0, (total ?? 0) - (active ?? 0))} />
        <SummaryCard label={t("totalExecutions")} value={totalExecs} />
      </div>

      <h2 className={textStyles.h2}>{t("rules")}</h2>

      <div className={cn(cardStyles.default, "overflow-x-auto")}>
        <table className="min-w-full text-xs">
          <thead className="bg-lia-bg-secondary">
            <tr className="text-left text-lia-text-secondary">
              <th className="px-3 py-2 font-medium">{t("colName")}</th>
              <th className="px-3 py-2 font-medium">{t("colTrigger")}</th>
              <th className="px-3 py-2 font-medium">{t("colPriority")}</th>
              <th className="px-3 py-2 font-medium">{t("colExecutions")}</th>
              <th className="px-3 py-2 font-medium">{t("colLastRun")}</th>
              <th className="px-3 py-2 font-medium">{t("colStatus")}</th>
              <th className="px-3 py-2 font-medium">{t("colActions")}</th>
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-lia-text-secondary">
                  {t("empty")}
                </td>
              </tr>
            )}
            {rules.map((rule) => {
              const id = rule.id ?? rule.rule_id ?? ""
              const isActive = rule.enabled ?? rule.active ?? false
              const isPending = pending[id]
              const lastRun =
                rule.last_executed_at ?? rule.last_execution_at ?? rule.last_run
              const execCount = rule.execution_count ?? rule.executions_count ?? 0
              const lastStatus = rule.last_execution_status
              return (
                <tr key={id} className="border-t border-lia-border-subtle">
                  <td className="px-3 py-2">
                    <div className="font-medium text-lia-text-primary">{rule.name}</div>
                    {rule.description && (
                      <div className="text-[11px] text-lia-text-secondary">{rule.description}</div>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono">{rule.trigger_type ?? rule.trigger ?? "-"}</td>
                  <td className="px-3 py-2 font-mono">{rule.priority ?? "-"}</td>
                  <td className="px-3 py-2 font-mono">{execCount}</td>
                  <td className="px-3 py-2 font-mono text-[11px]">
                    {lastRun ? (
                      <div>
                        <div>{new Date(lastRun).toLocaleString()}</div>
                        {lastStatus && (
                          <Chip
                            variant={lastStatus === "success" ? "success" : "danger"}
                            density="compact"
                          >
                            {lastStatus}
                          </Chip>
                        )}
                      </div>
                    ) : (
                      <span className="text-lia-text-secondary">{t("neverRun")}</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <Chip variant={isActive ? "success" : "neutral"} density="compact">
                      {isActive ? t("statusActive") : t("statusInactive")}
                    </Chip>
                  </td>
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      disabled={isPending || !id}
                      onClick={() => toggleRule(rule)}
                      data-testid={`automation-rule-toggle-${id}`}
                      className="rounded-md border border-lia-border-default px-2 py-1 text-xs font-medium hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isActive ? t("disable") : t("enable")}
                    </button>
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

function SummaryCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className={cn(cardStyles.default, "p-3")}>
      <div className={textStyles.subtitleMuted}>{label}</div>
      <div className="mt-1 font-mono text-xl font-semibold text-lia-text-primary">{value}</div>
    </div>
  )
}

export default AutomationRulesPanel
