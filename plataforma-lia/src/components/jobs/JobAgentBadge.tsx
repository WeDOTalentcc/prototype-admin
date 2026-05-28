"use client"

// Onda 2 F5 (2026-05-27) — badge cyan clicavel no header da vaga.
//
// Mostra "N agentes ativos" no KanbanJobHeader quando há agent_deployments
// com target_type=job e target_id={jobId}. Click navega para o Studio com
// filter pre-aplicado (Onda 3 — hoje navega para /agent-studio).
//
// CLAUDE.md REGRAS aplicadas:
//   - REGRA 1 settings/: server data via useQuery (useTargetDeployments)
//   - Design tokens: wedo-cyan canonical, sem hex
//   - prefers-reduced-motion: hover transitions desabilitadas
//
// SENSOR-EXEMPT: 1 fetch por mount (KanbanJobHeader nao remonta com freq).

import React from "react"
import Link from "next/link"
import { Brain } from "lucide-react"
import { useTargetDeployments } from "@/hooks/agents/use-target-deployments"

interface JobAgentBadgeProps {
  jobId: string | undefined
}

export function JobAgentBadge({ jobId }: JobAgentBadgeProps) {
  const { data } = useTargetDeployments({
    targetType: "job",
    targetId: jobId ?? null,
  })
  const deployments = data?.deployments ?? []
  const activeCount = deployments.filter((d) => d.is_active !== false).length
  if (activeCount === 0 || !jobId) return null

  const label =
    activeCount === 1 ? "1 agente ativo" : `${activeCount} agentes ativos`
  return (
    <Link
      href={`/agent-studio?target_type=job&target_id=${encodeURIComponent(jobId)}`}
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xl border border-wedo-cyan/40 bg-wedo-cyan/10 text-wedo-cyan-dark dark:text-wedo-cyan text-xs font-medium hover:bg-wedo-cyan/20 transition-colors motion-reduce:transition-none cursor-pointer"
      title={label}
      aria-label={label}
    >
      <span
        className="w-1.5 h-1.5 rounded-full bg-wedo-cyan"
        aria-hidden="true"
      />
      <Brain className="w-3 h-3" aria-hidden="true" />
      <span>{label}</span>
    </Link>
  )
}
