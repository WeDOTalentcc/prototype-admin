"use client"

import { Button } from "@/components/ui/button"
import {
  Users, Plus, Search, X, Eye, Star, Check,
  Pin, MapPin, Linkedin, CheckCircle, Filter, ArrowUpDown,
  ArrowUp, ArrowDown, ChevronsLeftRight, Target, User,
  Bookmark, Play, Edit, BarChart3, PieChart, Zap, Brain,
  Calendar, Clock, TrendingUp, Building, AlertCircle, DollarSign,
  Briefcase, ArrowLeft, Mail, Phone, MessageSquare, Github, Code, Layers, FileText, Globe, Home, Send, Lightbulb, Mic, Paperclip, Download, FileUp, GripVertical,
  Settings, GraduationCap, HelpCircle, Loader2, Crown, Rocket, Copy, List, Scale, ChevronRight,
  Maximize2, Minimize2, PanelLeftClose, PanelLeft, ChevronDown
} from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BatchApprovalModal } from "@/components/batch-approval-modal"
import { RubricEvaluationModal } from "@/components/rubric-evaluation-modal"
import { NewCandidateUnifiedModal } from "@/components/modals/new-candidate-unified-modal"
import { ContactModal, ScheduleModal } from "@/components/quick-actions-modals"
import { GlobalExpansionConfirmModal } from "@/components/pages/candidates/GlobalExpansionConfirmModal"
import { SourceChangeConfirmModal } from "@/components/pages/candidates/SourceChangeConfirmModal"
import { ContactFilterConfirmModal } from "@/components/pages/candidates/ContactFilterConfirmModal"
import { DeleteArchetypeModal } from "@/components/pages/candidates/DeleteArchetypeModal"
import { UnifiedCommunicationModal, type CommunicationType } from "@/components/modals/unified-communication-modal"
import { CandidateComparison } from "@/components/candidate-comparison"
import { FavoritesTab } from "@/components/talent-funnel-tabs/favorites-tab"
import { HistoryTab } from "@/components/talent-funnel-tabs/history-tab"
import { SavedSearchesTab } from "@/components/talent-funnel-tabs/saved-searches-tab"
import { ListsTab } from "@/components/talent-funnel-tabs/lists-tab"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { ShareSearchModal } from "@/components/modals/share-search-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { AddListToVacanciesModal } from "@/components/modals/add-list-to-vacancies-modal"
import { UnsavedPearchWarningModal } from "@/components/modals/unsaved-pearch-warning-modal"
import { WSITextScreeningModal, WSIVoiceScreeningStatus, WSIScorecard } from "@/components/wsi"
import { WSITriagemInviteModal } from "@/components/wsi/wsi-triagem-invite-modal"
import { SendEmailModal } from "@/components/email-templates"
import { CVPreview, type ParsedCVResponse } from "@/components/cv"
import type { TableColumn, TableSortConfig } from "@/components/tables/types"
import { RevealCreditsModal } from "@/components/reveal-credits-modal"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { CandidateTabs } from "@/components/pages/candidates/CandidateTabs"
import { CandidateSearchResultsView } from "@/components/pages/candidates/CandidateSearchResultsView"
import type { Candidate } from "@/components/pages/candidates/types"
import { CreditConfirmationModal } from "@/components/pages/candidates/CreditConfirmationModal"
import { SaveAsArchetypeModal } from "@/components/pages/candidates/SaveAsArchetypeModal"
import { EditQueryModal } from "@/components/pages/candidates/EditQueryModal"
import { PreviewSuggestionModal } from "@/components/pages/candidates/PreviewSuggestionModal"

import { liaApi } from "@/services/lia-api"
import dynamic from "next/dynamic"
import { CandidateSearchBar } from "@/components/pages/candidates/CandidateSearchBar"
import { useCandidatesPageCore } from "./candidates/hooks/useCandidatesPageCore"

