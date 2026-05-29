export { useCustomAgents, useAgentDeployments } from "./use-custom-agents"
export { usePendingApprovals } from "./use-approvals"
export { useStudioChatIntents } from "./use-studio-chat-intents"
export { useAgentVersions } from "./use-agent-versions"
export { useWebhooks } from "./use-webhooks"
export { useAgentActivities } from "./use-agent-activities"
// Onda 2 F1 (2026-05-27) — Studio surface presence hooks.
export {
  useActiveAgentsSummary,
  ACTIVE_AGENTS_SUMMARY_QUERY_KEY,
} from "./use-active-agents-summary"
export {
  useTargetDeployments,
  TARGET_DEPLOYMENTS_QUERY_KEY,
} from "./use-target-deployments"
export {
  useCandidateTouches,
  CANDIDATE_TOUCHES_QUERY_KEY,
} from "./use-candidate-touches"
// Onda 3 F1 (2026-05-28) — batch deployments lookup (elimina N+1 da Onda 2).
export {
  useDeploymentsByTargets,
  DEPLOYMENTS_BY_TARGETS_QUERY_KEY,
} from "./use-deployments-by-targets"
// CF-B B7 (2026-05-29) — PATCH de agent-deployment (pause/resume canonical).
export {
  useUpdateDeployment,
  type UpdateDeploymentVars,
} from "./use-update-deployment"
