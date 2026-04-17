"use client"
import type { ChatMessage } from "./candidates-core"
type LIAChatMessage = ChatMessage

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

// LIAChatMessage is the same as ChatMessage from candidates-core
export type { ChatMessage as LIAChatMessage } from './candidates-core'

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
  setCandidates: (v: Candidate[] | ((prev: Candidate[]) => Candidate[])) => void
  chatMessages: LIAChatMessage[]
  setChatMessages: (v: LIAChatMessage[] | ((prev: LIAChatMessage[]) => LIAChatMessage[])) => void
  liaPromptValue: string
  setLiaPromptValue: (v: string) => void
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
