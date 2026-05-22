"use client"

import React, { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Copy, ExternalLink, FileDown, Loader2 } from "lucide-react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import { apiFetch } from "@/lib/api/api-fetch"

interface FairnessLog {
  id?: string
  job_id?: string
  category?: string
  is_blocked?: boolean
  blocked_terms?: string[]
  soft_warnings?: string[]
  context?: string
  recruiter_id?: string
  created_at?: string
}

interface DimensionResult {
  dimension: string
  groups: Record<string, Record<string, number>>
  adverse_impact_ratio: number
  below_threshold: boolean
  alert_level: string
  eeoc_compliant?: boolean
}

interface BiasAuditReport {
  job_id: string
  evaluated_at: string
  total_candidates: number
  dimensions: DimensionResult[]
  has_alerts: boolean
}

// T-17 NYC LL144 Annual Bias Audit Report (canonical)
interface AnnualReportSummary {
  report_id: string
  year: number
  status: "draft" | "generated" | "published"
  dimensions_count: number
  four_fifths_pass: boolean
  generated_at?: string | null
  published_at?: string | null
  is_public?: boolean
  public_slug?: string | null
  chi2_p_value?: number | null
  eeoc_compliant?: boolean
}

const TRUST_PORTAL_HOST = "trust.wedotalent.cc"

