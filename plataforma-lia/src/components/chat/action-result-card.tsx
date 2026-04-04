"use client"

import React from "react"
import { CheckCircle2, ArrowRight, Mail, Calendar, FileSearch, AlertCircle, PauseCircle, XCircle, Copy, RefreshCw, Save, Globe, FileText, Brain, LayoutTemplate } from "lucide-react"

interface ActionResultData {
  candidate_id?: string
  candidate_name?: string
  from_stage?: string
  to_stage?: string
  subject?: string
  datetime?: string
  moved_at?: string
  sent_at?: string
  scheduled_at?: string
  simulated?: boolean
  action?: string
  [key: string]: unknown
}

interface ActionResultCardProps {
  actionType: string
  result: ActionResultData
  className?: string
}

const ACTION_CONFIGS: Record<string, { icon: React.ElementType; label: string; color: string }> = {
  move_candidate: { icon: ArrowRight, label: "Candidato Movido", color: "cyan" },
  send_email: { icon: Mail, label: "Email Enviado", color: "emerald" },
  schedule_interview: { icon: Calendar, label: "Entrevista Agendada", color: "violet" },
  start_screening: { icon: FileSearch, label: "Triagem Iniciada", color: "amber" },
  analyze_profile: { icon: FileSearch, label: "Perfil Analisado", color: "blue" },
  pause_job: { icon: PauseCircle, label: "Vaga Pausada", color: "amber" },
  close_job: { icon: XCircle, label: "Vaga Encerrada", color: "red" },
  duplicate_job: { icon: Copy, label: "Vaga Duplicada", color: "violet" },
  reopen_job: { icon: RefreshCw, label: "Vaga Reaberta", color: "emerald" },
  save_draft: { icon: Save, label: "Rascunho Salvo", color: "blue" },
  publish_job: { icon: Globe, label: "Vaga Publicada", color: "emerald" },
  generate_jd: { icon: FileText, label: "Descrição Gerada", color: "cyan" },
  generate_wsi: { icon: Brain, label: "Perguntas WSI Geradas", color: "violet" },
  apply_template: { icon: LayoutTemplate, label: "Template Aplicado", color: "blue" },
  wsi_screening: { icon: FileSearch, label: "Triagem WSI Iniciada", color: "amber" },
  contact_candidate: { icon: Mail, label: "Candidato Contatado", color: "emerald" },
}

export function ActionResultCard({ actionType, result, className = "" }: ActionResultCardProps) {
  const config = ACTION_CONFIGS[actionType] || {
    icon: CheckCircle2,
    label: "Ação Executada",
    color: "cyan",
  }

  const Icon = config.icon
  const colorMap: Record<string, string> = {
    cyan: "border-wedo-cyan/30 bg-wedo-cyan/5",
    emerald: "border-status-success/30/30 bg-status-success/5",
    violet: "border-wedo-purple/30/30 bg-wedo-purple/5",
    amber: "border-status-warning/30/30 bg-status-warning/5",
    blue: "border-wedo-cyan/30/30 bg-wedo-cyan/5",
    red: "border-status-error/30/30 bg-status-error/5",
  }
  const iconColorMap: Record<string, string> = {
    cyan: "text-wedo-cyan",
    emerald: "text-status-success",
    violet: "text-wedo-purple",
    amber: "text-status-warning",
    blue: "text-wedo-cyan-dark",
    red: "text-status-error",
  }
  const badgeColorMap: Record<string, string> = {
    cyan: "bg-wedo-cyan/20 text-wedo-cyan",
    emerald: "bg-status-success/20 text-status-success",
    violet: "bg-wedo-purple/20 text-wedo-purple",
    amber: "bg-status-warning/20 text-status-warning",
    blue: "bg-wedo-cyan/20 text-wedo-cyan-dark",
    red: "bg-status-error/20 text-status-error",
  }

  const borderBg = colorMap[config.color] || colorMap.cyan
  const iconColor = iconColorMap[config.color] || iconColorMap.cyan
  const badgeColor = badgeColorMap[config.color] || badgeColorMap.cyan

  return (
    <div className={`rounded-md border ${borderBg} p-3 my-2 ${className}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1 rounded-md ${badgeColor}`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <span className="text-sm font-medium text-lia-text-disabled">{config.label}</span>
        <CheckCircle2 className="w-4 h-4 text-status-success ml-auto" />
      </div>

      <div className="space-y-1 text-xs text-lia-text-tertiary">
        {result.candidate_name && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Candidato:</span>
            <span className="text-lia-text-disabled font-medium">{result.candidate_name}</span>
          </div>
        )}

        {actionType === "move_candidate" && result.to_stage && (
          <div className="flex items-center gap-2">
            {result.from_stage && (
              <>
                <span className="px-1.5 py-0.5 rounded-md bg-lia-bg-tertiary text-lia-text-disabled">{result.from_stage}</span>
                <ArrowRight className="w-3 h-3 text-lia-text-secondary" />
              </>
            )}
            <span className={`px-1.5 py-0.5 rounded-md ${badgeColor}`}>{result.to_stage}</span>
          </div>
        )}

        {actionType === "send_email" && result.subject && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Assunto:</span>
            <span className="text-lia-text-disabled">{result.subject}</span>
          </div>
        )}

        {actionType === "schedule_interview" && result.datetime && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Data:</span>
            <span className="text-lia-text-disabled">{result.datetime}</span>
          </div>
        )}

        {(actionType === "pause_job" || actionType === "close_job" || actionType === "reopen_job") && (
          <div className="flex items-center gap-2">
            {(result as any).job_title && (
              <>
                <span className="text-lia-text-secondary">Vaga:</span>
                <span className="text-lia-text-disabled font-medium">{String((result as any).job_title)}</span>
              </>
            )}
          </div>
        )}

        {(actionType === "duplicate_job" && result.new_job_id as any) && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Nova vaga ID:</span>
            <span className={`px-1.5 py-0.5 rounded-md ${badgeColor}`}>#{String(result.new_job_id)}</span>
          </div>
        )}

        {(actionType === "save_draft" || actionType === "publish_job") && result.completeness !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Completude:</span>
            <span className="text-lia-text-disabled font-medium">{result.completeness as number}%</span>
          </div>
        )}

        {actionType === "generate_jd" && result.sections_count !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Seções geradas:</span>
            <span className="text-lia-text-disabled font-medium">{result.sections_count as number}</span>
          </div>
        )}

        {actionType === "generate_wsi" && result.questions_count !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-lia-text-secondary">Perguntas geradas:</span>
            <span className="text-lia-text-disabled font-medium">{result.questions_count as number}</span>
          </div>
        )}

        {result.simulated && (
          <div className="flex items-center gap-1 mt-1 text-status-warning/60">
            <AlertCircle className="w-3 h-3" />
            <span className="text-micro">Simulado (aguardando integração real)</span>
          </div>
        )}
      </div>
    </div>
  )
}
