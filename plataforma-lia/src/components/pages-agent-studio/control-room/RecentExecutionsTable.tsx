// Onda 1 F4 (2026-05-27) — Sala de Controle: histórico paginado.
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { Inbox } from "lucide-react"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useCustomAgents } from "@/hooks/agents"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { cn } from "@/lib/utils"
import type { RecentExecution } from "../decision-tree/types"

interface RecentExecutionsTableProps {
  onOpenReasoning: (executionId: string) => void
  /**
   * Onda 3 F7 — quando provido pelo parent (StudioControlRoom), sobrepoe o
   * filtro local de surface. Quando undefined ou "all", o usuario controla
   * via Select local.
   */
  surfaceFilter?: SurfaceFilter
}

type SurfaceFilter = "all" | "talent_pool" | "job" | "pipeline_stage" | "candidate_list"
type StatusFilter = "all" | "completed" | "error"

export const RECENT_EXECUTIONS_QUERY_KEY = (
  filters: { agentId: string | null; surface: SurfaceFilter; status: StatusFilter },
) => ["agent-monitoring", "recent-executions", filters] as const

// Onda 5.6 — limit canonical de 100 rows.
//
// Decisao de trade-off vs virtualization:
//   - <table> semantico (a11y screen reader nativo: <th scope="col">, navegacao
//     por keyboard padrao) e materialmente melhor que virtual list para essa
//     surface.
//   - @tanstack/react-virtual esta disponivel no projeto e pode ser usado se o
//     baseline cliente alguma vez exceder 100 execucoes em janela razoavel.
//   - Pagination infinita (next page button) e o caminho canonical futuro, nao
//     virtualization — quando a lista virar > 200 rows, abrir backlog
//     "infinite-pagination RecentExecutionsTable" ao inves de migrar para
//     virtual.
//
// Threshold: 100 rows ~ 50ms paint em hardware do recrutador, suficiente para
// 99% dos clientes (auditoria 2026-05-28: media 7 execucoes/h por tenant).
const ROW_LIMIT = 100

async function fetchRecentExecutions(filters: {
  agentId: string | null
  surface: SurfaceFilter
  status: StatusFilter
}): Promise<RecentExecution[]> {
  const params = new URLSearchParams()
  params.set("limit", String(ROW_LIMIT))
  params.set("status", filters.status)
  if (filters.agentId) params.set("agent_id", filters.agentId)
  if (filters.surface !== "all") params.set("surface", filters.surface)
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(
    `/api/backend-proxy/agent-monitoring/recent-executions?${params.toString()}`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  )
  if (!res.ok) throw new Error(`Failed to fetch recent executions: ${res.status}`)
  const data = (await res.json()) as RecentExecution[]
  return Array.isArray(data) ? data : []
}

type ChipVariant = "neutral" | "success" | "warning" | "danger" | "info"

const STATUS_CHIP: Record<
  RecentExecution["status"],
  { label: keyof typeof STATUS_KEYS; variant: ChipVariant; className?: string }
> = {
  success: { label: "success", variant: "success" },
  error: { label: "error", variant: "danger" },
  timeout: { label: "timeout", variant: "warning" },
  cancelled: { label: "cancelled", variant: "neutral" },
  // White-label: "running" herda o variant "info" canonical do DS (sem
  // override de marca).
  running: { label: "running", variant: "info" },
  queued: { label: "queued", variant: "info" },
}

const STATUS_KEYS = {
  success: "success",
  error: "error",
  timeout: "timeout",
  cancelled: "cancelled",
  running: "running",
  queued: "queued",
} as const

function formatDateTime(iso: string | null): string {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleString()
}

function formatDuration(latencyMs: number | null): string {
  if (latencyMs === null || latencyMs === undefined) return "—"
  if (latencyMs < 1000) return `${latencyMs}ms`
  if (latencyMs < 60_000) return `${(latencyMs / 1000).toFixed(1)}s`
  return `${Math.floor(latencyMs / 60_000)}min`
}

