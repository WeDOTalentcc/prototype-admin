import type { Candidate } from "@/components/pages/candidates/types"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
import type { ParsedCVResponse } from "@/components/cv"
import type { JobLocationAddress } from "@/services/lia-api"
export interface ModalPearchSearchOptions {
  searchType?: 'fast'
  limit?: number
  requireEmails: boolean
  requirePhoneNumbers: boolean
  showEmails?: boolean
  showPhoneNumbers?: boolean
  highFreshness?: boolean
}

export interface ModalCreditEstimate {
  query: string
  pearch_type: 'fast'
  limit: number
  base_cost: number
  insights_cost: number
  freshness_cost: number
  email_cost: number
  phone_cost: number
  cost_per_candidate: number
  total_estimated: number
}

export interface ModalArchetype {
  id: string
  name: string
  description?: string
  emoji?: string
  query?: string
  filters?: Record<string, unknown>
  tags?: string[]
  industry?: string
  createdAt?: Date
  isDefault?: boolean
  usage_count?: number
}

export interface ModalAISuggestion {
  name: string
  description: string
  query: string
  filters: {
    job_title?: string
    seniority?: string
    skills?: string[]
    location?: string
  }
}

export interface ModalUnsavedCandidate {
  id: string
  name: string
  email?: string | null
  phone?: string | null
  best_personal_email?: string | null
  best_business_email?: string | null
  personal_emails?: string[]
  business_emails?: string[]
}

export interface ModalChatMessage {
  id?: string
  role?: string
  content?: string
  [key: string]: unknown
}

export interface CandidatesPageModalsProps {
  // Contact Modal
  selectedCandidateForAction: Candidate | null
  contactModalCandidate: Candidate | null
  showContactModal: boolean
  contactModalAction: "general" | "wsi_screening" | "interview_invite"
  setShowContactModal: (v: boolean) => void
  setSelectedCandidateForAction: (v: Candidate | null) => void
  setContactModalCandidate: (v: Candidate | null) => void
  setContactModalAction: (v: "general" | "wsi_screening" | "interview_invite") => void
  handleSendMessage: (...args: unknown[]) => unknown

  // Schedule Modal
  showScheduleModal: boolean
  setShowScheduleModal: (v: boolean) => void
  handleScheduleComplete: (...args: unknown[]) => unknown

  // Unified Communication Modal
  unifiedModalOpen: boolean
  unifiedModalCandidate: Candidate | null
  unifiedModalType: CommunicationType
  lastSearchQuery: string
  handleUnifiedModalClose: () => void
  handleUnifiedModalSend: (...args: unknown[]) => unknown

  // Candidate Comparison Modal
  showComparisonModal: boolean
  setShowComparisonModal: (v: boolean) => void
  selectedCandidatesForBatch: Set<string>
  sortedCandidates: Candidate[]
  candidates: Candidate[]
  handleNavigateToFullProfile: (c: Candidate) => void
  handleScheduleInterview: (c: Candidate) => void
  handleContactCandidate: (c: Candidate) => void

  // Candidate Page Modal
  showCandidatePage: boolean
  selectedCandidate: Candidate | null
  handleCloseCandidatePage: () => void

  // New Candidate Unified Modal
  showAddCandidateModal: boolean
  setShowAddCandidateModal: (v: boolean) => void
  preSelectedListForModal: { id: string; name: string } | null
  setPreSelectedListForModal: (v: { id: string; name: string } | null) => void
  handleAddCandidate: (c: unknown) => void
  setCandidateListsForModal: (v: unknown[]) => void
  bulkJobVacancies: Array<{ id: string; title: string; department?: string; location?: string | JobLocationAddress }>
  candidateListsForModal: Array<{ id: string; name: string; color?: string }>
  handleCandidatePageOpen: (c: Candidate) => void

  // Batch Approval Modal
  showBatchApproval: boolean
  setShowBatchApproval: (v: boolean) => void
  convertCandidatesForBatch: (candidates: Candidate[]) => Record<string, unknown>[]
  handleBatchApprovalComplete: (...args: unknown[]) => unknown

  // WSI Text Screening Modal
  wsiCandidateForScreening: Candidate | null
  setWsiCandidateForScreening: (v: Candidate | null) => void
  showWSITextModal: boolean
  setShowWSITextModal: (v: boolean) => void
  showWSIVoiceModal: boolean
  setShowWSIVoiceModal: (v: boolean) => void
  handleWSIScreeningComplete: (...args: unknown[]) => unknown

  // WSI Triagem Invite Modal
  showWSIInviteModal: boolean
  setShowWSIInviteModal: (v: boolean) => void
  wsiInviteCandidate: Candidate | null
  setWsiInviteCandidate: (v: Candidate | null) => void

  // Rubric Evaluation Modal
  showRubricModal: boolean
  setShowRubricModal: (v: boolean) => void
  rubricCandidate: Candidate | null
  setRubricCandidate: (v: Candidate | null) => void
  rubricEvaluationData: Record<string, unknown> | null
  setRubricEvaluationData: (v: Record<string, unknown> | null) => void
  // Send Email Modal
  showSendEmailModal: boolean
  setShowSendEmailModal: (v: boolean) => void
  emailCandidateSelected: Candidate | null
  setEmailCandidateSelected: (v: Candidate | null) => void

  // Reveal Contact Modal
  showRevealModal: boolean
  setShowRevealModal: (v: boolean) => void
  revealCandidate: Candidate | null
  setRevealCandidate: (v: Candidate | null) => void
  handleRevealContact: () => void
  revealType: 'email' | 'phone'

