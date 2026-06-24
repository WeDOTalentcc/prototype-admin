"use client"

import React, { useState } from "react"
import {
  ArrowLeft, FolderKanban, Users, CheckCircle2, UserCheck,
  Handshake, BadgeCheck, ChevronRight, ChevronDown, Loader2,
  AlertCircle, Bot, Activity, Zap, Pause, Play,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { badgeStyles } from "@/lib/design-tokens"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useProjectDetail } from "@/hooks/jobs/useProjectDetail"
import type { CampaignItem, CampaignStatus } from "@/hooks/jobs/useCampaignsList"
import { Button } from "@/components/ui/button"
import { EditProjetoModal } from "./EditProjetoModal"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

// ── Status helpers ─────────────────────────────────────────────────────────

const STATUS_LABEL: Record<CampaignStatus, string> = {
  active: "Ativa", paused: "Pausada", completed: "Concluída", cancelled: "Cancelada",
}
const STATUS_BADGE: Record<CampaignStatus, string> = {
  active: badgeStyles.success, paused: badgeStyles.warning,
  completed: badgeStyles.green, cancelled: badgeStyles.error,
}
const AUTOMATION_LABEL: Record<string, string> = {
  manual: "Sugerir", semi: "Rascunhar", full: "Executar",
}
const AUTOMATION_DESC: Record<string, string> = {
  manual: "__PERSONA__ sugere ações — você decide",
  semi: "__PERSONA__ prepara ações para sua aprovação antes de enviar",
  full: "__PERSONA__ executa automaticamente sem necessitar aprovação",
}

// ── Stage pipeline strip ───────────────────────────────────────────────────

function StagePipeline({ project }: { project: CampaignItem }) {
  const metricsByStage: Record<string, number> = {
    sourcing: project.total_candidates,
    screening: project.candidates_screened,
    outreach: project.candidates_contacted,
    interview: project.candidates_interviewed,
    evaluation: project.candidates_interviewed,
    offer: project.candidates_offered,
    follow_up: 0,
  }
  const metricLabel: Record<string, string> = {
    sourcing: "candidatos", screening: "aprovados", outreach: "contactados",
    interview: "ativos", evaluation: "avaliados", offer: "ofertas",
  }

  return (
    <div className="flex items-start overflow-x-auto pb-1 gap-0">
      {project.stages.map((stage, idx) => {
        const count = metricsByStage[stage.name] ?? 0
        const label = metricLabel[stage.name] ?? ""
        return (
          <React.Fragment key={stage.name}>
            {idx > 0 && (
              <div className={cn("h-px w-8 mt-5 shrink-0",
                stage.status === "pending" ? "bg-lia-border-subtle" : "bg-lia-btn-primary-bg")} />
            )}
            <div className="flex flex-col items-center gap-1 min-w-[80px] shrink-0">
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center border-2",
                stage.status === "completed" && "border-lia-btn-primary-bg bg-lia-btn-primary-bg",
                stage.status === "in_progress" && "border-lia-btn-primary-bg bg-lia-bg-primary ring-4 ring-lia-btn-primary-bg/20",
                stage.status === "pending" && "border-lia-border bg-lia-bg-secondary"
              )}>
                {stage.status === "completed" ? (
                  <CheckCircle2 className="w-4 h-4 text-white" />
                ) : stage.status === "in_progress" ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-lia-btn-primary-bg" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-lia-border" />
                )}
              </div>
              <span className={cn("text-micro font-semibold text-center",
                stage.status === "pending" ? "text-lia-text-tertiary" : "text-lia-btn-primary-bg"
              )}>{stage.label}</span>
              {count > 0 || stage.status !== "pending" ? (
                <span className="text-micro text-lia-text-secondary text-center">
                  {count > 0 ? `${count} ${label}` : "—"}
                </span>
              ) : null}
            </div>
          </React.Fragment>
        )
      })}
    </div>
  )
}

// ── Autonomia bar ──────────────────────────────────────────────────────────

type AutomationLevel = "manual" | "semi" | "full"
const AUTOMATION_MODES: AutomationLevel[] = ["manual", "semi", "full"]

