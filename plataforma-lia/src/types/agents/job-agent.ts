// Onda 3 F3/F4 (2026-05-28) — types canonical para deployments com joined agent.
// Mirror de `AgentDeploymentWithAgent` em
// lia-agent-system/app/schemas/agent_deployment.py.

import type {
  DeploymentTargetType,
} from "@/types/agents/agent-deployment"

/**
 * Trigger modes canonical per target_type.
 *
 * Backend enforça via `VALID_TRIGGER_MODES_BY_TARGET` em
 * lia-agent-system/app/shared/trigger_mode_validation.py.
 */
export const TRIGGER_MODES_BY_TARGET = {
  talent_pool: ["on_create", "on_schedule", "manual"],
  job: ["on_create", "on_schedule", "manual", "on_apply"],
  pipeline_stage: [
    "on_enter_stage",
    "on_exit_stage",
    "on_stuck_in_stage",
    "on_stage_change",
  ],
  candidate_list: ["on_schedule", "manual"],
} as const

export type TriggerMode =
  | "on_create"
  | "on_schedule"
  | "manual"
  | "on_apply"
  | "on_enter_stage"
  | "on_exit_stage"
  | "on_stuck_in_stage"
  | "on_stage_change"

export interface JobAgentDeployment {
  id: string
  agent_id: string
  company_id: string
  target_type: string
  target_id: string
  target_name: string | null
  trigger_mode: string
  schedule_cron: string | null
  is_active: boolean
  config_overrides: Record<string, unknown>
  execution_count: number
  candidates_processed: number
  last_execution_at: string | null
  last_execution_id: string | null
  created_by: string
  created_at: string | null
  updated_at: string | null
  agent_name: string | null
  agent_category: string | null
  agent_status: string | null
  agent_domain: string | null
  // Forward-compat.
  [extra: string]: unknown
}

export interface JobAgentListResponse {
  deployments: JobAgentDeployment[]
  total: number
}

export interface AttachJobAgentRequest {
  agent_id: string
  trigger_mode: TriggerMode
  schedule_cron?: string | null
  is_active?: boolean
  config_overrides?: Record<string, unknown>
}

export type { DeploymentTargetType }
