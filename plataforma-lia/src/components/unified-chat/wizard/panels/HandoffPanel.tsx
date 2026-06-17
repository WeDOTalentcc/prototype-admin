"use client"

import React from "react"
import { ExternalLink, Link2, PartyPopper } from "lucide-react"
import type { HandoffData } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
}

/**
 * HandoffPanel — final stage. Shows job page link + share link.
 */
export function HandoffPanel({ data }: Props) {
  const d = data as unknown as HandoffData

  return (
    <div className="px-4 py-6 flex flex-col items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-status-success/10 flex items-center justify-center">
        <PartyPopper className="w-6 h-6 text-status-success" />
      </div>

      <div className="text-center">
        <h4 className="text-sm font-semibold text-lia-text-primary">
          Vaga publicada!
        </h4>
        <p className="text-xs text-lia-text-secondary mt-1">
          A vaga esta ativa e o screening automatico foi iniciado.
        </p>
      </div>

      {d.handoff_url && (
        <a
          href={d.handoff_url}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors motion-reduce:transition-none"
        >
          <ExternalLink className="w-4 h-4" />
          Ir para a vaga
        </a>
      )}

      {d.share_link && (
        <div className="w-full p-2.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
          <div className="flex items-center gap-1.5 mb-1">
            <Link2 className="w-3.5 h-3.5 text-wedo-cyan" />
            <span className="text-xs font-medium text-lia-text-secondary">
              Link de compartilhamento
            </span>
          </div>
          <p className="text-xs text-lia-text-primary break-all">
            {d.share_link}
          </p>
        </div>
      )}
    </div>
  )
}
