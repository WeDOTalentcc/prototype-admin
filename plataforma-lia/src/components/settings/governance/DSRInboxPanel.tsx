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

export function DSRInboxPanel({ defaultRequestType }: { defaultRequestType?: string } = {}) {
  const t = useTranslations("settings.governanca.dsr")
  const { companyId } = useCompanyId()
  const [items, setItems] = useState<DSR[]>([])
  const [stats, setStats] = useState<DSRStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  // WT-2022 P1.B: filter por request_type default (usado quando hub passa defaultRequestType)
  const [requestTypeFilter, setRequestTypeFilter] = useState<string | undefined>(defaultRequestType)
  // WT-2022 P1-W4-02: sync stale state — useState initializer only runs on mount;
  // useEffect keeps requestTypeFilter in sync if defaultRequestType prop changes after mount.
  useEffect(() => {
    setRequestTypeFilter(defaultRequestType)
  }, [defaultRequestType])
  // WT-2022 P2.2: state pra controle de actions (assign/verify-identity/process/complete/reject)
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null)
  const [refetchSignal, setRefetchSignal] = useState<number>(0)
  // WT-2022 P1-W4-01: modal inline para ações DSR (substitui window.prompt/alert)
  const [actionModal, setActionModal] = useState<{
    type: "assign" | "verify" | "process" | "complete" | "reject" | null
    requestId: string | null
    value: string
    errorMsg: string | null
  }>({ type: null, requestId: null, value: "", errorMsg: null })

  useEffect(() => {
    if (!companyId) return
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        let qs = statusFilter !== "all" ? `?status=${statusFilter}` : ""
        if (requestTypeFilter) {
          qs += (qs ? "&" : "?") + `request_type=${requestTypeFilter}`
        }
        // CLAUDE.md REGRA 6: nao enviar X-Company-ID header — JWT canonical
        // (via apiFetch + proxy auth-headers) ja carrega company_id. Header
        // adicional risca cross-tenant divergence em get_verified_company_id.
        const [listRes, statsRes] = await Promise.all([
          apiFetch(`/api/backend-proxy/data-subject-requests${qs}`),
          apiFetch("/api/backend-proxy/data-subject-requests/stats"),
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
  }, [companyId, t, statusFilter, refetchSignal])

  // WT-2022 P1-W4-01: handlers que recebem value do modal inline (antes usavam window.prompt)
  const handleAssign = async (dsrId: string, assigneeEmail: string) => {
    await executeDsrAction(dsrId, "assign", "POST", { assignee_email: assigneeEmail })
  }
  const handleVerifyIdentity = async (dsrId: string, verificationMethod: string) => {
    await executeDsrAction(dsrId, "verify-identity", "POST", { verification_method: verificationMethod })
  }
  const handleProcess = async (dsrId: string, _value: string) => {
    await executeDsrAction(dsrId, "process", "PUT", {})
  }
  const handleComplete = async (dsrId: string, response: string) => {
    await executeDsrAction(dsrId, "complete", "PUT", { response })
  }
  const handleReject = async (dsrId: string, rejectionReason: string) => {
    await executeDsrAction(dsrId, "reject", "PUT", { rejection_reason: rejectionReason })
  }

  const executeDsrAction = async (
    dsrId: string,
    action: string,
    method: "POST" | "PUT",
    body: Record<string, unknown>,
  ) => {
    if (!dsrId) return
    setActionLoadingId(dsrId)
    try {
      const url = `/api/backend-proxy/data-subject-requests/${dsrId}/${action}`
      const resp = await apiFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!resp.ok) {
        const errText = await resp.text().catch(() => "")
        setActionModal(prev => ({ ...prev, errorMsg: `Erro ${resp.status}: ${errText.slice(0, 500)}` }))
        return
      }
      notifyChatOfSettingsUpdate({
        actionId: `dsr_${action}`,
        section: "governance",
        field: dsrId,
      })
      setRefetchSignal((n) => n + 1)
    } catch (err) {
      setActionModal(prev => ({ ...prev, errorMsg: `Erro de rede: ${err instanceof Error ? err.message : String(err)}` }))
    } finally {
      setActionLoadingId(null)
    }
  }

  // WT-2022 P2.2: handler para 5 actions — agora abre modal em vez de window.prompt
  const handleDsrAction = (
    id: string,
    action: "assign" | "verify-identity" | "process" | "complete" | "reject",
  ) => {
    const modalType = action === "verify-identity" ? "verify" : action as "assign" | "process" | "complete" | "reject"
    setActionModal({ type: modalType, requestId: id, value: "", errorMsg: null })
  }

  const confirmModalAction = async () => {
    const { type, requestId, value } = actionModal
    setActionModal({ type: null, requestId: null, value: "", errorMsg: null })
    if (!requestId || !type) return
    if (type === "assign") await handleAssign(requestId, value)
    else if (type === "verify") await handleVerifyIdentity(requestId, value)
    else if (type === "process") await handleProcess(requestId, value)
    else if (type === "complete") await handleComplete(requestId, value)
    else if (type === "reject") await handleReject(requestId, value)
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
          <div className="flex items-center gap-2">
            <span className="text-xs text-lia-text-secondary">{t("filterStatus")}:</span>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger
                className="h-8 w-[160px] text-xs"
                data-testid="dsr-status-filter"
              >
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("all")}</SelectItem>
                <SelectItem value="pending">{t("pending")}</SelectItem>
                <SelectItem value="in_progress">{t("inProgress")}</SelectItem>
                <SelectItem value="completed">{t("completed")}</SelectItem>
                <SelectItem value="rejected">{t("rejected")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => exportCsv(items)}
            disabled={items.length === 0}
            data-testid="dsr-export-csv"
            className="text-xs"
          >
            {t("exportCsv")}
          </Button>
        </div>
      </div>

      <div className={cn(cardStyles.default, "overflow-x-auto")} data-testid="dsr-inbox-list">
        <table className="min-w-full text-xs">
          <thead className="bg-lia-bg-secondary">
            <tr className="text-left text-lia-text-secondary">
              <th className="px-3 py-2 font-medium">{t("colId")}</th>
              <th className="px-3 py-2 font-medium">{t("colType")}</th>
              <th className="px-3 py-2 font-medium">{t("colSubject")}</th>
              <th className="px-3 py-2 font-medium">{t("colStatus")}</th>
              <th className="px-3 py-2 font-medium">{t("colCreated")}</th>
              <th className="px-3 py-2 font-medium">{t("colDue")}</th>
                          <th className="px-3 py-2 font-medium text-right">Acoes</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-lia-text-secondary">
                  {t("empty")}
                </td>
              </tr>
            )}
            {items.map((dsr) => {
              const id = dsr.id ?? dsr.request_id ?? ""
              const status = (dsr.status ?? "").toLowerCase()
              return (
                <tr key={id} className="border-t border-lia-border-subtle" data-testid={`dsr-row-${id}`}>
                  <td className="px-3 py-2 font-mono text-[11px]">{id.slice(0, 8) || "-"}</td>
                  <td className="px-3 py-2">{dsr.request_type ?? dsr.type ?? "-"}</td>
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
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    {/* WT-2022 P2.2: 5 actions */}
                    {!["completed", "rejected", "cancelled"].includes(status) && (
                      <div className="inline-flex gap-1">
                        {status === "pending" && (
                          <>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={actionLoadingId === id}
                              onClick={() => handleDsrAction(id, "assign")}
                              className="h-6 px-2 text-[10px]"
                              title="Atribuir DSR"
                              data-testid={`dsr-action-assign-${id}`}
                            >
                              Atribuir
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={actionLoadingId === id}
                              onClick={() => handleDsrAction(id, "verify-identity")}
                              className="h-6 px-2 text-[10px]"
                              title="Verificar identidade"
                              data-testid={`dsr-action-verify-${id}`}
                            >
                              Verificar
                            </Button>
                          </>
                        )}
                        {(status === "in_review" || status === "pending") && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            disabled={actionLoadingId === id}
                            onClick={() => handleDsrAction(id, "process")}
                            className="h-6 px-2 text-[10px]"
                            title="Mover para Processing"
                            data-testid={`dsr-action-process-${id}`}
                          >
                            Processar
                          </Button>
                        )}
                        {(status === "processing" || status === "in_progress") && (
                          <>
                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              disabled={actionLoadingId === id}
                              onClick={() => handleDsrAction(id, "complete")}
                              className="h-6 px-2 text-[10px]"
                              title="Concluir DSR (executa side-effect real)"
                              data-testid={`dsr-action-complete-${id}`}
                            >
                              Concluir
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={actionLoadingId === id}
                              onClick={() => handleDsrAction(id, "reject")}
                              className="h-6 px-2 text-[10px]"
                              title="Rejeitar"
                              data-testid={`dsr-action-reject-${id}`}
                            >
                              Rejeitar
                            </Button>
                          </>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* WT-2022 P1-W4-01: modal inline para ações DSR (substitui window.prompt/alert nativo) */}
      {actionModal.type && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4 shadow-xl">
            <h3 className="font-semibold text-lg mb-4">
              {actionModal.type === "assign" && "Atribuir Responsável"}
              {actionModal.type === "verify" && "Verificar Identidade"}
              {actionModal.type === "process" && "Processar Solicitação"}
              {actionModal.type === "complete" && "Concluir Solicitação"}
              {actionModal.type === "reject" && "Rejeitar Solicitação"}
            </h3>
            {actionModal.errorMsg && (
              <p className="text-xs text-status-error mb-3 rounded bg-status-error/10 p-2">
                {actionModal.errorMsg}
              </p>
            )}
            <input
              type="text"
              className="w-full border rounded px-3 py-2 mb-4 text-sm"
              placeholder={
                actionModal.type === "assign" ? "Email do responsável" :
                actionModal.type === "verify" ? "Método de verificação (ex: email_confirmation, gov_id)" :
                actionModal.type === "reject" ? "Motivo da rejeição" :
                "Observações (opcional)"
              }
              value={actionModal.value}
              onChange={e => setActionModal(prev => ({ ...prev, value: e.target.value }))}
              // eslint-disable-next-line jsx-a11y/no-autofocus
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
                onClick={() => setActionModal({ type: null, requestId: null, value: "", errorMsg: null })}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                onClick={confirmModalAction}
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}
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
