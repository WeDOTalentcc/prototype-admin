"use client"

// Onda 2 F4/F5 (2026-05-27) — pingo cyan estático para vagas com agentes acoplados.
// Onda 3 F2 (2026-05-28) — agora aceita `deployments` prop direta (skip fetch)
// para integração com batch endpoint `useDeploymentsByTargets`. O parent
// (ex: ActiveJobsCard) faz 1 fetch agregado e passa o slice pra cada card.
//
// Visual: 6px dot cyan estático. Tooltip "{n} agentes acoplados". Sem
// pulse — pulse é exclusivo do Funil (F7). Tooltip aparece sempre via
// title attribute (acessível por hover/touch/screen reader).

import React from "react"
import { useTranslations } from "next-intl"
import { useTargetDeployments } from "@/hooks/agents/use-target-deployments"
import type {
  AgentDeployment,
  DeploymentTargetType,
} from "@/types/agents/agent-deployment"

interface JobAgentDotProps {
  /** UUID da vaga (job_vacancy.id) ou null pra ocultar (sem fetch). */
  targetId: string | null
  /** Default 'job'. Aceita 'talent_pool' / 'pipeline_stage' para reuso. */
  targetType?: DeploymentTargetType
  /**
   * Onda 3 F2 — quando fornecido, NÃO faz fetch individual. Usa esses
   * deployments diretamente (parent já fez batch fetch). Quando undefined,
   * cai no fetch per-target legacy (Onda 2 behavior).
   */
  deployments?: AgentDeployment[]
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
  deployments: deploymentsProp,
  tooltip,
  size = "sm",
  hidden = false,
  ariaLabel,
}: JobAgentDotProps) {
  // Rules of Hooks discipline: hooks no topo, antes de qualquer early return.
  const t = useTranslations("agents.summary")
  // Onda 3 F2 — quando parent já provê deployments via batch, skip fetch.
  // Hook is always called (Rules of Hooks discipline) mas com enabled=false
  // quando deploymentsProp é fornecido.
  const { data } = useTargetDeployments({
    targetType,
    targetId,
    enabled: deploymentsProp === undefined,
  })

  const deployments =
    deploymentsProp ?? (data?.deployments as AgentDeployment[] | undefined) ?? []
  if (hidden || deployments.length === 0) return null

  const activeCount = deployments.filter((d) => d.is_active !== false).length
  if (activeCount === 0) return null

  const resolvedTooltip =
    tooltip ?? t("jobDot.tooltip", { count: activeCount })

  return (
    <span
      className={`inline-block ${SIZE_CLASS[size]} rounded-full bg-wedo-cyan flex-shrink-0`}
      title={resolvedTooltip}
      aria-label={ariaLabel ?? resolvedTooltip}
      role="img"
    />
  )
}
