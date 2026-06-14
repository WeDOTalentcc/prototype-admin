"use client"

import React from "react"
import { ArrowLeft, FolderKanban, Users, CheckCircle2, UserCheck, Handshake, BadgeCheck, ChevronRight, Loader2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { badgeStyles } from "@/lib/design-tokens"
import { StudioCardShell } from "@/components/pages-agent-studio/StudioCardShell"
import { useProjectDetail } from "@/hooks/jobs/useProjectDetail"
import type { CampaignItem, CampaignStatus } from "@/hooks/jobs/useCampaignsList"

// ── Status helpers ─────────────────────────────────────────────────────────

function statusLabel(status: CampaignStatus): string {
  const map: Record<CampaignStatus, string> = {
    active: "Ativo",
    paused: "Pausado",
    completed: "Concluído",
    cancelled: "Cancelado",
  }
  return map[status] ?? status
}

function statusBadge(status: CampaignStatus): string {
  const map: Record<CampaignStatus, string> = {
    active: badgeStyles.success,
    paused: badgeStyles.warning,
    completed: badgeStyles.green,
    cancelled: badgeStyles.error,
  }
  return map[status] ?? badgeStyles.default
}

function automationLabel(level: string): string {
  const map: Record<string, string> = {
    manual: "Manual",
    semi: "Semi-automático",
    full: "Totalmente automático",
  }
  return map[level] ?? level
}

// ── Stage pipeline strip ───────────────────────────────────────────────────

function StagePipeline({ project }: { project: CampaignItem }) {
  const { stages } = project
  if (!stages.length) return null
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {stages.map((stage, idx) => (
        <React.Fragment key={stage.name}>
          {idx > 0 && (
            <ChevronRight className="w-3 h-3 text-lia-text-tertiary shrink-0" />
          )}
          <div
            className={cn(
              "flex flex-col items-center gap-1 px-3 py-2 rounded-md text-center shrink-0 min-w-[80px]",
              stage.status === "completed" && "bg-lia-btn-primary-bg/10",
              stage.status === "in_progress" && "bg-lia-accent/10 ring-1 ring-lia-accent/50",
              stage.status === "pending" && "bg-lia-bg-secondary"
            )}
          >
            <span
              className={cn(
                "text-micro font-semibold uppercase tracking-wider",
                stage.status === "completed" && "text-lia-btn-primary-bg",
                stage.status === "in_progress" && "text-lia-accent",
                stage.status === "pending" && "text-lia-text-tertiary"
              )}
            >
              {stage.label}
            </span>
            <div
              className={cn(
                "h-1 w-full rounded-full",
                stage.status === "completed" && "bg-lia-btn-primary-bg",
                stage.status === "in_progress" && "bg-lia-accent",
                stage.status === "pending" && "bg-lia-bg-tertiary"
              )}
            />
          </div>
        </React.Fragment>
      ))}
    </div>
  )
}

// ── Metric cards ───────────────────────────────────────────────────────────

interface MetricCardProps {
  icon: React.ElementType
  label: string
  value: number
  highlight?: boolean
}

function MetricCard({ icon: Icon, label, value, highlight }: MetricCardProps) {
  return (
    <StudioCardShell tone="elevated">
      <div className="p-4 flex items-center gap-3">
        <div
          className={cn(
            "w-9 h-9 rounded-md flex items-center justify-center shrink-0",
            highlight ? "bg-lia-btn-primary-bg/10" : "bg-lia-bg-secondary"
          )}
        >
          <Icon
            className={cn(
              "w-4 h-4",
              highlight ? "text-lia-btn-primary-bg" : "text-lia-text-secondary"
            )}
          />
        </div>
        <div className="min-w-0">
          <p className="text-heading-md font-bold text-lia-text-primary">{value}</p>
          <p className="text-micro text-lia-text-secondary truncate">{label}</p>
        </div>
      </div>
    </StudioCardShell>
  )
}

// ── Skeleton ───────────────────────────────────────────────────────────────

function ProjetoDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary" />
        <div className="h-6 w-48 bg-lia-bg-tertiary rounded" />
        <div className="h-5 w-16 bg-lia-bg-tertiary rounded" />
      </div>
      <div className="h-16 bg-lia-bg-tertiary rounded-lg" />
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-20 bg-lia-bg-tertiary rounded-lg" />
        ))}
      </div>
    </div>
  )
}

// ── Main client component ──────────────────────────────────────────────────

interface ProjetoDetailClientProps {
  id: string
}

export default function ProjetoDetailClient({ id }: ProjetoDetailClientProps) {
  const { project, isLoading, isError, advance, isAdvancing } = useProjectDetail(id)

  if (isLoading) {
    return (
      <div className="p-6">
        <ProjetoDetailSkeleton />
      </div>
    )
  }

  if (isError || !project) {
    return (
      <div className="p-6 flex flex-col items-center justify-center min-h-[300px] gap-4">
        <AlertCircle className="w-10 h-10 text-lia-text-error" />
        <p className="text-body text-lia-text-secondary">Projeto não encontrado ou erro ao carregar.</p>
        <button
          type="button"
          className="text-small text-lia-btn-primary-bg hover:underline flex items-center gap-1"
          onClick={() => window.history.back()}
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Voltar
        </button>
      </div>
    )
  }

  const canAdvance =
    project.status === "active" &&
    project.current_stage_index < project.stages.length - 1

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button
          type="button"
          aria-label="Voltar para projetos"
          className="mt-0.5 p-1.5 rounded-md hover:bg-lia-bg-secondary text-lia-text-secondary hover:text-lia-text-primary transition-colors"
          onClick={() => window.history.back()}
        >
          <ArrowLeft className="w-4 h-4" />
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <FolderKanban className="w-5 h-5 text-lia-text-secondary shrink-0" />
            <h1 className="text-heading-md font-bold text-lia-text-primary">{project.name}</h1>
            <span className={cn("px-2 py-0.5 rounded text-micro font-medium shrink-0", statusBadge(project.status))}>
              {statusLabel(project.status)}
            </span>
            <span className="px-2 py-0.5 rounded text-micro font-medium bg-lia-bg-secondary text-lia-text-secondary shrink-0">
              {automationLabel(project.automation_level)}
            </span>
          </div>
          {project.description && (
            <p className="text-small text-lia-text-secondary mt-1">{project.description}</p>
          )}
        </div>

        {canAdvance && (
          <button
            type="button"
            disabled={isAdvancing}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-small font-medium shrink-0",
              "bg-lia-btn-primary-bg text-lia-btn-primary-text",
              "hover:opacity-90 transition-opacity",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            onClick={() => advance()}
          >
            {isAdvancing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
            Avançar etapa
          </button>
        )}
      </div>

      {/* Stage pipeline */}
      <StudioCardShell tone="elevated">
        <div className="p-4 space-y-3">
          <p className="text-small font-medium text-lia-text-secondary uppercase tracking-wider">Pipeline</p>
          <StagePipeline project={project} />
        </div>
      </StudioCardShell>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard icon={Users} label="Total" value={project.total_candidates} />
        <MetricCard icon={CheckCircle2} label="Triados" value={project.candidates_screened} />
        <MetricCard icon={UserCheck} label="Contactados" value={project.candidates_contacted} />
        <MetricCard icon={UserCheck} label="Entrevistados" value={project.candidates_interviewed} />
        <MetricCard icon={Handshake} label="Ofertas" value={project.candidates_offered} />
        <MetricCard icon={BadgeCheck} label="Contratados" value={project.candidates_hired} highlight />
      </div>
    </div>
  )
}
