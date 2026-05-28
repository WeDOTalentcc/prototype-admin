// Onda 4 F6.3 (2026-05-28) — tooltip contextual de primeira execução.
//
// Quando agente acabou de processar candidatos pela primeira vez (is_learning
// ou total_executions <= 1), mostrar dica única que se autodismiss + persiste
// em localStorage.
//
// localStorage flag: studio_first_execution_seen
//
// Reuso: AgentsCard (Decidir), LiveAgentsList (Sala de Controle).
"use client"

import { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

const STORAGE_KEY = "studio_first_execution_seen"

interface FirstExecutionTooltipProps {
  agentName: string
  className?: string
  /** Override storage key (testing). */
  storageKey?: string
}

export function FirstExecutionTooltip({
  agentName,
  className,
  storageKey = STORAGE_KEY,
}: FirstExecutionTooltipProps) {
  const t = useTranslations("agents.firstExecution")
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (typeof window === "undefined") return
    try {
      const seen = window.localStorage.getItem(storageKey)
      if (!seen) setVisible(true)
    } catch {
      // SSR or storage disabled — fallback to hidden
    }
  }, [storageKey])

  function handleDismiss() {
    setVisible(false)
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(storageKey, "1")
      } catch {
        /* noop */
      }
    }
  }

  if (!visible) return null

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="first-execution-tooltip"
      className={cn(
        "flex items-start gap-2 rounded-md border border-wedo-cyan/30 bg-wedo-cyan/10 p-3 text-xs",
        className,
      )}
    >
      <span aria-hidden="true" className="text-base leading-none">
        🩵
      </span>
      <p className="flex-1 text-lia-text-primary">
        {t("tooltip", { agentName })}
      </p>
      <button
        type="button"
        onClick={handleDismiss}
        aria-label={t("dismiss")}
        className="flex-shrink-0 rounded p-0.5 text-lia-text-tertiary hover:bg-wedo-cyan/15 hover:text-lia-text-primary transition-colors"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
