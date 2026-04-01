"use client"

import React, { useRef } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import {
  Users, X, Building, Target, List, ArrowLeft,
  Brain, Send, Maximize2, ArrowUpDown, CheckCircle,
  ChevronsLeftRight, Search, Check, Globe, ChevronRight,
  ChevronDown, Loader2
} from "lucide-react"
import { SearchResultsHeader } from "./SearchResultsHeader"
import { CrossTabFilterBanner } from "./CrossTabFilterBanner"
import { ViewingListBanner } from "./ViewingListBanner"
import { ColumnConfigSidebar } from "./ColumnConfigSidebar"
import { CandidatesLoadMoreFooter } from "./CandidatesLoadMoreFooter"
import { ContextualActionsBanner } from "@/components/contextual-actions-banner"
import { LIASearchSidebar } from "./LIASearchSidebar"
import { CandidatesFilterPanel } from "./CandidatesFilterPanel"
import { UnifiedCandidateTable } from "@/components/tables"
import type { TableCandidate } from "@/components/tables"
import type { Candidate } from "./types"
import type { TableFilters } from "@/hooks/use-candidate-filters"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { CalibrationCandidate } from "@/components/calibration-card"
import dynamic from "next/dynamic"

const CandidatePreview = dynamic(
  () => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })),
  { ssr: false }
)

import type { SearchTab, ChatMessage, TableColumn } from "./CandidateSearchResultsView.types"

