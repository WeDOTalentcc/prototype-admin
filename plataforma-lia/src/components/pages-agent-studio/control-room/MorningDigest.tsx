// Onda C4.2 (2026-05-29) — Morning Brief / Daily Digest no topo da Sala de
// Controle. "O que aconteceu enquanto você não estava."
//
// Curado por relevância pelo backend (errors > pending > celebrations >
// surfaced > info). Cada item clicável: com execution_id abre o
// DecisionTreeDrawer; sem ele (pending_approval) é informativo.
//
// Design /impeccable — The Quiet Operator: acolhedor mas profissional, cyan
// reservada pra IA/celebração, sem ruído visual. aria-live polite.
"use client"

import * as React from "react"
import { useTranslations } from "next-intl"
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  CircleDollarSign,
  Sparkles,
  Sun,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import { useDailyDigest } from "@/hooks/agents/use-daily-digest"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import type { DigestItem, DigestKind, DigestSeverity } from "@/types/agents/daily-digest"

interface MorningDigestProps {
  /** Abre o DecisionTreeDrawer pra um execution_id (mesmo callback do Live). */
  onOpenReasoning: (executionId: string) => void
}

/** Saudação por hora local — chave i18n (sem string hardcoded). */
function greetingKey(): "morning" | "afternoon" | "evening" {
  const hour = new Date().getHours()
  if (hour < 12) return "morning"
  if (hour < 18) return "afternoon"
  return "evening"
}

const KIND_ICON: Record<DigestKind, React.ComponentType<{ className?: string }>> = {
  agent_error: AlertTriangle,
  pending_approval: Bell,
  decision_approved: CheckCircle2,
  candidates_surfaced: Sparkles,
  high_cost: CircleDollarSign,
}

// Cor por severity. celebration = cyan da IA; attention = amber; info = neutro.
const SEVERITY_ICON_CLASS: Record<DigestSeverity, string> = {
  celebration: "text-lia-cyan",
  attention: "text-amber-500 dark:text-amber-400",
  info: "text-lia-text-tertiary",
}

interface DigestRowProps {
  item: DigestItem
  displaySummary: string
  onOpenReasoning: (executionId: string) => void
}

function DigestRow({ item, displaySummary, onOpenReasoning }: DigestRowProps) {
  const Icon = KIND_ICON[item.kind]
  const clickable = item.execution_id !== null
  const iconClass = SEVERITY_ICON_CLASS[item.severity]

  const content = (
    <>
      <Icon className={cn("h-4 w-4 shrink-0", iconClass)} aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate text-sm text-lia-text-primary">
        {displaySummary}
      </span>
    </>
  )

  if (clickable) {
    return (
      <li>
        <button
          type="button"
          onClick={() => onOpenReasoning(item.execution_id as string)}
          className="flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-lia-bg-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-cyan"
          data-testid={`digest-item-${item.kind}`}
        >
          {content}
        </button>
      </li>
    )
  }

  return (
    <li
      className="flex w-full items-center gap-2.5 rounded-md px-2 py-1.5"
      data-testid={`digest-item-${item.kind}`}
    >
      {content}
    </li>
  )
}

export function MorningDigest({ onOpenReasoning }: MorningDigestProps) {
  const t = useTranslations("agents.studio.dailyDigest")
  const { persona } = useAiPersona()
  const { data, isLoading, isError } = useDailyDigest()

  if (isLoading) {
    return (
      <section
        className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-4"
        data-testid="morning-digest-loading"
        aria-busy="true"
      >
        <Skeleton className="mb-3 h-5 w-56" />
        <Skeleton className="mb-2 h-7 w-full" />
        <Skeleton className="h-7 w-3/4" />
      </section>
    )
  }

  // Falha de carga não derruba a Sala de Controle: omitimos o digest.
  if (isError || !data) {
    return null
  }

  const greeting = t(`greeting.${greetingKey()}`)
  const items = data.items ?? []

  return (
    <section
      className="rounded-md border border-lia-border-subtle bg-lia-bg-elevated p-4"
      aria-labelledby="morning-digest-heading"
      data-testid="morning-digest"
    >
      <div className="mb-3 flex items-center gap-2">
        <Sun className="h-4 w-4 text-lia-cyan" aria-hidden="true" />
        <h3
          id="morning-digest-heading"
          className="text-sm font-semibold text-lia-text-primary"
        >
          {greeting}
        </h3>
        <span className="text-xs text-lia-text-tertiary">— {t("subtitle")}</span>
      </div>

      {items.length === 0 ? (
        <div
          className="rounded-md border border-dashed border-lia-border-subtle px-4 py-6 text-center"
          data-testid="morning-digest-empty"
        >
          <p className="text-sm text-lia-text-secondary">{t("empty")}</p>
        </div>
      ) : (
        <ul
          className="space-y-0.5"
          aria-live="polite"
          aria-relevant="additions text"
          data-testid="morning-digest-list"
        >
          {items.map((item, idx) => (
            <DigestRow
              key={item.execution_id ?? `${item.kind}-${item.agent_id}-${idx}`}
              item={item}
              // White-label canonical: nome do agente passa por useAiPersona
              // quando o backend não trouxe um nome próprio.
              displaySummary={
                item.agent_name
                  ? item.summary
                  : item.summary.replace(
                      /^Agente/,
                      persona?.name ?? "Agente",
                    )
              }
              onOpenReasoning={onOpenReasoning}
            />
          ))}
        </ul>
      )}

      <p
        className="mt-3 border-t border-lia-border-subtle pt-2.5 text-xs text-lia-text-tertiary"
        data-testid="morning-digest-footer"
      >
        {t("footer", {
          runs: data.total_runs,
          candidates: data.total_candidates_processed,
          hours: data.period_hours,
        })}
      </p>
    </section>
  )
}
