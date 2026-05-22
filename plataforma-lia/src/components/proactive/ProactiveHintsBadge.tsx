"use client"

/**
 * WT-2022 Camada IA Proativa: UI badge canonical para hints scheduler-driven.
 *
 * Diferenciacao do ProactiveActionsBell (existente):
 * - ActionsBell: actions por candidato/vaga (matching score, sourcing leads)
 * - HintsBadge (este): hints ambientais (profile, DSR, pipeline, workforce)
 *
 * Comportamento:
 * - Mostra count badge no botao (sumido se 0)
 * - Click abre dropdown com lista ordenada por severity (critical > high > ...)
 * - Click no item dispatches ui_action via lia:proactive-action event
 *   (reusa useProactiveActionRouter existente — zero duplicacao)
 * - Botao "Dispensar" marca hint como REJECTED (chama backend dismiss)
 *
 * Tokens: usa lia-* design tokens canonical (NUNCA hardcoded color).
 */
import { AlertCircle, Lightbulb, X } from "lucide-react"
import { useState } from "react"

import { cn } from "@/lib/utils"
import {
  type ProactiveHint,
  type ProactiveHintSeverity,
  useProactiveHints,
} from "@/hooks/proactive/use-proactive-hints"

interface ProactiveHintsBadgeProps {
  className?: string
}

const SEVERITY_STYLES: Record<ProactiveHintSeverity, string> = {
  critical: "bg-status-error text-white",
  high: "bg-status-warning text-white",
  medium: "bg-lia-accent text-white",
  low: "bg-lia-bg-tertiary text-lia-text-primary",
}

const SEVERITY_DOT: Record<ProactiveHintSeverity, string> = {
  critical: "bg-status-error",
  high: "bg-status-warning",
  medium: "bg-lia-accent",
  low: "bg-lia-text-tertiary",
}

function dispatchHintAction(hint: ProactiveHint): void {
  if (!hint.action) return
  // Reusa o pattern existente do useProactiveActionRouter.
  window.dispatchEvent(
    new CustomEvent("lia:proactive-action", {
      detail: {
        type: hint.detector,
        action: hint.action,
        metadata: hint.action_params ?? {},
      },
    }),
  )
}

export function ProactiveHintsBadge({ className }: ProactiveHintsBadgeProps) {
  const { hints, count, isLoading, dismiss } = useProactiveHints()
  const [open, setOpen] = useState(false)

  if (isLoading && count === 0) {
    return null // nao polui UI no primeiro load
  }

  const handleHintClick = (hint: ProactiveHint) => {
    dispatchHintAction(hint)
    // Mantem hint visivel ate user dispensar — multipla intencao
    setOpen(false)
  }

  const handleDismiss = (
    event: React.MouseEvent<HTMLButtonElement>,
    hintId: string,
  ) => {
    event.stopPropagation()
    void dismiss(hintId)
  }

  return (
    <div className={cn("relative inline-block", className)}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        data-testid="proactive-hints-badge-btn"
        aria-label={`Sugestoes da LIA (${count})`}
        aria-expanded={open}
        className={cn(
          "relative inline-flex items-center justify-center",
          "h-9 w-9 rounded-full",
          "text-lia-text-secondary hover:text-lia-text-primary",
          "hover:bg-lia-bg-secondary transition-colors",
        )}
      >
        <Lightbulb className="h-5 w-5" />
        {count > 0 && (
          <span
            data-testid="proactive-hints-count"
            className={cn(
              "absolute -top-0.5 -right-0.5",
              "h-4 min-w-4 rounded-full px-1",
              "flex items-center justify-center",
              "text-[10px] font-bold text-white",
              "bg-lia-accent",
            )}
          >
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Lista de sugestoes da LIA"
          className={cn(
            "absolute right-0 top-full mt-2 z-50",
            "w-80 max-h-96 overflow-y-auto",
            "rounded-lg shadow-lg",
            "bg-lia-bg-primary border border-lia-border-primary",
          )}
        >
          <div className="p-3 border-b border-lia-border-primary flex items-center justify-between">
            <div className="font-semibold text-lia-text-primary text-sm">
              Sugestoes da LIA
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Fechar"
              className="text-lia-text-tertiary hover:text-lia-text-primary"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {hints.length === 0 ? (
            <div className="p-6 text-center text-sm text-lia-text-tertiary">
              Tudo em ordem. Nenhuma sugestao no momento.
            </div>
          ) : (
            <ul className="divide-y divide-lia-border-primary">
              {hints.map((hint) => (
                <li
                  key={hint.id}
                  className="p-3 hover:bg-lia-bg-secondary cursor-pointer"
                  onClick={() => handleHintClick(hint)}
                  data-testid={`proactive-hint-item-${hint.detector}`}
                >
                  <div className="flex items-start gap-2">
                    <span
                      className={cn(
                        "mt-1 h-2 w-2 rounded-full shrink-0",
                        SEVERITY_DOT[hint.severity],
                      )}
                      aria-hidden
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <div className="font-medium text-sm text-lia-text-primary truncate">
                          {hint.title}
                        </div>
                        {hint.severity === "critical" && (
                          <AlertCircle className="h-3 w-3 text-status-error" />
                        )}
                      </div>
                      <p className="text-xs text-lia-text-secondary mt-1 line-clamp-2">
                        {hint.message}
                      </p>
                      <div className="mt-2 flex items-center gap-2">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-[10px] font-medium",
                            SEVERITY_STYLES[hint.severity],
                          )}
                        >
                          {hint.severity}
                        </span>
                        <button
                          type="button"
                          onClick={(event) => handleDismiss(event, hint.id)}
                          className="text-[11px] text-lia-text-tertiary hover:text-lia-text-primary underline"
                          data-testid={`proactive-hint-dismiss-${hint.id}`}
                        >
                          Dispensar
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

export default ProactiveHintsBadge
