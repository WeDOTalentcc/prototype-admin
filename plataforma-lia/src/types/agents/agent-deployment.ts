// Onda 2 F1 (2026-05-27) — types canonical do endpoint
// GET /agent-deployments?target_type&target_id.
// Schema espelha `DeploymentResponse` em
// lia-agent-system/app/api/v1/agent_deployments.py.

export type DeploymentTargetType =
  | "job"
  | "talent_pool"
  | "pipeline_stage"
  | "candidate_list"

export interface AgentDeployment {
  id: string
  agent_id: string
  target_type: DeploymentTargetType | string
  target_id: string
  target_name: string | null
  is_active: boolean
  created_at: string | null
  updated_at: string | null
  // Forward-compat: campos adicionais aceitos sem quebrar.
  [extra: string]: unknown
}

export interface DeploymentListResponse {
  deployments: AgentDeployment[]
  total: number
}
