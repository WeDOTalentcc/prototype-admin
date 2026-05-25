"use client"

import React, { useEffect, useState, useMemo, useCallback } from "react"
import { useTranslations } from "next-intl"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"

interface AuditLog {
  id: string
  log_id?: string
  event_type: string
  category?: string
  severity?: string
  actor_id?: string
  actor_email?: string
  resource_type?: string
  resource_id?: string
  outcome?: string
  timestamp?: string
  created_at?: string
}

interface AuditStats {
  total_logs?: number
  total?: number
  by_severity?: Record<string, number>
  recent_24h?: number
}

interface RetentionPolicy {
  id?: string
  category?: string
  event_type?: string
  retention_months?: number  // P2-GOV-008: canonical backend field (AuditRetentionPolicy.to_dict)
  retention_days?: number    // kept for legacy fallback
  description?: string
}

const PAGE_SIZE = 25

const severityChipVariant: Record<string, "neutral" | "info" | "warning" | "danger"> = {
  low: "neutral",
  info: "info",
  medium: "warning",
  warning: "warning",
  high: "danger",
  critical: "danger" }

export function AuditLogsDrillDownPanel() {
  const t = useTranslations("settings.governanca.auditLogs")
  const { companyId } = useCompanyId()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState<number>(0)
  const [stats, setStats] = useState<AuditStats | null>(null)
  const [retention, setRetention] = useState<RetentionPolicy[]>([])
  // Auditoria 2026-05-22: initial=false. Antes (true) + `if (!companyId) return`
  // no useEffect deixava spinner eterno se useCompanyId nao resolvesse o JWT.
  // Agora loading so vira true quando o fetch realmente arranca.
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [severityFilter, setSeverityFilter] = useState<string>("all")
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("")
  const [actorFilter, setActorFilter] = useState<string>("")
  const [days, setDays] = useState<number>(30)
  const [page, setPage] = useState<number>(0)

  const buildQuery = useCallback(
    (extra?: Record<string, string>): string => {
      const qs = new URLSearchParams()
      qs.set("limit", String(PAGE_SIZE))
      qs.set("offset", String(page * PAGE_SIZE))
      const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString()
      qs.set("date_from", since)
      if (eventTypeFilter.trim()) qs.set("action", eventTypeFilter.trim())
      if (actorFilter.trim()) qs.set("user_id", actorFilter.trim())
      if (extra) for (const [k, v] of Object.entries(extra)) qs.set(k, v)
      return qs.toString()
    },
    [page, days, eventTypeFilter, actorFilter],
  )

  useEffect(() => {
    if (!companyId) return
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [logsRes, statsRes, retRes] = await Promise.all([
          apiFetch(`/api/backend-proxy/audit-logs?${buildQuery()}`),
          apiFetch("/api/backend-proxy/audit-logs/stats"),
          apiFetch("/api/backend-proxy/audit-logs/retention-policies"),
        ])
        if (!logsRes.ok) throw new Error(`HTTP ${logsRes.status}`)
        const logsData = await logsRes.json()
        const statsData = statsRes.ok ? await statsRes.json() : null
        const retData = retRes.ok ? await retRes.json() : null
        if (cancelled) return
        const items: AuditLog[] = Array.isArray(logsData)
          ? logsData
          : logsData.logs ?? logsData.items ?? logsData.data ?? []
        setLogs(items)
        setTotal(
          typeof logsData?.total === "number"
            ? logsData.total
            : items.length + page * PAGE_SIZE,
        )
        setStats(statsData)
        const retItems: RetentionPolicy[] = Array.isArray(retData)
          ? retData
          : retData?.policies ?? retData?.items ?? []
        setRetention(retItems)
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
  }, [companyId, t, buildQuery, page])

  const exportHref = useMemo(() => {
    if (!companyId) return "#"
    return `/api/backend-proxy/audit-logs/export?${buildQuery({ limit: "1000", offset: "0" })}`
  }, [companyId, buildQuery])

  const hasNext = logs.length === PAGE_SIZE
  const hasPrev = page > 0
  const filtered = useMemo(() => {
    if (severityFilter === "all") return logs
    return logs.filter((l) => (l.severity ?? "").toLowerCase() === severityFilter)
  }, [logs, severityFilter])
  // P2-GOV-009: severityFilter is client-side (filters current page only, not full DB).
  // Display limit prevents heavy renders while server-side pagination is not implemented.
  const DISPLAY_LIMIT = 100
  const displayedFiltered = filtered.slice(0, DISPLAY_LIMIT)
  const hasMoreFiltered = filtered.length > DISPLAY_LIMIT

  if (loading && logs.length === 0) return <Loading variant="spinner" text={t("loading")} />
  if (error) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-status-error")}>
        {t("errorLoad")}: {error}
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="audit-logs-panel">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <SummaryCard label={t("totalLogs")} value={stats?.total_logs ?? stats?.total ?? total} />
        <SummaryCard label={t("recent24h")} value={stats?.recent_24h ?? "-"} />
        <SummaryCard label={t("severityHigh")} value={stats?.by_severity?.high ?? "-"} />
        <SummaryCard label={t("severityCritical")} value={stats?.by_severity?.critical ?? "-"} />
      </div>

      <div className={cn(cardStyles.default, "flex flex-wrap items-end gap-3 p-3")}>
        <FilterField label={t("filterEventType")}>
          <input
            value={eventTypeFilter}
            onChange={(e) => { setEventTypeFilter(e.target.value); setPage(0) }}
            placeholder="user.login"
            className="rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
            data-testid="audit-logs-event-type"
          />
        </FilterField>
        <FilterField label={t("filterActor")}>
          <input
            value={actorFilter}
            onChange={(e) => { setActorFilter(e.target.value); setPage(0) }}
            placeholder="actor_id"
            className="rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
            data-testid="audit-logs-actor"
          />
        </FilterField>
        <FilterField label={t("filterDays")}>
          <select
            value={days}
            onChange={(e) => { setDays(Number(e.target.value)); setPage(0) }}
            className="rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
            data-testid="audit-logs-days"
          >
            <option value={1}>1d</option>
            <option value={7}>7d</option>
            <option value={30}>30d</option>
            <option value={90}>90d</option>
          </select>
        </FilterField>
        <FilterField label={t("filterSeverity")}>
          <select
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(0) }}
            className="rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
            data-testid="audit-logs-severity-filter"
          >
            <option value="all">{t("all")}</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>
        </FilterField>
        <a
          href={exportHref}
          download
          data-testid="audit-logs-export"
          className="ml-auto rounded-md border border-lia-border-default bg-lia-bg-primary px-3 py-1 text-xs font-medium hover:bg-lia-bg-tertiary"
        >
          {t("exportCsv")}
        </a>
      </div>

      <div className={cn(cardStyles.default, "overflow-x-auto")}>
        <table className="min-w-full text-xs">
          <thead className="bg-lia-bg-secondary">
            <tr className="text-left text-lia-text-secondary">
              <th className="px-3 py-2 font-medium">{t("colTimestamp")}</th>
              <th className="px-3 py-2 font-medium">{t("colEvent")}</th>
              <th className="px-3 py-2 font-medium">{t("colSeverity")}</th>
              <th className="px-3 py-2 font-medium">{t("colActor")}</th>
              <th className="px-3 py-2 font-medium">{t("colResource")}</th>
              <th className="px-3 py-2 font-medium">{t("colOutcome")}</th>
            </tr>
          </thead>
          <tbody>
            {displayedFiltered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-lia-text-secondary">
                  {t("empty")}
                </td>
              </tr>
            )}
            {displayedFiltered.map((log) => {
              const ts = log.timestamp ?? log.created_at
              const sev = (log.severity ?? "low").toLowerCase()
              return (
                <tr key={log.id ?? log.log_id} className="border-t border-lia-border-subtle">
                  <td className="px-3 py-2 font-mono text-[11px]">
                    {ts ? new Date(ts).toLocaleString() : "-"}
                  </td>
                  <td className="px-3 py-2">{log.event_type}</td>
                  <td className="px-3 py-2">
                    <Chip variant={severityChipVariant[sev] ?? "neutral"} density="compact">
                      {sev}
                    </Chip>
                  </td>
                  <td className="px-3 py-2">{log.actor_email ?? log.actor_id ?? "-"}</td>
                  <td className="px-3 py-2">
                    {log.resource_type
                      ? `${log.resource_type}${log.resource_id ? ":" + log.resource_id : ""}`
                      : "-"}
                  </td>
                  <td className="px-3 py-2">{log.outcome ?? "-"}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {hasMoreFiltered && (
        <div className="px-3 py-2 text-xs text-lia-text-secondary bg-lia-bg-secondary border border-lia-border-subtle rounded-md" data-testid="audit-logs-display-limit">
          {/* P2-GOV-009: severityFilter client-side. Showing first {DISPLAY_LIMIT} of {filtered.length} filtered. */}
          Mostrando {DISPLAY_LIMIT} de {filtered.length} resultados filtrados. Use &ldquo;Exportar CSV&rdquo; para o conjunto completo.
        </div>
      )}
      <div className="flex items-center justify-between text-xs text-lia-text-secondary">
        <span data-testid="audit-logs-page-info">
          {t("pageInfo", { page: page + 1, count: logs.length })}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!hasPrev}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            data-testid="audit-logs-prev"
            className="rounded-md border border-lia-border-default px-3 py-1 hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("prev")}
          </button>
          <button
            type="button"
            disabled={!hasNext}
            onClick={() => setPage((p) => p + 1)}
            data-testid="audit-logs-next"
            className="rounded-md border border-lia-border-default px-3 py-1 hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("next")}
          </button>
        </div>
      </div>

      {retention.length > 0 && (
        <details className={cn(cardStyles.default, "p-3")} data-testid="audit-logs-retention">
          <summary className="cursor-pointer text-sm font-medium text-lia-text-primary">
            {t("retentionTitle")} ({retention.length})
          </summary>
          <ul className="mt-2 space-y-1 text-xs text-lia-text-secondary">
            {retention.slice(0, 8).map((p, i) => (
              <li key={p.id ?? `${p.category}-${i}`} className="flex justify-between gap-3">
                <span className="font-mono">{p.category ?? p.event_type ?? "-"}</span>
                <span className="font-mono">{p.retention_months != null ? p.retention_months + "m" : (p.retention_days != null ? p.retention_days + "d" : "-")}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-[11px] text-lia-text-secondary">
      <div className="mb-0.5">{label}</div>
      {children}
    </label>
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

export default AuditLogsPanel
