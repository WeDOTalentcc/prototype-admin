// Onda 1 F6 (2026-05-27) — Sala de Controle: painel de auditoria LGPD.
//
// Collapsed por padrão. Quando expandido carrega lista de execuções e permite
// exportar CSV agregado. Reutiliza GET /recent-executions com limit=100.
//
// LGPD canonical:
//   - dados acessados por execução vêm do endpoint individual reasoning.
//   - dados NUNCA acessados são fields proibidos (declarativo via backend).
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { ChevronDown, Database, FileLock2, Info, Loader2 } from "lucide-react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import type {
  ExecutionReasoningResponse,
  RecentExecution,
} from "../decision-tree/types"
import { buildLgpdTrailCsv, downloadLgpdTrailCsv } from "../decision-tree/lgpd-csv"

type DateRange = "7d" | "30d" | "90d"

async function fetchAuditRows(): Promise<RecentExecution[]> {
  const params = new URLSearchParams()
  params.set("limit", "100")
  params.set("status", "all")
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(
    `/api/backend-proxy/agent-monitoring/recent-executions?${params.toString()}`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  )
  if (!res.ok) throw new Error(`Failed to fetch audit rows: ${res.status}`)
  const data = (await res.json()) as RecentExecution[]
  return Array.isArray(data) ? data : []
}

async function fetchReasoningForExport(
  executionId: string,
): Promise<ExecutionReasoningResponse | null> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(
    `/api/backend-proxy/agent-monitoring/executions/${encodeURIComponent(executionId)}/reasoning`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  )
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`Failed to fetch reasoning for export: ${res.status}`)
  return res.json()
}

function rangeToMs(range: DateRange): number {
  const day = 24 * 60 * 60 * 1000
  if (range === "7d") return 7 * day
  if (range === "30d") return 30 * day
  return 90 * day
}

function formatDate(iso: string | null): string {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleDateString()
}

