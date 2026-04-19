"use client"

/**
 * ProactiveHintsList — Render proactive suggestions from LIA's PreConditionChecker.
 *
 * Shown inline in chat when the backend message contains `proactive_hints`:
 *   message.data.proactive_hints = [
 *     { type, message, severity, action, metadata }
 *   ]
 *
 * UX (E.2):
 *   - Click action button → dispatches `lia:proactive-action` event
 *     (handled by useProactiveActionRouter — click = authorization, no dialog)
 *   - Click X button → dismiss card locally + persist in sessionStorage
 *     so same hint type does not reappear in next turn.
 */

import React, { useCallback, useEffect, useState } from "react"
import { AlertTriangle, Info, AlertCircle, ArrowRight, Sparkles, X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ProactiveHint {
  type: string
  message: string
  severity: "info" | "warning" | "critical"
  action?: string | null
  metadata?: Record<string, unknown>
}

interface Props {
  hints: ProactiveHint[]
  className?: string
}

const ICONS: Record<ProactiveHint["severity"], React.ReactNode> = {
  info: <Info className="w-4 h-4 text-lia-text-secondary" />,
  warning: <AlertTriangle className="w-4 h-4 text-status-warning" />,
  critical: <AlertCircle className="w-4 h-4 text-status-danger" />,
}

const SEVERITY_STYLES: Record<ProactiveHint["severity"], string> = {
  info: "border-lia-border-subtle bg-lia-bg-secondary",
  warning: "border-status-warning/30 bg-status-warning/10",
  critical: "border-status-danger/30 bg-status-danger/10",
}

const ACTION_LABELS: Record<string, string> = {
  navigate_to_settings: "Abrir Configurações",
  request_website_and_scrape: "Informar site",
  culture_onboarding: "Começar onboarding",
  import_benefits: "Importar benefícios",
  suggest_recruiting_policy: "Sugerir política",
  batch_enrich_contacts: "Enriquecer em lote",
  suggest_screening_questions: "Sugerir perguntas",
}

const DISMISS_STORAGE_KEY = "lia:dismissed_hint_types"

function getDismissedTypes(): Set<string> {
  if (typeof window === "undefined") return new Set()
  try {
    const raw = window.sessionStorage.getItem(DISMISS_STORAGE_KEY)
    if (!raw) return new Set()
    const parsed = JSON.parse(raw)
    return new Set(Array.isArray(parsed) ? parsed : [])
  } catch {
    return new Set()
  }
}

function persistDismissed(types: Set<string>): void {
  if (typeof window === "undefined") return
  try {
    window.sessionStorage.setItem(DISMISS_STORAGE_KEY, JSON.stringify(Array.from(types)))
  } catch {
    // sessionStorage may be blocked (private mode); fail silently
  }
}

function handleAction(hint: ProactiveHint) {
  window.dispatchEvent(
    new CustomEvent("lia:proactive-action", {
      detail: {
        type: hint.type,
        action: hint.action,
        metadata: hint.metadata || {},
      },
    }),
  )
}

export function ProactiveHintsList({ hints, className }: Props) {
  const [dismissedTypes, setDismissedTypes] = useState<Set<string>>(() => getDismissedTypes())

  // Re-read sessionStorage when the component mounts (cross-tab sync not required)
  useEffect(() => {
    setDismissedTypes(getDismissedTypes())
  }, [])

  const dismiss = useCallback((type: string) => {
    setDismissedTypes((prev) => {
      const next = new Set(prev)
      next.add(type)
      persistDismissed(next)
      return next
    })
  }, [])

  const visibleHints = hints.filter((h) => !dismissedTypes.has(h.type))
  if (!visibleHints || visibleHints.length === 0) return null

  return (
    <div className={cn("flex flex-col gap-2 mt-3", className)}>
      {visibleHints.map((hint, idx) => {
        const actionLabel = hint.action ? ACTION_LABELS[hint.action] : null
        return (
          <div
            key={`${hint.type}-${idx}`}
            className={cn(
              "relative rounded-md border px-3 py-2.5 pr-8",
              "flex items-start gap-2.5",
              SEVERITY_STYLES[hint.severity] ?? SEVERITY_STYLES.info,
            )}
          >
            <button
              type="button"
              onClick={() => dismiss(hint.type)}
              aria-label="Dispensar sugestão"
              className={cn(
                "absolute top-1.5 right-1.5 p-1 rounded-md",
                "text-lia-text-tertiary hover:text-lia-text-secondary",
                "hover:bg-black/5 dark:hover:bg-white/5",
                "transition-colors motion-reduce:transition-none",
              )}
            >
              <X className="w-3 h-3" />
            </button>
            <Sparkles className="w-3.5 h-3.5 text-wedo-cyan mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-2">
                {ICONS[hint.severity] ?? ICONS.info}
                <p className="text-xs text-lia-text-primary leading-relaxed flex-1">
                  {hint.message}
                </p>
              </div>
              {hint.action && actionLabel && (
                <button
                  type="button"
                  onClick={() => handleAction(hint)}
                  className={cn(
                    "mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md",
                    "text-xs font-medium text-wedo-cyan",
                    "border border-wedo-cyan/30 bg-wedo-cyan/5",
                    "hover:bg-wedo-cyan/10 transition-colors motion-reduce:transition-none",
                  )}
                >
                  <span>{actionLabel}</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
