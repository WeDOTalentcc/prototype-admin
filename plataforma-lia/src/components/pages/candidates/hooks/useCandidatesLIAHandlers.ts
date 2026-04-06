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
  setCandidates: (v: Candidate[]) => void
  chatMessages: LIAChatMessage[]
  setChatMessages: (v: LIAChatMessage[]) => void
  liaPromptValue: string
  setLiaPromptValue: (v: string) => void
  liaWidth: number
  setLiaWidth: (v: number) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (v: SearchTab) => void
  talentConversationId: string | undefined
  setTalentConversationId: (v: string | undefined) => void
  liaIsParsingEntities: boolean
  setLiaIsParsingEntities: (v: boolean) => void
  liaSuggestions: string[]
  setLiaSuggestions: (v: string[]) => void
  showLiaSuggestions: boolean
  setShowLiaSuggestions: (v: boolean) => void
  showLiaAssistant: boolean
  setShowLiaAssistant: (v: boolean) => void
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
  setLiaPromptEntities: (v: ParsedEntities) => void
  setShowExpandedLIA: (v: boolean) => void
  userCollapsedLIA: boolean
  setUserCollapsedLIA: (v: boolean) => void
  selectedCandidateForLIA: Candidate | null
  setSelectedCandidateForLIA: (v: Candidate | null) => void
  showLIAPromptForCandidate: boolean
  setShowLIAPromptForCandidate: (v: boolean) => void
  selectedCandidate: Candidate | null
  setSelectedCandidate: (v: Candidate | null) => void
  showQuickViewModal: boolean
  setShowQuickViewModal: (v: boolean) => void
  showComparisonModal: boolean
  setShowComparisonModal: (v: boolean) => void
  setShowScheduleModal: (v: boolean) => void
  setUnifiedModalCandidate: (v: Candidate | null) => void
  setUnifiedModalType: (v: CommunicationType) => void
  setUnifiedModalOpen: (v: boolean) => void
  setShowAddToListModal: (v: boolean) => void
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  isLIAThinking: boolean
  setIsLIAThinking: (v: boolean) => void
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