export interface CandidateSearchResultsViewProps {
  // Search query state
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  // Back / modal openers
  onBack: () => void
  onOpenEditQueryModal: (value: string) => void
  onOpenAdvancedSearch: () => void
  // Contextual actions banner
  selectedCandidatesForBatch: Set<string>
  selectedPearchCount: number
  deselectAllCandidates: () => void
  onAddToVacancy: () => void
  onAddToList: () => void
  isAddingToList: boolean
  candidates: Candidate[]
  onShareSearch: () => void
  onBulkEmail: () => void
  onBulkWSIScreening: () => void
  onToggleFavoriteBatch: () => void
  onHideBatch: () => void
  onSaveToLocalBase: () => void
  isSavingToBase: boolean
  // Cross-tab banner
  showCrossTabBanner: boolean
  crossTabFilter: Record<string, unknown>
  clearCrossTabFilter: () => void
  // Viewing list banner
  viewingList: { id: string; name: string; color?: string } | null
  setViewingList: (value: null) => void
  setShowSearchResults: (value: boolean) => void
  setSearchTerm: (value: string) => void
  setLastSearchQuery: (value: string) => void
  setActiveTab: (tab: string) => void
  // Compact LIA prompt
  showExpandedLIA: boolean
  isLIAThinking: boolean
  liaPromptValue: string
  setLiaPromptValue: (value: string) => void
  setShowExpandedLIA: (value: boolean) => void
  onAICommand: (cmd: string) => void
  // Controls bar
  searchSortBy: string
  setSearchSortBy: (value: string) => void
  sortedCandidates: Candidate[]
  selectAllCandidates: () => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (value: boolean) => void
  getActiveTableFiltersCount: () => number
  showColumnConfig: boolean
  onToggleColumnConfig: () => void
  tableColumns: TableColumn[]
  // Active filters badge
  quickFilters: Set<string>
  searchTerm: string
  getActiveAdvancedFiltersCount: () => number
  // LIA Sidebar
  isLiaSuperChat: boolean
  setIsLiaSuperChat: (value: boolean) => void
  liaWidth: number
  setLiaWidth: (value: number) => void
  isResizingLIA: boolean
  setIsResizingLIA: (value: boolean) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (tab: SearchTab) => void
  chatMessages: ChatMessage[]
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
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
  setSearchResults: React.Dispatch<React.SetStateAction<{
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }>>
  currentSearchSource: string
  searchSource: string
  pearchSearchOptions: {
    searchType: 'fast' | 'pro'
    limit: number
    showEmails: boolean
    showPhoneNumbers: boolean
    highFreshness: boolean
    requireEmails: boolean
    requirePhoneNumbers: boolean
  }
  activeSearchFilters: SearchFilters
  setActiveSearchFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  isCreatingArchetype: boolean
  setIsCreatingArchetype: (value: boolean) => void
  archetypeCreationStep: 'initial' | 'input' | 'extracting' | 'review' | 'saving'
  setArchetypeCreationStep: (step: 'initial' | 'input' | 'extracting' | 'review' | 'saving') => void
  setNewArchetypeData: React.Dispatch<React.SetStateAction<Record<string, unknown>>>
  setShowSaveAsArchetypeModal: (value: boolean) => void
  setShowGlobalExpansionConfirm: (value: boolean) => void
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  setHasSearchResults: (value: boolean) => void
  setSearchResultsCount: (value: number) => void
  setLocalResultsCount: (value: number) => void
  setPearchResultsCount: (value: number) => void
  setDisplayedResultsCount: (value: number) => void
  onLIAChatMessage: (msg: string) => void
  onQuickAction: (action: Record<string, unknown>) => void
  onCalibrationLike: (candidate: CalibrationCandidate) => void
  onCalibrationDislike: (candidate: CalibrationCandidate) => void
  setUserCollapsedLIA: (value: boolean) => void
  // Filters panel
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (value: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (value: string) => void
  toggleTableFilter: (category: keyof TableFilters, value: string) => void
  clearAllTableFilters: () => void
  // Table
  isLoading: boolean
  visibleCandidates: Candidate[]
  visibleTableColumns: TableColumn[]
  columnWidths: Record<string, number>
  setColumnWidths: React.Dispatch<React.SetStateAction<Record<string, number>>>
  setTableColumns: React.Dispatch<React.SetStateAction<TableColumn[]>>
  pinnedCandidates: Set<string>
  favorites: Set<string>
  sortBy: string
  sortOrder: 'asc' | 'desc'
  setSortBy: (value: string) => void
  setSortOrder: (value: 'asc' | 'desc') => void
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  onCandidateClick: (candidate: Candidate) => void
  onTogglePin: (id: string) => void
  onToggleFavorite: (id: string) => void
  renderCellValue: (candidate: Candidate, columnId: string) => React.ReactNode
  tableContainerRef: React.RefObject<HTMLDivElement>
  // Pagination
  showSearchResults: boolean
  currentPage: number
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>
  itemsPerPage: number
  getPaginatedCandidates: () => { total: number; totalPages: number }
  clearAllFilters: () => void
  // Load more
  displayedResultsCount: number
  isLoadingMore: boolean
  onLoadMore: () => void
  // Column config
  columnSearchTerm: string
  setColumnSearchTerm: (value: string) => void
  setShowColumnConfig: (value: boolean) => void
  // Candidate preview
  showCandidatePreview: boolean
  previewCandidate: Candidate | null
  previewWidth: number
  onPreviewResize: (e: React.MouseEvent) => void
  isPreviewMaximized: boolean
  onCloseCandidatePreview: () => void
  onTogglePreviewMaximize: () => void
  onCandidatePageOpen: (candidate: Candidate) => void
  setSelectedCandidateForAction: (candidate: Candidate) => void
  setShowScheduleModal: (value: boolean) => void
  onStartWSITextScreening: (candidate: Candidate) => void
  onSendEmail: (candidate: Candidate) => void
  onSendWhatsApp: (candidate: Candidate) => void
  onSendTriagem: (candidate: Candidate) => void
  onSendAgendamento: (candidate: Candidate) => void
  onSendFeedback: (candidate: Candidate) => void
  setPreviewCandidate: (candidate: Candidate) => void
  // Share search helpers
  setShareSearchCandidates: React.Dispatch<React.SetStateAction<Array<{ id: string; name: string; email?: string; avatar_url?: string; current_title?: string; linkedin_url?: string }>>>
  setShareSearchTitle: (value: string) => void
  setShowShareSearchModal: (value: boolean) => void
  // Toast
  toast: (opts: { title: string; description?: string; variant?: string }) => void
  // Talent funnel
  talentFunnel: {
    toggleFavoriteCandidate: (id: string) => void
    hideCandidate: (id: string) => void
  }
  // Edit query modal
  setEditQueryValue: (value: string) => void
  setShowEditQueryModal: (value: boolean) => void
  setShowAddToVacancyModal: (value: boolean) => void
  // Add to list modal
  setShowAddToListModal?: (value: boolean) => void
}

export function CandidateSearchResultsView({
  lastSearchQuery,
  lastSearchEntities,
  onBack,
  onOpenEditQueryModal,
  onOpenAdvancedSearch,
  selectedCandidatesForBatch,
  selectedPearchCount,
  deselectAllCandidates,
  onAddToVacancy,
  onAddToList,
  isAddingToList,
  candidates,
  onShareSearch,
  onBulkEmail,
  onBulkWSIScreening,
  onToggleFavoriteBatch,
  onHideBatch,
  onSaveToLocalBase,
  isSavingToBase,
  showCrossTabBanner,
  crossTabFilter,
  clearCrossTabFilter,
  viewingList,
  setViewingList,
  setShowSearchResults,
  setSearchTerm,
  setLastSearchQuery,
  setActiveTab,
  showExpandedLIA,
  isLIAThinking,
  liaPromptValue,
  setLiaPromptValue,
  setShowExpandedLIA,
  onAICommand,
  searchSortBy,
  setSearchSortBy,
  sortedCandidates,
  selectAllCandidates,
  showTableFiltersPanel,
  setShowTableFiltersPanel,
  getActiveTableFiltersCount,
  showColumnConfig,
  onToggleColumnConfig,
  tableColumns,
  quickFilters,
  searchTerm,
  getActiveAdvancedFiltersCount,
  isLiaSuperChat,
  setIsLiaSuperChat,
  liaWidth,
  setLiaWidth,
  isResizingLIA,
  setIsResizingLIA,
  activeSearchTab,
  setActiveSearchTab,
  chatMessages,
  setChatMessages,
  searchResults,
  setSearchResults,
  currentSearchSource,
  searchSource,
  pearchSearchOptions,
  activeSearchFilters,
  setActiveSearchFilters,
  isCreatingArchetype,
  setIsCreatingArchetype,
  archetypeCreationStep,
  setArchetypeCreationStep,
  setNewArchetypeData,
  setShowSaveAsArchetypeModal,
  setShowGlobalExpansionConfirm,
  setCandidates,
  setHasSearchResults,
  setSearchResultsCount,
  setLocalResultsCount,
  setPearchResultsCount,
  setDisplayedResultsCount,
  onLIAChatMessage,
  onQuickAction,
  onCalibrationLike,
  onCalibrationDislike,
  setUserCollapsedLIA,
  tableFilters,
  setTableFilters,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  toggleTableFilter,
  clearAllTableFilters,
  isLoading,
  visibleCandidates,
  visibleTableColumns,
  columnWidths,
  setColumnWidths,
  setTableColumns,
  pinnedCandidates,
  favorites,
  sortBy,
  sortOrder,
  setSortBy,
  setSortOrder,
  setSelectedCandidatesForBatch,
  onCandidateClick,
  onTogglePin,
  onToggleFavorite,
  renderCellValue,
  tableContainerRef,
  showSearchResults,
  currentPage,
  setCurrentPage,
  itemsPerPage,
  getPaginatedCandidates,
  clearAllFilters,
  displayedResultsCount,
  isLoadingMore,
  onLoadMore,
  columnSearchTerm,
  setColumnSearchTerm,
  setShowColumnConfig,
  showCandidatePreview,
  previewCandidate,
  previewWidth,
  onPreviewResize,
  isPreviewMaximized,
  onCloseCandidatePreview,
  onTogglePreviewMaximize,
  onCandidatePageOpen,
  setSelectedCandidateForAction,
  setShowScheduleModal,
  onStartWSITextScreening,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  setPreviewCandidate,
  setShareSearchCandidates,
  setShareSearchTitle,
  setShowShareSearchModal,
  toast,
  talentFunnel,
  setEditQueryValue,
  setShowEditQueryModal,
  setShowAddToVacancyModal,
}: CandidateSearchResultsViewProps) {
  const chatScrollRef = useRef<HTMLDivElement>(null)
  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] gap-2">
      {/* Header com query da busca e opções de edição — extraído para SearchResultsHeader (Sprint G3) */}
      <SearchResultsHeader
        lastSearchQuery={lastSearchQuery}
        lastSearchEntities={lastSearchEntities}
        onBack={onBack}
        onOpenEditQueryModal={(value) => {
          setEditQueryValue(value)
          setShowEditQueryModal(true)
        }}
        onOpenAdvancedSearch={onOpenAdvancedSearch}
      />

