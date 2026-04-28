"use client"

import React, { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { cardStyles, textStyles } from "@/lib/design-tokens"
import { Loading } from "@/components/ui/loading"
import { Chip } from "@/components/ui/chip"
import { cn } from "@/lib/utils"

interface DSR {
  id: string
  request_id?: string
  request_type?: string
  type?: string
  status: string
  subject_email?: string
  email?: string
  created_at?: string
  sla_deadline?: string
  due_date?: string
  is_overdue?: boolean
  assigned_to?: string
}

interface DSRStats {
  total_requests?: number
  pending_requests?: number
  in_review_requests?: number
  processing_requests?: number
  completed_requests?: number
  rejected_requests?: number
  overdue_requests?: number
  sla_compliance_rate?: number
  by_status?: Record<string, number>
}

const statusVariant: Record<string, "neutral" | "info" | "warning" | "success" | "danger"> = {
  pending: "warning",
  in_progress: "info",
  in_review: "info",
  completed: "success",
  rejected: "danger",
  expired: "danger",
}

function escapeCsv(value: unknown): string {
  if (value == null) return ""
  const s = String(value)
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

function exportCsv(rows: DSR[]) {
  const header = ["id", "type", "status", "subject_email", "created_at", "due_date", "assigned_to"]
  const lines = [header.join(",")]
  for (const r of rows) {
    lines.push(
      [
        escapeCsv(r.id ?? r.request_id),
        escapeCsv(r.request_type ?? r.type),
        escapeCsv(r.status),
        escapeCsv(r.subject_email ?? r.email),
        escapeCsv(r.created_at),
        escapeCsv(r.due_date),
        escapeCsv(r.assigned_to),
      ].join(","),
    )
  }
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `dsr_inbox_${new Date().toISOString().split("T")[0]}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function DSRInboxPanel() {
  const t = useTranslations("settings.governanca.dsr")
  const { companyId } = useCompanyId()
  const [items, setItems] = useState<DSR[]>([])
  const [stats, setStats] = useState<DSRStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>("all")

  useEffect(() => {
    if (!companyId) return
    let cancelled = false
    const headers: HeadersInit = { "X-Company-ID": companyId }

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const qs = statusFilter !== "all" ? `?status=${statusFilter}` : ""
        const [listRes, statsRes] = await Promise.all([
          fetch(`/api/backend-proxy/data-subject-requests${qs}`, { headers }),
          fetch("/api/backend-proxy/data-subject-requests/stats", { headers }),
        ])
        if (!listRes.ok) throw new Error(`HTTP ${listRes.status}`)
        const listData = await listRes.json()
        const statsData = statsRes.ok ? await statsRes.json() : null
        if (cancelled) return
        const list: DSR[] = Array.isArray(listData)
          ? listData
          : listData.requests ?? listData.items ?? listData.data ?? []
        setItems(list)
        setStats(statsData)
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
  }, [companyId, t, statusFilter])

  if (loading) return <Loading variant="spinner" text={t("loading")} />
  if (error) {
    return (
      <div className={cn(cardStyles.default, "p-6 text-status-error")}>
        {t("errorLoad")}: {error}
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="dsr-inbox-panel">
      <p className={textStyles.description}>{t("description")}</p>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <SummaryCard label={t("total")} value={stats?.total_requests ?? items.length} />
        <SummaryCard
          label={t("pending")}
          value={stats?.pending_requests ?? stats?.by_status?.pending ?? "-"}
        />
        <SummaryCard
          label={t("inProgress")}
          value={stats?.processing_requests ?? stats?.by_status?.processing ?? "-"}
        />
        <SummaryCard
          label={t("overdue")}
          value={stats?.overdue_requests ?? "-"}
          accent="danger"
        />
      </div>

      <div className="flex items-center justify-between gap-3">
        <h2 className={textStyles.h2}>{t("requests")}</h2>
        <div className="flex items-center gap-2">
          <label className="text-xs text-lia-text-secondary">
            <span className="mr-2">{t("filterStatus")}:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              data-testid="dsr-status-filter"
              className="rounded-md border border-lia-border-default bg-lia-bg-primary px-2 py-1 text-xs"
            >
              <option value="all">{t("all")}</option>
              <option value="pending">{t("pending")}</option>
              <option value="in_progress">{t("inProgress")}</option>
              <option value="completed">{t("completed")}</option>
              <option value="rejected">{t("rejected")}</option>
            </select>
          </label>
          <button
            type="button"
            onClick={() => exportCsv(items)}
            disabled={items.length === 0}
            data-testid="dsr-export-csv"
            className="rounded-md border border-lia-border-default px-3 py-1 text-xs font-medium hover:bg-lia-bg-tertiary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {t("exportCsv")}
          </button>
        </div>
      </div>

      <div className={cn(cardStyles.default, "overflow-x-auto")}>
        <table className="min-w-full text-xs">
          <thead className="bg-lia-bg-secondary">
            <tr className="text-left text-lia-text-secondary">
              <th className="px-3 py-2 font-medium">{t("colId")}</th>
              <th className="px-3 py-2 font-medium">{t("colType")}</th>
              <th className="px-3 py-2 font-medium">{t("colSubject")}</th>
              <th className="px-3 py-2 font-medium">{t("colStatus")}</th>
              <th className="px-3 py-2 font-medium">{t("colCreated")}</th>
              <th className="px-3 py-2 font-medium">{t("colDue")}</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-lia-text-secondary">
                  {t("empty")}
                </td>
              </tr>
            )}
            {items.map((dsr) => {
              const id = dsr.id ?? dsr.request_id ?? ""
              const status = (dsr.status ?? "").toLowerCase()
              return (
                <tr key={id} className="border-t border-lia-border-subtle">
                  <td className="px-3 py-2 font-mono text-[11px]">{id.slice(0, 8) || "-"}</td>
                  <td className="px-3 py-2 font-mono">{dsr.request_type ?? dsr.type ?? "-"}</td>
                  <td className="px-3 py-2">{dsr.subject_email ?? dsr.email ?? "-"}</td>
                  <td className="px-3 py-2">
                    <Chip variant={statusVariant[status] ?? "neutral"} density="compact">
                      {status || "-"}
                    </Chip>
                  </td>
                  <td className="px-3 py-2 font-mono text-[11px]">
                    {dsr.created_at ? new Date(dsr.created_at).toLocaleDateString() : "-"}
                  </td>
                  <td className="px-3 py-2 font-mono text-[11px]">
                    {(() => {
                      const deadline = dsr.sla_deadline ?? dsr.due_date
                      return deadline ? new Date(deadline).toLocaleDateString() : "-"
                    })()}
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

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string
  value: number | string
  accent?: "danger"
}) {
  const color = accent === "danger" ? "text-status-error" : "text-lia-text-primary"
  return (
    <div className={cn(cardStyles.default, "p-3")}>
      <div className={textStyles.subtitleMuted}>{label}</div>
      <div className={cn("mt-1 font-mono text-xl font-semibold", color)}>{value}</div>
    </div>
  )
}

export default DSRInboxPanel
