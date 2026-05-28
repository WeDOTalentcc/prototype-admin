"use client"

// Onda 2 F8 (2026-05-27) — icone "tocado por agente" em card de candidato.
//
// Consome useCandidateTouches(candidateId, 24h). Backend MVP retorna
// touch_count: 0 hoje — componente so renderiza quando count > 0, contrato
// estavel. Quando agents canonical populam touches reais (Onda 3+), icone
// aparece automaticamente sem mudanca de UI.
//
// CLAUDE.md REGRAS:
//   - REGRA 4 anti-silent-fallback: erro silencioso = nao renderiza (sem
//     fallback string mascarando bug); fonte unica de verdade = backend
//   - Design tokens: wedo-cyan canonical
//   - aria-label rico (nome do agente + tempo relativo) para a11y
//
// SENSOR-EXEMPT: N+1 quando renderizado em kanban com 100 cards.
// Mitigacao 1: hook usa staleTime 5min — cache dedupa entre re-renders.
// Mitigacao 2: backend MVP retorna 0 pra todos (zero custo real).
// Onda 3 obrigatorio: batch endpoint OU gating IntersectionObserver.

import React from "react"
import { Brain } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useCandidateTouches } from "@/hooks/agents/use-candidate-touches"

interface CandidateTouchIndicatorProps {
  candidateId: string | null | undefined
  /** Janela de tempo. Default 24h. */
  sinceHours?: number
  /** Override visual: 'sm' (12px, default) ou 'xs' (10px). */
  size?: "xs" | "sm"
  /** Override tooltip. Quando ausente, gera "Tocado por {agent} {timeAgo}". */
  tooltipOverride?: string
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return ""
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ""
  const diffMs = Date.now() - then
  const minutes = Math.floor(diffMs / 60_000)
  if (minutes < 1) return "agora há pouco"
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `há ${hours}h`
  const days = Math.floor(hours / 24)
  return `há ${days}d`
}

const SIZE_CLASS = {
  xs: "w-2.5 h-2.5",
  sm: "w-3 h-3",
} as const

export function CandidateTouchIndicator({
  candidateId,
  sinceHours = 24,
  size = "sm",
  tooltipOverride,
}: CandidateTouchIndicatorProps) {
  const { data } = useCandidateTouches({
    candidateId: candidateId ?? null,
    sinceHours,
  })
  const touchCount = data?.touch_count ?? 0
  if (touchCount === 0) return null

  const lastTouch = data?.touches?.[0]
  const agentName = lastTouch?.agent_name ?? "Agente"
  const when = formatRelativeTime(data?.last_touch_at ?? null)
  const tooltip =
    tooltipOverride ??
    (when ? `Tocado por ${agentName} ${when}` : `Tocado por ${agentName}`)

  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className="inline-flex items-center justify-center rounded-full bg-wedo-cyan/15 p-0.5"
            role="img"
            aria-label={tooltip}
          >
            <Brain
              className={`${SIZE_CLASS[size]} text-wedo-cyan`}
              aria-hidden="true"
            />
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