      {/* Contextual Actions Banner - Ações para candidatos selecionados */}
      <ContextualActionsBanner
        selectedCount={selectedCandidatesForBatch.size}
        pearchCount={selectedPearchCount}
        onDeselectAll={deselectAllCandidates}
        onAddToVacancy={() => setShowAddToVacancyModal(true)}
        onAddToList={onAddToList}
        isAddingToList={isAddingToList}
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
        onSendMessage={onBulkEmail}
        onWSIScreening={onBulkWSIScreening}
        onToggleFavorite={() => {
          selectedCandidatesForBatch.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
          toast({
            title: "Favoritos atualizados",
            description: `${selectedCandidatesForBatch.size} candidato(s) adicionado(s) aos favoritos`
          })
        }}
        onHide={() => {
          selectedCandidatesForBatch.forEach(id => talentFunnel.hideCandidate(id))
          toast({
            title: "Candidatos ocultos",
            description: `${selectedCandidatesForBatch.size} candidato(s) oculto(s) da pesquisa`
          })
          deselectAllCandidates()
        }}
        onSaveToLocalBase={onSaveToLocalBase}
        isSavingToBase={isSavingToBase}
      />

      {/* ✨ Banner Cross-Tab Filter */}
      <CrossTabFilterBanner
        showCrossTabBanner={showCrossTabBanner}
        crossTabFilter={crossTabFilter}
        clearCrossTabFilter={clearCrossTabFilter}
      />

