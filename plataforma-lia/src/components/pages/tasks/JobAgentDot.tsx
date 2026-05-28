"use client"

// Onda 2 F4/F5 (2026-05-27) — pingo cyan estático para vagas com agentes acoplados.
//
// SENSOR-EXEMPT: N+1 batch endpoint pendente (Onda 3).
// Hoje cada JobListItem chama useTargetDeployments(jobId). Em lista de 30+
// vagas isso vira 30+ requests. Mitigado por staleTime=60s do hook (cache
// dedupa entre re-renders da mesma sessão). Endpoint batch
// /agent-deployments/by-targets?ids=... fica pra Onda 3.
//
// Visual: 6px dot cyan estático. Tooltip "{n} agentes acoplados". Sem
// pulse — pulse é exclusivo do Funil (F7). Tooltip aparece sempre via
// title attribute (acessível por hover/touch/screen reader).

import React from "react"
import { useTargetDeployments } from "@/hooks/agents/use-target-deployments"
import type { DeploymentTargetType } from "@/types/agents/agent-deployment"

interface JobAgentDotProps {
  /** UUID da vaga (job_vacancy.id) ou null pra ocultar (sem fetch). */
  targetId: string | null
  /** Default 'job'. Aceita 'talent_pool' / 'pipeline_stage' para reuso. */
  targetType?: DeploymentTargetType
  /** Override do tooltip. Quando ausente, gera "N agentes acoplados". */
  tooltip?: string
  /** Tamanho do dot. Default 6px (1.5 em Tailwind). */
  size?: "xs" | "sm"
  /** Quando true, oculta o dot mesmo com deployments (e.g., feature flag). */
  hidden?: boolean
  /** A11y override do aria-label. */
  ariaLabel?: string
}

const SIZE_CLASS = {
  xs: "w-1 h-1",
  sm: "w-1.5 h-1.5",
} as const

export function JobAgentDot({
  targetId,
  targetType = "job",
  tooltip,
  size = "sm",
  hidden = false,
  ariaLabel,
}: JobAgentDotProps) {
  const { data } = useTargetDeployments({ targetType, targetId })
  const deployments = data?.deployments ?? []
  if (hidden || deployments.length === 0) return null

  const activeCount = deployments.filter((d) => d.is_active !== false).length
  if (activeCount === 0) return null

  const resolvedTooltip =
    tooltip ??
    (activeCount === 1
      ? "1 agente acoplado"
      : `${activeCount} agentes acoplados`)

  return (
    <span
      className={`inline-block ${SIZE_CLASS[size]} rounded-full bg-wedo-cyan flex-shrink-0`}
      title={resolvedTooltip}
      aria-label={ariaLabel ?? resolvedTooltip}
      role="img"
    />
  )
}
