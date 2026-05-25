"use client"

import React, { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mail, ShieldCheck, AlertTriangle, FileCheck } from "lucide-react"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { apiFetch } from "@/lib/api/api-fetch"
import { cn } from "@/lib/utils"

/**
 * AuditLogsSummaryPanel — cliente DPO view (read-only, últimos 30d).
 *
 * Criado em 2026-05-25 (PR 3 plan canonical em ~/.claude/plans/jolly-roaming-moler.md).
 *
 * Função: dar ao DPO do cliente uma visão high-level de eventos LGPD nos
 * últimos 30 dias, SEM drill-down interativo. Para investigação detalhada
 * (filtros, drill-down por evento, export), DPO contata staff WeDOTalent
 * que tem acesso ao AuditLogsDrillDownPanel completo em /wedo-admin/governanca/audit-logs/.
 *
 * SEM filtros, SEM tabelas detalhadas, SEM export. Aprofundamento via staff.
 *
 * LGPD compliance: este panel é uma feature de TRANSPARÊNCIA pro DPO cliente,
 * não substitui o audit log completo (que continua sendo escrito em backend
 * via audit_service e disponível pra investigação WeDOTalent).
 */

interface AuditSummary {
  total_logs?: number
  total?: number
  critical_count?: number
  consent_revoked_count?: number
  erasure_count?: number
  ai_override_count?: number
  by_severity?: Record<string, number>
  recent_24h?: number
}

export function AuditLogsSummaryPanel() {
  const t = useTranslations("settings.fairnessCompliance.auditSummary")
  const { companyId } = useCompanyId()
  const [summary, setSummary] = useState<AuditSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!companyId) return
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await apiFetch("/api/backend-proxy/audit-logs/stats?days=30")
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (cancelled) return
        setSummary(data)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : t("errorLoad"))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [companyId, t])

  const critical = summary?.critical_count ?? summary?.by_severity?.critical ?? 0
  const consents = summary?.consent_revoked_count ?? 0
  const erasures = summary?.erasure_count ?? 0
  const aiOverrides = summary?.ai_override_count ?? 0
  const totalEvents = summary?.total_logs ?? summary?.total ?? 0

  return (
    <div className="space-y-4" data-testid="audit-summary-panel">
      <header>
        <h2 className={textStyles.subtitle}>{t("title")}</h2>
        <p className={textStyles.description}>{t("description")}</p>
      </header>

      {error && (
        <div className={cn(cardStyles.default, "p-4 text-status-error text-sm")}>
          {t("errorLoad")}: {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          icon={AlertTriangle}
          label={t("criticalEvents")}
          value={loading ? "..." : critical}
          accent="warning"
        />
        <SummaryCard
          icon={ShieldCheck}
          label={t("consentsRevoked")}
          value={loading ? "..." : consents}
          accent="info"
        />
        <SummaryCard
          icon={FileCheck}
          label={t("erasuresHandled")}
          value={loading ? "..." : erasures}
          accent="success"
        />
        <SummaryCard
          icon={ShieldCheck}
          label={t("aiOverrides")}
          value={loading ? "..." : aiOverrides}
          accent="neutral"
        />
      </div>

      <div className={cn(cardStyles.default, "p-4")}>
        <h3 className="text-sm font-medium text-lia-text-primary mb-2">
          {t("totalEventsTitle")}
        </h3>
        <p className="text-2xl font-semibold text-lia-text-primary">
          {loading ? "..." : totalEvents}
        </p>
        <p className="text-xs text-lia-text-secondary mt-1">{t("totalEventsHint")}</p>
      </div>

      <Card className={cardStyles.default}>
        <CardHeader className="pb-2">
          <CardTitle className={cn(textStyles.subtitle, "flex items-center gap-2")}>
            <Mail className="w-4 h-4 text-lia-text-secondary" />
            {t("needDeepDiveTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-lia-text-secondary mb-3">{t("needDeepDiveBody")}</p>
          <a
            href={`mailto:compliance@wedotalent.cc?subject=${encodeURIComponent(t("dpoEmailSubject"))}`}
            className="inline-flex items-center gap-2 text-sm font-medium text-lia-accent-primary hover:underline"
          >
            <Mail className="w-4 h-4" />
            {t("contactCompliance")}
          </a>
        </CardContent>
      </Card>
    </div>
  )
}

interface SummaryCardProps {
  icon: React.ElementType
  label: string
  value: number | string
  accent: "neutral" | "info" | "warning" | "danger" | "success"
}

function SummaryCard({ icon: Icon, label, value, accent }: SummaryCardProps) {
  const accentMap: Record<SummaryCardProps["accent"], string> = {
    neutral: "text-lia-text-secondary bg-lia-bg-tertiary",
    info: "text-wedo-cyan bg-wedo-cyan/10",
    warning: "text-status-warning bg-status-warning/10",
    danger: "text-status-error bg-status-error/10",
    success: "text-status-success bg-status-success/10",
  }
  return (
    <Card className={cardStyles.default}>
      <CardContent className="p-5">
        <div className="flex items-center gap-3 mb-2">
          <div className={cn("w-9 h-9 rounded-md flex items-center justify-center", accentMap[accent])}>
            <Icon className="w-5 h-5" />
          </div>
          <span className={textStyles.description}>{label}</span>
        </div>
        <p className="text-2xl font-semibold text-lia-text-primary">{value}</p>
      </CardContent>
    </Card>
  )
}