const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const AdvancedFiltersModal = dynamic(() => import("@/components/search/advanced-filters-modal").then(m => ({ default: m.AdvancedFiltersModal })), { ssr: false })

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
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden">
      {/* Header Fixo - Título e Tabs */}
      <div className="flex-shrink-0 px-4 pt-3 pb-0 bg-gray-50 dark:bg-gray-950">
        {/* Header Principal - Padrão Gestão de Vagas */}
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
                <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                Funil de Talentos
              </h1>
            </div>
          </div>
          <div className="flex gap-2">
            {/* Botão Novo Candidato - visível em todas as abas */}
            <Button
              className="gap-2 h-8 px-3 font-medium"
             
              onClick={() => setShowAddCandidateModal(true)}
            >
              <Plus className="w-4 h-4" />
              Novo Candidato
            </Button>

            {/* Botões específicos por aba */}
            {activeTab === 'search' && showSearchResults && (
              <>
                <Button
                  variant="outline"
                  className="gap-2 h-8 px-3"
                  onClick={() => {
                    setShowSearchResults(false)
                    setSearchTerm('')
                    setLastSearchQuery('')
                  }}
                >
                  <Search className="w-4 h-4" />
                  Nova Busca
                </Button>

                {/* Botão para salvar busca atual */}
                {(searchTerm || quickFilters.size > 0 || getActiveAdvancedFiltersCount() > 0) && (
                  <Button
                    variant="outline"
                    className="gap-2 h-8 px-3"
                    onClick={saveCurrentSearch}
                    title="Salvar esta busca para reutilizar"
                  >
                    <Bookmark className="w-4 h-4" />
                    Salvar Busca
                  </Button>
                )}
              </>
            )}

            {activeTab === 'favorites' && (
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={() => setActiveTab('search')}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>
            )}

            {activeTab === 'history' && (
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={() => setActiveTab('search')}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>
            )}

            {activeTab === 'saved-searches' && (
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={() => setActiveTab('search')}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>
            )}
          </div>
        </div>

        {/* Sistema de Abas - extraído para CandidateTabs (Sprint F5) */}
        <CandidateTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={handleTabChangeWithWarning}
        />
      </div>

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
            <div className={`${showCandidatePreview && previewCandidate ? 'flex-1' : 'w-full'} transition-all duration-300`}>
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
                  className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors z-10 group"
                  onMouseDown={handlePreviewResize}
                  title="Arraste para redimensionar"
                >
                  <div className="absolute inset-0 -left-1 -right-1"></div>
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-gray-600 group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors"></div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 h-[calc(100vh-6rem)] overflow-hidden">
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
              // Re-executar a busca do histórico
              setSearchTerm(historyItem.query)
              setLastSearchQuery(historyItem.query)
              setLastSearchMode(historyItem.mode || 'natural')
              if (historyItem.source) {
                setSearchSource(historyItem.source)
              }
              setActiveTab('search')
              // Trigger busca automática após um pequeno delay
              setTimeout(() => {
                setShowSearchResults(false) // Reset para mostrar a tela de busca
              }, 100)
            }}
            onSaveAsSearch={(historyItem, name, description) => {
              // Salvar busca usando o hook centralizado
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
              // Executar busca salva
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

      {/* Modals */}
      
      {/* Contact Modal */}
      {(selectedCandidateForAction || contactModalCandidate) && (
        <ContactModal
          isOpen={showContactModal}
          onClose={() => {
            setShowContactModal(false)
            setSelectedCandidateForAction(null)
            setContactModalCandidate(null)
            setContactModalAction('general')
          }}
          candidate={(() => {
            const c = contactModalCandidate || selectedCandidateForAction
            if (!c) return null
            return {
              id: c.id,
              name: c.name,
              role: c.position || c.role,
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score || 0,
              status: c.status || 'Novo',
              matchPercentage: c.liaAnalysis?.score || c.matchPercentage || c.score || 0,
              riskLevel: 'low',
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience || ''),
              seniority: c.seniority || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected?.toString() || '',
              preferredLocation: c.location,
              linkedin: c.linkedin,
              skills: c.skills || [],
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }
          })()}
          onSend={handleSendMessage}
          initialAction={contactModalAction}
        />
      )}

      {/* Schedule Modal */}
      {selectedCandidateForAction && (
        <ScheduleModal
          isOpen={showScheduleModal}
          onClose={() => {
            setShowScheduleModal(false)
            setSelectedCandidateForAction(null)
          }}
          candidate={{
            id: selectedCandidateForAction.id,
            name: selectedCandidateForAction.name,
            role: selectedCandidateForAction.position,
            email: selectedCandidateForAction.email,
            phone: selectedCandidateForAction.phone,
            location: selectedCandidateForAction.location,
            avatar: selectedCandidateForAction.avatar,
            score: selectedCandidateForAction.score,
            status: selectedCandidateForAction.status,
            matchPercentage: selectedCandidateForAction.liaAnalysis?.score || selectedCandidateForAction.score,
            riskLevel: 'low',
            culturalFit: 85,
            technicalMatch: 90,
            experience: String(selectedCandidateForAction.experience),
            seniority: selectedCandidateForAction.seniority || 'Pleno',
            availability: 'Imediata',
            expectedSalary: selectedCandidateForAction.salary?.expected?.toString() || '',
            preferredLocation: selectedCandidateForAction.location,
            linkedin: selectedCandidateForAction.linkedin,
            skills: selectedCandidateForAction.skills,
            lastActivity: new Date().toISOString(),
            source: 'internal'
          }}
          onSchedule={handleScheduleComplete}
        />
      )}

      {/* Unified Communication Modal - New standardized modal for all communication types */}
      <UnifiedCommunicationModal
        isOpen={unifiedModalOpen}
        onClose={handleUnifiedModalClose}
        candidate={unifiedModalCandidate ? {
          id: unifiedModalCandidate.id,
          name: unifiedModalCandidate.name,
          role: unifiedModalCandidate.position || unifiedModalCandidate.current_title || '',
          email: unifiedModalCandidate.email,
          phone: unifiedModalCandidate.phone,
          location: unifiedModalCandidate.location,
          avatar: unifiedModalCandidate.avatar,
          score: unifiedModalCandidate.score,
          matchPercentage: unifiedModalCandidate.liaAnalysis?.score || unifiedModalCandidate.score,
          skills: unifiedModalCandidate.skills
        } : null}
        type={unifiedModalType}
        jobTitle={lastSearchQuery || undefined}
        onSend={handleUnifiedModalSend}
        // TODO: Replace 'demo' with actual company_id from auth context when authentication is implemented.
        // This is required for proper multi-tenancy support.
        companyId="demo"
      />

      {/* Candidate Comparison Modal */}
      {showComparisonModal && selectedCandidatesForBatch.size >= 2 && (
        <CandidateComparison
          isOpen={showComparisonModal}
          onClose={() => setShowComparisonModal(false)}
          candidates={sortedCandidates
            .filter(c => selectedCandidatesForBatch.has(c.id))
            .map(c => ({
              id: c.id,
              name: c.name,
              role: c.position,
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score,
              status: c.status,
              matchPercentage: c.liaAnalysis?.score || c.score,
              riskLevel: 'low',
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience),
              seniority: c.seniority || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected?.toString() || '',
              skills: c.skills,
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }))}
          onSelectCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleNavigateToFullProfile(candidate)
          }}
          onScheduleInterview={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleScheduleInterview(candidate)
          }}
          onContactCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleContactCandidate(candidate)
          }}
        />
      )}

      {/* Candidate Page Modal */}
      {showCandidatePage && selectedCandidate && (
        <CandidatePage
          candidate={selectedCandidate}
          isOpen={showCandidatePage}
          onClose={handleCloseCandidatePage}
          onBackToKanban={() => {}}
        />
      )}

      {/* New Candidate Unified Modal - AI-first experience */}
      <NewCandidateUnifiedModal
        key={`modal-${preSelectedListForModal?.id || 'default'}`}
        isOpen={showAddCandidateModal}
        onClose={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
        }}
        onCandidateAdded={(candidate) => {
          handleAddCandidate(candidate)
          // Reload lists if a list was pre-selected
          if (preSelectedListForModal) {
            liaApi.getCandidateLists({ limit: 50 }).then(response => {
              if (response.items) {
                setCandidateListsForModal(response.items.map(list => ({
                  id: list.id,
                  name: list.name,
                  color: list.color
                })))
              }
            }).catch(() => {})
          }
        }}
        jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title, department: j.department, location: j.location }))}
        candidateLists={candidateListsForModal}
        preSelectedListId={preSelectedListForModal?.id}
        preSelectedListName={preSelectedListForModal?.name}
        onGoToSearch={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
          setActiveTab('search')
        }}
        onOpenFullProfile={(candidateId) => {
          const candidate = candidates.find(c => c.id === candidateId)
          if (candidate) {
            handleCandidatePageOpen(candidate)
          }
        }}
      />

      {/* Batch Approval Modal */}
      {showBatchApproval && (
        <BatchApprovalModal
          candidates={convertCandidatesForBatch(candidates.filter(c => selectedCandidatesForBatch.has(c.id)))}
          isOpen={showBatchApproval}
          onClose={() => setShowBatchApproval(false)}
          onApprovalComplete={handleBatchApprovalComplete}
        />
      )}

      {/* WSI Text Screening Modal */}
      {wsiCandidateForScreening && (
        <WSITextScreeningModal
          isOpen={showWSITextModal}
          onClose={() => {
            setShowWSITextModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            avatar: wsiCandidateForScreening.avatar,
            position: wsiCandidateForScreening.position
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || 'Vaga atual'
          }}
          onComplete={handleWSIScreeningComplete}
        />
      )}

      {/* WSI Voice Screening Modal */}
      {wsiCandidateForScreening && (
        <WSIVoiceScreeningStatus
          isOpen={showWSIVoiceModal}
          onClose={() => {
            setShowWSIVoiceModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            phone: wsiCandidateForScreening.phone
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || 'Vaga atual'
          }}
          onComplete={handleWSIScreeningComplete}
          autoStart={true}
        />
      )}

      {/* WSI Triagem Invite Modal */}
      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate ? {
          id: wsiInviteCandidate.id,
          name: wsiInviteCandidate.name,
          role: wsiInviteCandidate.position,
          email: wsiInviteCandidate.email,
          phone: wsiInviteCandidate.phone,
          location: wsiInviteCandidate.location,
          avatar: wsiInviteCandidate.avatar
        } : null}
        jobTitle={wsiInviteCandidate?.position || 'Vaga'}
        onSend={async (data) => {
          try {
            if (data.channel === 'email' && wsiInviteCandidate?.email) {
              await liaApi.sendEmail('wsi-triagem-invite', {
                recipient_email: wsiInviteCandidate.email,
                recipient_name: wsiInviteCandidate.name,
                candidate_id: wsiInviteCandidate.id,
                subject_override: data.subject || `Convite para Triagem - ${wsiInviteCandidate.position || 'Vaga'}`,
                body_override: data.message,
                variables: {
                  candidate_name: wsiInviteCandidate.name,
                  job_title: wsiInviteCandidate.position || 'Vaga'
                }
              })
            }
            
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          } catch (error) {
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          }
        }}
      />

      {/* Rubric Evaluation Modal - Análise LIA */}
      <RubricEvaluationModal
        isOpen={showRubricModal}
        onClose={() => {
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        evaluation={rubricEvaluationData}
        candidateId={rubricCandidate?.id || ''}
        candidateName={rubricCandidate?.name}
        jobId=""
        onApprove={async () => {
          toast({
            title: "Candidato aprovado",
            description: `${rubricCandidate?.name} foi aprovado com sucesso`
          })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        onReject={async () => {
          toast({
            title: "Candidato reprovado",
            description: `${rubricCandidate?.name} foi reprovado`
          })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
      />

      {/* Send Email Modal */}
      <SendEmailModal
        isOpen={showSendEmailModal}
        onClose={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
        candidate={emailCandidateSelected ? {
          id: emailCandidateSelected.id,
          name: emailCandidateSelected.name,
          email: emailCandidateSelected.email,
          phone: emailCandidateSelected.phone,
          current_title: emailCandidateSelected.position,
          technical_skills: emailCandidateSelected.skills,
          source: 'internal',
          is_active: true,
          is_remote: emailCandidateSelected.workModel === 'remoto',
          willing_to_relocate: false,
          tags: emailCandidateSelected.tags,
          status: emailCandidateSelected.status,
          lia_insights: {},
          soft_skills: [],
          languages: {},
          certifications: []
        } : null}
        onSuccess={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
      />

      {/* Reveal Contact Modal */}
      {revealCandidate && (
        <RevealCreditsModal
          isOpen={showRevealModal}
          onClose={() => {
            setShowRevealModal(false)
            setRevealCandidate(null)
          }}
          onConfirm={handleRevealContact}
          revealType={revealType}
          candidateName={revealCandidate.name}
          creditsRequired={revealType === 'email' ? 2 : 14}
        />
      )}

      {/* CV Preview Modal (legado - mantido para compatibilidade) */}
      {parsedCVData && (
        <CVPreview
          isOpen={showCVPreviewModal}
          onClose={() => {
            setShowCVPreviewModal(false)
            setParsedCVData(null)
          }}
          parsedData={parsedCVData}
          onConfirm={handleCVConfirmed}
          jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title }))}
        />
      )}

      {/* Bulk Actions Bar removido - ações agora aparecem no chat da LIA */}

      {/* Modal de Confirmação de Créditos Base Global */}
      <CreditConfirmationModal
        open={showCreditConfirmation}
        onOpenChange={setShowCreditConfirmation}
        creditEstimate={creditEstimate}
        pearchSearchOptions={pearchSearchOptions}
        onSearchOptionsChange={setPearchSearchOptions}
        onCancel={() => {
          setShowCreditConfirmation(false)
          setPendingSearchRequest(null)
        }}
        onConfirm={handleConfirmPearchSearch}
      />

      {/* Modal de Confirmação para Expansão Global */}
      <GlobalExpansionConfirmModal
        open={showGlobalExpansionConfirm}
        onOpenChange={setShowGlobalExpansionConfirm}
        lastSuccessfulQuery={lastSuccessfulQuery}
        lastSearchQuery={lastSearchQuery}
        localResultsCount={localResultsCount}
        isExpandingToGlobal={isExpandingToGlobal}
        onConfirm={handleExpandToGlobal}
      />

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <SourceChangeConfirmModal
        open={showSourceChangeModal}
        onOpenChange={setShowSourceChangeModal}
        pendingSourceChange={pendingSourceChange}
        onCancel={() => { setShowSourceChangeModal(false); setPendingSourceChange(null) }}
        onConfirm={confirmSourceChange}
      />

      {/* Modal de Confirmação para Filtro de Contato (Email/Telefone) */}
      <ContactFilterConfirmModal
        open={showContactFilterModal}
        onOpenChange={setShowContactFilterModal}
        pendingContactFilter={pendingContactFilter}
        onCancel={() => { setShowContactFilterModal(false); setPendingContactFilter(null) }}
        onConfirm={confirmContactFilterChange}
      />

      {/* Advanced Filters Modal */}
      {/* Modal de Filtros Avançados removido - agora usa painel lateral */}

      {/* Modal Salvar como Arquétipo */}
      <SaveAsArchetypeModal
        open={showSaveAsArchetypeModal}
        onOpenChange={setShowSaveAsArchetypeModal}
        currentQuery={lastSuccessfulQuery || searchResults.query || ''}
        isCreatingArchetype={isCreatingArchetype}
        newArchetypeData={newArchetypeData}
        onClose={() => {
          if (isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
        onSave={(archetype, message) => {
          setUserArchetypes(prev => [...prev, archetype])
          setShowSaveAsArchetypeModal(false)
          setChatMessages(prev => [...prev, message])
          if (isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
      />

      {/* Advanced Filters Modal */}
      <AdvancedFiltersModal
        isOpen={showAdvancedSearch}
        onClose={() => setShowAdvancedSearch(false)}
        onApply={(filters) => {
          setActiveSearchFilters(filters)
          setShowAdvancedSearch(false)
          
          // Sync hide viewed candidates filter to the hook
          const hideScope = filters.general?.hideViewedScope || "dont_hide"
          const hidePeriod = filters.general?.hideViewedPeriod || "all_time"
          hideViewedCandidates.setScope(hideScope)
          hideViewedCandidates.setPeriod(hidePeriod)
          
          // Fetch viewed candidates if filter is enabled
          if (hideScope !== "dont_hide") {
            hideViewedCandidates.fetchViewedCandidates()
          }
        }}
        initialFilters={activeSearchFilters}
        estimatedMatches={1000000}
      />

      {/* Add to List Modal */}
      <AddToListModal
        isOpen={showAddToListModal}
        onClose={() => {
          setShowAddToListModal(false)
          setAddToListCandidateIds([])
          setAddToListCandidateNames([])
        }}
        candidateIds={addToListCandidateIds}
        candidateNames={addToListCandidateNames}
        onSuccess={() => {
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à lista"
          })
        }}
      />

      {/* Share Search Modal */}
      <ShareSearchModal
        open={showShareSearchModal}
        onClose={() => {
          setShowShareSearchModal(false)
          setShareSearchCandidates([])
          setShareSearchTitle('')
        }}
        shareType="search"
        title={shareSearchTitle}
        candidateIds={shareSearchCandidates.map(c => c.id)}
        candidateCount={shareSearchCandidates.length}
        sourceQuery={lastSearchQuery || undefined}
      />

      {/* Add List to Vacancies Modal */}
      {selectedListForVacancies && (
        <AddListToVacanciesModal
          isOpen={showAddListToVacanciesModal}
          onClose={() => {
            setShowAddListToVacanciesModal(false)
            setSelectedListForVacancies(null)
          }}
          listId={selectedListForVacancies.id}
          listName={selectedListForVacancies.name}
          candidateCount={selectedListForVacancies.candidateCount}
          onSuccess={() => {
            toast({
              title: "Sucesso",
              description: "Candidatos adicionados às vagas selecionadas"
            })
          }}
        />
      )}

      {/* Add Candidates to Vacancy Modal */}
      <AddCandidatesToVacancyModal
        isOpen={showAddToVacancyModal}
        onClose={() => setShowAddToVacancyModal(false)}
        candidateIds={Array.from(selectedCandidatesForBatch)}
        candidateNames={candidates.filter(c => selectedCandidatesForBatch.has(c.id)).map(c => c.name)}
        currentRecruiterEmail={user?.email}
        onSuccess={() => {
          setSelectedCandidatesForBatch(new Set())
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à vaga"
          })
        }}
      />

      {/* Modal de aviso de candidatos Pearch não salvos */}
      <UnsavedPearchWarningModal
        isOpen={showUnsavedWarningModal}
        onClose={() => {
          setShowUnsavedWarningModal(false)
          setPendingTabChange(null)
        }}
        onSaveAndExit={handleSaveAllAndExit}
        onExitWithoutSaving={handleExitWithoutSaving}
        unsavedCount={unsavedPearchCandidates.length}
        unsavedCandidates={unsavedPearchCandidates}
        isSaving={isSavingToBase}
      />

      {/* Modal de Edição de Query - Centralizado na tela */}
      {/* Modal de Edição de Busca */}
      <EditQueryModal
        isOpen={showEditQueryModal}
        onClose={() => setShowEditQueryModal(false)}
        initialValue={editQueryValue}
        activeFiltersCount={getActiveSearchFiltersCount()}
        searchSource={searchSource}
        onSearchSourceChange={setSearchSource}
        pearchSearchOptions={pearchSearchOptions}
        onPearchOptionsChange={setPearchSearchOptions}
        onOpenFilters={() => setShowAdvancedSearch(true)}
        onSubmitNatural={async (query, entities, mode, metadata) => {
          setSearchTerm(query)
          setLastSearchQuery(query)
          setLastSearchMode(mode || 'natural')
          setLastSearchEntities(entities)
          setLastSearchMetadata(metadata)
          await executeSearch(query, entities, mode || 'natural', metadata, false)
        }}
        onSubmitAI={async (query) => {
          setSearchTerm(query)
          setLastSearchQuery(query)
          setLastSearchMode('ai-natural')
          setLastSearchEntities(null)
          await executeSearch(query, null, 'ai-natural', undefined, false)
        }}
      />

      {/* Modal de Preview de Sugestão IA */}
      <PreviewSuggestionModal
        previewSuggestion={previewSuggestion}
        previewingUserArchetype={previewingUserArchetype}
        onClose={() => {
          setPreviewSuggestion(null)
          setPreviewingUserArchetype(null)
        }}
        buildFiltersFromTags={buildFiltersFromTags}
        onUpdateArchetype={(id, updates) => {
          setUserArchetypes(prev => prev.map(a =>
            a.id === id ? { ...a, ...updates } : a
          ))
        }}
        onSaveArchetype={(newArchetype) => setUserArchetypes(prev => [...prev, newArchetype as Record<string, unknown>])}
        onExecuteSearch={async (query, filters, mode, metadata, usePearch) => {
          await executeSearch(query, filters as Record<string, unknown>, mode as string, metadata as Record<string, unknown>, usePearch)
        }}
        onSetLiaPromptValue={setLiaPromptValue}
        onSetActiveSearchTab={setActiveSearchTab}
      />

      {/* Modal de Confirmação de Exclusão de Arquétipo */}
      <DeleteArchetypeModal
        archetypeToDelete={archetypeToDelete}
        onClose={() => setArchetypeToDelete(null)}
        onDeleted={(id) => setUserArchetypes(prev => prev.filter(a => a.id !== id))}
      />

    </div>
  )
}

