"use client"

/**
 * Onda 3 F4 (2026-05-28) — JobAgentsTab canonical.
 *
 * Aba "Agentes" na página da Vaga (job-kanban-page). Mostra deployments
 * acoplados a esta vaga, com ações pause/resume/detach + view-reasoning
 * (DecisionTreeDrawer canonical da Onda 1).
 *
 * Não cria nova rota — é renderizada DENTRO de KanbanPageContent quando
 * activeTab === 'agents'.
 *
 * Reuso:
 *  - useJobAgents (Onda 3.F3) → GET deployments
 *  - useDetachJobAgent (Onda 3.F3) → DELETE
 *  - AssignAgentToJobModal (Onda 3.F3) → CTA primary
 *  - DecisionTreeDrawer (Onda 1) → raciocínio última exec
 *  - useAiPersona → white-label do nome quando o agente não tem nome próprio
 *
 * Pause/resume: PATCH /agent-deployments/{deployment_id} via inline fetch
 * (não há hook canonical ainda; defer extração).
 */
import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Brain, ChevronRight, Pause, Play, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { useJobAgents, useDetachJobAgent } from "@/hooks/agents/use-job-agents"
import { AssignAgentToJobModal } from "@/components/jobs/AssignAgentToJobModal"
import { DecisionTreeDrawer } from "@/components/pages-agent-studio/decision-tree/DecisionTreeDrawer"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { useQueryClient } from "@tanstack/react-query"
import { JOB_AGENTS_QUERY_KEY } from "@/hooks/agents/use-job-agents"
import type { JobAgentDeployment } from "@/types/agents/job-agent"

