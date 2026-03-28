/**
 * use-candidates-view-state.ts — Sprint 4.11
 *
 * Centraliza todos os estados relacionados à visualização de candidatos,
 * extraídos de CandidatesPage para reduzir o tamanho do componente.
 *
 * Portabilidade Vue: retorna { state, actions } → mapeia para data() + methods() em Vue 3.
 */

import { useState } from "react"
import type { Candidate } from "@/components/pages/candidates/types"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ViewState {
  selectedCandidate: Candidate | null
  showPreview: boolean
  isPreviewMaximized: boolean
  showCandidatePage: boolean
  showCandidatePreview: boolean
  previewCandidate: Candidate | null
  showSidePreview: boolean
  sidePreviewCandidate: Candidate | null
  selectedCandidateForLIA: Candidate | null
  showLIAPromptForCandidate: boolean
  showExpandedLIA: boolean
  liaPromptValue: string
  userCollapsedLIA: boolean
  talentConversationId: string | undefined
  viewedCandidateIds: Set<string>
  currentPage: number
  crossTabFilter: Record<string, unknown> | null
  showCrossTabBanner: boolean
  viewingList: { id: string; name: string; color?: string } | null
  sortBy: string
  sortOrder: "asc" | "desc"
}

interface ViewActions {
  setSelectedCandidate: (v: Candidate | null) => void
  setShowPreview: (v: boolean) => void
  setIsPreviewMaximized: (v: boolean) => void
  setShowCandidatePage: (v: boolean) => void
  setShowCandidatePreview: (v: boolean) => void
  setPreviewCandidate: (v: Candidate | null) => void
  setShowSidePreview: (v: boolean) => void
  setSidePreviewCandidate: (v: Candidate | null) => void
  setSelectedCandidateForLIA: (v: Candidate | null) => void
  setShowLIAPromptForCandidate: (v: boolean) => void
  setShowExpandedLIA: (v: boolean) => void
  setLiaPromptValue: (v: string) => void
  setUserCollapsedLIA: (v: boolean) => void
  setTalentConversationId: (v: string | undefined) => void
  setViewedCandidateIds: (v: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setCurrentPage: (v: number) => void
  setCrossTabFilter: (v: Record<string, unknown> | null) => void
  setShowCrossTabBanner: (v: boolean) => void
  setViewingList: (v: { id: string; name: string; color?: string } | null) => void
  setSortBy: (v: string) => void
  setSortOrder: (v: "asc" | "desc") => void
}

interface UseCandidatesViewStateReturn {
  state: ViewState
  actions: ViewActions
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useCandidatesViewState(): UseCandidatesViewStateReturn {
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [showPreview, setShowPreview] = useState<boolean>(false)
  const [isPreviewMaximized, setIsPreviewMaximized] = useState<boolean>(false)
  const [showCandidatePage, setShowCandidatePage] = useState<boolean>(false)
  const [showCandidatePreview, setShowCandidatePreview] = useState<boolean>(false)
  const [previewCandidate, setPreviewCandidate] = useState<Candidate | null>(null)
  const [showSidePreview, setShowSidePreview] = useState<boolean>(false)
  const [sidePreviewCandidate, setSidePreviewCandidate] = useState<Candidate | null>(null)
  const [selectedCandidateForLIA, setSelectedCandidateForLIA] = useState<Candidate | null>(null)
  const [showLIAPromptForCandidate, setShowLIAPromptForCandidate] = useState<boolean>(false)
  const [showExpandedLIA, setShowExpandedLIA] = useState<boolean>(false)
  const [liaPromptValue, setLiaPromptValue] = useState<string>("")
  const [userCollapsedLIA, setUserCollapsedLIA] = useState<boolean>(false)
  const [talentConversationId, setTalentConversationId] = useState<string | undefined>(undefined)
  const [viewedCandidateIds, setViewedCandidateIds] = useState<Set<string>>(new Set())
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [crossTabFilter, setCrossTabFilter] = useState<Record<string, unknown> | null>(null)
  const [showCrossTabBanner, setShowCrossTabBanner] = useState<boolean>(false)
  const [viewingList, setViewingList] = useState<{ id: string; name: string; color?: string } | null>(null)
  const [sortBy, setSortBy] = useState<string>("score")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")

  return {
    state: {
      selectedCandidate,
      showPreview,
      isPreviewMaximized,
      showCandidatePage,
      showCandidatePreview,
      previewCandidate,
      showSidePreview,
      sidePreviewCandidate,
      selectedCandidateForLIA,
      showLIAPromptForCandidate,
      showExpandedLIA,
      liaPromptValue,
      userCollapsedLIA,
      talentConversationId,
      viewedCandidateIds,
      currentPage,
      crossTabFilter,
      showCrossTabBanner,
      viewingList,
      sortBy,
      sortOrder,
    },
    actions: {
      setSelectedCandidate,
      setShowPreview,
      setIsPreviewMaximized,
      setShowCandidatePage,
      setShowCandidatePreview,
      setPreviewCandidate,
      setShowSidePreview,
      setSidePreviewCandidate,
      setSelectedCandidateForLIA,
      setShowLIAPromptForCandidate,
      setShowExpandedLIA,
      setLiaPromptValue,
      setUserCollapsedLIA,
      setTalentConversationId,
      setViewedCandidateIds,
      setCurrentPage,
      setCrossTabFilter,
      setShowCrossTabBanner,
      setViewingList,
      setSortBy,
      setSortOrder,
    },
  }
}
