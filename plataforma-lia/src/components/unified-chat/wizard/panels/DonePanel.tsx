"use client"

import React from "react"
import { CheckCircle2, ExternalLink, Plus, Target, X, Mail } from "lucide-react"

interface Props {
  data: Record<string, unknown>
}

/**
 * DonePanel — final wizard stage. Shows success state with links.
 */
export function DonePanel({ data }: Props) {
  const jobId = data.job_id as number | string | null
  const handoffUrl = data.handoff_url as string | null
  const shareLink = data.share_link as string | null
  const jobTitle = data.job_title as string | null
  const managerEmail = data.parsed_manager_email as string | null
  const managerName = data.parsed_manager_name as string | null

  return (
    <div className="p-4 space-y-5">
      {/* Success icon */}
      <div className="flex flex-col items-center gap-3 py-4">
        <div className="w-12 h-12 rounded-full bg-status-success/10 flex items-center justify-center">
          <CheckCircle2 className="w-7 h-7 text-status-success" />
        </div>
        <div className="text-center">
          <h3 className="text-sm font-semibold text-lia-text-primary">
            Vaga criada com sucesso!
          </h3>
          {jobTitle && (
            <p className="text-xs text-lia-text-secondary mt-1">{jobTitle}</p>
          )}
        </div>
      </div>

      {/* Action links */}
      <div className="space-y-2">
        {handoffUrl && (
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
              detail: { page: "vagas", hint: `Vaga ${jobTitle || jobId}` },
            }))}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-wedo-cyan/10 text-wedo-cyan-text hover:bg-wedo-cyan/20 transition-colors text-sm font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            Ir para a vaga
          </button>
        )}

        {/* CTA calibração — ação principal pós-publish */}
        <button
          onClick={() => window.dispatchEvent(new CustomEvent("lia:prefill-message", {
            detail: { message: `Quero calibrar perfis de candidatos para a vaga ${jobTitle || jobId || ''}` },
          }))}
          className="w-full flex flex-col gap-0.5 px-3 py-2.5 rounded-md bg-wedo-cyan/15 text-wedo-cyan-text hover:bg-wedo-cyan/25 transition-colors text-sm font-medium border border-wedo-cyan/20"
        >
          <div className="flex items-center gap-2.5">
            <Target className="w-4 h-4" />
            Calibrar perfis antes de buscar
          </div>
          <span className="text-[10px] text-wedo-cyan/70 font-normal ml-[26px]">
            A LIA aprende seu critério e libera o sourcing automático
          </span>
        </button>

        {/* W1-J: Briefing executivo para o gestor */}
        {managerEmail && (
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("lia:prefill-message", {
              detail: { message: "Enviar plano de trabalho para o gestor" },
            }))}
            className="w-full flex flex-col gap-0.5 px-3 py-2.5 rounded-md bg-lia-bg-secondary hover:bg-lia-interactive-hover transition-colors text-sm border border-lia-border-subtle"
          >
            <div className="flex items-center gap-2.5 text-lia-text-primary font-medium">
              <Mail className="w-4 h-4 text-lia-text-secondary" />
              Enviar briefing ao gestor
            </div>
            <span className="text-[10px] text-lia-text-tertiary font-normal ml-[26px]">
              {managerName ? `Para ${managerName}` : managerEmail}
            </span>
          </button>
        )}

        {shareLink && (
          <button
            onClick={() => {
              navigator.clipboard.writeText(shareLink)
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-lia-bg-secondary text-lia-text-primary hover:bg-lia-interactive-hover transition-colors text-sm"
          >
            <ExternalLink className="w-4 h-4 text-lia-text-secondary" />
            Copiar link de compartilhamento
          </button>
        )}

        <button
          onClick={() => window.dispatchEvent(new CustomEvent("lia:prefill-message", {
            detail: { message: "Criar nova vaga" },
          }))}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md bg-lia-bg-secondary text-lia-text-primary hover:bg-lia-interactive-hover transition-colors text-sm"
        >
          <Plus className="w-4 h-4 text-lia-text-secondary" />
          Criar outra vaga
        </button>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent("lia:wizard-close-panel"))}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md border border-lia-border text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors text-sm"
        >
          <X className="w-4 h-4" />
          Fechar painel
        </button>
      </div>

      {/* Summary stats */}
      {/* A-09 / WCAG 2.1 AA 1.4.3: was `text-[11px] text-lia-text-muted`. */}
      {jobId && (
        <div className="rounded-md bg-lia-bg-secondary p-2.5 text-xs text-lia-text-secondary text-center">
          Job ID: {jobId}
        </div>
      )}
    </div>
  )
}