function AutonomiaBар({ level }: { level: string }) {
  const { persona: _ap } = useAiPersona()
  const personaName = _ap?.name ?? "IA"
  const current = (level as AutomationLevel) ?? "semi"
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1 p-1 rounded-md bg-lia-bg-secondary">
        {AUTOMATION_MODES.map((m) => (
          <div key={m} className={cn(
            "px-3 py-1 rounded text-micro font-medium",
            current === m
              ? "bg-lia-bg-paper shadow-sm text-lia-text-primary border border-lia-border-subtle"
              : "text-lia-text-tertiary"
          )}>
            {AUTOMATION_LABEL[m]}
          </div>
        ))}
      </div>
      <span className="text-micro text-lia-text-secondary">{AUTOMATION_DESC[current].replace("__PERSONA__", personaName)}</span>
    </div>
  )
}

// ── Activity feed ──────────────────────────────────────────────────────────

function ActivityFeed({ project }: { project: CampaignItem }) {
  const events = [
    project.candidates_interviewed > 0 && {
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-lia-btn-primary-bg" />,
      text: `${project.candidates_interviewed} entrevistas agendadas`,
      when: "há 2h",
    },
    project.candidates_screened > 0 && {
      icon: <Zap className="w-3.5 h-3.5 text-status-success" />,
      text: `Triagem concluída: ${project.candidates_screened} de ${project.total_candidates} aprovados`,
      when: "ontem",
    },
    project.total_candidates > 0 && {
      icon: <Users className="w-3.5 h-3.5 text-lia-text-secondary" />,
      text: `${project.total_candidates} candidatos importados`,
      when: project.created_at ? new Date(project.created_at).toLocaleDateString("pt-BR", { day: "numeric", month: "short" }) : "",
    },
  ].filter(Boolean) as Array<{ icon: React.ReactNode; text: string; when: string }>

  if (!events.length) return (
    <p className="text-micro text-lia-text-tertiary py-2">Nenhuma atividade ainda.</p>
  )

  return (
    <div className="space-y-2">
      {events.map((e, i) => (
        <div key={i} className="flex items-start gap-2">
          <div className="mt-0.5 shrink-0">{e.icon}</div>
          <div className="flex-1 min-w-0">
            <p className="text-micro text-lia-text-primary leading-snug">{e.text}</p>
            <p className="text-micro text-lia-text-tertiary">{e.when}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function ProjetoDetailSkeleton() {
  return (
    <div className="space-y-4 animate-pulse p-6">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary" />
        <div className="h-6 w-56 bg-lia-bg-tertiary rounded" />
        <div className="h-5 w-16 bg-lia-bg-tertiary rounded" />
      </div>
      <div className="h-10 bg-lia-bg-tertiary rounded-md" />
      <div className="h-20 bg-lia-bg-tertiary rounded-md" />
      <div className="grid grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-16 bg-lia-bg-tertiary rounded-md" />
        ))}
      </div>
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────

export default function ProjetoDetailClient({ id }: { id: string }) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const queryClient = useQueryClient()
  const { project, isLoading, isError, advance, isAdvancing, update, isUpdating, addCheckpoint, isAddingCheckpoint } = useProjectDetail(id)

  const { data: jobData } = useQuery<{ title?: string } | null>({
    queryKey: ["job-vacancy", project?.job_id],
    queryFn: () => fetch(`/api/backend-proxy/job-vacancies/${project!.job_id}`).then(r => r.json()),
    enabled: Boolean(project?.job_id),
    staleTime: 60_000,
  })
  const [showEdit, setShowEdit] = useState(false)
  const [checkpointNote, setCheckpointNote] = useState("")

  if (isLoading) return <ProjetoDetailSkeleton />

  if (isError || !project) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-[300px] gap-4">
        <AlertCircle className="w-10 h-10 text-lia-text-error" />
        <p className="text-body text-lia-text-secondary">Projeto não encontrado.</p>
        <button type="button" className="text-small text-lia-btn-primary-bg hover:underline flex items-center gap-1"
          onClick={() => window.history.back()}>
          <ArrowLeft className="w-3.5 h-3.5" />Voltar
        </button>
      </div>
    )
  }

  const canAdvance = project.status === "active" && project.current_stage_index < project.stages.length - 1

  return (
    <div className="flex flex-col min-h-full">
      {/* Breadcrumb + header */}
      <div className="px-6 pt-5 pb-4 border-b border-lia-border-subtle space-y-3">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-micro text-lia-text-tertiary">
          <button type="button" onClick={() => window.history.back()}
            className="hover:text-lia-text-secondary transition-colors">
            Projetos
          </button>
          <ChevronRight className="w-3 h-3" />
          <span className="text-lia-text-secondary truncate max-w-xs">{project.name}</span>
        </nav>

        {/* Title row */}
        <div className="flex items-start gap-3">
          <button type="button" aria-label="Voltar"
            className="mt-0.5 p-1.5 rounded-md hover:bg-lia-bg-secondary text-lia-text-secondary transition-colors"
            onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4" />
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <FolderKanban className="w-5 h-5 text-lia-text-secondary shrink-0" />
              <h1 className="text-heading-md font-bold text-lia-text-primary">{project.name}</h1>
              <span className={cn("shrink-0", STATUS_BADGE[project.status])}>
                {STATUS_LABEL[project.status]}
              </span>
            </div>
            <p className="text-micro text-lia-text-tertiary mt-1">
              {project.automation_level && (
                <span>{AUTOMATION_LABEL[project.automation_level] ?? project.automation_level} · </span>
              )}
              {project.job_id && <span>{jobData?.title ?? `Vaga #${project.job_id.slice(-4)}`} · </span>}
              {project.created_at && (
                <span>Criada {new Date(project.created_at).toLocaleDateString("pt-BR", { day: "numeric", month: "short", year: "numeric" })}</span>
              )}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {project.status === "active" && (
              <button type="button"
                disabled={isUpdating}
                onClick={() => update({ status: "paused" })}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-lia-border text-small font-medium text-lia-text-secondary hover:bg-lia-bg-secondary transition-colors disabled:opacity-50">
                {isUpdating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Pause className="w-3.5 h-3.5" />}
                Pausar
              </button>
            )}
            {project.status === "paused" && (
              <button type="button"
                disabled={isUpdating}
                onClick={() => update({ status: "active" })}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-lia-border text-small font-medium text-lia-text-secondary hover:bg-lia-bg-secondary transition-colors disabled:opacity-50">
                {isUpdating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                Retomar
              </button>
            )}
            {canAdvance && (
              <button type="button" disabled={isAdvancing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text text-small font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                onClick={() => advance()}>
                {isAdvancing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
                Avançar etapa
              </button>
            )}
          </div>
        </div>

        {/* Autonomia bar */}
        <AutonomiaBар level={project.automation_level} />
      </div>

      {/* Stage pipeline */}
      <div className="px-6 py-4 border-b border-lia-border-subtle overflow-x-auto">
        <StagePipeline project={project} />
      </div>

      {/* Body: candidates + sidebar */}
      <div className="flex flex-1 gap-0 overflow-hidden">
        {/* Main: candidatos por etapa */}
        <div className="flex-1 px-6 py-4 space-y-4 overflow-y-auto">
          <p className="text-small font-semibold text-lia-text-tertiary uppercase tracking-wider">Candidatos por etapa</p>

          {project.stages.map((stage) => {
            const counts: Record<string, number> = {
              sourcing: project.total_candidates,
              screening: project.candidates_screened,
              outreach: project.candidates_contacted,
              interview: project.candidates_interviewed,
              evaluation: project.candidates_interviewed,
              offer: project.candidates_offered,
              follow_up: 0,
            }
            const count = counts[stage.name] ?? 0
            const isCurrent = stage.status === "in_progress"

            return (
              <div key={stage.name} className={cn(
                "rounded-md border border-lia-border-subtle bg-lia-bg-paper p-4 space-y-2",
                isCurrent && "ring-1 ring-lia-btn-primary-bg/30"
              )}>
                  <div className="flex items-center gap-2">
                    <span className={cn("text-small font-semibold",
                      isCurrent ? "text-lia-btn-primary-bg" : "text-lia-text-primary"
                    )}>
                      {stage.label}
                    </span>
                    {count > 0 && (
                      <span className="text-micro text-lia-text-secondary">{count} candidatos</span>
                    )}
                    {isCurrent && (
                      <span className="ml-auto text-micro px-1.5 py-0.5 rounded-full bg-lia-btn-primary-bg/10 text-lia-btn-primary-bg font-medium">
                        Etapa atual
                      </span>
                    )}
                  </div>
                  {stage.status === "pending" && (
                    <p className="text-micro text-lia-text-tertiary">Aguardando etapa anterior</p>
                  )}
                  {(stage.status === "completed" || stage.status === "in_progress") && count === 0 && (
                    <p className="text-micro text-lia-text-tertiary">Nenhum candidato nesta etapa</p>
                  )}
              </div>
            )
          })}
        </div>

        {/* Sidebar */}
        <div className="w-64 shrink-0 border-l border-lia-border-subtle px-4 py-4 space-y-5 overflow-y-auto">
          <div>
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Agentes rodando</p>
            <div className="space-y-2">
              <div className="flex items-center gap-2 p-2 rounded-md bg-lia-bg-secondary">
                <div className="w-1.5 h-1.5 rounded-full bg-status-success shrink-0" />
                <Bot className="w-3.5 h-3.5 text-lia-text-secondary shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-micro font-medium text-lia-text-primary truncate">Screener</p>
                  <p className="text-micro text-lia-text-tertiary">Processando CVs</p>
                </div>
              </div>
              <p className="text-micro text-lia-text-tertiary px-1">
                {project.status === "active" ? "Agente ativo" : "Nenhum agente rodando"}
              </p>
            </div>
          </div>

          <div>
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Atividade recente</p>
            <ActivityFeed project={project} />
          </div>

          <div>
            <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider mb-2">Adicionar nota</p>
            <textarea
              value={checkpointNote}
              onChange={(e) => setCheckpointNote(e.target.value)}
              placeholder="Anotação sobre o progresso..."
              rows={3}
              className="w-full px-2.5 py-2 rounded-md border border-lia-border-subtle bg-lia-bg-paper text-micro text-lia-text-primary placeholder:text-lia-text-tertiary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/30 resize-none"
            />
            <Button
              size="sm"
              variant="outline"
              className="mt-1.5 w-full text-micro"
              disabled={!checkpointNote.trim() || isAddingCheckpoint}
              onClick={() => {
                const note = checkpointNote.trim()
                if (!note) return
                addCheckpoint(note, { onSuccess: () => setCheckpointNote("") })
              }}
            >
              {isAddingCheckpoint ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Salvar nota"}
            </Button>
          </div>
        </div>
      </div>

      {/* Bottom metrics bar */}
      <div className="border-t border-lia-border-subtle px-6 py-3 flex items-center gap-6 bg-lia-bg-secondary text-small">
        <span><span className="font-bold text-lia-text-primary">{project.total_candidates}</span> <span className="text-lia-text-secondary">candidatos</span></span>
        <span><span className="font-bold text-lia-text-primary">{project.candidates_screened}</span> <span className="text-lia-text-secondary">triados</span></span>
        <span><span className="font-bold text-lia-text-primary">{project.candidates_interviewed}</span> <span className="text-lia-text-secondary">em entrevista</span></span>
        <span><span className="font-bold text-lia-text-primary">{project.candidates_hired}</span> <span className="text-lia-text-secondary">contratados</span></span>
        <button type="button" className="ml-auto text-micro text-lia-btn-primary-bg hover:underline flex items-center gap-1"
          onClick={() => setShowEdit(true)}>
          Editar projeto
          <ChevronRight className="w-3 h-3" />
        </button>
      </div>

      {showEdit && project && (
        <EditProjetoModal
          project={project}
          open={showEdit}
          onClose={() => setShowEdit(false)}
          onSaved={(updated) => {
            queryClient.setQueryData(["recruitment-campaign", id], updated)
            queryClient.invalidateQueries({ queryKey: ["recruitment-campaigns"] })
            setShowEdit(false)
          }}
        />
      )}
    </div>
  )
}
