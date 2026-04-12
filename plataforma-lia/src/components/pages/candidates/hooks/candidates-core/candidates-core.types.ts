// candidates-core.types.ts
// All TypeScript interfaces and types for the candidates page core hook.
// Pure types — no Next.js or React runtime dependencies.

import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { CalibrationCandidate } from "@/components/calibration-card"
import type { JobVacancy, EmailTemplate } from "@/services/lia-api"

/** Source of candidate data for a search run */
export type SearchSource = 'local' | 'global' | 'hybrid'

/** Props accepted by the page core hook */
export interface CandidatesPageCoreProps {
  onAddRecentItem?: (item: {
    id: string
    type: 'vaga' | 'chat' | 'candidato'
    title: string
    subtitle?: string
    meta?: Record<string, string | undefined>
  }) => void
  pendingCandidateOpen?: { candidateId: string; candidateName: string } | null
  onCandidateOpened?: () => void
}

/** A single message in the LIA chat thread */
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

/** Pearch (global) search tuning options */
export interface PearchSearchOptions {
  searchType: 'fast'
  limit: number
  showEmails: boolean
  showPhoneNumbers: boolean
  highFreshness: boolean
  requireEmails: boolean
  requirePhoneNumbers: boolean
}
