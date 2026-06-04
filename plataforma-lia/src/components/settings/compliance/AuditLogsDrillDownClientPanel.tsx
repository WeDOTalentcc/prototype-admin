"use client"

/**
 * Sprint 7.3 LGPD Art. 9 — tenant admin audit log drill-down.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
 *
 * Cliente admin acessa logs detalhados do PRÓPRIO tenant (LGPD Art. 9 — titular
 * direito de acesso aos próprios dados de processamento). Diferente do drill-down
 * em /wedo-admin/governanca/audit-logs/ (cross-tenant, staff WeDOTalent).
 *
 * Backend gate: list_audit_logs (app/api/v1/audit_logs.py) tem
 * _require_tenant_admin(current_user) gate baseado em role.
 */

import { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Shield, AlertCircle, RefreshCw } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { apiFetch } from "@/lib/api/api-fetch"
import { textStyles } from "@/lib/design-tokens"

interface AuditLogRow {
  id: string
  timestamp: string
  user_email: string | null
  action: string
  action_category: string
  resource_type: string | null
  resource_id: string | null
  status: string
  details: Record<string, unknown> | null
}

const CATEGORY_FILTERS = [
  { value: "", label: "Todas as categorias" },
  { value: "data_access", label: "Acesso a dados (PII)" },
  { value: "user_management", label: "Gestão de usuários" },
  { value: "authentication", label: "Autenticação" },
  { value: "configuration", label: "Configuração" },
  { value: "ai_decision", label: "Decisão de IA" },
]

const CATEGORY_BADGE: Record<string, string> = {
  data_access: "bg-wedo-cyan/10 text-wedo-cyan",
  user_management: "bg-wedo-purple/10 text-wedo-purple",
  authentication: "bg-muted text-muted-foreground",
  configuration: "bg-status-warning/10 text-status-warning",
  ai_decision: "bg-cyan-100 text-cyan-800",
}

export function AuditLogsDrillDownClientPanel() {
  const t = useTranslations("settings.fairnessCompliance.auditDrillDown")
  const { user: authUser } = useAuth()
  const isAdmin =
    authUser?.role === "admin" || authUser?.role === "wedotalent_admin"

  const [logs, setLogs] = useState<AuditLogRow[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState("")

  const fetchLogs = async () => {
    if (!isAdmin) {
      setError(t("notAdmin"))
      return
    }
    setLoading(true)
    setError(null)
    try {
      const qs = new URLSearchParams({ limit: "50", offset: "0" })
      if (categoryFilter) qs.set("action_category", categoryFilter)
      const res = await apiFetch(`/api/backend-proxy/audit-logs?${qs.toString()}`)
      if (res.status === 403) {
        setError(t("forbiddenByBackend"))
        return
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const data = await res.json()
      setLogs(Array.isArray(data?.logs) ? data.logs : [])
      setTotal(data?.total ?? 0)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro desconhecido")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAdmin) fetchLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin, categoryFilter])

  if (!isAdmin) {
    return (
      <Card className="border-status-warning-border-light bg-status-warning-bg">
        <CardContent className="p-4 flex items-start gap-3">
          <Shield className="w-5 h-5 text-status-warning mt-0.5" />
          <div>
            <p className={textStyles.subtitle}>{t("notAdminTitle")}</p>
            <p className={`${textStyles.description} mt-1`}>
              {t("notAdminBody")}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-status-success" />
          {t("title")}
        </CardTitle>
        <p className={textStyles.description}>{t("subtitle")}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <select
            data-testid="audit-category-filter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md bg-lia-bg-primary"
          >
            {CATEGORY_FILTERS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <Button
            data-testid="audit-refresh"
            variant="outline"
            size="sm"
            onClick={fetchLogs}
            disabled={loading}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
            {t("refresh")}
          </Button>
          <span className="text-xs text-lia-text-secondary">
            {t("total", { count: total })}
          </span>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-2 rounded-md bg-status-error/10 border border-status-error/30 text-status-error text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-lia-bg-secondary">
              <tr>
                <th className="px-2 py-2 text-left text-micro uppercase font-medium text-lia-text-secondary">
                  {t("colWhen")}
                </th>
                <th className="px-2 py-2 text-left text-micro uppercase font-medium text-lia-text-secondary">
                  {t("colUser")}
                </th>
                <th className="px-2 py-2 text-left text-micro uppercase font-medium text-lia-text-secondary">
                  {t("colCategory")}
                </th>
                <th className="px-2 py-2 text-left text-micro uppercase font-medium text-lia-text-secondary">
                  {t("colAction")}
                </th>
                <th className="px-2 py-2 text-left text-micro uppercase font-medium text-lia-text-secondary">
                  {t("colResource")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-lia-border-subtle">
              {logs.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="px-2 py-4 text-center text-lia-text-secondary">
                    {t("empty")}
                  </td>
                </tr>
              )}
              {logs.map((log) => (
                <tr
                  key={log.id}
                  data-testid={`audit-row-${log.id}`}
                  className="hover:bg-lia-bg-secondary"
                >
                  <td className="px-2 py-1.5 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString("pt-BR", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="px-2 py-1.5">
                    {log.user_email || (
                      <span className="text-lia-text-secondary italic">system</span>
                    )}
                  </td>
                  <td className="px-2 py-1.5">
                    <Chip
                      variant="neutral"
                      muted
                      className={`${CATEGORY_BADGE[log.action_category] || ""} text-micro`}
                    >
                      {log.action_category}
                    </Chip>
                  </td>
                  <td className="px-2 py-1.5">{log.action}</td>
                  <td className="px-2 py-1.5">
                    {log.resource_type && (
                      <span className="text-lia-text-secondary">
                        {log.resource_type}/{log.resource_id?.slice(0, 8)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={`${textStyles.description} pt-2`}>{t("retentionNote")}</p>
      </CardContent>
    </Card>
  )
}
