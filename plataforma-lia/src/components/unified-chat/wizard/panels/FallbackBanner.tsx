"use client"

import React from "react"
import { AlertTriangle } from "lucide-react"

/**
 * Task #1065 — banner discreto exibido quando um nó do wizard caiu no
 * fallback determinístico (timeout do LLM ou exception). Sinaliza ao
 * recrutador que o conteúdo é uma sugestão mínima e merece revisão extra
 * antes da aprovação HITL. NÃO substitui o HITL — só dá contexto.
 *
 * Mantido como componente puro (sem estado, sem efeitos) para reuso nos
 * 4 painéis (`JdEnrichment`, `BigFive`, `Salary`, `WsiQuestions`) e para
 * portabilidade futura ao Vue/Vuetify.
 */
interface Props {
  message?: string
}

export function FallbackBanner({
  message = "Geração automática indisponível agora — sugestão mínima, revise antes de aprovar.",
}: Props) {
  return (
    <div
      role="status"
      data-testid="wizard-fallback-banner"
      className="mx-4 mt-3 flex items-start gap-2 rounded-md border border-status-warning/30 bg-status-warning/5 px-3 py-2"
    >
      <AlertTriangle
        className="w-3.5 h-3.5 text-status-warning flex-shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <p className="text-xs text-status-warning leading-snug">{message}</p>
    </div>
  )
}