export function LgpdAuditPanel() {
  const t = useTranslations("agents.studio.controlRoom.lgpdSection")
  const tCols = useTranslations("agents.studio.controlRoom.lgpdSection.columns")
  const { persona } = useAiPersona()
  const [expanded, setExpanded] = React.useState(false)
  const [range, setRange] = React.useState<DateRange>("30d")
  const [exporting, setExporting] = React.useState(false)

  const { data, isLoading, isError } = useQuery({
    queryKey: ["agent-monitoring", "lgpd-audit", "all"],
    queryFn: fetchAuditRows,
    enabled: expanded,
    staleTime: 60_000,
  })

  const filteredRows = React.useMemo(() => {
    if (!data) return []
    const cutoff = Date.now() - rangeToMs(range)
    return data.filter((row) => {
      const startedAt = row.started_at ? new Date(row.started_at).getTime() : 0
      return startedAt >= cutoff
    })
  }, [data, range])

  const handleExportAll = React.useCallback(async () => {
    if (!filteredRows.length) return
    setExporting(true)
    try {
      // Header agregado.
      const header = [
        "execution_id",
        "agent_id",
        "agent_name",
        "started_at",
        "data_fields_accessed",
        "data_fields_NOT_accessed",
      ].join(",")
      const lines: string[] = [header]
      // Fetch reasoning para cada row (sequencial para não saturar backend).
      for (const row of filteredRows) {
        try {
          const reasoning = await fetchReasoningForExport(row.execution_id)
          const fields = reasoning?.data_fields_accessed_summary?.join(";") ?? ""
          const notAccessed = reasoning?.data_fields_NOT_accessed?.join(";") ?? ""
          lines.push(
            [
              row.execution_id,
              row.agent_id,
              JSON.stringify(row.agent_name ?? ""),
              row.started_at ?? "",
              JSON.stringify(fields),
              JSON.stringify(notAccessed),
            ].join(","),
          )
        } catch {
          // Skip row em erro — não bloqueia o export todo.
          lines.push(
            [
              row.execution_id,
              row.agent_id,
              JSON.stringify(row.agent_name ?? ""),
              row.started_at ?? "",
              "",
              "",
            ].join(","),
          )
        }
      }
      const csv = `${lines.join("\n")}\n`
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      const ymd = new Date().toISOString().slice(0, 10)
      a.download = `lgpd-audit-${range}-${ymd}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } finally {
      setExporting(false)
    }
  }, [filteredRows, range])

  const handleExportRow = React.useCallback(async (executionId: string) => {
    const reasoning = await fetchReasoningForExport(executionId)
    if (!reasoning) {
      // Legacy / não-instrumentado: gera CSV degradado com header.
      const csv = buildLgpdTrailCsv({
        execution_id: executionId,
        agent_id: "",
        agent_name: "",
        started_at: null,
        completed_at: null,
        model_used: null,
        cost_usd: null,
        latency_ms: null,
        input_tokens: null,
        output_tokens: null,
        reasoning_trace: [],
        data_fields_accessed_summary: [],
        data_fields_NOT_accessed: ["cpf", "raca", "religiao", "genero", "estado_civil"],
      })
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `lgpd-trail-${executionId}-legacy.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      return
    }
    downloadLgpdTrailCsv(reasoning)
  }, [])

  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-md border border-lia-border-subtle bg-lia-bg-elevated px-4 py-3 text-left transition-colors hover:bg-lia-bg-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-border-medium"
          data-testid="lgpd-audit-toggle"
        >
          <div className="flex items-center gap-2">
            <FileLock2 className="h-4 w-4 text-lia-text-primary" aria-hidden="true" />
            <div>
              <div className="text-sm font-semibold text-lia-text-primary">{t("title")}</div>
              <div className="text-xs text-lia-text-tertiary">{t("subtitle")}</div>
            </div>
          </div>
          <ChevronDown
            className={cn(
              "h-4 w-4 text-lia-text-tertiary transition-transform motion-reduce:transition-none",
              expanded && "rotate-180",
            )}
            aria-hidden="true"
          />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent
        className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-4"
        data-testid="lgpd-audit-content"
      >
        <div className="mb-3 flex items-start gap-2 rounded-md bg-lia-bg-tertiary p-3 text-xs text-lia-text-secondary">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-lia-text-tertiary" aria-hidden="true" />
          <p>{t("description")}</p>
        </div>

        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-lia-text-secondary">
            {t("rangeLabel")}
          </span>
          <Select value={range} onValueChange={(v) => setRange(v as DateRange)}>
            <SelectTrigger
              className="h-8 w-44 border-lia-border-default text-xs"
              aria-label={t("rangeLabel")}
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">{t("range7d")}</SelectItem>
              <SelectItem value="30d">{t("range30d")}</SelectItem>
              <SelectItem value="90d">{t("range90d")}</SelectItem>
            </SelectContent>
          </Select>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleExportAll}
            disabled={exporting || !filteredRows.length}
            className="ml-auto gap-2 border-lia-border-default"
            data-testid="lgpd-audit-export-all"
          >
            {exporting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            ) : (
              <Database className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            {t("exportAll")}
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-1" aria-busy="true">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : isError ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-200">
            {t("empty")}
          </div>
        ) : filteredRows.length === 0 ? (
          <div className="rounded-md border border-dashed border-lia-border-subtle p-4 text-center text-xs text-lia-text-tertiary">
            {t("empty")}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-md border border-lia-border-subtle">
            <table className="w-full text-xs" data-testid="lgpd-audit-table">
              <thead className="bg-lia-bg-tertiary text-left uppercase tracking-wide text-lia-text-tertiary">
                <tr>
                  <th scope="col" className="px-3 py-2">{tCols("agent")}</th>
                  <th scope="col" className="px-3 py-2">{tCols("date")}</th>
                  <th scope="col" className="px-3 py-2">{tCols("fieldsRead")}</th>
                  <th scope="col" className="sr-only">{tCols("actions")}</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row) => {
                  const displayName = row.agent_name || persona?.name || "Agente"
                  return (
                    <tr
                      key={row.execution_id}
                      className="border-t border-lia-border-subtle text-lia-text-primary"
                    >
                      <td className="px-3 py-2 font-medium">{displayName}</td>
                      <td className="px-3 py-2 text-lia-text-secondary tabular-nums">
                        {formatDate(row.started_at)}
                      </td>
                      <td className="px-3 py-2 text-lia-text-tertiary">
                        {row.success_summary?.slice(0, 60) ?? "—"}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleExportRow(row.execution_id)}
                          className="text-[11px] text-lia-text-secondary hover:text-lia-text-primary"
                          data-testid={`lgpd-audit-export-${row.execution_id}`}
                        >
                          {t("exportRow")}
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  )
}
