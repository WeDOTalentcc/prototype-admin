// Re-exports from the canonical types file so chat-core consumers
// only need to import from one place.
export type { Message, ContextPanelData, AgentData, AgentActivity } from "../types"

// Additional types that are specific to chat-core sub-hooks

export interface SelectedCandidateForScheduling {
  name: string
  email: string
  id?: string
  job_title: string
  job_vacancy_id?: string
}

export interface PendingPearchSearch {
  query: string
  threadId?: string
}
