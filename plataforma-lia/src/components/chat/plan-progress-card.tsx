"use client"

/**
 * PlanProgressCard — Visual feedback for multi-step Lia execution plans.
 *
 * Renders when a message contains `execution_plan` data (e.g. after a PlanDetector match).
 * Shows each AgentTask as a step with status: pending → running → completed/skipped/failed.
 *
 * Design: compact card, consistent with lia-bg-primary palette.
 */

import React, { memo } from "react"
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  SkipForward,
  Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Chip, type ChipVariant } from "@/components/ui/chip"

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PlanTask {
  task_id: string
  domain_id: string
  action_id: string
  status: "pending" | "running" | "completed" | "failed" | "skipped"
  duration_ms?: number | null
  error?: string | null
  skip_reason?: string | null
}

export interface ExecutionPlanData {
  plan_id: string
  status: "pending" | "in_progress" | "completed" | "partial" | "failed"
  total_tasks: number
  completed: number
  failed: number
  skipped: number
  pending: number
  total_duration_ms?: number
  detected_pattern?: string
  tasks: PlanTask[]
}

interface PlanProgressCardProps {
  plan: ExecutionPlanData
  className?: string
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const DOMAIN_LABELS: Record<string, string> = {
  cv_screening: "Triagem de CV",
  sourcing: "Captação",
  job_management: "Gestão de Vagas",
  analytics: "Analytics",
  communication: "Comunicação",
  automation: "Automação",
  interview_scheduling: "Agendamento",
  recruiter_assistant: "Assistente",
}

const ACTION_LABELS: Record<string, string> = {
  parse_and_create_candidate: "Parsear e criar candidato",
  add_to_vacancy: "Adicionar à vaga",
  run_wsi_screening: "Disparar triagem WSI",
  add_candidate_to_vacancy: "Adicionar candidato à vaga",
  analyze_cv_match: "Avaliação BARS",
  search_candidates: "Buscar candidatos",
  generate_report: "Gerar relatório",
  export_report: "Exportar relatório",
  move_candidate_stage: "Mover candidato de etapa",
  send_notification: "Enviar notificação",
  create_job: "Criar vaga",
  screen_candidates: "Triar candidatos",
  evaluate_candidate: "Avaliar candidato",
  filter_candidates: "Filtrar candidatos",
}

function getTaskLabel(task: PlanTask): string {
  return ACTION_LABELS[task.action_id] ||
    task.action_id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())
}

function getDomainLabel(domain: string): string {
  return DOMAIN_LABELS[domain] || domain
}

