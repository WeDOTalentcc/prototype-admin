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
  name: string
  description?: string
  trigger_type?: string
  is_active?: boolean
  priority?: string
  execution_count?: number
  last_executed_at?: string
  created_at?: string
  updated_at?: string
}

export function AutomationRulesPanel() {
  const t = useTranslations("settings.governanca.automationRules")
  const { companyId } = useCompanyId()
  const [rules, setRules] = useState<AutomationRule[]>([])
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
        const res = await apiFetch("/api/backend-proxy/automations?limit=100")
        if (!res.ok) throw new Error()
        const body = await res.json()
        if (cancelled) return
        // canonical shape: { success: true, data: { automations: [...], total: N } }
        const items: AutomationRule[] = body?.data?.automations ?? body?.data ?? []
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
    const id = rule.id
    if (!id) return
    setPending((p) => ({ ...p, [id]: true }))
    const nextActive = !(rule.is_active ?? false)
    try {
      const res = await apiFetch(`/api/backend-proxy/automations/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: nextActive }),
      })
      notifyChatOfSettingsUpdate({ actionId: "configure_automation", section: "governance" })
      if (!res.ok) throw new Error()
      setRules((curr) =>
        curr.map((r) => (r.id === id ? { ...r, is_active: nextActive } : r)),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : t("errorToggle"))
    } finally {
      setPending((p) => ({ ...p, [id]: false }))
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

  const total = rules.length
  const active = rules.filter((r) => r.is_active ?? false).length
  const totalExecs = rules.reduce(
    (sum, r) => sum + (r.execution_count ?? 0),
    0,
  )

  return (
    <div className="space-y-4" data-testid="automation-rules-panel">
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
              const isActive = rule.is_active ?? false
              const isPending = pending[rule.id]
              return (
                <tr key={rule.id} className="border-t border-lia-border-subtle">
                  <td className="px-3 py-2">
                    <div className="font-medium text-lia-text-primary">{rule.name}</div>
                    {rule.description && (
                      <div className="text-[11px] text-lia-text-secondary">{rule.description}</div>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono">{rule.trigger_type ?? "-"}</td>
                  <td className="px-3 py-2 font-mono">{rule.priority ?? "-"}</td>
                  <td className="px-3 py-2 font-mono">{rule.execution_count ?? 0}</td>
                  <td className="px-3 py-2 font-mono text-[11px]">
                    {rule.last_executed_at ? (
                      <div>{new Date(rule.last_executed_at).toLocaleString()}</div>
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
                      disabled={isPending}
                      onClick={() => toggleRule(rule)}
                      data-testid={rule.id ? `toggle-automation-${rule.id}` : undefined}
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
