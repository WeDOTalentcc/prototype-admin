"use client"

import React from "react"
import { CheckCircle2, ExternalLink, Plus } from "lucide-react"

interface Props {
  data: Record<string, unknown>
}

/**
 * DonePanel — final wizard stage. Shows success state with links.
 */
export function DonePanel({ data }: Props) {
  const jobId = data.job_id as number | null
  const handoffUrl = data.handoff_url as string | null
  const shareLink = data.share_link as string | null
  const jobTitle = data.job_title as string | null

  return (
    <div className="p-4 space-y-5 font-['Open_Sans',sans-serif]">
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
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-wedo-cyan/10 text-wedo-cyan hover:bg-wedo-cyan/20 transition-colors text-sm font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            Ir para a vaga
          </button>
        )}

        {shareLink && (
          <button
            onClick={() => {
              navigator.clipboard.writeText(shareLink)
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-lia-bg-secondary text-lia-text-primary hover:bg-lia-interactive-hover transition-colors text-sm"
          >
            <ExternalLink className="w-4 h-4 text-lia-text-secondary" />
            Copiar link de compartilhamento
          </button>
        )}

        <button
          onClick={() => window.dispatchEvent(new CustomEvent("lia:prefill-message", {
            detail: { message: "Criar nova vaga" },
          }))}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-lia-bg-secondary text-lia-text-primary hover:bg-lia-interactive-hover transition-colors text-sm"
        >
          <Plus className="w-4 h-4 text-lia-text-secondary" />
          Criar outra vaga
        </button>
      </div>

      {/* Summary stats */}
      {jobId && (
        <div className="rounded-md bg-lia-bg-secondary p-2.5 text-[11px] text-lia-text-disabled text-center">
          Job ID: {jobId}
        </div>
      )}
    </div>
  )
}
