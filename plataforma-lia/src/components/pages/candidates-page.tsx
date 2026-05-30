"use client"

/**
 * ─────────────────────────────────────────────────────────────────────────────
 *  CANÔNICO 719L — Funil de Talentos
 * ─────────────────────────────────────────────────────────────────────────────
 *  Esta é a ÚNICA implementação válida do Funil de Talentos. Orquestrada por
 *  `useCandidatesPageCore` + `CandidatesPageHeader` + `CandidatesPageModals` +
 *  `CandidateSearchResultsView` + `CandidateSearchBar`, com 6 abas (Busca /
 *  Favoritos / Listas / Bancos de Talentos / Buscas Salvas / Histórico) e
 *  busca multi-modo (Linguagem Natural / Boolean / Job Description / Filtros
 *  Avançados / URL LinkedIn / Arquétipos) sobre 3 fontes (local / híbrida /
 *  global=Pearch).
 *
 *  HISTÓRICO DE QUEDAS (não recriar duplicatas — vide replit.md "Gotchas"):
 *    • a2282c541 (29/abr) experimento substituiu por FunilDeTalentosClient
 *      413L stub → revertido em b7b0b047c + 7afd60a9e (1/mai).
 *    • 1119d216d Task #963 cherry-pick com `--theirs` reintroduziu o stub
 *      sobre o canônico → restaurado em 5/mai (esta versão).
 *
 *  REGRAS:
 *    1. Não criar `FunilDeTalentosClient.tsx`, `funil-page-v2.tsx` ou
 *       qualquer "alternativa". Edite ESTE arquivo.
 *    2. A rota `/funil-de-talentos/page.tsx` deve renderizar
 *       `<CandidatesPage />` direto — nunca `redirect()`.
 *    3. `src/lib/navigation/routes.ts` PAGE_PATHS deve conter
 *       `"Funil de Talentos": "/funil-de-talentos"` (fonte única consumida
 *       por dashboard-app.tsx e DashboardLayoutClient.tsx).
 *    4. `sidebar.tsx` item "Funil de Talentos" deve ter `navigateOnClick: true`.
 *    5. Em cherry-picks de bundles externos, NUNCA usar `--theirs` em massa
 *       em arquivos do Funil — revisar cada conflito manualmente.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { FavoritesTab } from "@/components/talent-funnel-tabs/favorites-tab"
import { HistoryTab } from "@/components/talent-funnel-tabs/history-tab"
import { SavedSearchesTab } from "@/components/talent-funnel-tabs/saved-searches-tab"
import { ListsTab } from "@/components/talent-funnel-tabs/lists-tab"
import TalentPoolsTab from "@/components/pages-candidates/TalentPoolsTab"
import { CandidateSearchResultsView } from "@/components/pages/candidates/CandidateSearchResultsView"
import type { Candidate } from "@/components/pages/candidates/types"
import type { CandidatesPageModalsProps } from "@/components/pages/candidates/CandidatesPageModals.types"
import { liaApi } from "@/services/lia-api"
import dynamic from "next/dynamic"
import { CandidateSearchBar } from "@/components/pages/candidates/CandidateSearchBar"
import { useCandidatesPageCore } from "./candidates/hooks/useCandidatesPageCore"
import { CandidatesPageHeader } from "@/components/pages/candidates/CandidatesPageHeader"
const CandidatesPageModals = dynamic(() => import("@/components/pages/candidates/CandidatesPageModals").then(m => ({ default: m.CandidatesPageModals })), { ssr: false, loading: () => null })
import { toast } from "sonner"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { SearchFingerprintProvider } from "@/components/search/SearchFingerprintContext"

import { LoadingModal as CandidatesLoadingModal } from "@/components/ui/loading"
const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false, loading: () => <CandidatesLoadingModal /> })

export function CandidatesPage({ onAddRecentItem, pendingCandidateOpen, onCandidateOpened }: { onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void; pendingCandidateOpen?: { candidateId: string; candidateName: string } | null; onCandidateOpened?: () => void } = {}) {
  const {
    searchFingerprint,
    handleReSearchWithFilters,
    activeSearchFilters, activeSearchTab, activeTab, addToListCandidateIds, addToListCandidateNames, bulkJobVacancies,
    candidateListsForModal, candidates, chatMessages, clearAllFilters, clearAllTableFilters, clearCrossTabFilter,
    columnSearchTerm, columnWidths, confirmContactFilterChange, confirmSourceChange, contactModalAction, contactModalCandidate,
    convertCandidatesForBatch, creditEstimate, deselectAllCandidates, emailCandidateSelected, executeSearch, favoriteNotes,
    favorites, getActiveAdvancedFiltersCount, getActiveSearchFiltersCount, getActiveTableFiltersCount, getPaginatedCandidates, handleAICommand,
    handleAddCandidate, handleAddToList, handleBatchApprovalComplete, handleBulkEmail, handleBulkWSIScreening, handleCVConfirmed,
    handleCVDragLeave, handleCVDragOver, handleCVDrop, handleCalibrationDislike, handleCalibrationLike, handleCandidateClick,
    handleCandidatePageOpen, handleCloseCandidatePage, handleCloseCandidatePreview, handleConfirmPearchSearch, handleContactCandidate, handleExitWithoutSaving,
    handleExpandToGlobal, handleLIAChatMessage, handleLIAClick, handleLoadMore, handleNavigateToFullProfile, handlePreviewResize,
    handleQuickAction, handleRevealContact, handleSaveAllAndExit, handleSaveToLocalBase, handleScheduleComplete, handleScheduleInterview,
    handleSendAgendamento, handleSendEmail, handleSendFeedback, handleSendMessage, handleSendTriagem, handleSendWhatsApp,
    handleStartWSITextScreening, handleTabChangeWithWarning, handleToggleColumnConfig, handleToggleFavorite, handleTogglePin, handleTogglePreviewMaximize,
    handleUnifiedModalClose, handleUnifiedModalSend, handleUpdateFavoriteNote, handleWSIScreeningComplete, hideViewedCandidates, isAddingToList,
    isLIAThinking, isLoading, isSavingToBase, isSearchActive,
    newCertificationFilter, newSoftSkillFilter, parsedCVData, pearchSearchOptions, pendingContactFilter,
    pendingSourceChange, pinnedCandidates, preSelectedListForModal, previewWidth, renderCellValue, revealCandidate,
    revealType, rubricCandidate, rubricEvaluationData, saveCurrentSearch, searchResults,
    selectAllCandidates, selectedCandidateForAction, selectedCandidatesForBatch, selectedListForVacancies, selectedPearchCount, setActiveSearchFilters,
    setActiveSearchTab, setActiveTab, setAddToListCandidateIds, setAddToListCandidateNames, setCandidateListsForModal, setCandidates,
    setChatMessages, setColumnSearchTerm, setColumnWidths, setContactModalAction, setContactModalCandidate, setEmailCandidateSelected,
    setIsLoading, setNewCertificationFilter, setNewSoftSkillFilter,
    setParsedCVData, setPearchSearchOptions, setPendingContactFilter, setPendingSearchRequest, setPendingSourceChange, setPendingTabChange,
    setPreSelectedListForModal, setRevealCandidate, setRubricCandidate, setRubricEvaluationData, setSearchResults, setSelectedCandidateForAction,
    setSelectedCandidatesForBatch, setSelectedListForVacancies, setShareSearchCandidates, setShareSearchTitle, setShowAddCandidateModal, setShowAddListToVacanciesModal,
    setShowAddToListModal, setShowAddToVacancyModal, setShowAdvancedSearch, setShowBatchApproval, setShowCVPreviewModal, setShowColumnConfig,
    setShowComparisonModal, setShowContactFilterModal, setShowContactModal, setShowCreditConfirmation, setShowRevealModal, setShowRubricModal,
    setShowScheduleModal, setShowSendEmailModal, setShowShareSearchModal, setShowSourceChangeModal, setShowTableFiltersPanel, setShowUnsavedWarningModal,
    setShowWSIInviteModal, setShowWSITextModal, setShowWSIVoiceModal, setTableColumns, setTableFilters, setWsiCandidateForScreening,
    setWsiInviteCandidate, shareSearchCandidates, shareSearchTitle, showAddCandidateModal, showAddListToVacanciesModal, showAddToListModal,
    showAddToVacancyModal, showAdvancedSearch, showBatchApproval, showCVPreviewModal, showColumnConfig, showComparisonModal,
    showContactFilterModal, showContactModal, showCreditConfirmation, showRevealModal, showRubricModal, showScheduleModal,
    showSendEmailModal, showShareSearchModal, showSourceChangeModal, showTableFiltersPanel, showUnsavedWarningModal, showWSIInviteModal,
    showWSITextModal, showWSIVoiceModal, sortedCandidates, tableColumns, tableContainerRef, tableFilters,
    talentFunnel, toggleTableFilter, unifiedModalCandidate, unifiedModalOpen, unifiedModalType,
    unsavedPearchCandidates, user, visibleCandidates, visibleTableColumns, wsiCandidateForScreening, wsiInviteCandidate,
    tabs: tabsRaw,
    archetypeCreationStep, archetypeToDelete, buildFiltersFromTags, crossTabFilter, currentPage, currentSearchSource,
    cvUploadLoading, displayedResultsCount, editQueryValue, isCreatingArchetype, isDroppingCV, isExpandingToGlobal,
    isLoadingMore, isPreviewMaximized, itemsPerPage, lastSearchEntities, lastSearchQuery, lastSuccessfulQuery,
    liaPromptValue, localResultsCount, newArchetypeData, previewCandidate, previewingUserArchetype, previewSuggestion,
    quickFilters, searchSortBy, searchSource, searchTerm, selectedCandidate,
    setArchetypeCreationStep, setArchetypeToDelete, setCurrentPage, setDisplayedResultsCount, setEditQueryValue,
    setHasSearchResults, setIsCreatingArchetype, setLastSearchEntities, setLastSearchMetadata, setLastSearchMode, setLastSearchQuery,
    setLiaPromptValue, setLocalResultsCount, setNewArchetypeData, setPearchResultsCount, setPreviewCandidate, setPreviewingUserArchetype,
    setPreviewSuggestion, setSearchResultsCount, setSearchSortBy, setSearchSource, setSearchTerm, setShowEditQueryModal,
    setShowGlobalExpansionConfirm, setShowSaveAsArchetypeModal, setShowSearchResults, setSortBy, setSortOrder,
    setUserArchetypes, setViewingList, showCrossTabBanner, showEditQueryModal,
    showGlobalExpansionConfirm, showSaveAsArchetypeModal, showSearchResults, sortBy, sortOrder, viewingList,
    showCandidatePage, showCandidatePreview,
    candidatesError, refreshCandidatesList,
    tabs,
  } = useCandidatesPageCore({ onAddRecentItem, pendingCandidateOpen, onCandidateOpened })

  return (
    <SearchFingerprintProvider value={searchFingerprint}>
    <ErrorBoundarySection>
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      {/* Header Fixo - Título e Tabs */}
      <CandidatesPageHeader
        tabs={tabs as unknown as Parameters<typeof CandidatesPageHeader>[0]["tabs"]}
        activeTab={activeTab}
        showSearchResults={showSearchResults}
        searchTerm={searchTerm}
        quickFilters={quickFilters}
        getActiveAdvancedFiltersCount={getActiveAdvancedFiltersCount}
        onTabChange={handleTabChangeWithWarning}
        onAddCandidate={() => setShowAddCandidateModal(true)}
        onNewSearch={() => {
          setShowSearchResults(false)
          setSearchTerm('')
          setLastSearchQuery('')
          setActiveTab('search')
        }}
        onSaveCurrentSearch={saveCurrentSearch}
      />

      {/* Área de Conteúdo Scrollável */}
      <div className="flex-1 flex flex-col overflow-hidden px-4 pt-2 pb-2">
        {/* Conteúdo das Abas */}
        
        {/* ========== TAB BUSCA (AI-First) — extraído para CandidateSearchBar (Sprint F5) ========== */}
        {activeTab === 'search' && !showSearchResults && (
          <CandidateSearchBar
            isSearchActive={isSearchActive}
            isDroppingCV={isDroppingCV}
            cvUploadLoading={cvUploadLoading}
            searchTerm={searchTerm}
            isLoading={isLoading}
            activeFiltersCount={getActiveSearchFiltersCount()}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            onSearchTermChange={setSearchTerm}
            onSubmit={async (query, entities, mode, metadata) => {
              setLastSearchQuery(query)
              setLastSearchMode(mode || 'natural')
              await executeSearch(query, entities, mode, metadata, false)
            }}
            onDrop={handleCVDrop as unknown as Parameters<typeof CandidateSearchBar>[0]["onDrop"]}
            onDragOver={handleCVDragOver as unknown as Parameters<typeof CandidateSearchBar>[0]["onDragOver"]}
            onDragLeave={handleCVDragLeave as unknown as Parameters<typeof CandidateSearchBar>[0]["onDragLeave"]}
            onOpenFilters={() => setShowAdvancedSearch(true)}
            onGoToResults={() => setShowSearchResults(true)}
            onSearchSourceChange={setSearchSource}
            onRequireEmailsChange={(value) => setPearchSearchOptions(prev => ({ ...prev, requireEmails: value }))}
            onRequirePhoneNumbersChange={(value) => setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: value }))}
          />
        )}

        {/* ========== TAB BUSCA - RESULTADOS INLINE ========== */}
        {activeTab === 'search' && showSearchResults && (
          <CandidateSearchResultsView
            lastSearchQuery={lastSearchQuery}
            lastSearchEntities={lastSearchEntities}
            onReSearchWithFilters={handleReSearchWithFilters}
            onBack={() => setShowSearchResults(false)}
            onOpenEditQueryModal={(value) => {
              setEditQueryValue(value)
              setShowEditQueryModal(true)
            }}
            onOpenAdvancedSearch={() => setShowAdvancedSearch(true)}
            selectedCandidatesForBatch={selectedCandidatesForBatch}
            selectedPearchCount={selectedPearchCount}
            deselectAllCandidates={deselectAllCandidates}
            onAddToVacancy={() => setShowAddToVacancyModal(true)}
            onAddToList={handleAddToList}
            isAddingToList={isAddingToList}
            candidates={candidates}
            onShareSearch={() => {
              const selectedList = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
              const searchTitle = lastSearchQuery || `Busca - ${new Date().toLocaleDateString('pt-BR')}`
              setShareSearchCandidates(selectedList.map(c => ({
                id: c.id,
                name: c.name,
                email: c.email,
                avatar_url: c.avatar,
                current_title: c.position,
                linkedin_url: c.linkedin
              })))
              setShareSearchTitle(searchTitle)
              setShowShareSearchModal(true)
            }}
            onBulkEmail={handleBulkEmail}
            onBulkWSIScreening={handleBulkWSIScreening}
            onToggleFavoriteBatch={() => {
              selectedCandidatesForBatch.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
              toast.success("Favoritos atualizados", { description: `${selectedCandidatesForBatch.size} candidato(s) adicionado(s) aos favoritos` })
            }}
            onHideBatch={() => {
              selectedCandidatesForBatch.forEach(id => (talentFunnel as unknown as Record<string, (id: string) => void>).hideCandidate?.(id))
              toast.success("Candidatos ocultos", { description: `${selectedCandidatesForBatch.size} candidato(s) oculto(s) da pesquisa` })
              deselectAllCandidates()
            }}
            onSaveToLocalBase={handleSaveToLocalBase}
            isSavingToBase={isSavingToBase}
            showCrossTabBanner={showCrossTabBanner}
            crossTabFilter={crossTabFilter as unknown as Parameters<typeof CandidateSearchResultsView>[0]["crossTabFilter"]}
            clearCrossTabFilter={clearCrossTabFilter}
            viewingList={viewingList}
            setViewingList={setViewingList}

            setShowSearchResults={setShowSearchResults}
            setSearchTerm={setSearchTerm}
            setLastSearchQuery={setLastSearchQuery}
            setActiveTab={setActiveTab as unknown as Parameters<typeof CandidateSearchResultsView>[0]["setActiveTab"]}
            searchSortBy={searchSortBy}
            setSearchSortBy={setSearchSortBy}
            sortedCandidates={sortedCandidates}
            selectAllCandidates={selectAllCandidates}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            getActiveTableFiltersCount={getActiveTableFiltersCount}
            showColumnConfig={showColumnConfig}
            onToggleColumnConfig={handleToggleColumnConfig}
            tableColumns={tableColumns}
            quickFilters={quickFilters}
            searchTerm={searchTerm}
            getActiveAdvancedFiltersCount={getActiveAdvancedFiltersCount}
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            newSoftSkillFilter={newSoftSkillFilter}
            setNewSoftSkillFilter={setNewSoftSkillFilter}
            newCertificationFilter={newCertificationFilter}
            setNewCertificationFilter={setNewCertificationFilter}
            toggleTableFilter={toggleTableFilter}
            clearAllTableFilters={clearAllTableFilters}
            isLoading={isLoading}
            visibleCandidates={visibleCandidates}
            visibleTableColumns={visibleTableColumns}
            columnWidths={columnWidths}
            setColumnWidths={setColumnWidths}
            setTableColumns={setTableColumns as unknown as Parameters<typeof CandidateSearchResultsView>[0]["setTableColumns"]}
            pinnedCandidates={pinnedCandidates}
            favorites={favorites}
            sortBy={sortBy}
            sortOrder={sortOrder}
            setSortBy={setSortBy}
            setSortOrder={setSortOrder}
            setSelectedCandidatesForBatch={setSelectedCandidatesForBatch}
            onCandidateClick={handleCandidateClick}
            onTogglePin={handleTogglePin}
            onToggleFavorite={handleToggleFavorite}
            renderCellValue={renderCellValue}
            tableContainerRef={tableContainerRef as unknown as Parameters<typeof CandidateSearchResultsView>[0]["tableContainerRef"]}
            showSearchResults={showSearchResults}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage as unknown as Parameters<typeof CandidateSearchResultsView>[0]["setCurrentPage"]}
            itemsPerPage={itemsPerPage}
            getPaginatedCandidates={getPaginatedCandidates}
            clearAllFilters={clearAllFilters}
            displayedResultsCount={displayedResultsCount}
            isLoadingMore={isLoadingMore}
            onLoadMore={handleLoadMore}
            columnSearchTerm={columnSearchTerm}
            setColumnSearchTerm={setColumnSearchTerm}
            setShowColumnConfig={setShowColumnConfig}
            showCandidatePreview={showCandidatePreview}
            previewCandidate={previewCandidate}
            previewWidth={previewWidth}
            onPreviewResize={handlePreviewResize}
            isPreviewMaximized={isPreviewMaximized}
            onCloseCandidatePreview={handleCloseCandidatePreview}
            onTogglePreviewMaximize={handleTogglePreviewMaximize}
            onCandidatePageOpen={handleCandidatePageOpen}
            setSelectedCandidateForAction={setSelectedCandidateForAction}
            setShowScheduleModal={setShowScheduleModal}
            onStartWSITextScreening={handleStartWSITextScreening}
            onSendEmail={handleSendEmail}
            onSendWhatsApp={handleSendWhatsApp}
            onSendTriagem={handleSendTriagem}
            onSendAgendamento={handleSendAgendamento}
            onSendFeedback={handleSendFeedback}
            setPreviewCandidate={setPreviewCandidate}
            setShareSearchCandidates={setShareSearchCandidates}
            setShareSearchTitle={setShareSearchTitle}
            setShowShareSearchModal={setShowShareSearchModal}
            talentFunnel={talentFunnel as unknown as Parameters<typeof CandidateSearchResultsView>[0]["talentFunnel"]}
            setEditQueryValue={setEditQueryValue}
            setShowEditQueryModal={setShowEditQueryModal}
            setShowAddToVacancyModal={setShowAddToVacancyModal}
            isEnrichingContacts={searchResults?.isEnrichingContacts}
            filteredNoContact={searchResults?.filteredNoContact}
            enrichmentAttempted={searchResults?.enrichmentAttempted}
            filteredCandidates={searchResults?.filteredCandidates}
            onDiscardedCandidateEnriched={({ candidate, email, phone }) => {
              // Task #402: ao re-enriquecer um descartado com sucesso, movemos
              // ele para a lista principal e o tiramos do conjunto de descartados
              // (e do contador) para o aviso refletir a realidade atualizada.
              const enrichedCandidate = {
                id: candidate.id,
                candidateId: candidate.id?.substring(0, 8).toUpperCase() || 'CAND',
                name: candidate.name,
                email: email || '',
                phone: phone || '',
                mobile_phone: phone || undefined,
                current_title: candidate.current_title || candidate.headline || '',
                current_company: candidate.current_company || '',
                location: candidate.location || '',
                linkedin_url: candidate.linkedin_url || undefined,
                avatar_url: candidate.picture_url || undefined,
                avatar: candidate.picture_url || undefined,
                linkedin: candidate.linkedin_url || '',
                position: candidate.current_title || candidate.headline || '',
                source: candidate.source || 'pearch',
                has_email: !!email,
                has_phone: !!phone,
                technical_skills: [],
                skills: [],
                experiences: [],
                workHistory: [],
                education: [],
                liaAnalysis: { score: 75, strengths: [], concerns: [], recommendation: '' },
                score: 75,
                workModel: 'remoto' as const,
                contractType: 'CLT' as const,
                monthlySalary: 0,
                experience: 0,
              } as unknown as Candidate
              setCandidates((prev) => {
                const exists = prev.some((c) => c.id === candidate.id)
                return exists ? prev : [enrichedCandidate, ...prev]
              })
              setSearchResults((prev) => ({
                ...prev,
                filteredCandidates: (prev.filteredCandidates || []).filter((c) => c.id !== candidate.id),
                filteredNoContact: Math.max(0, (prev.filteredNoContact || 0) - 1),
              }))
            }}
            error={candidatesError}
            onRetry={refreshCandidatesList}
          />
        )}

        {/* Aba Favoritos */}
        {activeTab === 'favorites' && (
          <div className="flex gap-6">
            <div className={`${showCandidatePreview && previewCandidate ? 'flex-1' : 'w-full'} transition-colors motion-reduce:transition-none duration-300`}>
              <FavoritesTab
                candidates={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id)) as unknown as Parameters<typeof FavoritesTab>[0]["candidates"]}
                pinnedCandidates={pinnedCandidates}
                favoriteCandidates={favorites}
                favoriteNotes={favoriteNotes}
                onTogglePin={handleTogglePin}
                onToggleFavorite={handleToggleFavorite}
                onCandidateClick={handleCandidateClick as unknown as Parameters<typeof FavoritesTab>[0]["onCandidateClick"]}
                onLIAClick={handleLIAClick as unknown as Parameters<typeof FavoritesTab>[0]["onLIAClick"]}
                onUpdateFavoriteNote={handleUpdateFavoriteNote}
              />
            </div>
            
            {/* Candidate Preview - Painel lateral direito */}
            {showCandidatePreview && previewCandidate && (
              <div className="flex-shrink-0 relative" style={{width: `${previewWidth}px`}}>
                <div
                  className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-lia-border-medium dark:hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none z-10 group"
                  onMouseDown={handlePreviewResize}
                  title="Arraste para redimensionar"
                >
                  <div className="absolute inset-0 -left-1 -right-1"></div>
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-lia-border-default dark:bg-lia-bg-elevated group-hover:bg-lia-border-medium dark:group-hover:bg-lia-bg-secondary rounded-full transition-colors motion-reduce:transition-none"></div>
                </div>
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
                  <CandidatePreview
                    candidate={previewCandidate as unknown as Record<string, unknown>}
                    isOpen={showCandidatePreview}
                    onClose={handleCloseCandidatePreview}
                    isMaximized={isPreviewMaximized}
                    onToggleMaximize={handleTogglePreviewMaximize}
                    candidates={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id)) as unknown as Record<string, unknown>[]}
                    currentIndex={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id)).findIndex(c => c.id === previewCandidate.id)}
                    onNavigateCandidate={(index) => {
                      const favoriteCandidates = candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))
                      if (favoriteCandidates[index]) {
                        setPreviewCandidate(favoriteCandidates[index])
                      }
                    }}
                    onOpenFullPage={handleCandidatePageOpen as unknown as (candidate: Record<string, unknown>) => void}
                    onScheduleInterview={(candidate: Record<string, unknown>) => {
                      setSelectedCandidateForAction(candidate as unknown as Parameters<typeof setSelectedCandidateForAction>[0])
                      setShowScheduleModal(true)
                    }}
                    onAddToVacancy={(candidate: Record<string, unknown>) => {
                      setSelectedCandidatesForBatch(new Set([candidate.id as string]) as unknown as Parameters<typeof setSelectedCandidatesForBatch>[0])
                      setShowAddToVacancyModal(true)
                    }}
                    onToggleFavorite={(candidateId: string) => handleToggleFavorite(candidateId)}
                    onWSIScreening={(candidate: Record<string, unknown>) => handleStartWSITextScreening(candidate as unknown as Parameters<typeof handleStartWSITextScreening>[0])}
                    isFavorite={favorites.has(previewCandidate.id)}
                    onSendEmail={(candidate: Record<string, unknown>) => handleSendEmail(candidate as unknown as Parameters<typeof handleSendEmail>[0])}
                    onSendWhatsApp={(candidate: Record<string, unknown>) => handleSendWhatsApp(candidate as unknown as Parameters<typeof handleSendWhatsApp>[0])}
                    onSendTriagem={(candidate: Record<string, unknown>) => handleSendTriagem(candidate as unknown as Parameters<typeof handleSendTriagem>[0])}
                    onSendAgendamento={(candidate: Record<string, unknown>) => handleSendAgendamento(candidate as unknown as Parameters<typeof handleSendAgendamento>[0])}
                    onSendFeedback={(candidate: Record<string, unknown>) => handleSendFeedback(candidate as unknown as Parameters<typeof handleSendFeedback>[0])}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Aba Listas */}
        {activeTab === 'lists' && (
          <ListsTab
            onListSelect={async (listId) => {
              try {
                setIsLoading(true)
                const listDetails = await liaApi.getCandidateList(listId, { limit: 100 })
                
                const mappedCandidates = (((listDetails as unknown as Record<string, unknown>).candidates as unknown as { items?: Record<string, unknown>[] })?.items?.map((member: Record<string, unknown>) => {
                  const c = member.candidate as Record<string, unknown>
                  const location = [c.location_city, c.location_state, c.location_country].filter(Boolean).join(', ') || 'Não informado'
                  const workModel = c.work_model_preference === 'remote' ? 'remoto' : 
                                   c.work_model_preference === 'hybrid' ? 'híbrido' : 'presencial'
                  
                  return {
                    id: c.id,
                    candidateId: c.id,
                    name: c.name || 'Sem nome',
                    email: c.email || '',
                    phone: c.phone || c.mobile_phone || '',
                    linkedin_url: c.linkedin_url,
                    github_url: c.github_url,
                    portfolio_url: c.portfolio_url,
                    avatar_url: c.avatar_url,
                    current_title: c.current_title,
                    current_company: c.current_company,
                    seniority_level: c.seniority_level,
                    years_of_experience: c.years_of_experience,
                    technical_skills: c.technical_skills || [],
                    soft_skills: c.soft_skills || [],
                    languages: c.languages || {},
                    certifications: c.certifications || [],
                    location_city: c.location_city,
                    location_state: c.location_state,
                    location_country: c.location_country,
                    is_remote: c.is_remote,
                    willing_to_relocate: c.willing_to_relocate,
                    work_model_preference: c.work_model_preference,
                    contract_type_preference: c.contract_type_preference,
                    current_salary: c.current_salary,
                    desired_salary_min: c.desired_salary_min,
                    desired_salary_max: c.desired_salary_max,
                    resume_url: c.resume_url,
                    source: c.source || 'local',
                    lia_score: c.lia_score,
                    lia_insights: c.lia_insights,
                    status: c.status,
                    tags: c.tags || [],
                    created_at: c.created_at,
                    updated_at: c.updated_at,
                    position: c.current_title || 'Profissional',
                    monthlySalary: c.current_salary || 0,
                    location: location,
                    workModel: workModel as 'remoto' | 'híbrido' | 'presencial',
                    score: c.lia_score || 0,
                    contractType: (c.contract_type_preference === 'PJ' ? 'PJ' : 
                                   c.contract_type_preference === 'Freelancer' ? 'Freelancer' : 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
                    linkedin: c.linkedin_url || '',
                    skills: c.technical_skills || [],
                    experience: c.years_of_experience || 0,
                    education: '',
                    workHistory: [] as unknown[],
                  }
                }) || []) as unknown as Candidate[]
                
                setCandidates(mappedCandidates as unknown as Parameters<typeof setCandidates>[0])
                setViewingList({ 
                  id: listDetails.id,
                  name: listDetails.name,
                  color: listDetails.color || undefined
                })
                setActiveTab('search')
                setShowSearchResults(true)
                setDisplayedResultsCount(10)
                setLastSearchQuery(`Lista: ${listDetails.name}`)
                
                toast.success("Lista carregada", { description: `Exibindo ${mappedCandidates.length} candidatos da lista "${listDetails.name}"` })
              } catch (error) {
                toast.error("Erro ao carregar lista", { description: error instanceof Error ? error.message : "Não foi possível carregar os candidatos da lista." })
              } finally {
                setIsLoading(false)
              }
            }}
            onAddToJobs={(listId) => {
              liaApi.getCandidateList(listId).then(list => {
                setSelectedListForVacancies({
                  id: listId,
                  name: list.name,
                  candidateCount: list.candidate_count
                })
                setShowAddListToVacanciesModal(true)
              }).catch(err => {
                toast.error("Erro ao carregar lista", { description: err.message })
              })
            }}
            onAddCandidateToList={(listId, listName) => {
              setPreSelectedListForModal({ id: listId, name: listName })
              setShowAddCandidateModal(true)
            }}
          />
        )}

        {/* Aba Histórico */}
        {activeTab === 'history' && (
          <HistoryTab
            history={talentFunnel.history}
            onReExecuteSearch={(historyItem) => {
              setSearchTerm(historyItem.query)
              setLastSearchQuery(historyItem.query)
              setLastSearchMode(historyItem.mode || 'natural')
              if (historyItem.source) {
                setSearchSource(historyItem.source)
              }
              setActiveTab('search')
              setTimeout(() => {
                setShowSearchResults(false)
              }, 100)
            }}
            onSaveAsSearch={(historyItem, name, description) => {
              talentFunnel.saveHistoryAsSearch(historyItem, name, description)
            }}
            onDeleteItem={(id) => {
              talentFunnel.removeFromHistory(id)
            }}
            onClearAll={() => {
              talentFunnel.clearHistory()
            }}
          />
        )}

        {(activeTab as string) === 'talent-pools' && (
          <TalentPoolsTab onSelectPool={(id) => {}} />
        )}

        {/* Aba Buscas Salvas */}
        {activeTab === 'saved-searches' && (
          <SavedSearchesTab
            savedSearches={talentFunnel.savedSearches}
            onExecuteSearch={(search) => {
              setSearchTerm(search.query)
              setLastSearchQuery(search.query)
              setLastSearchMode(search.mode)
              setSearchSource(search.source)
              setActiveTab('search')
              talentFunnel.incrementSavedSearchUsage(search.id)
              setTimeout(() => {
                setShowSearchResults(false)
              }, 100)
            }}
            onAddSearch={(search) => {
              talentFunnel.addSavedSearch(search)
            }}
            onUpdateSearch={(id, updates) => {
              talentFunnel.updateSavedSearch(id, updates)
            }}
            onDeleteSearch={(id) => {
              talentFunnel.removeSavedSearch(id)
            }}
            onToggleFavorite={(id) => {
              talentFunnel.toggleSavedSearchFavorite(id)
            }}
            onNavigateToSearch={() => {
              setActiveTab('search')
              setShowSearchResults(false)
            }}
          />
        )}

      </div>

      {/* Modals - extracted to CandidatesPageModals */}
      <CandidatesPageModals
        selectedCandidateForAction={selectedCandidateForAction}
        contactModalCandidate={contactModalCandidate as unknown as CandidatesPageModalsProps["contactModalCandidate"]}
        showContactModal={showContactModal}
        contactModalAction={contactModalAction}
        setShowContactModal={setShowContactModal}
        setSelectedCandidateForAction={setSelectedCandidateForAction as unknown as CandidatesPageModalsProps["setSelectedCandidateForAction"]}
        setContactModalCandidate={setContactModalCandidate as unknown as CandidatesPageModalsProps["setContactModalCandidate"]}
        setContactModalAction={setContactModalAction}
        handleSendMessage={handleSendMessage as unknown as CandidatesPageModalsProps["handleSendMessage"]}
        showScheduleModal={showScheduleModal}
        setShowScheduleModal={setShowScheduleModal}
        handleScheduleComplete={handleScheduleComplete as unknown as CandidatesPageModalsProps["handleScheduleComplete"]}
        unifiedModalOpen={unifiedModalOpen}
        unifiedModalCandidate={unifiedModalCandidate}
        unifiedModalType={unifiedModalType}
        lastSearchQuery={lastSearchQuery}
        handleUnifiedModalClose={handleUnifiedModalClose}
        handleUnifiedModalSend={handleUnifiedModalSend as unknown as CandidatesPageModalsProps["handleUnifiedModalSend"]}
        showComparisonModal={showComparisonModal}
        setShowComparisonModal={setShowComparisonModal}
        selectedCandidatesForBatch={selectedCandidatesForBatch}
        sortedCandidates={sortedCandidates}
        candidates={candidates}
        handleNavigateToFullProfile={handleNavigateToFullProfile}
        handleScheduleInterview={handleScheduleInterview}
        handleContactCandidate={handleContactCandidate}
        showCandidatePage={showCandidatePage}
        selectedCandidate={selectedCandidate}
        handleCloseCandidatePage={handleCloseCandidatePage}
        showAddCandidateModal={showAddCandidateModal}
        setShowAddCandidateModal={setShowAddCandidateModal}
        preSelectedListForModal={preSelectedListForModal}
        setPreSelectedListForModal={setPreSelectedListForModal}
        handleAddCandidate={handleAddCandidate as unknown as CandidatesPageModalsProps["handleAddCandidate"]}
        setCandidateListsForModal={setCandidateListsForModal as unknown as CandidatesPageModalsProps["setCandidateListsForModal"]}
        bulkJobVacancies={bulkJobVacancies}
        candidateListsForModal={candidateListsForModal}
        handleCandidatePageOpen={handleCandidatePageOpen}
        showBatchApproval={showBatchApproval}
        setShowBatchApproval={setShowBatchApproval}
        convertCandidatesForBatch={convertCandidatesForBatch}
        handleBatchApprovalComplete={handleBatchApprovalComplete as unknown as CandidatesPageModalsProps["handleBatchApprovalComplete"]}
        wsiCandidateForScreening={wsiCandidateForScreening}
        setWsiCandidateForScreening={setWsiCandidateForScreening}
        showWSITextModal={showWSITextModal}
        setShowWSITextModal={setShowWSITextModal}
        showWSIVoiceModal={showWSIVoiceModal}
        setShowWSIVoiceModal={setShowWSIVoiceModal}
        handleWSIScreeningComplete={handleWSIScreeningComplete as unknown as CandidatesPageModalsProps["handleWSIScreeningComplete"]}
        showWSIInviteModal={showWSIInviteModal}
        setShowWSIInviteModal={setShowWSIInviteModal}
        wsiInviteCandidate={wsiInviteCandidate}
        setWsiInviteCandidate={setWsiInviteCandidate}
        showRubricModal={showRubricModal}
        setShowRubricModal={setShowRubricModal}
        rubricCandidate={rubricCandidate}
        setRubricCandidate={setRubricCandidate}
        rubricEvaluationData={rubricEvaluationData}
        setRubricEvaluationData={setRubricEvaluationData}
        showSendEmailModal={showSendEmailModal}
        setShowSendEmailModal={setShowSendEmailModal}
        emailCandidateSelected={emailCandidateSelected}
        setEmailCandidateSelected={setEmailCandidateSelected}
        showRevealModal={showRevealModal}
        setShowRevealModal={setShowRevealModal}
        revealCandidate={revealCandidate}
        setRevealCandidate={setRevealCandidate}
        handleRevealContact={handleRevealContact as unknown as CandidatesPageModalsProps["handleRevealContact"]}
        revealType={revealType}
        showCVPreviewModal={showCVPreviewModal}
        setShowCVPreviewModal={setShowCVPreviewModal}
        parsedCVData={parsedCVData}
        setParsedCVData={setParsedCVData}
        handleCVConfirmed={handleCVConfirmed as unknown as CandidatesPageModalsProps["handleCVConfirmed"]}
        showCreditConfirmation={showCreditConfirmation}
        setShowCreditConfirmation={setShowCreditConfirmation}
        creditEstimate={creditEstimate as unknown as CandidatesPageModalsProps["creditEstimate"]}
        pearchSearchOptions={pearchSearchOptions as unknown as CandidatesPageModalsProps["pearchSearchOptions"]}
        setPearchSearchOptions={setPearchSearchOptions as unknown as CandidatesPageModalsProps["setPearchSearchOptions"]}
        setPendingSearchRequest={setPendingSearchRequest as unknown as CandidatesPageModalsProps["setPendingSearchRequest"]}
        handleConfirmPearchSearch={handleConfirmPearchSearch}
        showGlobalExpansionConfirm={showGlobalExpansionConfirm}
        setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
        lastSuccessfulQuery={lastSuccessfulQuery}
        localResultsCount={localResultsCount}
        isExpandingToGlobal={isExpandingToGlobal}
        handleExpandToGlobal={handleExpandToGlobal}
        showSourceChangeModal={showSourceChangeModal}
        setShowSourceChangeModal={setShowSourceChangeModal}
        pendingSourceChange={pendingSourceChange as unknown as CandidatesPageModalsProps["pendingSourceChange"]}
        setPendingSourceChange={setPendingSourceChange as unknown as CandidatesPageModalsProps["setPendingSourceChange"]}
        confirmSourceChange={confirmSourceChange}
        showContactFilterModal={showContactFilterModal}
        setShowContactFilterModal={setShowContactFilterModal}
        pendingContactFilter={pendingContactFilter as unknown as CandidatesPageModalsProps["pendingContactFilter"]}
        setPendingContactFilter={setPendingContactFilter as unknown as CandidatesPageModalsProps["setPendingContactFilter"]}
        confirmContactFilterChange={confirmContactFilterChange}
        showSaveAsArchetypeModal={showSaveAsArchetypeModal}
        setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
        searchResults={searchResults}
        isCreatingArchetype={isCreatingArchetype}
        setIsCreatingArchetype={setIsCreatingArchetype}
        archetypeCreationStep={archetypeCreationStep}
        setArchetypeCreationStep={setArchetypeCreationStep as unknown as CandidatesPageModalsProps["setArchetypeCreationStep"]}
        newArchetypeData={newArchetypeData}
        setNewArchetypeData={setNewArchetypeData}
        setUserArchetypes={setUserArchetypes as unknown as CandidatesPageModalsProps["setUserArchetypes"]}
        setChatMessages={setChatMessages as unknown as CandidatesPageModalsProps["setChatMessages"]}
        showAdvancedSearch={showAdvancedSearch}
        setShowAdvancedSearch={setShowAdvancedSearch}
        activeSearchFilters={activeSearchFilters as unknown as CandidatesPageModalsProps["activeSearchFilters"]}
        setActiveSearchFilters={setActiveSearchFilters as unknown as CandidatesPageModalsProps["setActiveSearchFilters"]}
        hideViewedCandidates={hideViewedCandidates as unknown as CandidatesPageModalsProps["hideViewedCandidates"]}
        showAddToListModal={showAddToListModal}
        setShowAddToListModal={setShowAddToListModal}
        addToListCandidateIds={addToListCandidateIds}
        setAddToListCandidateIds={setAddToListCandidateIds}
        addToListCandidateNames={addToListCandidateNames}
        setAddToListCandidateNames={setAddToListCandidateNames}
        showShareSearchModal={showShareSearchModal}
        setShowShareSearchModal={setShowShareSearchModal}
        shareSearchTitle={shareSearchTitle}
        setShareSearchTitle={setShareSearchTitle}
        shareSearchCandidates={shareSearchCandidates}
        setShareSearchCandidates={setShareSearchCandidates as unknown as CandidatesPageModalsProps["setShareSearchCandidates"]}
        showAddListToVacanciesModal={showAddListToVacanciesModal}
        setShowAddListToVacanciesModal={setShowAddListToVacanciesModal}
        selectedListForVacancies={selectedListForVacancies}
        setSelectedListForVacancies={setSelectedListForVacancies as unknown as CandidatesPageModalsProps["setSelectedListForVacancies"]}
        showAddToVacancyModal={showAddToVacancyModal}
        setShowAddToVacancyModal={setShowAddToVacancyModal}
        setSelectedCandidatesForBatch={setSelectedCandidatesForBatch}
        user={user}
        showUnsavedWarningModal={showUnsavedWarningModal}
        setShowUnsavedWarningModal={setShowUnsavedWarningModal}
        setPendingTabChange={setPendingTabChange as unknown as CandidatesPageModalsProps["setPendingTabChange"]}
        handleSaveAllAndExit={handleSaveAllAndExit}
        handleExitWithoutSaving={handleExitWithoutSaving}
        unsavedPearchCandidates={unsavedPearchCandidates as unknown as CandidatesPageModalsProps["unsavedPearchCandidates"]}
        isSavingToBase={isSavingToBase}
        showEditQueryModal={showEditQueryModal}
        setShowEditQueryModal={setShowEditQueryModal}
        editQueryValue={editQueryValue}
        getActiveSearchFiltersCount={getActiveSearchFiltersCount}
        searchSource={searchSource}
        setSearchSource={setSearchSource as unknown as CandidatesPageModalsProps["setSearchSource"]}
        setSearchTerm={setSearchTerm}
        setLastSearchQuery={setLastSearchQuery}
        setLastSearchMode={setLastSearchMode}
        setLastSearchEntities={setLastSearchEntities}
        setLastSearchMetadata={setLastSearchMetadata as unknown as CandidatesPageModalsProps["setLastSearchMetadata"]}
        executeSearch={executeSearch as unknown as CandidatesPageModalsProps["executeSearch"]}
        previewSuggestion={previewSuggestion}
        setPreviewSuggestion={setPreviewSuggestion as unknown as CandidatesPageModalsProps["setPreviewSuggestion"]}
        previewingUserArchetype={previewingUserArchetype}
        setPreviewingUserArchetype={setPreviewingUserArchetype as unknown as CandidatesPageModalsProps["setPreviewingUserArchetype"]}
        buildFiltersFromTags={buildFiltersFromTags as unknown as CandidatesPageModalsProps["buildFiltersFromTags"]}
        setLiaPromptValue={setLiaPromptValue}
        setActiveSearchTab={setActiveSearchTab as unknown as CandidatesPageModalsProps["setActiveSearchTab"]}
        archetypeToDelete={archetypeToDelete}
        setArchetypeToDelete={setArchetypeToDelete as unknown as CandidatesPageModalsProps["setArchetypeToDelete"]}
      />
    </div>
    </ErrorBoundarySection>
    </SearchFingerprintProvider>
  )
}