export function BiasAuditPanel() {
  const t = useTranslations("settings.governanca.biasAudit")
  const { companyId } = useCompanyId()
  const [logs, setLogs] = useState<FairnessLog[]>([])
  // Auditoria 2026-05-22: initial=false. Antes (true) + `if (!companyId) return`
  // no useEffect deixava spinner eterno se useCompanyId nao resolvesse o JWT.
  // Agora loading so vira true quando o fetch realmente arranca.
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [drillJobId, setDrillJobId] = useState<string>("")
  const [drillReport, setDrillReport] = useState<BiasAuditReport | null>(null)
  const [drillLoading, setDrillLoading] = useState(false)
  const [drillError, setDrillError] = useState<string | null>(null)

  // T-17 Annual Report state
  const [annualReports, setAnnualReports] = useState<AnnualReportSummary[]>([])
  const [annualLoading, setAnnualLoading] = useState(false)
  const [annualError, setAnnualError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [publishingId, setPublishingId] = useState<string | null>(null)
  const [copiedSlug, setCopiedSlug] = useState<string | null>(null)

  useEffect(() => {
    if (!companyId) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await apiFetch("/api/backend-proxy/fairness-audit/logs?limit=50")
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (cancelled) return
        const items: FairnessLog[] = Array.isArray(data)
          ? data
          : data.logs ?? data.items ?? data.data ?? []
        setLogs(items)
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

  const runDrillDown = async (jobId: string) => {
    if (!companyId || !jobId.trim()) return
    setDrillLoading(true)
    setDrillError(null)
    setDrillReport(null)
    try {
      const res = await apiFetch(`/api/backend-proxy/bias-audit/job/${encodeURIComponent(jobId.trim())}`,
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: BiasAuditReport = await res.json()
      setDrillReport(data)
    } catch (err) {
      setDrillError(err instanceof Error ? err.message : t("errorDrill"))
    } finally {
      setDrillLoading(false)
    }
  }

  // T-17 — Fetch existing annual reports
  const loadAnnualReports = useCallback(async () => {
    if (!companyId) return
    setAnnualLoading(true)
    setAnnualError(null)
    try {
      const res = await apiFetch("/api/backend-proxy/bias-audit/annual")
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const items: AnnualReportSummary[] = Array.isArray(data)
        ? data
        : data.reports ?? data.items ?? data.data ?? []
      setAnnualReports(items)
    } catch (err) {
      setAnnualError(err instanceof Error ? err.message : t("annualErrorLoad"))
    } finally {
      setAnnualLoading(false)
    }
  }, [companyId, t])

  // T-17 — Eager load on mount (annual reports are small + canonical UX for both Annual + Trust tabs)
  useEffect(() => {
    if (!companyId) return
    loadAnnualReports()
  }, [companyId, loadAnnualReports])

  // T-17 — Generate annual report for current year
  const generateAnnualReport = async () => {
    if (!companyId || generating) return
    setGenerating(true)
    setAnnualError(null)
    try {
      const year = new Date().getFullYear()
      const res = await apiFetch("/api/backend-proxy/bias-audit/annual/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json" },
        body: JSON.stringify({ year }) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await loadAnnualReports()
    } catch (err) {
      setAnnualError(err instanceof Error ? err.message : t("annualErrorGenerate"))
    } finally {
      setGenerating(false)
    }
  }

  // T-17 Trust Portal — Toggle public publication
  const togglePublish = async (report: AnnualReportSummary, makePublic: boolean) => {
    if (!companyId || publishingId) return
    setPublishingId(report.report_id)
    setAnnualError(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/bias-audit/annual/${encodeURIComponent(report.report_id)}/publish`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json" },
          body: JSON.stringify({ is_public: makePublic }) },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await loadAnnualReports()
    } catch (err) {
      setAnnualError(err instanceof Error ? err.message : t("annualErrorPublish"))
    } finally {
      setPublishingId(null)
    }
  }

  const exportPdf = (reportId: string) => {
    if (!companyId) return
    const url = `/api/backend-proxy/bias-audit/annual/${encodeURIComponent(reportId)}/export?format=pdf`
    window.open(url, "_blank", "noopener,noreferrer")
  }

  const copyPublicUrl = async (slug: string) => {
    const publicUrl = `https://${TRUST_PORTAL_HOST}/${slug}`
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(publicUrl)
      }
      setCopiedSlug(slug)
      setTimeout(() => setCopiedSlug((s) => (s === slug ? null : s)), 2000)
    } catch {
      // silencioso — UX nao critica
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

  const total = logs.length
  const blocked = logs.filter((l) => l.is_blocked).length
  const warnings = total - blocked

  // Find the most recent published report for trust portal preview
  const latestPublished = annualReports.find((r) => r.is_public && r.public_slug)
  const latestReport = annualReports[0]

  return (
    <div className="space-y-4" data-testid="bias-audit-panel">
      <p className={textStyles.description}>{t("description")}</p>

      <Tabs defaultValue="real-time">
        <TabsList>
          <TabsTrigger value="real-time" data-testid="bias-audit-tab-realtime">
            {t("tabRealTime")}
          </TabsTrigger>
        </TabsList>

        {/* Tab 1 — Real-time (conteudo existing preservado canonical) */}
        <TabsContent value="real-time" className="space-y-4 pt-3">
          <div className="grid grid-cols-3 gap-3">
            <SummaryCard label={t("totalAudits")} value={total} />
            <SummaryCard label={t("warnings")} value={warnings} accent="warning" />
            <SummaryCard label={t("blocked")} value={blocked} accent="danger" />
          </div>

          <div className={cn(cardStyles.default, "space-y-3 p-3")} data-testid="bias-audit-drilldown">
            <h2 className={textStyles.h2}>{t("drillDownTitle")}</h2>
            <p className="text-xs text-lia-text-secondary">{t("drillDownHelp")}</p>
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                runDrillDown(drillJobId)
              }}
            >
              <input
                value={drillJobId}
                onChange={(e) => setDrillJobId(e.target.value)}
                placeholder={t("drillJobPlaceholder")}
                data-testid="bias-audit-job-input"
                className="flex-1 rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
              />
              <button
                type="submit"
                disabled={drillLoading || !drillJobId.trim()}
                data-testid="bias-audit-drill-submit"
                className="rounded-md bg-wedo-purple px-3 py-1 text-xs font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {drillLoading ? "…" : t("drillRun")}
              </button>
            </form>
            {drillError && <div className="text-xs text-status-error">{drillError}</div>}
            {drillReport && <FourFifthsTable report={drillReport} t={t} />}
          </div>

          <h2 className={textStyles.h2}>{t("recentAudits")}</h2>

          <div className={cn(cardStyles.default, "overflow-x-auto")}>
            <table className="min-w-full text-xs">
              <thead className="bg-lia-bg-secondary">
                <tr className="text-left text-lia-text-secondary">
                  <th className="px-3 py-2 font-medium">{t("colJob")}</th>
                  <th className="px-3 py-2 font-medium">{t("colCategory")}</th>
                  <th className="px-3 py-2 font-medium">{t("colTerms")}</th>
                  <th className="px-3 py-2 font-medium">{t("colStatus")}</th>
                  <th className="px-3 py-2 font-medium">{t("colWhen")}</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-center text-lia-text-secondary">
                      {t("empty")}
                    </td>
                  </tr>
                )}
                {logs.map((log, i) => {
                  const ts = log.created_at
                  const blockedRow = log.is_blocked === true
                  return (
                    <tr key={log.id ?? `${log.job_id}-${i}`} className="border-t border-lia-border-subtle">
                      <td className="px-3 py-2 font-mono text-[11px]">{log.job_id ?? "-"}</td>
                      <td className="px-3 py-2">{log.category ?? "-"}</td>
                      <td className="px-3 py-2 text-[11px]">
                        {(log.blocked_terms ?? []).slice(0, 3).join(", ") ||
                          (log.soft_warnings ?? []).slice(0, 3).join(", ") ||
                          "-"}
                      </td>
                      <td className="px-3 py-2">
                        <Chip variant={blockedRow ? "danger" : "warning"} density="compact">
                          {blockedRow ? t("blockedShort") : t("warnShort")}
                        </Chip>
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px]">
                        {ts ? new Date(ts).toLocaleString() : "-"}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* Tab 2 — T-17 NYC LL144 Annual Bias Audit Report */}
        {/* WT-2022 P4.3: TabsContent annual-report removed */}

        {/* Tab 3 — T-17 Trust Portal (HireVue/Eightfold pattern canonical) */}
        {/* WT-2022 P4.3: TabsContent trust-portal removed */}
      </Tabs>
    </div>
  )
}

function FourFifthsTable({
  report,
  t }: {
  report: BiasAuditReport
  t: ReturnType<typeof useTranslations>
}) {
  return (
    <div className="space-y-3" data-testid="bias-audit-fourfifths">
      <div className="flex items-center justify-between text-xs text-lia-text-secondary">
        <span>{t("evaluatedAt")}: {new Date(report.evaluated_at).toLocaleString()}</span>
        <span>{t("totalCandidates")}: {report.total_candidates}</span>
      </div>
      <table className="min-w-full text-xs">
        <thead className="bg-lia-bg-secondary">
          <tr className="text-left text-lia-text-secondary">
            <th className="px-3 py-2 font-medium">{t("colDimension")}</th>
            <th className="px-3 py-2 font-medium">{t("colGroups")}</th>
            <th className="px-3 py-2 font-medium">{t("colRatio")}</th>
            <th className="px-3 py-2 font-medium">{t("colAlert")}</th>
          </tr>
        </thead>
        <tbody>
          {report.dimensions.map((d) => {
            const variant = d.alert_level === "warning" || d.below_threshold ? "danger" : "success"
            return (
              <tr key={d.dimension} className="border-t border-lia-border-subtle">
                <td className="px-3 py-2 font-mono">{d.dimension}</td>
                <td className="px-3 py-2 text-[11px]">{Object.keys(d.groups).join(", ")}</td>
                <td className="px-3 py-2 font-mono">{d.adverse_impact_ratio?.toFixed(3)}</td>
                <td className="px-3 py-2">
                  <Chip variant={variant} density="compact">
                    {d.alert_level}
                  </Chip>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function SummaryCard({
  label,
  value,
  accent }: {
  label: string
  value: number | string
  accent?: "warning" | "danger"
}) {
  const color =
    accent === "danger"
      ? "text-status-error"
      : accent === "warning"
        ? "text-wedo-orange"
        : "text-lia-text-primary"
  return (
    <div className={cn(cardStyles.default, "p-3")}>
      <div className={textStyles.subtitleMuted}>{label}</div>
      <div className={cn("mt-1 font-mono text-xl font-semibold", color)}>{value}</div>
    </div>
  )
}

export default BiasAuditPanel