  // CV Preview Modal
  showCVPreviewModal: boolean
  setShowCVPreviewModal: (v: boolean) => void
  parsedCVData: ParsedCVResponse | null
  setParsedCVData: (v: ParsedCVResponse | null) => void
  handleCVConfirmed: (...args: unknown[]) => unknown

  // Credit Confirmation Modal
  showCreditConfirmation: boolean
  setShowCreditConfirmation: (v: boolean) => void
  creditEstimate: ModalCreditEstimate | null
  pearchSearchOptions: ModalPearchSearchOptions
  setPearchSearchOptions: (v: ModalPearchSearchOptions) => void
  setPendingSearchRequest: (v: Record<string, unknown> | null) => void
  handleConfirmPearchSearch: () => void

  // Global Expansion Confirm Modal
  showGlobalExpansionConfirm: boolean
  setShowGlobalExpansionConfirm: (v: boolean) => void
  lastSuccessfulQuery: string
  localResultsCount: number
  isExpandingToGlobal: boolean
  handleExpandToGlobal: () => void

  // Source Change Confirm Modal
  showSourceChangeModal: boolean
  setShowSourceChangeModal: (v: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  setPendingSourceChange: (v: 'hybrid' | 'global' | null) => void
  confirmSourceChange: () => void

  // Contact Filter Confirm Modal
  showContactFilterModal: boolean
  setShowContactFilterModal: (v: boolean) => void
  pendingContactFilter: 'email' | 'phone' | null
  setPendingContactFilter: (v: 'email' | 'phone' | null) => void
  confirmContactFilterChange: () => void

  // Save As Archetype Modal
  showSaveAsArchetypeModal: boolean
  setShowSaveAsArchetypeModal: (v: boolean) => void
  searchResults: { query?: string }
  isCreatingArchetype: boolean
  setIsCreatingArchetype: (v: boolean) => void
  archetypeCreationStep: string
  setArchetypeCreationStep: (v: string) => void
  newArchetypeData: Record<string, unknown>
  setNewArchetypeData: (v: Record<string, unknown>) => void
  setUserArchetypes: (fn: (prev: ModalArchetype[]) => ModalArchetype[]) => void
  setChatMessages: (fn: (prev: ModalChatMessage[]) => ModalChatMessage[]) => void

  // Advanced Filters Modal
  showAdvancedSearch: boolean
  setShowAdvancedSearch: (v: boolean) => void
  activeSearchFilters: Record<string, unknown>
  setActiveSearchFilters: (v: Record<string, unknown>) => void
  hideViewedCandidates: {
    setScope: (s: string) => void
    setPeriod: (p: string) => void
    fetchViewedCandidates: () => void
  }

  // Add to List Modal
  showAddToListModal: boolean
  setShowAddToListModal: (v: boolean) => void
  addToListCandidateIds: string[]
  setAddToListCandidateIds: (v: string[]) => void
  addToListCandidateNames: string[]
  setAddToListCandidateNames: (v: string[]) => void

  // Share Search Modal
  showShareSearchModal: boolean
  setShowShareSearchModal: (v: boolean) => void
  shareSearchTitle: string
  setShareSearchTitle: (v: string) => void
  shareSearchCandidates: Array<{ id: string }>
  setShareSearchCandidates: (v: unknown[]) => void

  // Add List to Vacancies Modal
  showAddListToVacanciesModal: boolean
  setShowAddListToVacanciesModal: (v: boolean) => void
  selectedListForVacancies: { id: string; name: string; candidateCount: number } | null
  setSelectedListForVacancies: (v: unknown) => void

  // Add Candidates to Vacancy Modal
  showAddToVacancyModal: boolean
  setShowAddToVacancyModal: (v: boolean) => void
  setSelectedCandidatesForBatch: (v: Set<string>) => void
  user: { email?: string } | null

  // Unsaved Pearch Warning Modal
  showUnsavedWarningModal: boolean
  setShowUnsavedWarningModal: (v: boolean) => void
  setPendingTabChange: (v: unknown) => void
  handleSaveAllAndExit: () => void
  handleExitWithoutSaving: () => void
  unsavedPearchCandidates: ModalUnsavedCandidate[]
  isSavingToBase: boolean

  // Edit Query Modal
  showEditQueryModal: boolean
  setShowEditQueryModal: (v: boolean) => void
  editQueryValue: string
  getActiveSearchFiltersCount: () => number
  searchSource: string
  setSearchSource: (v: string) => void
  setSearchTerm: (v: string) => void
  setLastSearchQuery: (v: string) => void
  setLastSearchMode: (v: string) => void
  setLastSearchEntities: (v: Record<string, unknown> | null) => void
  setLastSearchMetadata: (v: Record<string, unknown> | undefined) => void
  executeSearch: (...args: unknown[]) => Promise<void>

  // Preview Suggestion Modal
  previewSuggestion: ModalAISuggestion | null
  setPreviewSuggestion: (v: ModalAISuggestion | null) => void
  previewingUserArchetype: ModalArchetype | null
  setPreviewingUserArchetype: (v: ModalArchetype | null) => void
  buildFiltersFromTags: (tags: string[]) => Record<string, string[]>
  setLiaPromptValue: (v: string) => void
  setActiveSearchTab: (v: string) => void

  // Delete Archetype Modal
  archetypeToDelete: ModalArchetype | null
  setArchetypeToDelete: (v: ModalArchetype | null) => void
}

