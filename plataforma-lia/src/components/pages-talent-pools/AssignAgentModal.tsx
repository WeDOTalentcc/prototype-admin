"use client"

/**
 * Sprint 7B-2 → Onda 4 Agent E (2026-05-29) — wrapper thin sobre AssignAgentModal.
 *
 * Refatorado em Onda 4 Agent E (Rule of Three): a logica antes inline aqui
 * (~230 LOC: category filter + cards clicaveis + schedule_type radio) virou
 * generic em src/components/shared/agents/AssignAgentModal.tsx, alinhada com
 * canonical job/stage modals.
 *
 * MIGRATION NOTE — divergencias absorvidas no refactor:
 *   - Category filter chips: removido (consumer pode adicionar pre-filter no
 *     parent se necessario; canonical agent list ja e curta).
 *   - Render cards clicaveis -> select dropdown: alinhamento canonical com
 *     job/stage modal. UX leve diferente mas funcionalmente equivalente.
 *   - Schedule_type "on_demand|cron|event_driven" -> trigger_mode canonical
 *     "manual|on_schedule|on_create": mapeamento abaixo. Backend pool aceita
 *     trigger_mode legacy via LEGACY_TRIGGER_MODES; mapeamos pra valores
 *     canonical pra UX consistente.
 *
 * Backward-compat API publica:
 *   (poolId, open, initialCategory?, onClose, onAssigned) — initialCategory
 *   agora e parametro no-op aceito pra nao quebrar callers existentes.
 */
import React from "react"
import { assignAgentToPool } from "@/hooks/talent-pools/use-pool-agents"
import {
  AssignAgentModal as AssignAgentModalGeneric,
  type AssignAgentPayload,
} from "@/components/shared/agents/AssignAgentModal"
import type { ScheduleType } from "@/types/pool-agent-assignment"

interface AssignAgentModalProps {
  poolId: string
  open: boolean
  /**
   * @deprecated Onda 4 Agent E: category filter removido no refactor. Aceito
   * por backward-compat com callers existentes; sera ignorado.
   */
  initialCategory?: string
  onClose: () => void
  onAssigned: () => void
}

function triggerModeToScheduleType(mode: string): ScheduleType {
  if (mode === "on_schedule") return "cron"
  if (mode === "on_create") return "event_driven"
  return "on_demand"
}

export function AssignAgentModal({
  poolId,
  open,
  onClose,
  onAssigned,
}: AssignAgentModalProps) {
  const handleSubmit = async (payload: AssignAgentPayload) => {
    const scheduleType = triggerModeToScheduleType(payload.trigger_mode)
    const scheduleConfig: Record<string, unknown> =
      scheduleType === "cron" && payload.schedule_cron
        ? { cron: payload.schedule_cron }
        : {}
    await assignAgentToPool(poolId, {
      custom_agent_id: payload.agent_id,
      schedule_type: scheduleType,
      schedule_config: scheduleConfig,
    })
  }

  return (
    <AssignAgentModalGeneric
      open={open}
      onClose={onClose}
      targetType="talent_pool"
      targetId={poolId}
      onSubmit={handleSubmit}
      onAssigned={onAssigned}
      testIdPrefix="assign-agent-to-pool"
    />
  )
}
