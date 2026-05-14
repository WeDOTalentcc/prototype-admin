"use client"

import React from "react"
import { ShieldAlert } from "lucide-react"
import type { AiDegradedMode } from "../wizard-types"

/**
 * Task #1070 — banner exibido quando o `WizardFallbackTracker` agrega varios
 * fallbacks (`*_fallback_reason`) na mesma sessao de wizard ou no tenant
 * inteiro nos ultimos N minutos. Sinaliza ao recrutador que o provedor de
 * IA esta degradado AGORA — nao e ruido pontual de uma chamada — e que
 * vale a pena revisar com mais cuidado ou aguardar.
 *
 * Mais alto na hierarquia visual que o `FallbackBanner` por causa: este
 * cobre a sessao/tenant, nao apenas o stage atual.
 */
interface Props {
  state: AiDegradedMode | null | undefined
}

const SCOPE_COPY: Record<string, string> = {
  session:
    "A IA caiu em modo de emergencia varias vezes nesta sessao. Recomendamos revisar com mais cuidado as sugestoes ou aguardar antes de aprovar.",
  tenant:
    "Detectamos varias falhas do provedor de IA na ultima hora. A qualidade das sugestoes esta degradada agora — recomendamos revisar com mais cuidado ou aguardar.",
}

function formatBreakdown(breakdown: Record<string, number> | undefined): string {
  if (!breakdown) return ""
  const parts = Object.entries(breakdown)
    .filter(([, n]) => n > 0)
    .map(([reason, n]) => `${n}x ${reason}`)
  return parts.join(", ")
}

export function AiDegradedModeBanner({ state }: Props) {
  if (!state || !state.active) return null
  const scope = state.scope
  const message = SCOPE_COPY[scope] ?? SCOPE_COPY.session
  const breakdown = formatBreakdown(state.reason_breakdown)

  return (
    <div
      role="alert"
      data-testid="wizard-ai-degraded-banner"
      data-scope={scope}
      className="mx-4 mt-3 flex items-start gap-2 rounded-md border border-status-error/40 bg-status-error/10 px-3 py-2"
    >
      <ShieldAlert
        className="w-4 h-4 text-status-error flex-shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <div className="flex-1 space-y-0.5">
        <p className="text-xs font-medium text-status-error leading-snug">
          Qualidade da IA degradada agora
        </p>
        <p className="text-xs text-status-error/90 leading-snug">{message}</p>
        {breakdown && (
          <p className="text-[10px] text-status-error/80 leading-snug">
            {state.count} falha{state.count === 1 ? "" : "s"} ({breakdown})
          </p>
        )}
      </div>
    </div>
  )
}
