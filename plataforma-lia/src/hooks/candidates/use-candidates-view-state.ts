"use client"

import { useCandidatesStore } from "@/stores/candidates-store"
import type { Candidate } from "@/components/pages/candidates/types"

interface ViewState {
  selectedCandidate: Candidate | null
  showPreview: boolean
  isPreviewMaximized: boolean
  showCandidatePage: boolean
  showCandidatePreview: boolean
  previewCandidate: Candidate | null
  showSidePreview: boolean
  sidePreviewCandidate: Candidate | null
  liaPromptValue: string
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
  setLiaPromptValue: (v: string) => void
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

export function useCandidatesViewState(): UseCandidatesViewStateReturn {
  const store = useCandidatesStore()

  return {
    state: {
      selectedCandidate: store.selectedCandidate as Candidate | null,
      showPreview: store.showPreview,
      isPreviewMaximized: store.isPreviewMaximized,
      showCandidatePage: store.showCandidatePage,
      showCandidatePreview: store.showCandidatePreview,
      previewCandidate: store.previewCandidate as Candidate | null,
      showSidePreview: store.showSidePreview,
      sidePreviewCandidate: store.sidePreviewCandidate as Candidate | null,
      liaPromptValue: store.liaPromptValue,
      talentConversationId: store.talentConversationId,
      viewedCandidateIds: store.viewedCandidateIds,
      currentPage: store.currentPage,
      crossTabFilter: store.crossTabFilter,
      showCrossTabBanner: store.showCrossTabBanner,
      viewingList: store.viewingList,
      sortBy: store.sortBy,
      sortOrder: store.sortOrder,
    },
    actions: {
      setSelectedCandidate: store.setSelectedCandidate as ViewActions['setSelectedCandidate'],
      setShowPreview: store.setShowPreview,
      setIsPreviewMaximized: store.setIsPreviewMaximized,
      setShowCandidatePage: store.setShowCandidatePage,
      setShowCandidatePreview: store.setShowCandidatePreview,
      setPreviewCandidate: store.setPreviewCandidate as ViewActions['setPreviewCandidate'],
      setShowSidePreview: store.setShowSidePreview,
      setSidePreviewCandidate: store.setSidePreviewCandidate as ViewActions['setSidePreviewCandidate'],
      setLiaPromptValue: store.setLiaPromptValue,
      setTalentConversationId: store.setTalentConversationId,
      setViewedCandidateIds: store.setViewedCandidateIds,
      setCurrentPage: store.setCurrentPage,
      setCrossTabFilter: store.setCrossTabFilter,
      setShowCrossTabBanner: store.setShowCrossTabBanner,
      setViewingList: store.setViewingList,
      setSortBy: store.setSortBy,
      setSortOrder: store.setSortOrder,
    },
  }
}
