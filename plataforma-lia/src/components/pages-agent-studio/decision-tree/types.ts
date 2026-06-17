// Onda 1 F5 (2026-05-27) — Studio Control Room canonical types.
//
// Schema espelha ExecutionReasoningResponse do backend
// (lia-agent-system/app/api/v1/agent_monitoring.py).
//
// AgentReasoningStep espelha lia_agents_core/agent_interface.py:AgentReasoningStep.

export type AgentReasoningStepType = "criterion" | "thought" | "action" | "observation"

export interface AgentReasoningStep {
  step_type: AgentReasoningStepType
  label: string
  score?: number | null
  matched?: boolean | null
  detail?: string | null
  data_fields_accessed: string[]
  // Backend pode incluir timestamp ISO ou outros campos no payload, mas só
  // os campos canonical acima são contratuais.
  timestamp?: string | null
}

export interface ExecutionReasoningResponse {
  execution_id: string
  agent_id: string
  agent_name: string
  started_at: string | null
  completed_at: string | null
  model_used: string | null
  cost_usd: number | null
  latency_ms: number | null
  input_tokens: number | null
  output_tokens: number | null
  reasoning_trace: AgentReasoningStep[]
  data_fields_accessed_summary: string[]
  data_fields_NOT_accessed: string[]
}

export interface ActiveExecution {
  execution_id: string
  agent_id: string
  agent_name: string
  target_type: "talent_pool" | "job" | "pipeline_stage" | "candidate_list" | string
  target_id: string
  target_name: string | null
  status: "running" | "completed" | "error"
  started_at: string
  progress_pct: number | null
  candidates_processed: number | null
  eta_seconds: number | null
}

export interface RecentExecution {
  execution_id: string
  agent_id: string
  agent_name: string
  target_type: string
  target_id: string
  target_name: string | null
  status: "success" | "error" | "timeout" | "cancelled" | "running" | "queued"
  started_at: string | null
  finished_at: string | null
  latency_ms: number | null
  success_summary: string | null
}