      {/* ✨ Banner Visualizando Lista */}
      <ViewingListBanner
        viewingList={viewingList}
        candidates={candidates}
        setViewingList={setViewingList}
        setShowSearchResults={setShowSearchResults}
        setSearchTerm={setSearchTerm}
        setLastSearchQuery={setLastSearchQuery}
        setActiveTab={setActiveTab}
      />


      {/* Toolbar Compacto - Prompt LIA + Controles */}
      {/* Esconde o prompt compacto quando o expandido estiver aberto */}
      {!showExpandedLIA && (
        <div className="flex items-center justify-between gap-4 mb-1 mt-1">
          {/* Prompt LIA - Compacto (max 300px) - Design Specs v3.1 */}
          <div className="flex-1 max-w-panel-sm">
            <div
              className={`relative flex items-center h-10 rounded-md bg-lia-bg-primary transition-colors motion-reduce:transition-none ${
                isLIAThinking ? 'cursor-wait' : ''
              } border border-lia-border-subtle`} style={{paddingLeft: '16px', paddingRight: '80px'}} /* [OPT-043] paddingLeft:16px=pl-4, paddingRight:80px=pr-20 */
            >
              <input
                type="text"
                placeholder={isLIAThinking ? "LIA está pensando..." : "Ex: Analisar candidatos com..."}
                value={liaPromptValue}
                onChange={(e) => setLiaPromptValue(e.target.value)}
                disabled={isLIAThinking}
                className="flex-1 h-full text-base-ui bg-transparent focus:outline-none text-lia-text-primary placeholder:text-lia-text-secondary"

                onFocus={(e) => {
                  // Focus state: borda cyan + shadow
                  const container = e.target.parentElement
                  if (container) {
                    container.style.borderColor = 'var(--gray-200)'
                    container.style.boxShadow = '0 0 0 2px var(--wedo-cyan-bg-12)'
                  }
                  // Expandir LIA sidebar ao focar
                  if (!isLIAThinking) {
                    setShowExpandedLIA(true)
                  }
                }}
                onBlur={(e) => {
                  const container = e.target.parentElement
                  if (container) {
                    container.style.borderColor = 'var(--gray-200)'
                    container.style.boxShadow = 'none'
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && liaPromptValue.trim() && !isLIAThinking) {
                    onAICommand(liaPromptValue)
                    setLiaPromptValue('')
                  }
                }}
              />
              {/* Botões: Maximize + Send */}
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button
                  className="p-1.5 rounded-full hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                  onClick={() => setShowExpandedLIA(true)}
                  title="Expandir"
                  aria-label="Expandir chat da LIA"
                >
                  <Maximize2 className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
                </button>
                <button
                  className={`p-1.5 rounded-full transition-colors motion-reduce:transition-none ${
                    isLIAThinking ? 'cursor-wait opacity-50' : 'hover:bg-gray-100'
                  }`}
                  onClick={() => {
                    if (liaPromptValue.trim() && !isLIAThinking) {
                      onAICommand(liaPromptValue)
                      setLiaPromptValue('')
                    }
                  }}
                  disabled={isLIAThinking}
                  title="Enviar"
                  aria-label="Enviar mensagem para a LIA"
                >
                  {isLIAThinking ? (
                    <div className="w-4 h-4 border-2 border-gray-900 dark:border-lia-border-medium border-t-transparent rounded-full animate-spin motion-reduce:animate-none" aria-hidden="true" />
                  ) : (
                    <Send className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>

            {/* Indicador de Thinking - Aparece quando LIA está processando */}
            {isLIAThinking && (
              <div className="mt-2 flex items-center gap-2 text-xs px-3 py-1.5 rounded-md animate-fade-in bg-gray-200/30 border border-wedo-cyan/20">
                <Brain className="w-3 h-3 animate-pulse motion-reduce:animate-none text-wedo-cyan" />
                <span className="font-medium text-lia-text-primary">LIA está pensando</span>
                <div className="flex gap-0.5">
                  <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce motion-reduce:animate-none" style={{animationDelay: '0ms'}}></span>
                  <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce motion-reduce:animate-none" style={{animationDelay: '150ms'}}></span>
                  <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce motion-reduce:animate-none" style={{animationDelay: '300ms'}}></span>
                </div>
              </div>
            )}
        </div>

        {/* Controles e Info - Sempre visíveis à direita */}
        <div className="flex items-center gap-3">
          {/* Badge de seleção */}
          {selectedCandidatesForBatch.size > 0 && (
            <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary border-0 text-xs font-medium">
              🎯 {selectedCandidatesForBatch.size}
            </Badge>
          )}

          {/* Sort indicator - mostra ordenação ativa (configuração dentro dos filtros) */}
          {searchSortBy !== 'relevance' && (
            <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary border-0 text-xs font-medium gap-1">
              <ArrowUpDown className="w-3 h-3" />
              {searchSortBy === 'score_desc' ? 'Maior Score' :
               searchSortBy === 'score_asc' ? 'Menor Score' :
               searchSortBy === 'name_asc' ? 'Nome A-Z' :
               searchSortBy === 'name_desc' ? 'Nome Z-A' :
               searchSortBy === 'experience_desc' ? 'Maior Experiência' : 'Relevância'}
            </Badge>
          )}

          {/* Botão Selecionar Todos - Padronizado conforme design */}
          {selectedCandidatesForBatch.size === 0 && sortedCandidates.length > 0 && (
            <button
              onClick={selectAllCandidates}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-lia-text-primary bg-lia-bg-primary border border-lia-border-subtle rounded-full hover:bg-gray-50 transition-colors motion-reduce:transition-none"

            >
              <CheckCircle className="w-4 h-4 text-lia-text-tertiary" />
              Selecionar Todos
            </button>
          )}

          {/* Botões de controle - Filtros da Tabela (tableFilters) - Padronizado */}
          <button
            onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none ${
              showTableFiltersPanel
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'text-lia-text-primary bg-lia-bg-primary border border-lia-border-subtle hover:bg-gray-50'
            }`}

          >
            <Target className="w-4 h-4" />
            Filtros
            {getActiveTableFiltersCount() > 0 && (
              <span className={`text-xs font-medium ${showTableFiltersPanel ? 'text-lia-text-disabled' : 'text-lia-text-tertiary'}`}>
                {getActiveTableFiltersCount()}
              </span>
            )}
          </button>

          <button
            onClick={onToggleColumnConfig}
            title="Configurar colunas da tabela"
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none ${
              showColumnConfig
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'text-lia-text-primary bg-lia-bg-primary border border-lia-border-subtle hover:bg-gray-50'
            }`}

          >
            <ChevronsLeftRight className="w-4 h-4" />
            Colunas
            <span className={`text-xs font-medium ${showColumnConfig ? 'text-lia-text-disabled' : 'text-lia-text-tertiary'}`}>
              {tableColumns.filter(col => col.visible && col.id !== 'acoes').length}
            </span>
          </button>
        </div>
      </div>
      )}

      {/* Badge de Filtros Ativos - Simplificado */}
      {(quickFilters.size > 0 || searchTerm || getActiveAdvancedFiltersCount() > 0) && (
        <div className="mb-1.5 flex items-center gap-2">
          <Badge className="text-xs bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary border-0">
            filtros ativos
          </Badge>
          {selectedCandidatesForBatch.size > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={deselectAllCandidates}
              className="h-6 px-2 text-xs text-lia-text-primary hover:text-lia-text-primary"
            >
              <X className="w-3 h-3 mr-1" />
              Limpar seleção
            </Button>
          )}
        </div>
      )}


