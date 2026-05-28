"use client"

// Onda 2 F3 (2026-05-27) — banner global "N agentes trabalhando agora".
//
// Aparece no topo do Decidir (acima do TasksMetricsBar) quando há ≥1
// agent rodando agora. Discreto + estático (sem pulse — pulse é exclusivo
// do Funil F7). Link "Ver na Sala de Controle" navega ao Studio.
//
// CTA secundário — não compete com pingos nem com AgentsCard. Confirma o
// estado em uma palavra ("trabalhando") e oferece zoom-out.

import React from "react"
import Link from "next/link"
import { Brain } from "lucide-react"
import { useActiveAgentsSummary } from "@/hooks/agents/use-active-agents-summary"

const COPY = {
  countMessage: (n: number) =>
    n === 1
      ? "1 agente trabalhando agora"
      : `${n} agentes trabalhando agora`,
  controlRoomLink: "Ver na Sala de Controle",
} as const

export function AgentRunningBanner() {
  // Reusa a mesma query key do AgentsCard (surface=decidir, limit=5).
  // React Query dedupa: 1 fetch para os dois consumers.
  const { data } = useActiveAgentsSummary({
    surface: "decidir",
    limit: 5,
  })
  const running = data?.running_count ?? 0
  if (running === 0) return null

  return (
    <div
      className="flex items-center gap-2 px-3 py-2 mb-3 bg-wedo-cyan/10 border border-wedo-cyan/30 rounded-lg text-sm"
      role="status"
      aria-live="polite"
    >
      <Brain className="w-4 h-4 text-wedo-cyan" aria-hidden="true" />
      <span className="text-wedo-cyan-dark dark:text-wedo-cyan font-medium">
        {COPY.countMessage(running)}
      </span>
      <Link
        href="/agent-studio?tab=control-room"
        className="ml-auto text-wedo-cyan-dark dark:text-wedo-cyan hover:underline"
      >
        {COPY.controlRoomLink} →
      </Link>
    </div>
  )
}
