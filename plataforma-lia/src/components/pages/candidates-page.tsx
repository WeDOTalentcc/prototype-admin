"use client"

import { FavoritesTab } from "@/components/talent-funnel-tabs/favorites-tab"
import { HistoryTab } from "@/components/talent-funnel-tabs/history-tab"
import { SavedSearchesTab } from "@/components/talent-funnel-tabs/saved-searches-tab"
import { ListsTab } from "@/components/talent-funnel-tabs/lists-tab"
import { CandidateSearchResultsView } from "@/components/pages/candidates/CandidateSearchResultsView"
import type { Candidate } from "@/components/pages/candidates/types"
import { liaApi } from "@/services/lia-api"
import dynamic from "next/dynamic"
import { CandidateSearchBar } from "@/components/pages/candidates/CandidateSearchBar"
import { useCandidatesPageCore } from "./candidates/hooks/useCandidatesPageCore"
import { CandidatesPageHeader } from "@/components/pages/candidates/CandidatesPageHeader"
import { CandidatesPageModals } from "@/components/pages/candidates/CandidatesPageModals"

const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })

export function CandidatesPage({ onAddRecentItem, pendingCandidateOpen, onCandidateOpened }: { onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void; pendingCandidateOpen?: { candidateId: string; candidateName: string } | null; onCandidateOpened?: () => void } = {}) {
  const {
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
    isLIAThinking, isLiaSuperChat, isLoading, isResizingLIA, isSavingToBase, isSearchActive,
    liaWidth, newCertificationFilter, newSoftSkillFilter, parsedCVData, pearchSearchOptions, pendingContactFilter,
    pendingSourceChange, pinnedCandidates, preSelectedListForModal, previewWidth, renderCellValue, revealCandidate,
    revealType, rubricCandidate, rubricEvaluationData, saveCurrentSearch, savedSearches, searchResults,
    selectAllCandidates, selectedCandidateForAction, selectedCandidatesForBatch, selectedListForVacancies, selectedPearchCount, setActiveSearchFilters,
    setActiveSearchTab, setActiveTab, setAddToListCandidateIds, setAddToListCandidateNames, setCandidateListsForModal, setCandidates,
    setChatMessages, setColumnSearchTerm, setColumnWidths, setContactModalAction, setContactModalCandidate, setEmailCandidateSelected,
    setIsLiaSuperChat, setIsLoading, setIsResizingLIA, setLiaWidth, setNewCertificationFilter, setNewSoftSkillFilter,
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
    talentFunnel, toast, toggleTableFilter, unifiedModalCandidate, unifiedModalOpen, unifiedModalType,
    unsavedPearchCandidates, user, visibleCandidates, visibleTableColumns, wsiCandidateForScreening, wsiInviteCandidate,
    tabs,
    archetypeCreationStep, archetypeToDelete, buildFiltersFromTags, crossTabFilter, currentPage, currentSearchSource,
    cvUploadLoading, displayedResultsCount, editQueryValue, isCreatingArchetype, isDroppingCV, isExpandingToGlobal,
    isLoadingMore, isPreviewMaximized, itemsPerPage, lastSearchEntities, lastSearchQuery, lastSuccessfulQuery,
    liaPromptValue, localResultsCount, newArchetypeData, previewCandidate, previewingUserArchetype, previewSuggestion,
    quickFilters, searchSortBy, searchSource, searchTerm, selectedCandidate,
    setArchetypeCreationStep, setArchetypeToDelete, setCurrentPage, setDisplayedResultsCount, setEditQueryValue,
    setHasSearchResults, setIsCreatingArchetype, setLastSearchEntities, setLastSearchMetadata, setLastSearchMode, setLastSearchQuery,
    setLiaPromptValue, setLocalResultsCount, setNewArchetypeData, setPearchResultsCount, setPreviewCandidate, setPreviewingUserArchetype,
    setPreviewSuggestion, setSearchResultsCount, setSearchSortBy, setSearchSource, setSearchTerm, setShowEditQueryModal,
    setShowExpandedLIA, setShowGlobalExpansionConfirm, setShowSaveAsArchetypeModal, setShowSearchResults, setSortBy, setSortOrder,
    setUserArchetypes, setUserCollapsedLIA, setViewingList, showCrossTabBanner, showEditQueryModal, showExpandedLIA,
    showGlobalExpansionConfirm, showSaveAsArchetypeModal, showSearchResults, sortBy, sortOrder, viewingList,
    showCandidatePage, showCandidatePreview,
  } = useCandidatesPageCore({ onAddRecentItem, pendingCandidateOpen, onCandidateOpened })

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-lia-bg-primary overflow-hidden">
      {/* Header Fixo - Título e Tabs */}
      <CandidatesPageHeader
        tabs={tabs}
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
            onDrop={handleCVDrop}
            onDragOver={handleCVDragOver}
            onDragLeave={handleCVDragLeave}
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
              toast({
                title: "Favoritos atualizados",
                description: `${selectedCandidatesForBatch.size} candidato(s) adicionado(s) aos favoritos`
              })
            }}
            onHideBatch={() => {
              selectedCandidatesForBatch.forEach(id => talentFunnel.hideCandidate(id))
              toast({
                title: "Candidatos ocultos",
                description: `${selectedCandidatesForBatch.size} candidato(s) oculto(s) da pesquisa`
              })
              deselectAllCandidates()
            }}
            onSaveToLocalBase={handleSaveToLocalBase}
            isSavingToBase={isSavingToBase}
            showCrossTabBanner={showCrossTabBanner}
            crossTabFilter={crossTabFilter}
            clearCrossTabFilter={clearCrossTabFilter}
            viewingList={viewingList}
            setViewingList={setViewingList}

            setShowSearchResults={setShowSearchResults}
            setSearchTerm={setSearchTerm}
            setLastSearchQuery={setLastSearchQuery}
            setActiveTab={setActiveTab}
            showExpandedLIA={showExpandedLIA}
            isLIAThinking={isLIAThinking}
            liaPromptValue={liaPromptValue}
            setLiaPromptValue={setLiaPromptValue}
            setShowExpandedLIA={setShowExpandedLIA}
            onAICommand={handleAICommand}
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
            isLiaSuperChat={isLiaSuperChat}
            setIsLiaSuperChat={setIsLiaSuperChat}
            liaWidth={liaWidth}
            setLiaWidth={setLiaWidth}
            isResizingLIA={isResizingLIA}
            setIsResizingLIA={setIsResizingLIA}
            activeSearchTab={activeSearchTab}
            setActiveSearchTab={setActiveSearchTab}
            chatMessages={chatMessages}
            setChatMessages={setChatMessages}
            searchResults={searchResults}
            setSearchResults={setSearchResults}
            currentSearchSource={currentSearchSource}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            activeSearchFilters={activeSearchFilters}
            setActiveSearchFilters={setActiveSearchFilters}
            isCreatingArchetype={isCreatingArchetype}
            setIsCreatingArchetype={setIsCreatingArchetype}
            archetypeCreationStep={archetypeCreationStep}
            setArchetypeCreationStep={setArchetypeCreationStep}
            setNewArchetypeData={setNewArchetypeData}
            setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
            setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
            setCandidates={setCandidates}
            setHasSearchResults={setHasSearchResults}
            setSearchResultsCount={setSearchResultsCount}
            setLocalResultsCount={setLocalResultsCount}
            setPearchResultsCount={setPearchResultsCount}
            setDisplayedResultsCount={setDisplayedResultsCount}
            onLIAChatMessage={handleLIAChatMessage}
            onQuickAction={handleQuickAction}
            onCalibrationLike={handleCalibrationLike}
            onCalibrationDislike={handleCalibrationDislike}
            setUserCollapsedLIA={setUserCollapsedLIA}
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
            setTableColumns={setTableColumns}
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
            tableContainerRef={tableContainerRef}
            showSearchResults={showSearchResults}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
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
            toast={toast}
            talentFunnel={talentFunnel}
            setEditQueryValue={setEditQueryValue}
            setShowEditQueryModal={setShowEditQueryModal}
            setShowAddToVacancyModal={setShowAddToVacancyModal}
          />
        )}

        {/* Aba Favoritos */}
        {activeTab === 'favorites' && (
          <div className="flex gap-6">
            <div className={`${showCandidatePreview && previewCandidate ? 'flex-1' : 'w-full'} transition-colors motion-reduce:transition-none duration-300`}>
              <FavoritesTab
                candidates={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))}
                pinnedCandidates={pinnedCandidates}
                favoriteCandidates={favorites}
                favoriteNotes={favoriteNotes}
                onTogglePin={handleTogglePin}
                onToggleFavorite={handleToggleFavorite}
                onCandidateClick={handleCandidateClick}
                onLIAClick={handleLIAClick}
                onUpdateFavoriteNote={handleUpdateFavoriteNote}
              />
            </div>
            
            {/* Candidate Preview - Painel lateral direito */}
            {showCandidatePreview && previewCandidate && (
              <div className="flex-shrink-0 relative" style={{width: `${previewWidth}px`}}>
                <div
                  className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors motion-reduce:transition-none z-10 group"
                  onMouseDown={handlePreviewResize}
                  title="Arraste para redimensionar"
                >
                  <div className="absolute inset-0 -left-1 -right-1"></div>
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-lia-bg-elevated group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors motion-reduce:transition-none"></div>
                </div>
                <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
                  <CandidatePreview
                    candidate={previewCandidate}
                    isOpen={showCandidatePreview}
                    onClose={handleCloseCandidatePreview}
                    isMaximized={isPreviewMaximized}
                    onToggleMaximize={handleTogglePreviewMaximize}
                    candidates={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))}
                    currentIndex={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id)).findIndex(c => c.id === previewCandidate.id)}
                    onNavigateCandidate={(index) => {
                      const favoriteCandidates = candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))
                      if (favoriteCandidates[index]) {
                        setPreviewCandidate(favoriteCandidates[index])
                      }
                    }}
                    onOpenFullPage={handleCandidatePageOpen}
                    onScheduleInterview={(candidate) => {
                      setSelectedCandidateForAction(candidate)
                      setShowScheduleModal(true)
                    }}
                    onAddToVacancy={(candidate) => {
                      setSelectedCandidatesForBatch(new Set([candidate.id]))
                      setShowAddToVacancyModal(true)
                    }}
                    onToggleFavorite={(candidateId) => handleToggleFavorite(candidateId)}
                    onWSIScreening={(candidate) => handleStartWSITextScreening(candidate)}
                    isFavorite={favorites.has(previewCandidate.id)}
                    onSendEmail={(candidate) => handleSendEmail(candidate)}
                    onSendWhatsApp={(candidate) => handleSendWhatsApp(candidate)}
                    onSendTriagem={(candidate) => handleSendTriagem(candidate)}
                    onSendAgendamento={(candidate) => handleSendAgendamento(candidate)}
                    onSendFeedback={(candidate) => handleSendFeedback(candidate)}
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
                
                const mappedCandidates: Candidate[] = listDetails.candidates.items.map((member) => {
                  const c = member.candidate
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
                    workHistory: [],
                  }
                })
                
                setCandidates(mappedCandidates)
                setViewingList({ 
                  id: listDetails.id, 
                  name: listDetails.name, 
                  color: listDetails.color 
                })
                setActiveTab('search')
                setShowSearchResults(true)
                setDisplayedResultsCount(10)
                setLastSearchQuery(`Lista: ${listDetails.name}`)
                
                toast({
                  title: "Lista carregada",
                  description: `Exibindo ${mappedCandidates.length} candidatos da lista "${listDetails.name}"`,
                })
              } catch (error) {
                toast({
                  title: "Erro ao carregar lista",
                  description: error instanceof Error ? error.message : "Não foi possível carregar os candidatos da lista.",
                  variant: "destructive"
                })
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
                toast({
                  title: "Erro ao carregar lista",
                  description: err.message,
                  variant: "destructive"
                })
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
        contactModalCandidate={contactModalCandidate}
        showContactModal={showContactModal}
        contactModalAction={contactModalAction}
        setShowContactModal={setShowContactModal}
        setSelectedCandidateForAction={setSelectedCandidateForAction}
        setContactModalCandidate={setContactModalCandidate}
        setContactModalAction={setContactModalAction}
        handleSendMessage={handleSendMessage}
        showScheduleModal={showScheduleModal}
        setShowScheduleModal={setShowScheduleModal}
        handleScheduleComplete={handleScheduleComplete}
        unifiedModalOpen={unifiedModalOpen}
        unifiedModalCandidate={unifiedModalCandidate}
        unifiedModalType={unifiedModalType}
        lastSearchQuery={lastSearchQuery}
        handleUnifiedModalClose={handleUnifiedModalClose}
        handleUnifiedModalSend={handleUnifiedModalSend}
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
        handleAddCandidate={handleAddCandidate}
        setCandidateListsForModal={setCandidateListsForModal}
        bulkJobVacancies={bulkJobVacancies}
        candidateListsForModal={candidateListsForModal}
        handleCandidatePageOpen={handleCandidatePageOpen}
        showBatchApproval={showBatchApproval}
        setShowBatchApproval={setShowBatchApproval}
        convertCandidatesForBatch={convertCandidatesForBatch}
        handleBatchApprovalComplete={handleBatchApprovalComplete}
        wsiCandidateForScreening={wsiCandidateForScreening}
        setWsiCandidateForScreening={setWsiCandidateForScreening}
        showWSITextModal={showWSITextModal}
        setShowWSITextModal={setShowWSITextModal}
        showWSIVoiceModal={showWSIVoiceModal}
        setShowWSIVoiceModal={setShowWSIVoiceModal}
        handleWSIScreeningComplete={handleWSIScreeningComplete}
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
        toast={toast}
        showSendEmailModal={showSendEmailModal}
        setShowSendEmailModal={setShowSendEmailModal}
        emailCandidateSelected={emailCandidateSelected}
        setEmailCandidateSelected={setEmailCandidateSelected}
        showRevealModal={showRevealModal}
        setShowRevealModal={setShowRevealModal}
        revealCandidate={revealCandidate}
        setRevealCandidate={setRevealCandidate}
        handleRevealContact={handleRevealContact}
        revealType={revealType}
        showCVPreviewModal={showCVPreviewModal}
        setShowCVPreviewModal={setShowCVPreviewModal}
        parsedCVData={parsedCVData}
        setParsedCVData={setParsedCVData}
        handleCVConfirmed={handleCVConfirmed}
        showCreditConfirmation={showCreditConfirmation}
        setShowCreditConfirmation={setShowCreditConfirmation}
        creditEstimate={creditEstimate}
        pearchSearchOptions={pearchSearchOptions}
        setPearchSearchOptions={setPearchSearchOptions}
        setPendingSearchRequest={setPendingSearchRequest}
        handleConfirmPearchSearch={handleConfirmPearchSearch}
        showGlobalExpansionConfirm={showGlobalExpansionConfirm}
        setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
        lastSuccessfulQuery={lastSuccessfulQuery}
        localResultsCount={localResultsCount}
        isExpandingToGlobal={isExpandingToGlobal}
        handleExpandToGlobal={handleExpandToGlobal}
        showSourceChangeModal={showSourceChangeModal}
        setShowSourceChangeModal={setShowSourceChangeModal}
        pendingSourceChange={pendingSourceChange}
        setPendingSourceChange={setPendingSourceChange}
        confirmSourceChange={confirmSourceChange}
        showContactFilterModal={showContactFilterModal}
        setShowContactFilterModal={setShowContactFilterModal}
        pendingContactFilter={pendingContactFilter}
        setPendingContactFilter={setPendingContactFilter}
        confirmContactFilterChange={confirmContactFilterChange}
        showSaveAsArchetypeModal={showSaveAsArchetypeModal}
        setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
        searchResults={searchResults}
        isCreatingArchetype={isCreatingArchetype}
        setIsCreatingArchetype={setIsCreatingArchetype}
        archetypeCreationStep={archetypeCreationStep}
        setArchetypeCreationStep={setArchetypeCreationStep}
        newArchetypeData={newArchetypeData}
        setNewArchetypeData={setNewArchetypeData}
        setUserArchetypes={setUserArchetypes}
        setChatMessages={setChatMessages}
        showAdvancedSearch={showAdvancedSearch}
        setShowAdvancedSearch={setShowAdvancedSearch}
        activeSearchFilters={activeSearchFilters}
        setActiveSearchFilters={setActiveSearchFilters}
        hideViewedCandidates={hideViewedCandidates}
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
        setShareSearchCandidates={setShareSearchCandidates}
        showAddListToVacanciesModal={showAddListToVacanciesModal}
        setShowAddListToVacanciesModal={setShowAddListToVacanciesModal}
        selectedListForVacancies={selectedListForVacancies}
        setSelectedListForVacancies={setSelectedListForVacancies}
        showAddToVacancyModal={showAddToVacancyModal}
        setShowAddToVacancyModal={setShowAddToVacancyModal}
        setSelectedCandidatesForBatch={setSelectedCandidatesForBatch}
        user={user}
        showUnsavedWarningModal={showUnsavedWarningModal}
        setShowUnsavedWarningModal={setShowUnsavedWarningModal}
        setPendingTabChange={setPendingTabChange}
        handleSaveAllAndExit={handleSaveAllAndExit}
        handleExitWithoutSaving={handleExitWithoutSaving}
        unsavedPearchCandidates={unsavedPearchCandidates}
        isSavingToBase={isSavingToBase}
        showEditQueryModal={showEditQueryModal}
        setShowEditQueryModal={setShowEditQueryModal}
        editQueryValue={editQueryValue}
        getActiveSearchFiltersCount={getActiveSearchFiltersCount}
        searchSource={searchSource}
        setSearchSource={setSearchSource}
        setSearchTerm={setSearchTerm}
        setLastSearchQuery={setLastSearchQuery}
        setLastSearchMode={setLastSearchMode}
        setLastSearchEntities={setLastSearchEntities}
        setLastSearchMetadata={setLastSearchMetadata}
        executeSearch={executeSearch}
        previewSuggestion={previewSuggestion}
        setPreviewSuggestion={setPreviewSuggestion}
        previewingUserArchetype={previewingUserArchetype}
        setPreviewingUserArchetype={setPreviewingUserArchetype}
        buildFiltersFromTags={buildFiltersFromTags}
        setLiaPromptValue={setLiaPromptValue}
        setActiveSearchTab={setActiveSearchTab}
        archetypeToDelete={archetypeToDelete}
        setArchetypeToDelete={setArchetypeToDelete}
      />
    </div>
  )
}