      {/* Results Layout with Sidebars - Layout flex responsivo */}
      {/* ORDEM: LIA à esquerda, Filtros à direita, Tabela ao centro */}
      <div className="flex gap-4 overflow-hidden transition-colors motion-reduce:transition-none duration-300 flex-1 min-h-0 w-full">
        {/* LIA Sidebar Expandida - Sistema de Pesquisa Avançada */}
        {showExpandedLIA && (
          <LIASearchSidebar
            isLiaSuperChat={isLiaSuperChat}
            setIsLiaSuperChat={setIsLiaSuperChat}
            liaWidth={liaWidth}
            setLiaWidth={setLiaWidth}
            isResizingLIA={isResizingLIA}
            setIsResizingLIA={setIsResizingLIA}
            // @ts-ignore TODO: fix type
            activeSearchTab={activeSearchTab}
            // @ts-ignore TODO: fix type
            setActiveSearchTab={setActiveSearchTab}
            liaPromptValue={liaPromptValue}
            // @ts-ignore TODO: fix type
            setLiaPromptValue={setLiaPromptValue}
            chatMessages={chatMessages}
            setChatMessages={setChatMessages}
            searchResults={searchResults}
            // @ts-ignore TODO: fix type
            setSearchResults={setSearchResults}
            currentSearchSource={currentSearchSource}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            // @ts-ignore TODO: fix type
            activeSearchFilters={activeSearchFilters}
            setActiveSearchFilters={setActiveSearchFilters}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            isCreatingArchetype={isCreatingArchetype}
            setIsCreatingArchetype={setIsCreatingArchetype}
            archetypeCreationStep={archetypeCreationStep}
            // @ts-ignore TODO: fix type
            setArchetypeCreationStep={setArchetypeCreationStep}
            setNewArchetypeData={setNewArchetypeData}
            setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
            setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
            selectedCandidatesForBatch={selectedCandidatesForBatch}
            // @ts-ignore TODO: fix type
            setCandidates={setCandidates}
            setHasSearchResults={setHasSearchResults}
            setSearchResultsCount={setSearchResultsCount}
            setLocalResultsCount={setLocalResultsCount}
            setPearchResultsCount={setPearchResultsCount}
            setShowSearchResults={setShowSearchResults}
            setDisplayedResultsCount={setDisplayedResultsCount}
            onLIAChatMessage={onLIAChatMessage}
            onAICommand={onAICommand}
            // @ts-ignore TODO: fix type
            onQuickAction={onQuickAction}
            // @ts-ignore TODO: fix type
            onCalibrationLike={onCalibrationLike}
            // @ts-ignore TODO: fix type
            chatScrollRef={chatScrollRef}
            // @ts-ignore TODO: fix type
            onCalibrationDislike={onCalibrationDislike}
            onClose={() => {
              setShowExpandedLIA(false)
              setUserCollapsedLIA(true)
              setIsLiaSuperChat(false)
            }}
          />
        )}

