/**
 * Onda 4 Agent E (2026-05-29) — VALID_TRIGGER_MODES_BY_TARGET canonical TS.
 *
 * Single source of truth no frontend para a matriz target_type × trigger_mode.
 * Espelha `VALID_TRIGGER_MODES_BY_TARGET` em
 * lia-agent-system/app/shared/trigger_mode_validation.py.
 *
 * Sensor schema-sync: scripts/check_trigger_modes_ts_sync.py garante que esta
 * tabela TS bate com o Python canonical. Adicionar um trigger_mode novo exige
 * commit nos DOIS lados.
 *
 * Compatibilidade: o tipo `TriggerMode` continua em
 * `@/types/agents/job-agent` (mantido por backward-compat com hooks/types já
 * importando de lá). Os arrays aqui são derivados dessa fonte.
 */
import type { DeploymentTargetType } from "@/types/agents/agent-deployment"
import type { TriggerMode } from "@/types/agents/job-agent"

export const VALID_TRIGGER_MODES_BY_TARGET = {
  talent_pool: ["on_create", "on_schedule", "manual"],
  job: ["on_create", "on_schedule", "manual", "on_apply"],
  pipeline_stage: [
    "on_enter_stage",
    "on_exit_stage",
    "on_stuck_in_stage",
    "on_stage_change",
  ],
  candidate_list: ["on_schedule", "manual"],
} as const satisfies Record<DeploymentTargetType, readonly TriggerMode[]>

/**
 * Helper: retorna trigger modes válidos para um target_type.
 * Tipo retornado é o union exato (tooling consegue inferir branches).
 */
export function getValidTriggerModes(
  targetType: DeploymentTargetType,
): readonly TriggerMode[] {
  return VALID_TRIGGER_MODES_BY_TARGET[targetType]
}

/**
 * Helper: trigger_mode default canonical por target_type.
 *
 * - talent_pool / job → "manual" (mais conservador, user explicita execução)
 * - pipeline_stage → "on_enter_stage" (event-driven natural pra stage)
 * - candidate_list → "manual"
 */
export function getDefaultTriggerMode(
  targetType: DeploymentTargetType,
): TriggerMode {
  if (targetType === "pipeline_stage") return "on_enter_stage"
  return "manual"
}

/**
 * Helper: trigger_mode é cron-compatível (precisa de schedule_cron picker)?
 */
export function isScheduleTrigger(mode: TriggerMode | string): boolean {
  return mode === "on_schedule"
}
