"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
/**
 * AutomationLogsView — Sprint C canonical impeccable + Sprint C.5 CSV export.
 *
 * Table de execution logs com filters + drill-down + CSV export (LGPD audit trail).
 * Voice "Quiet Operator": logs sao confirmacao calma de que a LIA fez.
 *
 * Audit ref: AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint C / C.5
 */

import { useState, useMemo } from "react"
import { useTranslations } from "next-intl"
import {
  useAutomationsList,
  useAutomationLogs,
} from "@/hooks/automations/useAutomationMutations"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  CheckCircle,
  AlertCircle,
  Clock,
  ChevronRight,
  Sparkles,
  Download,
} from "lucide-react"

interface LogEntry {
  id: string
  automation_id: string
  automation_name?: string
  trigger_event: string
  trigger_data?: Record<string, unknown>
  action_type: string
  action_result?: string
  candidate_id?: string
  candidate_name?: string
  status: "success" | "failure" | "skipped"
  error_message?: string
  execution_time_ms: number
  executed_at: string
}

type StatusFilter = "all" | "success" | "failure" | "skipped"

// Canonical CSV cell escape: wrap em "..." se contem virgula/aspas/quebra; double-up aspas internas.
function csvCell(value: unknown): string {
  if (value === null || value === undefined) return ""
  const s = String(value)
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

// Export client-side dos logs visiveis. Respeita filtros aplicados (filteredLogs).
export function exportLogsToCsv(
  logs: LogEntry[],
  headers: {
    executedAt: string
    automation: string
    trigger: string
    status: string
    candidate: string
    error: string
  },
  filename: string,
): number {
  const headerRow = [
    headers.executedAt,
    headers.automation,
    headers.trigger,
    headers.status,
    headers.candidate,
    headers.error,
  ]
    .map(csvCell)
    .join(",")

  const dataRows = logs.map((l) =>
    [
      l.executed_at,
      l.automation_name ?? l.automation_id ?? "",
      l.trigger_event,
      l.status,
      l.candidate_name ?? l.candidate_id ?? "",
      l.error_message ?? "",
    ]
      .map(csvCell)
      .join(","),
  )

  // UTF-8 BOM para Excel reconhecer acentos.
  const csv = "﻿" + [headerRow, ...dataRows].join("\r\n")
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  return logs.length
}

export function AutomationLogsView() {
  const t = useTranslations("settings.recruitment.automationsTab")
  const { data: automations = [] } = useAutomationsList()
  const [selectedAutomationId, setSelectedAutomationId] = useState<string | "all">("all")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('automation-log-detail', !!selectedLog)

  // Quando "all", precisa agregar logs de multiplas automations.
  // Por agora: se "all", lista vazia + hint "selecione uma automacao".
  // Sprint C+: criar endpoint GET /automations/logs?date_from=... agregado.
  const { data: logsData, isLoading, error } = useAutomationLogs(
    selectedAutomationId === "all" ? null : selectedAutomationId,
  )

  const logs: LogEntry[] = useMemo(() => {
    if (!logsData) return []
    if (Array.isArray(logsData)) return logsData as LogEntry[]
    const obj = logsData as { logs?: LogEntry[]; items?: LogEntry[] }
    return obj.logs ?? obj.items ?? []
  }, [logsData])

  const filteredLogs = useMemo(() => {
    if (statusFilter === "all") return logs
    return logs.filter((l) => l.status === statusFilter)
  }, [logs, statusFilter])

  const handleExportCsv = () => {
    if (filteredLogs.length === 0) return
    const today = format(new Date(), "yyyy-MM-dd")
    const filename = `automation-logs-${today}.csv`
    const exported = exportLogsToCsv(
      filteredLogs,
      {
        executedAt: t("csvHeaderExecutedAt"),
        automation: t("csvHeaderAutomation"),
        trigger: t("csvHeaderTrigger"),
        status: t("csvHeaderStatus"),
        candidate: t("csvHeaderCandidate"),
        error: t("csvHeaderError"),
      },
      filename,
    )
    // Quiet Operator: console confirmation; toast pode ser wired Sprint posterior.
    console.log(t("csvExportSuccess", { count: exported }))
  }

  return (
    <div className="space-y-4" data-testid="automation-logs-view">
      <div className="space-y-1">
        <h3 className="text-sm font-medium text-lia-text-primary">
          Historico de execucao
        </h3>
        <p className="text-xs text-lia-text-secondary">
          Veja quando cada automacao rodou, sucesso ou falha.
        </p>
      </div>

      {/* Filters */}
      <div
        className="flex flex-wrap items-center gap-2"
        data-testid="logs-filters"
      >
        <select
          value={selectedAutomationId}
          onChange={(e) => setSelectedAutomationId(e.target.value)}
          className="text-xs border border-lia-border-default rounded-md px-2 py-1 bg-lia-bg-primary"
          data-testid="filter-automation"
          aria-label="Selecionar automacao"
        >
          <option value="all">Todas as automacoes</option>
          {automations.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name ?? a.id.slice(0, 8)}
            </option>
          ))}
        </select>

        <div className="flex gap-1" data-testid="filter-status">
          {(["all", "success", "failure", "skipped"] as StatusFilter[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStatusFilter(s)}
              className={`text-xs px-2 py-1 rounded-md border transition-colors motion-reduce:transition-none ${
                statusFilter === s
                  ? "bg-wedo-cyan/10 text-wedo-cyan-text border-wedo-cyan/40"
                  : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-secondary"
              }`}
              data-testid={`filter-status-${s}`}
            >
              {s === "all"
                ? "Todos"
                : s === "success"
                  ? "OK"
                  : s === "failure"
                    ? "Falhou"
                    : "Pulou"}
            </button>
          ))}
        </div>

        {/* C.5 CSV export — LGPD audit trail download */}
        <div className="ml-auto">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            disabled={filteredLogs.length === 0}
            data-testid="export-csv-btn"
            aria-label={t("csvExportAriaLabel")}
          >
            <Download className="w-3 h-3 mr-1" aria-hidden="true" />
            {t("csvExportButton")}
          </Button>
        </div>
      </div>

      {/* Empty / loading / error states */}
      {selectedAutomationId === "all" && (
        <div
          className="flex flex-col items-center py-12 text-center"
          data-testid="logs-hint-select"
        >
          <Sparkles
            className="w-8 h-8 text-wedo-cyan-text mb-3"
            aria-hidden="true"
          />
          <p className="text-sm font-medium text-lia-text-primary mb-1">
            Selecione uma automacao acima
          </p>
          <p className="text-xs text-lia-text-secondary max-w-xs">
            Os logs sao mostrados por automacao. Selecione qual voce quer ver no filtro acima.
          </p>
        </div>
      )}

      {isLoading && selectedAutomationId !== "all" && (
        <p
          className="text-xs text-lia-text-secondary py-4"
          data-testid="logs-loading"
        >
          Carregando historico...
        </p>
      )}

      {error && (
        <div
          className="p-3 rounded-md border border-status-error/30 bg-status-error/5"
          data-testid="logs-error"
        >
          <p className="text-xs text-status-error">
            Falha ao carregar historico: {error.message}
          </p>
        </div>
      )}

      {!isLoading &&
        !error &&
        selectedAutomationId !== "all" &&
        filteredLogs.length === 0 && (
          <p
            className="text-xs text-lia-text-secondary py-4"
            data-testid="logs-empty"
          >
            Esta automacao ainda nao foi executada
            {statusFilter !== "all" ? ` (status ${statusFilter})` : ""}.
          </p>
        )}

      {/* Log table */}
      {filteredLogs.length > 0 && (
        <div
          className="border border-lia-border-subtle rounded-xl overflow-hidden"
          data-testid="logs-table"
        >
          <table className="w-full text-xs">
            <thead className="bg-lia-bg-secondary text-lia-text-secondary">
              <tr>
                <th className="px-3 py-2 text-left">Quando</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Candidato</th>
                <th className="px-3 py-2 text-left">Acao</th>
                <th className="px-3 py-2 text-right" aria-label="" />
              </tr>
            </thead>
            <tbody className="divide-y divide-lia-border-subtle">
              {filteredLogs.map((log) => (
                <tr
                  key={log.id}
                  className="hover:bg-lia-bg-secondary/50 cursor-pointer"
                  onClick={() => setSelectedLog(log)}
                  data-testid={`log-row-${log.id}`}
                >
                  <td className="px-3 py-2 text-lia-text-primary whitespace-nowrap">
                    {format(new Date(log.executed_at), "dd MMM HH:mm", {
                      locale: ptBR,
                    })}
                  </td>
                  <td className="px-3 py-2">
                    {log.status === "success" ? (
                      <span className="inline-flex items-center gap-1 text-status-success">
                        <CheckCircle className="w-3 h-3" /> OK
                      </span>
                    ) : log.status === "failure" ? (
                      <span className="inline-flex items-center gap-1 text-status-error">
                        <AlertCircle className="w-3 h-3" /> Falhou
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-lia-text-tertiary">
                        <Clock className="w-3 h-3" /> Pulou
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-lia-text-secondary truncate max-w-[150px]">
                    {log.candidate_name ?? log.candidate_id?.slice(0, 8) ?? "—"}
                  </td>
                  <td className="px-3 py-2 text-lia-text-secondary truncate max-w-[200px]">
                    {log.action_type}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <ChevronRight className="w-4 h-4 text-lia-text-tertiary inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Drill-down detail modal */}
      <Dialog
        open={!!selectedLog}
        onOpenChange={(open) => !open && setSelectedLog(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detalhes da execucao</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-3 text-sm" data-testid="log-detail-modal">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-lia-text-secondary">Quando</p>
                  <p>
                    {format(
                      new Date(selectedLog.executed_at),
                      "dd MMM yyyy as HH:mm:ss",
                      { locale: ptBR },
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-lia-text-secondary">
                    Tempo de execucao
                  </p>
                  <p>{selectedLog.execution_time_ms}ms</p>
                </div>
                <div>
                  <p className="text-xs text-lia-text-secondary">Trigger</p>
                  <p>{selectedLog.trigger_event}</p>
                </div>
                <div>
                  <p className="text-xs text-lia-text-secondary">Acao</p>
                  <p>{selectedLog.action_type}</p>
                </div>
              </div>

              {selectedLog.error_message && (
                <div
                  className="p-3 rounded-md border border-status-error/30 bg-status-error/5"
                  data-testid="log-detail-error"
                >
                  <p className="text-xs font-medium text-status-error mb-1">
                    Erro
                  </p>
                  <p className="text-xs text-status-error">
                    {selectedLog.error_message}
                  </p>
                </div>
              )}

              {selectedLog.trigger_data && (
                <details className="text-xs">
                  <summary className="cursor-pointer text-lia-text-secondary">
                    Dados do trigger (raw)
                  </summary>
                  <pre className="mt-2 p-2 bg-lia-bg-secondary rounded text-[10px] overflow-x-auto">
                    {JSON.stringify(selectedLog.trigger_data, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