interface JobAgentsTabProps {
  jobId: string
  jobTitle?: string
}

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("auth_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function patchDeploymentActive(
  deploymentId: string,
  isActive: boolean,
): Promise<void> {
  const res = await fetch(
    `/api/backend-proxy/agent-deployments/${encodeURIComponent(deploymentId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ is_active: isActive }),
    },
  )
  if (!res.ok) {
    throw new Error(`Failed to update deployment: ${res.status}`)
  }
}

export function JobAgentsTab({ jobId, jobTitle }: JobAgentsTabProps) {
  const t = useTranslations("jobs.agents")
  const tTrigger = useTranslations("jobs.agents.triggerMode")
  const { persona } = useAiPersona()
  const qc = useQueryClient()

  const { data, isLoading, isError } = useJobAgents(jobId)
  const detach = useDetachJobAgent(jobId)
  const [attachOpen, setAttachOpen] = useState(false)
  const [openExecutionId, setOpenExecutionId] = useState<string | null>(null)
  const [busyDeploymentId, setBusyDeploymentId] = useState<string | null>(null)

  const deployments = data?.deployments ?? []

  const handleTogglePause = async (d: JobAgentDeployment) => {
    setBusyDeploymentId(d.id)
    try {
      await patchDeploymentActive(d.id, !d.is_active)
      qc.invalidateQueries({ queryKey: JOB_AGENTS_QUERY_KEY(jobId) })
      qc.invalidateQueries({ queryKey: ["agent-deployments"] })
    } catch {
      // soft fail; UI mantém estado anterior por causa do invalidate
    } finally {
      setBusyDeploymentId(null)
    }
  }

  const handleDetach = async (d: JobAgentDeployment) => {
    const confirmed = typeof window !== "undefined"
      ? window.confirm(t("detachConfirm"))
      : true
    if (!confirmed) return
    setBusyDeploymentId(d.id)
    try {
      await detach.mutateAsync(d.id)
    } finally {
      setBusyDeploymentId(null)
    }
  }

  return (
    <div
      className="flex-1 overflow-y-auto bg-lia-bg-primary"
      data-testid="job-agents-tab"
    >
      <div className="mx-auto max-w-5xl px-4 py-6">
        <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-lia-text-primary">
              {t("header")}
            </h2>
            <p className="mt-1 text-xs text-lia-text-secondary">
              {t("subheader")}
            </p>
          </div>
          <Button
            onClick={() => setAttachOpen(true)}
            data-testid="attach-agent-cta"
            className="gap-1.5 bg-lia-cyan text-white hover:bg-lia-cyan/90"
          >
            <Plus className="h-4 w-4" />
            {t("cta.attach")}
          </Button>
        </header>

        {isLoading ? (
          <div
            className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-6 text-center text-sm text-lia-text-tertiary"
            data-testid="job-agents-loading"
            aria-busy="true"
          >
            {t("loading")}
          </div>
        ) : isError ? (
          <div
            className="rounded-md border border-status-error/30 bg-status-error/10 p-3 text-sm text-status-error"
            role="alert"
            data-testid="job-agents-error"
          >
            {t("loadError")}
          </div>
        ) : deployments.length === 0 ? (
          <div
            className="rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-elevated px-4 py-10 text-center"
            data-testid="job-agents-empty"
          >
            <Brain className="mx-auto h-8 w-8 text-lia-text-tertiary" aria-hidden="true" />
            <p className="mt-2 text-sm font-medium text-lia-text-primary">
              {t("emptyTitle")}
            </p>
            <p className="mx-auto mt-1 max-w-md text-xs text-lia-text-tertiary">
              {t("empty")}
            </p>
          </div>
        ) : (
          <ul className="space-y-2" data-testid="job-agents-list">
            {deployments.map((d) => {
              const displayName =
                d.agent_name || persona?.name || t("fallbackAgentName")
              const isBusy = busyDeploymentId === d.id
              return (
                <li
                  key={d.id}
                  className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-4"
                  data-testid={`job-agent-card-${d.id}`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-lia-cyan text-white">
                      <Brain className="h-4.5 w-4.5" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-lia-text-primary">
                          {displayName}
                        </span>
                        <Chip variant="neutral" muted>
                          {tTrigger(d.trigger_mode as string)}
                        </Chip>
                        {!d.is_active ? (
                          <Chip variant="neutral" muted className="text-status-warning">
                            {t("status.paused")}
                          </Chip>
                        ) : (
                          <Chip variant="neutral" muted className="text-lia-cyan">
                            {t("status.active")}
                          </Chip>
                        )}
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-lia-text-secondary">
                        {d.last_execution_at ? (
                          <span>
                            {t("lastRun")}:{" "}
                            {new Date(d.last_execution_at).toLocaleString()}
                          </span>
                        ) : (
                          <span>{t("neverRun")}</span>
                        )}
                        <span>
                          {t("processed", { count: d.candidates_processed ?? 0 })}
                        </span>
                      </div>
                    </div>
                    <div className="flex shrink-0 flex-wrap items-center gap-1">
                      {d.last_execution_id ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            // Onda 5+2 D — backend agora popula last_execution_id
                            // (PoolAgentRun.id mais recente). DecisionTreeDrawer
                            // canonical resolve via /agent-monitoring/executions/
                            // {id}/reasoning. Botão só renderiza se houver execução.
                            setOpenExecutionId(d.last_execution_id as string)
                          }}
                          className="gap-1 text-lia-text-secondary hover:text-lia-text-primary"
                          data-testid={`view-reasoning-${d.id}`}
                        >
                          <span className="text-xs">{t("action.viewReasoning")}</span>
                          <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                      ) : d.last_execution_at ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled
                          title={t("action.viewReasoningUnavailable")}
                          aria-label={t("action.viewReasoningUnavailable")}
                          className="gap-1 text-lia-text-tertiary"
                          data-testid={`view-reasoning-disabled-${d.id}`}
                        >
                          <span className="text-xs">{t("action.viewReasoning")}</span>
                          <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                      ) : null}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleTogglePause(d)}
                        disabled={isBusy}
                        data-testid={`toggle-pause-${d.id}`}
                        className="gap-1 text-lia-text-secondary hover:text-lia-text-primary"
                      >
                        {d.is_active ? (
                          <>
                            <Pause className="h-3.5 w-3.5" />
                            <span className="text-xs">{t("action.pause")}</span>
                          </>
                        ) : (
                          <>
                            <Play className="h-3.5 w-3.5" />
                            <span className="text-xs">{t("action.resume")}</span>
                          </>
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDetach(d)}
                        disabled={isBusy}
                        data-testid={`detach-${d.id}`}
                        className="gap-1 text-status-error hover:bg-status-error/10"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span className="text-xs">{t("action.detach")}</span>
                      </Button>
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      <AssignAgentToJobModal
        jobId={jobId}
        jobTitle={jobTitle}
        open={attachOpen}
        onClose={() => setAttachOpen(false)}
      />

      <DecisionTreeDrawer
        executionId={openExecutionId}
        onClose={() => setOpenExecutionId(null)}
      />
    </div>
  )
}
