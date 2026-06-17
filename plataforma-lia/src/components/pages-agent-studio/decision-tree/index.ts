// Onda 1 F5 (2026-05-27) — Studio Control Room canonical barrel.
//
// Exports estáveis pra Ondas 2-3 consumirem. Mudar API aqui DEVE bumpar
// a baseline do sensor check_decision_tree_drawer_uses_canonical_props.py.
export { DecisionTreeDrawer } from "./DecisionTreeDrawer"
export type { DecisionTreeDrawerProps } from "./DecisionTreeDrawer"
export { useExecutionReasoning, DECISION_TREE_QUERY_KEY } from "./use-execution-reasoning"
export { buildLgpdTrailCsv, downloadLgpdTrailCsv } from "./lgpd-csv"
export type {
  AgentReasoningStep,
  AgentReasoningStepType,
  ExecutionReasoningResponse,
  ActiveExecution,
  RecentExecution,
} from "./types"
