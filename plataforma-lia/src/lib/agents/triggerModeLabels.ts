// Onda 3 F8 (2026-05-28) — single source of truth canonical para labels de
// trigger mode na UI. Sensor `check_trigger_mode_label_canonical.py` verifica
// que componentes que renderizam trigger modes passam pelo helper i18n,
// NÃO hardcoded em PT-BR.
//
// Convention: i18n key paths
//   - job: jobs.agents.triggerMode.{mode}
//   - pipeline_stage: pipeline.stage.triggerMode.{mode}
//   - talent_pool / candidate_list: reuse jobs.agents.triggerMode.{mode} for now
//
// Backend canonical: `VALID_TRIGGER_MODES_BY_TARGET` em
// lia-agent-system/app/shared/trigger_mode_validation.py.

import type { TriggerMode } from "@/types/agents/job-agent"
import type { DeploymentTargetType } from "@/types/agents/agent-deployment"

type Translator = (key: string) => string

/**
 * Returns the i18n key (without leading namespace) for a trigger mode in a
 * given target_type context. Use with `useTranslations(<ns>)` to render.
 */
export function getTriggerModeI18nKey(
  mode: TriggerMode | string,
  targetType: DeploymentTargetType,
): string {
  if (targetType === "pipeline_stage") {
    return `pipeline.stage.triggerMode.${mode}`
  }
  // job / talent_pool / candidate_list share the same i18n bundle
  return `jobs.agents.triggerMode.${mode}`
}

/**
 * Resolves a translated label using two translators (root-level).
 * Falls back to the raw mode string if no translator wires it.
 */
export function resolveTriggerModeLabel(
  mode: TriggerMode | string,
  targetType: DeploymentTargetType,
  tRoot: Translator,
): string {
  const key = getTriggerModeI18nKey(mode, targetType)
  try {
    const value = tRoot(key)
    return value && value !== key ? value : mode
  } catch {
    return mode
  }
}
