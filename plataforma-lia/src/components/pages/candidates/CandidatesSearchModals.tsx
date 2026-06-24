"use client"

import { useTranslations } from "next-intl"
import { GlobalExpansionConfirmModal } from "@/components/pages/candidates/GlobalExpansionConfirmModal"
import { SourceChangeConfirmModal } from "@/components/pages/candidates/SourceChangeConfirmModal"
import { ContactFilterConfirmModal } from "@/components/pages/candidates/ContactFilterConfirmModal"
import { CreditConfirmationModal } from "@/components/pages/candidates/CreditConfirmationModal"
import { SaveAsArchetypeModal } from "@/components/pages/candidates/SaveAsArchetypeModal"
import { EditQueryModal } from "@/components/pages/candidates/EditQueryModal"
import { PreviewSuggestionModal } from "@/components/pages/candidates/PreviewSuggestionModal"
import { DeleteArchetypeModal } from "@/components/pages/candidates/DeleteArchetypeModal"
import { UnsavedPearchWarningModal } from "@/components/modals/unsaved-pearch-warning-modal"
import { useNavGuardStore } from "@/stores/nav-guard-store"
import dynamic from "next/dynamic"
import { toast } from "sonner"
import type { CandidatesPageModalsProps, ModalArchetype, ModalChatMessage } from "./CandidatesPageModals.types"

const AdvancedFiltersModal = dynamic(() => import("@/components/search/advanced-filters-modal").then(m => ({ default: m.AdvancedFiltersModal })), { ssr: false, loading: () => null })
const AddToListModal = dynamic(() => import("@/components/modals/add-to-list-modal").then(m => ({ default: m.AddToListModal })), { ssr: false, loading: () => null })
const ShareSearchModal = dynamic(() => import("@/components/modals/share-search-modal").then(m => ({ default: m.ShareSearchModal })), { ssr: false, loading: () => null })
const AddCandidatesToVacancyModal = dynamic(() => import("@/components/modals/add-candidates-to-vacancy-modal").then(m => ({ default: m.AddCandidatesToVacancyModal })), { ssr: false, loading: () => null })
const AddListToVacanciesModal = dynamic(() => import("@/components/modals/add-list-to-vacancies-modal").then(m => ({ default: m.AddListToVacanciesModal })), { ssr: false, loading: () => null })

type CandidatesSearchModalsProps = Pick<CandidatesPageModalsProps,
  | 'showCreditConfirmation'
  | 'setShowCreditConfirmation'
  | 'creditEstimate'
  | 'pearchSearchOptions'
  | 'setPearchSearchOptions'
  | 'setPendingSearchRequest'
  | 'handleConfirmPearchSearch'
  | 'showGlobalExpansionConfirm'
  | 'setShowGlobalExpansionConfirm'
  | 'lastSuccessfulQuery'
  | 'lastSearchQuery'
  | 'localResultsCount'
  | 'isExpandingToGlobal'
  | 'handleExpandToGlobal'
  | 'showSourceChangeModal'
  | 'setShowSourceChangeModal'
  | 'pendingSourceChange'
  | 'setPendingSourceChange'
  | 'confirmSourceChange'
  | 'showContactFilterModal'
  | 'setShowContactFilterModal'
  | 'pendingContactFilter'
  | 'setPendingContactFilter'
  | 'confirmContactFilterChange'
  | 'showSaveAsArchetypeModal'
  | 'setShowSaveAsArchetypeModal'
  | 'searchResults'
  | 'isCreatingArchetype'
  | 'setIsCreatingArchetype'
  | 'archetypeCreationStep'
  | 'setArchetypeCreationStep'
  | 'newArchetypeData'
  | 'setNewArchetypeData'
  | 'setUserArchetypes'
  | 'setChatMessages'
  | 'showAdvancedSearch'
  | 'setShowAdvancedSearch'
  | 'activeSearchFilters'
  | 'setActiveSearchFilters'
  | 'hideViewedCandidates'
  | 'showAddToListModal'
  | 'setShowAddToListModal'
  | 'addToListCandidateIds'
  | 'setAddToListCandidateIds'
  | 'addToListCandidateNames'
  | 'setAddToListCandidateNames'
  | 'showShareSearchModal'
  | 'setShowShareSearchModal'
  | 'shareSearchTitle'
  | 'setShareSearchTitle'
  | 'shareSearchCandidates'
  | 'setShareSearchCandidates'
  | 'showAddListToVacanciesModal'
  | 'setShowAddListToVacanciesModal'
  | 'selectedListForVacancies'
  | 'setSelectedListForVacancies'
  | 'showAddToVacancyModal'
  | 'setShowAddToVacancyModal'
  | 'selectedCandidatesForBatch'
  | 'setSelectedCandidatesForBatch'
  | 'candidates'
  | 'user'
  | 'showUnsavedWarningModal'
  | 'setShowUnsavedWarningModal'
  | 'setPendingTabChange'
  | 'handleSaveAllAndExit'
  | 'handleExitWithoutSaving'
  | 'unsavedPearchCandidates'
  | 'isSavingToBase'
  | 'showEditQueryModal'
  | 'setShowEditQueryModal'
  | 'editQueryValue'
  | 'getActiveSearchFiltersCount'
  | 'searchSource'
  | 'setSearchSource'
  | 'setSearchTerm'
  | 'setLastSearchQuery'
  | 'setLastSearchMode'
  | 'setLastSearchEntities'
  | 'setLastSearchMetadata'
  | 'executeSearch'
  | 'previewSuggestion'
  | 'setPreviewSuggestion'
  | 'previewingUserArchetype'
  | 'setPreviewingUserArchetype'
  | 'buildFiltersFromTags'
  | 'setLiaPromptValue'
  | 'setActiveSearchTab'
  | 'archetypeToDelete'
  | 'setArchetypeToDelete'
