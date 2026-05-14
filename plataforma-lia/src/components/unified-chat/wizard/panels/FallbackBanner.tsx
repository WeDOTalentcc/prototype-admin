"use client"

import React from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"

/**
 * Task #1065 — banner discreto exibido quando um nó do wizard caiu no
 * fallback determinístico (timeout do LLM ou exception). Sinaliza ao
 * recrutador que o conteúdo é uma sugestão mínima e merece revisão extra
 * antes da aprovação HITL. NÃO substitui o HITL — só dá contexto.
 *
 * Task #1067 — agora aceita um `reason` (root-cause label vindo do
 * backend: `"timeout"`, `"provider_error"`, `"exception"`) e oferece
 * "Tentar novamente" via `onRetry`. A copy é específica por causa para
 * o recrutador entender se vale tentar de novo ou aceitar o mínimo.
 *
 * Mantido como componente puro (sem estado, sem efeitos) para reuso nos
 * 4 painéis (`JdEnrichment`, `BigFive`, `Salary`, `WsiQuestions`) e para
 * portabilidade futura ao Vue/Vuetify.
 */
type FallbackReason = "timeout" | "provider_error" | "exception" | string

interface Props {
  reason?: FallbackReason | null
  message?: string
  onRetry?: () => void
}

const DEFAULT_MESSAGE =
  "Geração automática indisponível agora — sugestão mínima, revise antes de aprovar."

const REASON_COPY: Record<string, string> = {
  timeout:
    "Tempo esgotado — o provedor de IA não respondeu a tempo. Mostramos uma sugestão mínima; tente de novo ou revise antes de aprovar.",
  provider_error:
    "Erro do provedor de IA (cota ou indisponibilidade). Mostramos uma sugestão mínima; tente de novo em alguns instantes ou revise antes de aprovar.",
  exception:
    "Falha inesperada na geração automática. Mostramos uma sugestão mínima; tente de novo ou revise antes de aprovar.",
}

export function FallbackBanner({ reason, message, onRetry }: Props) {
  const resolvedMessage =
    message ?? (reason && REASON_COPY[reason]) ?? DEFAULT_MESSAGE

  return (
    <div
      role="status"
      data-testid="wizard-fallback-banner"
      data-reason={reason ?? "unknown"}
      className="mx-4 mt-3 flex items-start gap-2 rounded-md border border-status-warning/30 bg-status-warning/5 px-3 py-2"
    >
      <AlertTriangle
        className="w-3.5 h-3.5 text-status-warning flex-shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <p className="flex-1 text-xs text-status-warning leading-snug">
        {resolvedMessage}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          data-testid="wizard-fallback-retry"
          className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium text-status-warning hover:bg-status-warning/10 transition-colors motion-reduce:transition-none"
        >
          <RefreshCw className="w-3 h-3" aria-hidden="true" />
          Tentar novamente
        </button>
      )}
    </div>
  )
}