export function RecentExecutionsTable({ onOpenReasoning, surfaceFilter }: RecentExecutionsTableProps) {
  const t = useTranslations("agents.studio.controlRoom.recentSection")
  const tFilters = useTranslations("agents.studio.controlRoom.recentSection.filters")
  const tCols = useTranslations("agents.studio.controlRoom.recentSection.columns")
  const tStatus = useTranslations("agents.studio.controlRoom.recentSection.status")
  const { persona } = useAiPersona()
  const { agents } = useCustomAgents()

  const [agentId, setAgentId] = React.useState<string | null>(null)
  const [surface, setSurface] = React.useState<SurfaceFilter>("all")
  const [status, setStatus] = React.useState<StatusFilter>("all")

  // Onda 3 F7 — parent (StudioControlRoom) pode sobrepor o filtro local.
  const effectiveSurface: SurfaceFilter =
    surfaceFilter && surfaceFilter !== "all" ? surfaceFilter : surface

  const { data, isLoading, isError } = useQuery({
    queryKey: RECENT_EXECUTIONS_QUERY_KEY({ agentId, surface: effectiveSurface, status }),
    queryFn: () => fetchRecentExecutions({ agentId, surface: effectiveSurface, status }),
    staleTime: 30_000,
  })

  return (
    <div className="flex flex-col gap-3">
      {/* Filtros */}
      <div
        className="grid grid-cols-1 gap-2 sm:grid-cols-3"
        data-testid="recent-executions-filters"
      >
        <Select
          value={agentId ?? "all"}
          onValueChange={(v) => setAgentId(v === "all" ? null : v)}
        >
          <SelectTrigger className="border-lia-border-default" aria-label={tFilters("agent")}>
            <SelectValue placeholder={tFilters("agent")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{tFilters("agentAll")}</SelectItem>
            {agents.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={surface} onValueChange={(v) => setSurface(v as SurfaceFilter)}>
          <SelectTrigger className="border-lia-border-default" aria-label={tFilters("surface")}>
            <SelectValue placeholder={tFilters("surface")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{tFilters("surfaceAll")}</SelectItem>
            <SelectItem value="talent_pool">{tFilters("surfaceTalentPool")}</SelectItem>
            <SelectItem value="job">{tFilters("surfaceJob")}</SelectItem>
            <SelectItem value="pipeline_stage">{tFilters("surfacePipelineStage")}</SelectItem>
            <SelectItem value="candidate_list">{tFilters("surfaceCandidateList")}</SelectItem>
          </SelectContent>
        </Select>

        <Select value={status} onValueChange={(v) => setStatus(v as StatusFilter)}>
          <SelectTrigger className="border-lia-border-default" aria-label={tFilters("status")}>
            <SelectValue placeholder={tFilters("status")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{tFilters("statusAll")}</SelectItem>
            <SelectItem value="completed">{tFilters("statusSuccess")}</SelectItem>
            <SelectItem value="error">{tFilters("statusError")}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-1" aria-busy="true" data-testid="recent-executions-loading">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-9 w-full" />
        </div>
      ) : isError ? (
        <div
          className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-200"
          data-testid="recent-executions-error"
        >
          {t("loadError")}
        </div>
      ) : !data || data.length === 0 ? (
        <div
          className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-elevated px-4 py-8 text-center"
          data-testid="recent-executions-empty"
        >
          <Inbox className="h-6 w-6 text-lia-text-tertiary" aria-hidden="true" />
          <div className="text-sm font-medium text-lia-text-primary">{t("empty")}</div>
          <div className="max-w-xs text-xs text-lia-text-tertiary">{t("emptyHint")}</div>
        </div>
      ) : (
        <div
          className="overflow-x-auto rounded-md border border-lia-border-subtle"
          data-testid="recent-executions-table-wrapper"
        >
          <table className="w-full text-sm" data-testid="recent-executions-table">
            <thead className="bg-lia-bg-tertiary text-left text-xs uppercase tracking-wide text-lia-text-tertiary">
              <tr>
                <th scope="col" className="px-3 py-2">{tCols("agent")}</th>
                <th scope="col" className="px-3 py-2">{tCols("surface")}</th>
                <th scope="col" className="px-3 py-2">{tCols("startedAt")}</th>
                <th scope="col" className="px-3 py-2">{tCols("duration")}</th>
                <th scope="col" className="px-3 py-2">{tCols("status")}</th>
                <th scope="col" className="sr-only">{tCols("actions")}</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => {
                const badge = STATUS_CHIP[row.status]
                const displayName = row.agent_name || persona?.name || "Agente"
                return (
                  <tr
                    key={row.execution_id}
                    className="cursor-pointer border-t border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary"
                    onClick={() => onOpenReasoning(row.execution_id)}
                    data-testid={`recent-row-${row.execution_id}`}
                  >
                    <td className="px-3 py-2 font-medium">{displayName}</td>
                    <td className="px-3 py-2 text-lia-text-secondary">
                      {row.target_name || row.target_type}
                    </td>
                    <td className="px-3 py-2 text-lia-text-secondary tabular-nums">
                      {formatDateTime(row.started_at)}
                    </td>
                    <td className="px-3 py-2 text-lia-text-secondary tabular-nums">
                      {formatDuration(row.latency_ms)}
                    </td>
                    <td className="px-3 py-2">
                      <Chip
                        variant={badge.variant}
                        density="comfortable"
                        className={cn(badge.className)}
                      >
                        {tStatus(badge.label)}
                      </Chip>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onOpenReasoning(row.execution_id)
                        }}
                        className="text-xs text-lia-text-secondary hover:text-lia-text-primary"
                        data-testid={`recent-view-reasoning-${row.execution_id}`}
                      >
                        {t("viewReasoning")}
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