function formatDuration(ms?: number | null): string {
  if (!ms) return ""
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const PATTERN_LABELS: Record<string, string> = {
  adicionar_analisar_wsi: "Adicionar + Triagem WSI",
  upload_cadastrar_triar: "Upload CV → Cadastrar → Triar",
  buscar_e_comparar: "Buscar + Comparar",
  triagem_e_agendar: "Triagem + Agendar",
  mover_e_notificar: "Mover + Notificar",
  filtrar_e_reportar: "Filtrar + Relatório",
  relatorio_e_exportar: "Relatório + Exportar",
}

// ─── Status Icon ─────────────────────────────────────────────────────────────

function StatusIcon({ status }: { status: PlanTask["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="w-4 h-4 text-status-success flex-shrink-0" />
    case "failed":
      return <XCircle className="w-4 h-4 text-status-error flex-shrink-0" />
    case "running":
      return <Loader2 className="w-4 h-4 text-lia-interactive-active animate-spin motion-reduce:animate-none flex-shrink-0" />
    case "skipped":
      return <SkipForward className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
    default:
      return <Clock className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
  }
}

// ─── Plan Status Badge ────────────────────────────────────────────────────────

function PlanStatusBadge({ status }: { status: ExecutionPlanData["status"] }) {
  const config: Record<string, { label: string; variant: ChipVariant; muted?: boolean }> = {
    completed: { label: "Concluído", variant: "success" },
    partial: { label: "Parcial", variant: "warning" },
    failed: { label: "Falhou", variant: "danger" },
    in_progress: { label: "Em progresso", variant: "info" },
    pending: { label: "Aguardando", variant: "neutral", muted: true },
  }
  const { label, variant, muted } = config[status] || config.pending
  return (
    <Chip density="compact" variant={variant} muted={muted}>
      {label}
    </Chip>
  )
}

// ─── Component ───────────────────────────────────────────────────────────────

const PlanProgressCardComponent = memo(function PlanProgressCard({
  plan,
  className,
}: PlanProgressCardProps) {
  const patternLabel = PATTERN_LABELS[plan.detected_pattern || ""] || plan.detected_pattern

  return (
    <div
      className={cn(
        "mt-3 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-lia-bg-primary/40">
        <div className="flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-wedo-cyan" />
          <span className="text-xs font-semibold text-lia-text-primary">
            {patternLabel || "Plano de Execução"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {plan.total_duration_ms ? (
            <span className="text-[10px] text-lia-text-tertiary">
              {formatDuration(plan.total_duration_ms)}
            </span>
          ) : null}
          <PlanStatusBadge status={plan.status} />
        </div>
      </div>

      {/* Tasks */}
      <div className="px-3 py-2 space-y-2">
        {plan.tasks.map((task, index) => (
          <div key={task.task_id} className="flex items-start gap-2.5">
            {/* Step number + connector */}
            <div className="flex flex-col items-center flex-shrink-0 mt-0.5">
              <div className="flex items-center justify-center w-5 h-5 rounded-full bg-lia-bg-primary text-[10px] font-bold text-lia-text-tertiary border border-lia-border-subtle">
                {index + 1}
              </div>
              {index < plan.tasks.length - 1 && (
                <div className="w-px h-4 bg-lia-border-subtle mt-1" />
              )}
            </div>

            {/* Task content */}
            <div className="flex-1 min-w-0 pb-1">
              <div className="flex items-center gap-1.5">
                <StatusIcon status={task.status} />
                <span
                  className={cn(
                    "text-xs font-medium truncate",
                    task.status === "completed" ? "text-lia-text-primary" :
                    task.status === "failed" ? "text-status-error" :
                    task.status === "running" ? "text-lia-text-primary" :
                    "text-lia-text-tertiary"
                  )}
                >
                  {getTaskLabel(task)}
                </span>
                {task.duration_ms ? (
                  <span className="text-[10px] text-lia-text-tertiary ml-auto flex-shrink-0">
                    {formatDuration(task.duration_ms)}
                  </span>
                ) : null}
              </div>

              {/* Domain label */}
              <span className="text-[10px] text-lia-text-tertiary ml-5">
                {getDomainLabel(task.domain_id)}
              </span>

              {/* Error/Skip reason */}
              {(task.error || task.skip_reason) && (
                <p className={cn(
                  "text-[10px] mt-0.5 ml-5",
                  task.error ? "text-status-error" : "text-lia-text-tertiary"
                )}>
                  {task.skip_reason || task.error}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Footer summary */}
      {plan.status !== "in_progress" && plan.status !== "pending" && (
        <div className="px-3 py-1.5 border-t border-lia-border-subtle bg-lia-bg-primary/20 flex gap-3">
          {plan.completed > 0 && (
            <span className="text-[10px] text-status-success">✓ {plan.completed} concluído{plan.completed !== 1 ? "s" : ""}</span>
          )}
          {plan.skipped > 0 && (
            <span className="text-[10px] text-lia-text-tertiary">⤼ {plan.skipped} ignorado{plan.skipped !== 1 ? "s" : ""}</span>
          )}
          {plan.failed > 0 && (
            <span className="text-[10px] text-status-error">✗ {plan.failed} falhou{plan.failed !== 1 ? "ram" : ""}</span>
          )}
        </div>
      )}
    </div>
  )
})

PlanProgressCardComponent.displayName = "PlanProgressCard"
export const PlanProgressCard = PlanProgressCardComponent
