// Local types for CandidateSearchResultsView
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { CalibrationCandidate } from "@/components/calibration-card"

export type SearchTab = 'ia-natural' | 'boolean' | 'filters' | 'archetypes'

export type ChatMessage = {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

export type TableColumn = {
  id: string
  label: string
  visible: boolean
  order: number
  width?: number
  minWidth?: number
  category?: string
  sortable?: boolean
  isGlobalSearch?: boolean
}
