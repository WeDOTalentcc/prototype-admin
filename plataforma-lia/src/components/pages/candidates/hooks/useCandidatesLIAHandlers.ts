"use client"

import React from "react"
import { isConversationalMessage, isGenericQuestion } from "./liaMessageUtils"
import type { Candidate } from "../types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { CalibrationCandidate } from "@/components/calibration-card"

import { useLIAQuickActions } from "./useLIAQuickActions"
import { useLIAChatMessage } from "./useLIAChatMessage"
import { useLIAAICommands } from "./useLIAAICommands"

type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

export interface LIAChatMessage {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
}

interface AppRouter {
  push: (href: string) => void
  replace: (href: string) => void
  back: () => void
  refresh: () => void
}

interface AuthUser {
  id?: string
  email?: string
  company?: string
  name?: string
}

export interface CandidatesLIAHandlersContext {
  candidates: Candidate[]
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  chatMessages: LIAChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<LIAChatMessage[]>>
  liaPromptValue: string
  setLiaPromptValue: React.Dispatch<React.SetStateAction<string>>
  liaWidth: number
  setLiaWidth: React.Dispatch<React.SetStateAction<number>>
  activeSearchTab: SearchTab
  setActiveSearchTab: React.Dispatch<React.SetStateAction<SearchTab>>
  talentConversationId: string | undefined
  setTalentConversationId: React.Dispatch<React.SetStateAction<string | undefined>>
  liaIsParsingEntities: boolean
  setLiaIsParsingEntities: React.Dispatch<React.SetStateAction<boolean>>
  liaSuggestions: string[]
  setLiaSuggestions: React.Dispatch<React.SetStateAction<string[]>>
  showLiaSuggestions: boolean
  setShowLiaSuggestions: React.Dispatch<React.SetStateAction<boolean>>
  showLiaAssistant: boolean
  setShowLiaAssistant: React.Dispatch<React.SetStateAction<boolean>>
  selectedCandidatesForBatch: Set<string>
  searchResults: {
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }
  lastSearchQuery: string
  activeSearchFilters: SearchFilters
  liaPromptEntities: ParsedEntities
  setLiaPromptEntities: React.Dispatch<React.SetStateAction<ParsedEntities>>
  setShowExpandedLIA: React.Dispatch<React.SetStateAction<boolean>>
  userCollapsedLIA: boolean
  setUserCollapsedLIA: React.Dispatch<React.SetStateAction<boolean>>
  selectedCandidateForLIA: Candidate | null
  setSelectedCandidateForLIA: React.Dispatch<React.SetStateAction<Candidate | null>>
  showLIAPromptForCandidate: boolean
  setShowLIAPromptForCandidate: React.Dispatch<React.SetStateAction<boolean>>
  selectedCandidate: Candidate | null
  setSelectedCandidate: React.Dispatch<React.SetStateAction<Candidate | null>>
  showQuickViewModal: boolean
  setShowQuickViewModal: React.Dispatch<React.SetStateAction<boolean>>
  showComparisonModal: boolean
  setShowComparisonModal: React.Dispatch<React.SetStateAction<boolean>>
  setShowScheduleModal: React.Dispatch<React.SetStateAction<boolean>>
  setUnifiedModalCandidate: React.Dispatch<React.SetStateAction<Candidate | null>>
  setUnifiedModalType: React.Dispatch<React.SetStateAction<CommunicationType>>
  setUnifiedModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  setShowAddToListModal: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  isLIAThinking: boolean
  setIsLIAThinking: React.Dispatch<React.SetStateAction<boolean>>
  handleStartWSITextScreening: (candidate: Candidate) => void
  handleOpenWSIModal: (candidate: Candidate) => void
  openUnifiedModal: (candidate: Candidate, type: CommunicationType) => void
  handleCandidateClick: (candidate: Candidate) => void
  executeSearch: (
    query: string,
    entities?: ParsedEntities,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch?: boolean
  ) => Promise<void>
  talentFunnel: {
    toggleFavoriteCandidate: (id: string, note?: string) => void
  }
  user: AuthUser | null
  router: AppRouter
}

export function useCandidatesLIAHandlers(ctx: CandidatesLIAHandlersContext) {
  const {
    handleQuickAction,
    handleTalentUIAction,
    handleCalibrationLike,
    handleCalibrationDislike,
  } = useLIAQuickActions(ctx)

  const { handleAICommand } = useLIAAICommands(ctx)

  const {
    handleOrchestratedTalentMessage,
    handleLIAChatMessage,
  } = useLIAChatMessage(ctx, handleAICommand, handleTalentUIAction)

  return {
    handleQuickAction,
    handleOrchestratedTalentMessage,
    handleTalentUIAction,
    handleCalibrationLike,
    handleCalibrationDislike,
    handleLIAChatMessage,
    handleAICommand,
    isConversationalMessage,
    isGenericQuestion,
  }
}
