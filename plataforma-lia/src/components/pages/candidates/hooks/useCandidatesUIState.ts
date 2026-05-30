"use client"

// useCandidatesUIState.ts
// Owns all local modal-open flags and UI-only state that does not belong to
// a specific domain hook (search state, view state, etc.).

import { useState, useMemo, useCallback } from "react"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"
import { type ParsedCVResponse } from "@/components/cv"
import { type CreditEstimate } from "@/lib/api/candidate-search"
import { type ParsedEntities, type SearchMode, type SearchMetadata } from "@/components/search/smart-search-input"
import { type SearchFilters } from "@/components/search/advanced-filters-modal"
import type { Candidate } from "@/components/pages/candidates/types"
import {
  DEFAULT_PEARCH_OPTIONS,
  PREVIEW_WIDTH_DEFAULT,
  LIA_ASSISTANT_TIPS_DEFAULT,
  type PearchSearchOptions,
  type ChatMessage,
} from "./candidates-core"
import { useLiaChatContext } from "@/contexts/lia-float-context"

export type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

export function useCandidatesUIState() {
  // ── LIA / sidebar UI ─────────────────────────────────────────────────────
  const [liaPromptEntities, setLiaPromptEntities] = useState<ParsedEntities>({
    job_title: undefined, location: undefined, skills: [],
    years_experience: undefined, industry: undefined,
    seniority: undefined, company: undefined,
  })
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(true)
  const [showLiaAssistant, setShowLiaAssistant] = useState(false)
  const [liaIsParsingEntities, setLiaIsParsingEntities] = useState(false)
  const [liaSuggestions, setLiaSuggestions] = useState<string[]>([])
  const [liaAssistantTips, setLiaAssistantTips] = useState<string[]>(LIA_ASSISTANT_TIPS_DEFAULT)
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('ia-natural')
  const [isLIAThinking, setIsLIAThinking] = useState(false)
  const { chatMessages: unifiedMessages, setChatMessages: setUnifiedMessages, addChatMessage: addUnifiedMessage } = useLiaChatContext()
  const chatMessages = useMemo<ChatMessage[]>(() => unifiedMessages.map(m => ({
    id: m.id,
    type: (m.sender === 'user' ? 'user' : 'lia') as ChatMessage['type'],
    content: m.content,
    timestamp: new Date(),
    metadata: m.metadata as ChatMessage['metadata'],
  })), [unifiedMessages])
  const setChatMessages = useCallback((val: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => {
    const toUnified = (arr: ChatMessage[]) => arr.map(m => ({
      id: m.id,
      sender: (m.type === 'user' ? 'user' : 'lia') as 'user' | 'lia',
      content: m.content,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      metadata: m.metadata as Record<string, unknown> | undefined,
    }))
    if (typeof val === 'function') {
      setUnifiedMessages(prevUnified => {
        const prevChat: ChatMessage[] = prevUnified.map(m => ({
          id: m.id,
          type: (m.sender === 'user' ? 'user' : 'lia') as ChatMessage['type'],
          content: m.content,
          timestamp: new Date(),
          metadata: m.metadata as ChatMessage['metadata'],
        }))
        return toUnified(val(prevChat))
      })
    } else if (val.length === 0) {
      setUnifiedMessages([])
    } else {
      setUnifiedMessages(toUnified(val))
    }
  }, [setUnifiedMessages])

  // ── Search / pearch options ──────────────────────────────────────────────
  const [pearchSearchOptions, setPearchSearchOptions] = useState<PearchSearchOptions>(DEFAULT_PEARCH_OPTIONS)
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({
    ppiOptions: {} as Record<string, unknown>, general: {}, job: {}, company: {},
    skills: {}, education: {}, languages: {},
  })
  const [searchResults, setSearchResults] = useState<{
    local: Candidate[]; global: Candidate[]
    localCount: number; globalCount: number; query: string
    isLoading: boolean; showGlobalResults: boolean; globalDismissed: boolean
    isEnrichingContacts: boolean
    filteredNoContact: number
    enrichmentAttempted: number
    filteredCandidates: import('./useCandidatesExecuteSearch').DiscardedCandidate[]
  }>({
    local: [], global: [], localCount: 0, globalCount: 0, query: '',
    isLoading: false, showGlobalResults: false, globalDismissed: false,
    isEnrichingContacts: false,
    filteredNoContact: 0,
    enrichmentAttempted: 0,
    filteredCandidates: [],
  })
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [searchThreadId, setSearchThreadId] = useState<string | undefined>(undefined)
  const [searchFingerprint, setSearchFingerprint] = useState<string | undefined>(undefined)
  const [creditEstimate, setCreditEstimate] = useState<CreditEstimate | null>(null)
  const [pendingSearchRequest, setPendingSearchRequest] = useState<{
    query: string; entities?: ParsedEntities; mode?: SearchMode; metadata?: SearchMetadata
  } | null>(null)

  // ── Preview / resize ─────────────────────────────────────────────────────
  const [previewWidth, setPreviewWidth] = useState(PREVIEW_WIDTH_DEFAULT)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  // ── Modal open/close flags ───────────────────────────────────────────────
  const [showBatchApproval, setShowBatchApproval] = useState(false)
  const [showContactModal, setShowContactModal] = useState(false)
  const [contactModalAction, setContactModalAction] = useState<'general' | 'wsi_screening' | 'interview_invite'>('general')
  const [contactModalCandidate, setContactModalCandidate] = useState<Record<string, unknown> | null>(null)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [unifiedModalOpen, setUnifiedModalOpen] = useState(false)
  const [unifiedModalType, setUnifiedModalType] = useState<CommunicationType>('email')
  const [unifiedModalCandidate, setUnifiedModalCandidate] = useState<Candidate | null>(null)
  const [showQuickViewModal, setShowQuickViewModal] = useState(false)
  const [showComparisonModal, setShowComparisonModal] = useState(false)
  const [selectedCandidateForAction, setSelectedCandidateForAction] = useState<Candidate | null>(null)
  const [showAddCandidateModal, setShowAddCandidateModal] = useState(false)
  const [preSelectedListForModal, setPreSelectedListForModal] = useState<{ id: string; name: string } | null>(null)
  const [showWSITextModal, setShowWSITextModal] = useState(false)
  const [showWSIVoiceModal, setShowWSIVoiceModal] = useState(false)
  const [wsiCandidateForScreening, setWsiCandidateForScreening] = useState<Candidate | null>(null)
  const [showWSIInviteModal, setShowWSIInviteModal] = useState(false)
  const [wsiInviteCandidate, setWsiInviteCandidate] = useState<Candidate | null>(null)
  const [showRubricModal, setShowRubricModal] = useState(false)
  const [rubricCandidate, setRubricCandidate] = useState<Candidate | null>(null)
  const [rubricEvaluationData, setRubricEvaluationData] = useState<Record<string, unknown> | null>(null)
  const [showSendEmailModal, setShowSendEmailModal] = useState(false)
  const [emailCandidateSelected, setEmailCandidateSelected] = useState<Candidate | null>(null)
  const [showCVPreviewModal, setShowCVPreviewModal] = useState(false)
  const [parsedCVData, setParsedCVData] = useState<ParsedCVResponse | null>(null)
  const [showAddToListModal, setShowAddToListModal] = useState(false)
  const [addToListCandidateIds, setAddToListCandidateIds] = useState<string[]>([])
  const [addToListCandidateNames, setAddToListCandidateNames] = useState<string[]>([])
  const [showAddListToVacanciesModal, setShowAddListToVacanciesModal] = useState(false)
  const [selectedListForVacancies, setSelectedListForVacancies] = useState<{ id: string; name: string; candidateCount: number } | null>(null)
  const [showAddToVacancyModal, setShowAddToVacancyModal] = useState(false)
  const [showShareSearchModal, setShowShareSearchModal] = useState(false)
  const [shareSearchCandidates, setShareSearchCandidates] = useState<Array<{ id: string; name: string; email?: string; avatar_url?: string; current_title?: string; linkedin_url?: string }>>([])
  const [shareSearchTitle, setShareSearchTitle] = useState('')
  const [showCreditConfirmation, setShowCreditConfirmation] = useState(false)
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [showContactFilterModal, setShowContactFilterModal] = useState(false)
  const [pendingContactFilter, setPendingContactFilter] = useState<'email' | 'phone' | null>(null)
  const [isSavingToBase, setIsSavingToBase] = useState(false)
  const [isAddingToList, setIsAddingToList] = useState(false)
  const [showUnsavedWarningModal, setShowUnsavedWarningModal] = useState(false)
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [pendingTabChange, setPendingTabChange] = useState<string | null>(null)

  return {
    // LIA UI
    liaPromptEntities, setLiaPromptEntities,
    showLiaSuggestions, setShowLiaSuggestions,
    showLiaAssistant, setShowLiaAssistant,
    liaIsParsingEntities, setLiaIsParsingEntities,
    liaSuggestions, setLiaSuggestions,
    liaAssistantTips, setLiaAssistantTips,
    activeSearchTab, setActiveSearchTab,
    isLIAThinking, setIsLIAThinking,
    chatMessages, setChatMessages,
    // Search
    pearchSearchOptions, setPearchSearchOptions,
    activeSearchFilters, setActiveSearchFilters,
    searchResults, setSearchResults,
    selectedTemplate, setSelectedTemplate,
    searchThreadId, setSearchThreadId,
    searchFingerprint, setSearchFingerprint,
    creditEstimate, setCreditEstimate,
    pendingSearchRequest, setPendingSearchRequest,
    // Preview
    previewWidth, setPreviewWidth,
    expandedRows, setExpandedRows,
    // Modals
    showBatchApproval, setShowBatchApproval,
    showContactModal, setShowContactModal,
    contactModalAction, setContactModalAction,
    contactModalCandidate, setContactModalCandidate,
    showScheduleModal, setShowScheduleModal,
    unifiedModalOpen, setUnifiedModalOpen,
    unifiedModalType, setUnifiedModalType,
    unifiedModalCandidate, setUnifiedModalCandidate,
    showQuickViewModal, setShowQuickViewModal,
    showComparisonModal, setShowComparisonModal,
    selectedCandidateForAction, setSelectedCandidateForAction,
    showAddCandidateModal, setShowAddCandidateModal,
    preSelectedListForModal, setPreSelectedListForModal,
    showWSITextModal, setShowWSITextModal,
    showWSIVoiceModal, setShowWSIVoiceModal,
    wsiCandidateForScreening, setWsiCandidateForScreening,
    showWSIInviteModal, setShowWSIInviteModal,
    wsiInviteCandidate, setWsiInviteCandidate,
    showRubricModal, setShowRubricModal,
    rubricCandidate, setRubricCandidate,
    rubricEvaluationData, setRubricEvaluationData,
    showSendEmailModal, setShowSendEmailModal,
    emailCandidateSelected, setEmailCandidateSelected,
    showCVPreviewModal, setShowCVPreviewModal,
    parsedCVData, setParsedCVData,
    showAddToListModal, setShowAddToListModal,
    addToListCandidateIds, setAddToListCandidateIds,
    addToListCandidateNames, setAddToListCandidateNames,
    showAddListToVacanciesModal, setShowAddListToVacanciesModal,
    selectedListForVacancies, setSelectedListForVacancies,
    showAddToVacancyModal, setShowAddToVacancyModal,
    showShareSearchModal, setShowShareSearchModal,
    shareSearchCandidates, setShareSearchCandidates,
    shareSearchTitle, setShareSearchTitle,
    showCreditConfirmation, setShowCreditConfirmation,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    showContactFilterModal, setShowContactFilterModal,
    pendingContactFilter, setPendingContactFilter,
    isSavingToBase, setIsSavingToBase,
    isAddingToList, setIsAddingToList,
    showUnsavedWarningModal, setShowUnsavedWarningModal,
    showAdvancedSearch, setShowAdvancedSearch,
    pendingTabChange, setPendingTabChange,
  }
}
