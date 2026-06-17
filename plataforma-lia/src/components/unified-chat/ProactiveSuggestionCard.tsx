"use client"

/**
 * ProactiveSuggestionCard — renderiza as sugestões proativas scheduler-driven
 * como cards inline dentro de uma mensagem da LIA no chat unificado.
 *
 * Aposenta o dropdown `ProactiveHintsBadge`. Cada card mostra severidade
 * (acento via tokens `status-*`/`lia-*`), título, mensagem, um botão de ação
 * (dispara `lia:proactive-action`, roteado por `useProactiveActionRouter`) e
 * "Dispensar" (POST direto no endpoint de dismiss).
 *
 * Tokens canônicos: acento de IA via `wedo-cyan`; severidade via `status-*`.
 */
import React, { useState } from "react"
import { AlertCircle, ArrowRight, X } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import {
  useProactiveHints,
  type ProactiveHint,
  type ProactiveHintSeverity,
} from "@/hooks/proactive/use-proactive-hints"

interface Props {
  hints: ProactiveHint[]
  className?: string
}

const SEVERITY_ACCENT: Record<ProactiveHintSeverity, string> = {
  critical: "border-l-status-error",
  high: "border-l-status-warning",
  medium: "border-l-lia-accent",
  low: "border-l-lia-border-default",
}

const SEVERITY_DOT: Record<ProactiveHintSeverity, string> = {
  critical: "bg-status-error",
  high: "bg-status-warning",
  medium: "bg-lia-accent",
  low: "bg-lia-text-tertiary",
}

const SEVERITY_LABEL: Record<ProactiveHintSeverity, string> = {
  critical: "Crítico",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
}

// Rótulos amigáveis para os action ids conhecidos (mesmos tratados em
// useProactiveActionRouter). Fallback conversacional para ids não mapeados.
const ACTION_LABELS: Record<string, string> = {
  request_website_and_scrape: "Analisar nosso site",
  suggest_recruiting_policy: "Sugerir política",
  culture_onboarding: "Configurar cultura",
  batch_enrich_contacts: "Enriquecer contatos",
  suggest_screening_questions: "Sugerir perguntas",
  navigate_to_settings: "Abrir configurações",
  navigate_to_company_data: "Abrir dados da empresa",
  navigate_to_benefits_import: "Importar benefícios",
}

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? "Resolver com a IA"
}

function dispatchHintAction(hint: ProactiveHint): void {
  if (!hint.action) return
  window.dispatchEvent(
    new CustomEvent("lia:proactive-action", {
      detail: {
        type: hint.detector,
        action: hint.action,
        metadata: {
          ...(hint.action_params ?? {}),
          related_job_id: hint.related_job_id,
          related_candidate_id: hint.related_candidate_id,
        },
      },
    }),
  )
}

export function ProactiveSuggestionCard({ hints, className }: Props) {
  // Usa o MESMO key SWR que o injetor (useProactiveHintsInChat) — o dismiss
  // muta o cache canônico compartilhado, então o hint NÃO reaparece após
  // restore de histórico / troca de conversa (fix da janela de inconsistência).
  const { dismiss: dismissHint } = useProactiveHints()
  // Hide local: os cards renderizam do snapshot `hints` (metadata da mensagem),
  // não da lista SWR — então precisamos esconder visualmente também.
  const [dismissed, setDismissed] = useState<Set<string>>(() => new Set())

  const handleDismiss = async (hintId: string): Promise<void> => {
    // Optimistic hide.
    setDismissed((prev) => {
      const next = new Set(prev)
      next.add(hintId)
      return next
    })
    try {
      // SWR dismiss: optimistic mutate + POST + revalidate (fail-loud — em erro
      // re-lança e o revalidate do `finally` restaura o estado do servidor).
      await dismissHint(hintId)
    } catch (err) {
      // Fail-loud: restaura o card, sinaliza o erro, NUNCA finge sucesso.
      console.error("[ProactiveSuggestionCard] dismiss failed:", err)
      setDismissed((prev) => {
        const next = new Set(prev)
        next.delete(hintId)
        return next
      })
      toast.error("Não consegui dispensar a sugestão. Tente novamente.", { description: "Verifique sua conexão e tente novamente." })
    }
  }

  const visible = hints.filter((h) => !dismissed.has(h.id))
  if (visible.length === 0) return null

  return (
    <div
      className={cn("mt-2 space-y-2", className)}
      data-testid="proactive-suggestion-card"
    >
      {visible.map((hint) => (
        <div
          key={hint.id}
          data-testid={`proactive-suggestion-${hint.detector}`}
          className={cn(
            "rounded-md border border-lia-border-default border-l-2 bg-lia-bg-secondary px-3 py-2.5",
            SEVERITY_ACCENT[hint.severity],
          )}
        >
          <div className="flex items-start gap-2">
            <span
              className={cn(
                "mt-1.5 h-2 w-2 rounded-full shrink-0",
                SEVERITY_DOT[hint.severity],
              )}
              aria-hidden
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-[13px] text-lia-text-primary">
                  {hint.title}
                </span>
                {hint.severity === "critical" && (
                  <AlertCircle className="h-3.5 w-3.5 text-status-error shrink-0" />
                )}
                <span className="ml-auto text-[10px] text-lia-text-tertiary shrink-0">
                  {SEVERITY_LABEL[hint.severity]}
                </span>
              </div>
              <p className="text-[12px] text-lia-text-secondary mt-1">
                {hint.message}
              </p>
              <div className="mt-2 flex items-center gap-3">
                {hint.action && (
                  <button
                    type="button"
                    onClick={() => dispatchHintAction(hint)}
                    data-testid={`proactive-suggestion-action-${hint.id}`}
                    className={cn(
                      "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px]",
                      "border border-wedo-cyan/30 bg-wedo-cyan/5 text-wedo-cyan-text",
                      "hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none",
                    )}
                  >
                    <span>{actionLabel(hint.action)}</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => void handleDismiss(hint.id)}
                  data-testid={`proactive-suggestion-dismiss-${hint.id}`}
                  className="inline-flex items-center gap-1 text-[11px] text-lia-text-tertiary hover:text-lia-text-primary"
                >
                  <X className="h-3 w-3" />
                  <span>Dispensar</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default ProactiveSuggestionCard
