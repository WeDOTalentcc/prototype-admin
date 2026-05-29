// Onda 1 F3 (2026-05-27) — Sala de Controle: agentes rodando agora.
//
// React Query com polling 5s (refetchInterval). aria-live="polite" para
// leitores de tela perceberem atualizações. prefers-reduced-motion respeitado
// no pulse cyan via motion-reduce:animate-none.
"use client"

import * as React from "react"
import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { Brain, ChevronRight, Clock, Inbox } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { FirstExecutionTooltip } from "@/components/pages-agent-studio/FirstExecutionTooltip"
import type { ActiveExecution } from "../decision-tree/types"

export type LiveSurfaceFilter =
  | "all"
  | "talent_pool"
  | "job"
  | "pipeline_stage"
  | "candidate_list"

export const LIVE_EXECUTIONS_QUERY_KEY = (surface: LiveSurfaceFilter = "all") =>
  ["agent-monitoring", "active-executions", surface] as const

interface LiveAgentsListProps {
  onOpenReasoning: (executionId: string) => void
  /**
   * Onda 3 F7 — filtro "Por surface" propagado da Sala de Controle. Quando
   * "all" não envia query param e backend retorna todos.
   */
  surfaceFilter?: LiveSurfaceFilter
}

async function fetchActiveExecutions(
  surface: LiveSurfaceFilter = "all",
): Promise<ActiveExecution[]> {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const url =
    surface === "all"
      ? "/api/backend-proxy/agent-monitoring/active-executions"
      : `/api/backend-proxy/agent-monitoring/active-executions?surface=${encodeURIComponent(surface)}`
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    throw new Error(`Failed to fetch active executions: ${res.status}`)
  }
  const data = (await res.json()) as ActiveExecution[]
  return Array.isArray(data) ? data : []
}

function formatEta(seconds: number | null): string | null {
  if (seconds === null || seconds === undefined) return null
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}min`
  return `${Math.floor(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}min`
}

interface LiveCardProps {
  execution: ActiveExecution
  onOpenReasoning: (executionId: string) => void
  displayName: string
}

function LiveCard({ execution, onOpenReasoning, displayName }: LiveCardProps) {
  const t = useTranslations("agents.studio.controlRoom.liveSection")
  const eta = formatEta(execution.eta_seconds)
  const targetTypeKey = `target.${execution.target_type}` as const

  return (
    <li className="flex items-center gap-3 rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-3">
      <div
        className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-wedo-cyan text-white"
        aria-hidden="true"
      >
        <Brain className="h-5 w-5" />
        <span className="absolute -right-0.5 -top-0.5 flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-wedo-cyan opacity-60 motion-reduce:animate-none" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-wedo-cyan ring-2 ring-lia-bg-elevated" />
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2">
          <div className="truncate font-medium text-lia-text-primary">{displayName}</div>
          <span className="shrink-0 text-[10px] font-medium uppercase tracking-wide text-wedo-cyan">
            {t("statusPill")}
          </span>
        </div>
        <div className="mt-0.5 truncate text-xs text-lia-text-secondary">
          {t(targetTypeKey)}
          {execution.target_name ? `: ${execution.target_name}` : ""}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-lia-text-tertiary">
          {execution.candidates_processed !== null ? (
            <span>
              {t("processedCount", { count: execution.candidates_processed })}
            </span>
          ) : null}
          {eta ? (
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" aria-hidden="true" />
              {t("etaLabel", { value: eta })}
            </span>
          ) : null}
        </div>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => onOpenReasoning(execution.execution_id)}
        className="shrink-0 gap-1 text-lia-text-secondary hover:text-lia-text-primary"
        data-testid={`live-open-reasoning-${execution.execution_id}`}
      >
        <span className="text-xs">{t("openReasoning")}</span>
        <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
      </Button>
    </li>
  )
}

export function LiveAgentsList({
  onOpenReasoning,
  surfaceFilter = "all",
}: LiveAgentsListProps) {
  const t = useTranslations("agents.studio.controlRoom.liveSection")
  const { persona } = useAiPersona()
  const { data, isLoading, isError } = useQuery({
    queryKey: LIVE_EXECUTIONS_QUERY_KEY(surfaceFilter),
    queryFn: () => fetchActiveExecutions(surfaceFilter),
    refetchInterval: 5000,
    staleTime: 2000,
  })

  if (isLoading) {
    return (
      <div className="space-y-2" data-testid="live-agents-loading" aria-busy="true">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <div
        className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-200"
        data-testid="live-agents-error"
      >
        {t("loadError")}
      </div>
    )
  }

  const executions = data ?? []
  if (executions.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-elevated px-4 py-8 text-center"
        data-testid="live-agents-empty"
      >
        <Inbox className="h-6 w-6 text-lia-text-tertiary" aria-hidden="true" />
        <div className="text-sm font-medium text-lia-text-primary">{t("empty")}</div>
        <div className="max-w-xs text-xs text-lia-text-tertiary">{t("emptyHint")}</div>
      </div>
    )
  }

  // Onda 5.1 — tooltip 1x por agente quando primeira execução está rodando.
  // Heurística: primeiro item running (executions são active = status running).
  // Storage key inclui agent_id pra gate per-agent.
  const firstExec = executions[0]

  return (
    <div className="space-y-2">
      {firstExec && (
        <FirstExecutionTooltip
          agentName={firstExec.agent_name || persona?.name || "Agente"}
          storageKey={`studio_first_execution_seen_${firstExec.agent_id}`}
        />
      )}
      <ul
        className={cn("space-y-2")}
        aria-live="polite"
        aria-relevant="additions text"
        data-testid="live-agents-list"
      >
        {executions.map((exec) => (
          <LiveCard
            key={exec.execution_id}
            execution={exec}
            onOpenReasoning={onOpenReasoning}
            // White-label canonical: nome do agente passa por useAiPersona.
            // Custom agent tem nome próprio (agent_name canonical); fallback é o
            // persona name configurado pela cliente em Configurações.
            displayName={exec.agent_name || persona?.name || "Agente"}
          />
        ))}
      </ul>
    </div>
  )
}