        {/* Filtros da Tabela de Resultados - Coluna inline entre LIA e tabela */}
        {/* SEPARADO dos filtros de busca (activeSearchFilters) - usa tableFilters para filtrar resultados localmente */}
        {showTableFiltersPanel && (
          <CandidatesFilterPanel
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            searchSortBy={searchSortBy}
            onSortChange={setSearchSortBy}
            newSoftSkillFilter={newSoftSkillFilter}
            setNewSoftSkillFilter={setNewSoftSkillFilter}
            newCertificationFilter={newCertificationFilter}
            setNewCertificationFilter={setNewCertificationFilter}
            activeFiltersCount={getActiveTableFiltersCount()}
            onToggleFilter={toggleTableFilter}
            onClearAll={clearAllTableFilters}
            onClose={() => setShowTableFiltersPanel(false)}
          />
        )}


        {/* Main Content Area - Candidatos Table with Superchat collapse support */}
        <div className={`bg-white dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none duration-300 ${
          isLiaSuperChat
            ? 'w-14 flex-shrink-0'
            : 'flex-1 min-w-0 h-full'
        }`}>
          {isLiaSuperChat ? (
            /* Versão Contraída - Apenas ícone para expandir */
            <div className="h-full flex flex-col items-center py-4 gap-3">
              {/* Botão para expandir tabela */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsLiaSuperChat(false)}
                className="h-10 w-10 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                title="Expandir tabela de candidatos"
              >
                <ChevronRight className="w-5 h-5 text-lia-text-primary dark:text-lia-text-tertiary" />
              </Button>

              {/* Ícone da tabela */}
              <div className="flex flex-col items-center gap-2 text-lia-text-primary">
                <Users className="w-5 h-5" />
                <span className="text-xs font-medium" style={{writingMode: 'vertical-rl', textOrientation: 'mixed'}} aria-live="polite" aria-atomic="true">
                  Candidatos ({sortedCandidates.length})
                </span>
              </div>

              {/* Indicador de candidatos selecionados */}
              {selectedCandidatesForBatch.size > 0 && (
                <Badge className="bg-gray-900 dark:bg-gray-50 text-white text-xs px-1.5 py-0.5">
                  {selectedCandidatesForBatch.size}
                </Badge>
              )}
            </div>
          ) : (
            /* Versão Expandida - Tabela completa */
            <div className="h-full flex flex-col overflow-hidden">
          {/* Table Container - Scrollável */}
          <div
            ref={tableContainerRef}
            className="flex-1 relative overflow-auto"
          >
            {/* Loading Overlay */}
            {isLoading && (
              <div className="flex items-center justify-center h-full absolute inset-0 z-20 bg-white dark:bg-lia-bg-primary" role="status" aria-live="polite" aria-label="Carregando...">
                <div className="text-center" role="status" aria-live="polite" aria-label="Carregando...">
                  <div className="animate-spin motion-reduce:animate-none rounded-full h-10 w-10 border-b-2 border-wedo-cyan/30 mx-auto mb-4" role="status" aria-live="polite" aria-label="Carregando..."></div>
                  <p className="text-lia-text-primary text-sm" aria-live="polite" aria-atomic="true">Carregando candidatos...</p>
                </div>
              </div>
            )}

            {/* Unified Candidate Table */}
            {!isLoading && sortedCandidates.length > 0 && (
              <UnifiedCandidateTable
                candidates={visibleCandidates as unknown as TableCandidate[]}
                columns={visibleTableColumns.map((col) => ({
                  id: col.id,
                  label: col.label,
                  visible: col.visible,
                  sortable: true,
                  width: columnWidths[col.id] || 120,
                  minWidth: 80,
                  align: col.id === 'name' ? 'left' as const : 'center' as const,
                  order: col.order,
                  isGlobalSearch: col.isGlobalSearch
                }))}
                selectedIds={selectedCandidatesForBatch}
                pinnedIds={pinnedCandidates}
                favoriteIds={favorites}
                sortConfig={sortBy ? { field: sortBy, direction: sortOrder } : undefined}
                isLoading={false}
                emptyMessage="Nenhum candidato encontrado"
                showCheckboxes={true}
                showPagination={false}
                enableColumnResize={true}
                enableColumnReorder={true}
                enableVirtualScroll={visibleCandidates.length > 50}
                onColumnResize={(columnId, newWidth) => {
                  setColumnWidths(prev => ({
                    ...prev,
                    [columnId]: newWidth
                  }))
                }}
                onColumnReorder={(reorderedColumns) => {
                  // @ts-ignore TODO: fix type
                  setTableColumns(prev => prev.map(col => {
                    const reordered = reorderedColumns.find(r => r.id === col.id)
                    return reordered ? { ...col, order: reordered.order } : col
                  }))
                }}
                onCandidateClick={(candidate) => onCandidateClick(candidate as unknown as Candidate)}
                onSelectionChange={(ids) => setSelectedCandidatesForBatch(ids)}
                onSortChange={(config) => {
                  setSortBy(config.field)
                  setSortOrder(config.direction)
                }}
                onTogglePin={(candidateId) => onTogglePin(candidateId)}
                onToggleFavorite={(candidateId) => onToggleFavorite(candidateId)}
                renderCustomCell={(candidate, columnId) => renderCellValue(candidate as unknown as Candidate, columnId)}
              />
            )}
            {/* Paginação (como Gestão de Vagas) - oculta quando usando Load More em resultados de busca */}
            {!isLoading && !showSearchResults && getPaginatedCandidates().totalPages > 1 && (
              <div className="bg-white dark:bg-lia-bg-primary rounded-md p-3 mt-2">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-lia-text-primary dark:text-lia-text-tertiary">
                    Mostrando {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, getPaginatedCandidates().total)} de {getPaginatedCandidates().total} candidatos
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="h-8"
                    >
                      Primeira
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="h-8"
                    >
                      Anterior
                    </Button>

                    {/* Page numbers */}
                    <div className="flex items-center gap-1">
                      {Array.from({ length: getPaginatedCandidates().totalPages }, (_, i) => i + 1)
                        .filter(page => {
                          return page === 1 ||
                                 page === getPaginatedCandidates().totalPages ||
                                 (page >= currentPage - 1 && page <= currentPage + 1)
                        })
                        .map((page, index, array) => (
                          <React.Fragment key={page}>
                            {index > 0 && page - array[index - 1] > 1 && (
                              <span className="px-2 text-lia-text-primary">...</span>
                            )}
                            <Button
                              // @ts-ignore TODO: fix type
                              variant={currentPage === page ? 'default' : 'outline'}
                              size="sm"
                              onClick={() => setCurrentPage(page)}
                              className="h-8 w-8 p-0"
                            >
                              {page}
                            </Button>
                          </React.Fragment>
                        ))
                      }
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(prev => Math.min(getPaginatedCandidates().totalPages, prev + 1))}
                      disabled={currentPage === getPaginatedCandidates().totalPages}
                      className="h-8"
                    >
                      Próxima
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(getPaginatedCandidates().totalPages)}
                      disabled={currentPage === getPaginatedCandidates().totalPages}
                      className="h-8"
                    >
                      Última
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!isLoading && sortedCandidates.length === 0 && (
              <div className="bg-white dark:bg-lia-bg-primary rounded-md p-8 text-center">
                <Users className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
                <h3 className="text-lg font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                  Nenhum candidato encontrado
                </h3>
                <p className="text-lia-text-primary dark:text-lia-text-tertiary mb-4">
                  Tente ajustar os filtros ou termos de busca
                </p>
                <Button
                  variant="outline"
                  onClick={clearAllFilters}
                >
                  Limpar filtros
                </Button>
              </div>
            )}
          </div>
          {/* Load More - extracted to CandidatesLoadMoreFooter */}
          <CandidatesLoadMoreFooter
            showSearchResults={showSearchResults}
            displayedResultsCount={displayedResultsCount}
            sortedCandidatesLength={sortedCandidates.length}
            isLoadingMore={isLoadingMore}
            onLoadMore={onLoadMore}
          />
        </div>
          )}
        </div>

          {/* Column Configuration Sidebar - Right - WeDOTalent Light Design */}
          <ColumnConfigSidebar
            showColumnConfig={showColumnConfig}
            tableColumns={tableColumns}
            setTableColumns={setTableColumns}
            columnSearchTerm={columnSearchTerm}
            setColumnSearchTerm={setColumnSearchTerm}
            setShowColumnConfig={setShowColumnConfig}
          />

          {/* Candidate Preview - Painel lateral direito */}
          {showCandidatePreview && previewCandidate && (
            <div className="flex-shrink-0 relative" style={{width: `${previewWidth}px`}}>
              {/* Resize Handle */}
              <div
                className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors motion-reduce:transition-none z-10 group"
                onMouseDown={onPreviewResize}
                title="Arraste para redimensionar"
              >
                <div className="absolute inset-0 -left-1 -right-1"></div>
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-lia-bg-elevated group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors motion-reduce:transition-none"></div>
              </div>
              <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
                // @ts-ignore TODO: fix type
                <CandidatePreview
                  // @ts-ignore TODO: fix type
                  candidate={previewCandidate}
                  isOpen={showCandidatePreview}
                  onClose={onCloseCandidatePreview}
                  isMaximized={isPreviewMaximized}
                  onToggleMaximize={onTogglePreviewMaximize}
                  candidates={sortedCandidates}
                  currentIndex={sortedCandidates.findIndex(c => c.id === previewCandidate.id)}
                  onNavigateCandidate={(index) => {
                    if (sortedCandidates[index]) {
                      setPreviewCandidate(sortedCandidates[index])
                    }
                  }}
                  onOpenFullPage={onCandidatePageOpen}
                  onScheduleInterview={(candidate) => {
                    // @ts-ignore TODO: fix type
                    setSelectedCandidateForAction(candidate)
                    setShowScheduleModal(true)
                  }}
                  onAddToVacancy={(candidate) => {
                    // @ts-ignore TODO: fix type
                    setSelectedCandidatesForBatch(new Set([candidate.id]))
                    setShowAddToVacancyModal(true)
                  }}
                  onToggleFavorite={(candidateId) => onToggleFavorite(candidateId)}
                  // @ts-ignore TODO: fix type
                  onWSIScreening={(candidate) => onStartWSITextScreening(candidate)}
                  isFavorite={favorites.has(previewCandidate.id)}
                  // @ts-ignore TODO: fix type
                  onSendEmail={(candidate) => onSendEmail(candidate)}
                  // @ts-ignore TODO: fix type
                  onSendWhatsApp={(candidate) => onSendWhatsApp(candidate)}
                  // @ts-ignore TODO: fix type
                  onSendTriagem={(candidate) => onSendTriagem(candidate)}
                  // @ts-ignore TODO: fix type
                  onSendAgendamento={(candidate) => onSendAgendamento(candidate)}
                  // @ts-ignore TODO: fix type
                  onSendFeedback={(candidate) => onSendFeedback(candidate)}
                />
              </div>
            </div>
          )}
        </div>
    </div>
  )
}
