"use client"

import * as React from "react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface JobKanbanMiniFunnelProps {
  funnel: {
    total: number
    screening: number
    interview: number
    final: number
    hired: number
  }
  labels: {
    screening: string
    interview: string
    final: string
    hired: string
  }
}

/**
 * Task #562 — Mini funil horizontal exibido no card de vaga.
 *
 * 4 segmentos proporcionais aos contadores (screening, interview, final,
 * hired). Tokens semânticos (`lia-interactive-active`, `wedo-purple`,
 * `wedo-orange`, `status-success`) seguem DS LIA v4.2 (regra 90/10).
 *
 * Princípio canonical-fix: o componente NÃO inventa números. Caller só
 * deve renderizar quando `funnel.total > 0` (mapper já garante isso em
 * `jobToKanbanItem`).
 */
export const JobKanbanMiniFunnel = React.memo(function JobKanbanMiniFunnel({
  funnel,
  labels,
}: JobKanbanMiniFunnelProps) {
  const segments = [
    { key: "screening", value: funnel.screening, label: labels.screening, cls: "bg-lia-interactive-active" },
    { key: "interview", value: funnel.interview, label: labels.interview, cls: "bg-wedo-purple" },
    { key: "final",     value: funnel.final,     label: labels.final,     cls: "bg-wedo-orange" },
    { key: "hired",     value: funnel.hired,     label: labels.hired,     cls: "bg-status-success" },
  ]

  // Soma de segmentos (pode ser < total se houver candidatos não
  // classificados). Normalizamos pelo total para manter coerência visual.
  const denom = funnel.total > 0 ? funnel.total : 1

  return (
    <TooltipProvider delayDuration={200}>
      <div
        className="flex h-1.5 w-full overflow-hidden rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated"
        role="img"
        aria-label={`${labels.screening}: ${funnel.screening}, ${labels.interview}: ${funnel.interview}, ${labels.final}: ${funnel.final}, ${labels.hired}: ${funnel.hired}`}
      >
        {segments.map((seg) => {
          if (seg.value <= 0) return null
          const widthPct = Math.max(2, (seg.value / denom) * 100)
          return (
            <Tooltip key={seg.key}>
              <TooltipTrigger asChild>
                <span
                  className={`${seg.cls} h-full transition-[width] motion-reduce:transition-none`}
                  style={{ width: `${widthPct}%` }}
                  data-testid={`mini-funnel-${seg.key}`}
                />
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                {seg.label}: {seg.value}
              </TooltipContent>
            </Tooltip>
          )
        })}
      </div>
    </TooltipProvider>
  )
})