>

export function CandidatesSearchModals(props: CandidatesSearchModalsProps) {
  const t = useTranslations('candidates.modals')
  const p = props
  return (
    <>
      <CreditConfirmationModal
        open={p.showCreditConfirmation}
        onOpenChange={p.setShowCreditConfirmation}
        creditEstimate={p.creditEstimate}
        pearchSearchOptions={p.pearchSearchOptions}
        onSearchOptionsChange={p.setPearchSearchOptions}
        onCancel={() => { p.setShowCreditConfirmation(false); p.setPendingSearchRequest(null) }}
        onConfirm={p.handleConfirmPearchSearch}
      />

      <GlobalExpansionConfirmModal
        open={p.showGlobalExpansionConfirm}
        onOpenChange={p.setShowGlobalExpansionConfirm}
        lastSuccessfulQuery={p.lastSuccessfulQuery}
        lastSearchQuery={p.lastSearchQuery}
        localResultsCount={p.localResultsCount}
        isExpandingToGlobal={p.isExpandingToGlobal}
        onConfirm={p.handleExpandToGlobal}
      />

      <SourceChangeConfirmModal
        open={p.showSourceChangeModal}
        onOpenChange={p.setShowSourceChangeModal}
        pendingSourceChange={p.pendingSourceChange}
        onCancel={() => { p.setShowSourceChangeModal(false); p.setPendingSourceChange(null) }}
        onConfirm={p.confirmSourceChange}
      />

      <ContactFilterConfirmModal
        open={p.showContactFilterModal}
        onOpenChange={p.setShowContactFilterModal}
        pendingContactFilter={p.pendingContactFilter}
        onCancel={() => { p.setShowContactFilterModal(false); p.setPendingContactFilter(null) }}
        onConfirm={p.confirmContactFilterChange}
      />

      <SaveAsArchetypeModal
        open={p.showSaveAsArchetypeModal}
        onOpenChange={p.setShowSaveAsArchetypeModal}
        currentQuery={p.lastSuccessfulQuery || p.searchResults.query || ''}
        isCreatingArchetype={p.isCreatingArchetype}
        newArchetypeData={p.newArchetypeData}
        onClose={() => {
          if (p.isCreatingArchetype) {
            p.setIsCreatingArchetype(false)
            p.setArchetypeCreationStep('initial')
            p.setNewArchetypeData({})
          }
        }}
        onSave={(archetype, message) => {
          p.setUserArchetypes(prev => [...prev, archetype as unknown as ModalArchetype])
          p.setShowSaveAsArchetypeModal(false)
          p.setChatMessages(prev => [...prev, message as unknown as ModalChatMessage])
          if (p.isCreatingArchetype) {
            p.setIsCreatingArchetype(false)
            p.setArchetypeCreationStep('initial')
            p.setNewArchetypeData({})
          }
        }}
      />

      <AdvancedFiltersModal
        isOpen={p.showAdvancedSearch}
        onClose={() => p.setShowAdvancedSearch(false)}
        onApply={(filters) => {
          p.setActiveSearchFilters(filters as Record<string, unknown>)
          p.setShowAdvancedSearch(false)
          const hideScope = (filters as Record<string, unknown>).general ? ((filters as Record<string, unknown>).general as Record<string, unknown>)?.hideViewedScope as string || "dont_hide" : "dont_hide"
          const hidePeriod = (filters as Record<string, unknown>).general ? ((filters as Record<string, unknown>).general as Record<string, unknown>)?.hideViewedPeriod as string || "all_time" : "all_time"
          p.hideViewedCandidates.setScope(hideScope)
          p.hideViewedCandidates.setPeriod(hidePeriod)
          if (hideScope !== "dont_hide") { p.hideViewedCandidates.fetchViewedCandidates() }
        }}
        initialFilters={p.activeSearchFilters}
        estimatedMatches={1000000}
      />

      <AddToListModal
        isOpen={p.showAddToListModal}
        onClose={() => { p.setShowAddToListModal(false); p.setAddToListCandidateIds([]); p.setAddToListCandidateNames([]) }}
        candidateIds={p.addToListCandidateIds}
        candidateNames={p.addToListCandidateNames}
        onSuccess={() => { toast.success(t('success'), { description: t('candidatesAddedToList') }) }}
      />

      <ShareSearchModal
        open={p.showShareSearchModal}
        onClose={() => { p.setShowShareSearchModal(false); p.setShareSearchCandidates([]); p.setShareSearchTitle('') }}
        shareType="search"
        title={p.shareSearchTitle}
        candidateIds={p.shareSearchCandidates.map(c => c.id)}
        candidateCount={p.shareSearchCandidates.length}
        sourceQuery={p.lastSearchQuery || undefined}
      />

      {p.selectedListForVacancies && (
        <AddListToVacanciesModal
          isOpen={p.showAddListToVacanciesModal}
          onClose={() => { p.setShowAddListToVacanciesModal(false); p.setSelectedListForVacancies(null) }}
          listId={p.selectedListForVacancies.id}
          listName={p.selectedListForVacancies.name}
          candidateCount={p.selectedListForVacancies.candidateCount}
          onSuccess={() => { toast.success(t('success'), { description: t('candidatesAddedToSelectedJobs') }) }}
        />
      )}

      <AddCandidatesToVacancyModal
        isOpen={p.showAddToVacancyModal}
        onClose={() => p.setShowAddToVacancyModal(false)}
        candidateIds={Array.from(p.selectedCandidatesForBatch)}
        candidateNames={p.candidates.filter(c => p.selectedCandidatesForBatch.has(c.id)).map(c => c.name)}
        currentRecruiterEmail={p.user?.email}
        onSuccess={() => { p.setSelectedCandidatesForBatch(new Set()); toast.success(t('success'), { description: t('candidatesAddedToJob') }) }}
      />

      <UnsavedPearchWarningModal
        isOpen={p.showUnsavedWarningModal}
        onClose={() => { p.setShowUnsavedWarningModal(false); p.setPendingTabChange(null); useNavGuardStore.getState().clear() }}
        onSaveAndExit={p.handleSaveAllAndExit}
        onExitWithoutSaving={p.handleExitWithoutSaving}
        unsavedCount={p.unsavedPearchCandidates.length}
        unsavedCandidates={p.unsavedPearchCandidates}
        isSaving={p.isSavingToBase}
      />

      <EditQueryModal
        isOpen={p.showEditQueryModal}
        onClose={() => p.setShowEditQueryModal(false)}
        initialValue={p.editQueryValue}
        activeFiltersCount={p.getActiveSearchFiltersCount()}
        searchSource={p.searchSource}
        onSearchSourceChange={p.setSearchSource}
        pearchSearchOptions={p.pearchSearchOptions}
        onPearchOptionsChange={p.setPearchSearchOptions}
        onOpenFilters={() => p.setShowAdvancedSearch(true)}
        onSubmitNatural={async (query, entities, mode, metadata) => {
          p.setSearchTerm(query)
          p.setLastSearchQuery(query)
          p.setLastSearchMode(mode || 'natural')
          p.setLastSearchEntities(entities as unknown as Record<string, unknown>)
          p.setLastSearchMetadata(metadata as unknown as Record<string, unknown>)
          await p.executeSearch(query, entities, mode || 'natural', metadata, false)
        }}
        onSubmitAI={async (query) => {
          p.setSearchTerm(query)
          p.setLastSearchQuery(query)
          p.setLastSearchMode('ai-natural')
          p.setLastSearchEntities(null)
          await p.executeSearch(query, null, 'ai-natural', undefined, false)
        }}
      />

      <PreviewSuggestionModal
        previewSuggestion={p.previewSuggestion}
        previewingUserArchetype={p.previewingUserArchetype}
        onClose={() => { p.setPreviewSuggestion(null); p.setPreviewingUserArchetype(null) }}
        buildFiltersFromTags={p.buildFiltersFromTags}
        onUpdateArchetype={(id, updates) => {
          p.setUserArchetypes(prev => prev.map((a) => a.id === id ? { ...a, ...updates } : a))
        }}
        onSaveArchetype={(newArchetype) => p.setUserArchetypes(prev => [...prev, newArchetype as unknown as ModalArchetype])}
        onExecuteSearch={async (query, filters, mode, metadata, usePearch) => {
          await p.executeSearch(query, filters as Record<string, unknown>, mode as string, metadata as Record<string, unknown>, usePearch)
        }}
        onSetLiaPromptValue={p.setLiaPromptValue}
        onSetActiveSearchTab={p.setActiveSearchTab}
      />

      <DeleteArchetypeModal
        archetypeToDelete={p.archetypeToDelete}
        onClose={() => p.setArchetypeToDelete(null)}
        onDeleted={(id) => p.setUserArchetypes(prev => prev.filter(a => a.id !== id))}
      />
    </>
  )
}
