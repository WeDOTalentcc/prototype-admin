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

type SearchTab = 'ia-natural' | 'boolean' | 'filters' | 'archetypes'

type ChatMessage = {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

type TableColumn = {
  id: string
  label: string
  visible: boolean
  order: number
  width?: number
  minWidth?: number
  category?: string
  sortable?: boolean
  isGlobalSearch?: boolean
}

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
  crossTabFilter: any
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
  setNewArchetypeData: React.Dispatch<React.SetStateAction<any>>
  setShowSaveAsArchetypeModal: (value: boolean) => void
  setShowGlobalExpansionConfirm: (value: boolean) => void
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  setHasSearchResults: (value: boolean) => void
  setSearchResultsCount: (value: number) => void
  setLocalResultsCount: (value: number) => void
  setPearchResultsCount: (value: number) => void
  setDisplayedResultsCount: (value: number) => void
  onLIAChatMessage: (msg: string) => void
  onQuickAction: (action: any) => void
  onCalibrationLike: (candidate: any) => void
  onCalibrationDislike: (candidate: any) => void
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
      {showCrossTabBanner && crossTabFilter && (
        <Card className="bg-gray-50 dark:bg-gray-800">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-900 dark:bg-gray-100 rounded-md flex items-center justify-center">
                {crossTabFilter.type === 'company' ? (
                  <Building className="w-5 h-5 text-white dark:text-gray-900" />
                ) : (
                  <Target className="w-5 h-5 text-white dark:text-gray-900" />
                )}
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                  🎯 Filtro Aplicado: {crossTabFilter.type === 'company' ? 'Empresa' : 'Inteligência Competitiva'}
                </h3>
                <p className="text-sm text-gray-800 dark:text-gray-400 mb-3">
                  {crossTabFilter.type === 'company' && crossTabFilter.company && (
                    `Mostrando candidatos da empresa "${crossTabFilter.company}" mapeada`
                  )}
                  {crossTabFilter.type === 'company' && crossTabFilter.companies && (
                    `Mostrando candidatos das empresas: ${crossTabFilter.companies.join(', ')}`
                  )}
                  {crossTabFilter.filter === 'discontented_talents' && (
                    `Talentos com indicações de descontentamento detectadas pela LIA`
                  )}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearCrossTabFilter}
                  >
                    <X className="w-3 h-3 mr-1" />
                    Limpar Filtro
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ✨ Banner Visualizando Lista */}
      {viewingList && (
        <Card className="bg-gray-50 dark:bg-gray-800 border-l-4" style={{ borderLeftColor: viewingList.color || 'var(--gray-600)' }}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-md flex items-center justify-center"
                style={{ backgroundColor: viewingList.color || 'var(--gray-600)' }}
              >
                <List className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                  📋 Visualizando Lista: {viewingList.name}
                </h3>
                <p className="text-sm text-gray-800 dark:text-gray-400">
                  {candidates.length} {candidates.length === 1 ? 'candidato' : 'candidatos'} nesta lista
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setViewingList(null)
                    setShowSearchResults(false)
                    setSearchTerm('')
                    setLastSearchQuery('')
                  }}
                >
                  <X className="w-3 h-3 mr-1" />
                  Fechar Lista
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveTab('lists')}
                >
                  <ArrowLeft className="w-3 h-3 mr-1" />
                  Voltar às Listas
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}


      {/* Toolbar Compacto - Prompt LIA + Controles */}
      {/* Esconde o prompt compacto quando o expandido estiver aberto */}
      {!showExpandedLIA && (
        <div className="flex items-center justify-between gap-4 mb-1 mt-1">
          {/* Prompt LIA - Compacto (max 300px) - Design Specs v3.1 */}
          <div className="flex-1 max-w-[300px]">
            <div
              className={`relative flex items-center h-10 rounded-md bg-white transition-all ${
                isLIAThinking ? 'cursor-wait' : ''
              } border border-gray-200`} style={{ paddingLeft: '16px', paddingRight: '80px' }}
            >
              <input
                type="text"
                placeholder={isLIAThinking ? "LIA está pensando..." : "Ex: Analisar candidatos com..."}
                value={liaPromptValue}
                onChange={(e) => setLiaPromptValue(e.target.value)}
                disabled={isLIAThinking}
                className="flex-1 h-full text-base-ui bg-transparent focus:outline-none text-gray-950 placeholder:text-gray-600"

                onFocus={(e) => {
                  // Focus state: borda cyan + shadow
                  const container = e.target.parentElement
                  if (container) {
                    container.style.borderColor = 'var(--gray-200)'
                    container.style.boxShadow = '0 0 0 2px color-mix(in srgb, var(--wedo-cyan) 12%, transparent)'
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
                  className="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
                  onClick={() => setShowExpandedLIA(true)}
                  title="Expandir"
                  aria-label="Expandir chat da LIA"
                >
                  <Maximize2 className="w-4 h-4 text-gray-700" aria-hidden="true" />
                </button>
                <button
                  className={`p-1.5 rounded-full transition-colors ${
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
                    <div className="w-4 h-4 border-2 border-gray-900 dark:border-gray-50 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                  ) : (
                    <Send className="w-4 h-4 text-gray-700" aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>

            {/* Indicador de Thinking - Aparece quando LIA está processando */}
            {isLIAThinking && (
              <div className="mt-2 flex items-center gap-2 text-xs px-3 py-1.5 rounded-md animate-fade-in bg-gray-200/30 border border-wedo-cyan/20">
                <Brain className="w-3 h-3 animate-pulse text-wedo-cyan" />
                <span className="font-medium text-gray-800">LIA está pensando</span>
                <div className="flex gap-0.5">
                  <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            )}
        </div>

        {/* Controles e Info - Sempre visíveis à direita */}
        <div className="flex items-center gap-3">
          {/* Badge de seleção */}
          {selectedCandidatesForBatch.size > 0 && (
            <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0 text-xs font-medium">
              🎯 {selectedCandidatesForBatch.size}
            </Badge>
          )}

          {/* Sort indicator - mostra ordenação ativa (configuração dentro dos filtros) */}
          {searchSortBy !== 'relevance' && (
            <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0 text-xs font-medium gap-1">
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
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-gray-800 bg-white border border-gray-200 rounded-full hover:bg-gray-50 transition-colors"

            >
              <CheckCircle className="w-4 h-4 text-gray-500" />
              Selecionar Todos
            </button>
          )}

          {/* Botões de controle - Filtros da Tabela (tableFilters) - Padronizado */}
          <button
            onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors ${
              showTableFiltersPanel
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'text-gray-800 bg-white border border-gray-200 hover:bg-gray-50'
            }`}

          >
            <Target className="w-4 h-4" />
            Filtros
            {getActiveTableFiltersCount() > 0 && (
              <span className={`text-xs font-medium ${showTableFiltersPanel ? 'text-gray-300' : 'text-gray-500'}`}>
                {getActiveTableFiltersCount()}
              </span>
            )}
          </button>

          <button
            onClick={onToggleColumnConfig}
            title="Configurar colunas da tabela"
            className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors ${
              showColumnConfig
                ? 'bg-gray-900 text-white hover:bg-gray-800'
                : 'text-gray-800 bg-white border border-gray-200 hover:bg-gray-50'
            }`}

          >
            <ChevronsLeftRight className="w-4 h-4" />
            Colunas
            <span className={`text-xs font-medium ${showColumnConfig ? 'text-gray-300' : 'text-gray-500'}`}>
              {tableColumns.filter(col => col.visible && col.id !== 'acoes').length}
            </span>
          </button>
        </div>
      </div>
      )}

      {/* Badge de Filtros Ativos - Simplificado */}
      {(quickFilters.size > 0 || searchTerm || getActiveAdvancedFiltersCount() > 0) && (
        <div className="mb-1.5 flex items-center gap-2">
          <Badge className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0">
            filtros ativos
          </Badge>
          {selectedCandidatesForBatch.size > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={deselectAllCandidates}
              className="h-6 px-2 text-xs text-gray-800 hover:text-gray-900"
            >
              <X className="w-3 h-3 mr-1" />
              Limpar seleção
            </Button>
          )}
        </div>
      )}


      {/* Results Layout with Sidebars - Layout flex responsivo */}
      {/* ORDEM: LIA à esquerda, Filtros à direita, Tabela ao centro */}
      <div className="flex gap-4 overflow-hidden transition-all duration-300 flex-1 min-h-0 w-full">
        {/* LIA Sidebar Expandida - Sistema de Pesquisa Avançada */}
        {showExpandedLIA && (
          <LIASearchSidebar
            isLiaSuperChat={isLiaSuperChat}
            setIsLiaSuperChat={setIsLiaSuperChat}
            liaWidth={liaWidth}
            setLiaWidth={setLiaWidth}
            isResizingLIA={isResizingLIA}
            setIsResizingLIA={setIsResizingLIA}
            activeSearchTab={activeSearchTab}
            setActiveSearchTab={setActiveSearchTab}
            liaPromptValue={liaPromptValue}
            setLiaPromptValue={setLiaPromptValue}
            chatMessages={chatMessages}
            setChatMessages={setChatMessages}
            searchResults={searchResults}
            setSearchResults={setSearchResults}
            currentSearchSource={currentSearchSource}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            activeSearchFilters={activeSearchFilters}
            setActiveSearchFilters={setActiveSearchFilters}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            isCreatingArchetype={isCreatingArchetype}
            setIsCreatingArchetype={setIsCreatingArchetype}
            archetypeCreationStep={archetypeCreationStep}
            setArchetypeCreationStep={setArchetypeCreationStep}
            setNewArchetypeData={setNewArchetypeData}
            setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
            setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
            selectedCandidatesForBatch={selectedCandidatesForBatch}
            setCandidates={setCandidates}
            setHasSearchResults={setHasSearchResults}
            setSearchResultsCount={setSearchResultsCount}
            setLocalResultsCount={setLocalResultsCount}
            setPearchResultsCount={setPearchResultsCount}
            setShowSearchResults={setShowSearchResults}
            setDisplayedResultsCount={setDisplayedResultsCount}
            onLIAChatMessage={onLIAChatMessage}
            onAICommand={onAICommand}
            onQuickAction={onQuickAction}
            onCalibrationLike={onCalibrationLike}
            chatScrollRef={chatScrollRef}
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
        <div className={`bg-white dark:bg-gray-800 rounded-md transition-all duration-300 ${
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
                <ChevronRight className="w-5 h-5 text-gray-800 dark:text-gray-400" />
              </Button>

              {/* Ícone da tabela */}
              <div className="flex flex-col items-center gap-2 text-gray-800">
                <Users className="w-5 h-5" />
                <span className="text-xs font-medium" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
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
              <div className="flex items-center justify-center h-full absolute inset-0 z-20 bg-white dark:bg-gray-900">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-wedo-cyan/30 mx-auto mb-4"></div>
                  <p className="text-gray-800 text-sm">Carregando candidatos...</p>
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
                onColumnResize={(columnId, newWidth) => {
                  setColumnWidths(prev => ({
                    ...prev,
                    [columnId]: newWidth
                  }))
                }}
                onColumnReorder={(reorderedColumns) => {
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
              <div className="bg-white dark:bg-gray-900 rounded-md p-3 mt-2">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-800 dark:text-gray-400">
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
                              <span className="px-2 text-gray-800">...</span>
                            )}
                            <Button
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
              <div className="bg-white dark:bg-gray-900 rounded-md p-8 text-center">
                <Users className="w-12 h-12 text-gray-800 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
                  Nenhum candidato encontrado
                </h3>
                <p className="text-gray-800 dark:text-gray-400 mb-4">
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
          {/* Load More - Fase 1 Funil de Talentos (FORA do scroll container, sempre visível) */}
          {showSearchResults && displayedResultsCount < sortedCandidates.length && (
            <div className="flex-shrink-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 py-3 px-4">
              <div className="flex flex-col items-center gap-1.5">
                <Button
                  variant="outline"
                  className="w-full max-w-md h-10 gap-2 text-sm font-medium"
                  onClick={onLoadMore}
                  disabled={isLoadingMore}
                >
                  {isLoadingMore ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                  {isLoadingMore ? 'Carregando...' : 'Carregar mais 10 candidatos'}
                </Button>
                <span className="text-xs text-gray-500">
                  {Math.min(displayedResultsCount, sortedCandidates.length)} de {sortedCandidates.length} candidatos
                </span>
              </div>
            </div>
          )}
          {showSearchResults && displayedResultsCount >= sortedCandidates.length && sortedCandidates.length > 10 && (
            <p className="flex-shrink-0 text-center text-sm text-gray-500 py-3">
              Todos os {sortedCandidates.length} candidatos carregados
            </p>
          )}
        </div>
          )}
        </div>

          {/* Column Configuration Sidebar - Right - WeDOTalent Light Design */}
          {showColumnConfig && (
            <div className="flex-shrink-0 w-80 transition-all duration-300">
              <div className="bg-white rounded-md h-[calc(100vh-6rem)] overflow-hidden">
                {/* Header */}
                <div className="p-4 flex items-center justify-between border-b border-gray-100">
                  <div>
                    <h3
                      className="text-sm font-semibold text-gray-950 dark:text-gray-50"

                    >
                      Configurar Colunas
                    </h3>
                    <p
                      className="text-xs mt-0.5 text-gray-800"

                    >
                      {tableColumns.filter(c => c.visible && c.id !== 'acoes').length} de {tableColumns.filter(c => c.id !== 'acoes').length} colunas ativas
                    </p>
                  </div>
                  <button
                    onClick={() => setShowColumnConfig(false)}
                    className="h-8 w-8 rounded-md flex items-center justify-center transition-all text-gray-800 hover:text-gray-950 hover:bg-gray-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Search and Actions */}
                <div className="p-3 space-y-3 border-b border-gray-100">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-800" />
                    <input
                      type="text"
                      placeholder="Buscar coluna..."
                      value={columnSearchTerm}
                      onChange={(e) => setColumnSearchTerm(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-gray-50 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-gray-950 dark:text-gray-50"

                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="flex-1 text-xs h-8 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600"
                      onClick={() => {
                        setTableColumns(prev => prev.map((col, idx) => ({
                          ...col,
                          visible: col.id === 'acoes' || idx < 7,
                          order: col.id === 'acoes' ? 0.5 : idx
                        })))
                      }}
                    >
                      Restaurar Padrão
                    </button>
                    <button
                      className="text-xs h-8 px-4 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600"
                      onClick={() => {
                        setTableColumns(prev => prev.map(col => ({ ...col, visible: true })))
                      }}
                    >
                      Todas
                    </button>
                  </div>
                </div>

                {/* Column List */}
                <div className="overflow-y-auto h-[calc(100%-160px)] p-3">
                  {(() => {
                    const categoryLabels: Record<string, string> = {
                      basico: 'Identificação Básica',
                      contato: 'Contato',
                      pessoal: 'Informações Pessoais',
                      profissional: 'Perfil Profissional',
                      competencias: 'Competências',
                      localizacao: 'Localização',
                      endereco: 'Endereço Completo',
                      preferencias: 'Preferências de Trabalho',
                      salario: 'Salário e Expectativas',
                      documentos: 'Currículo e Documentos',
                      origem: 'Origem e Integração',
                      busca_global: 'Busca Global',
                      ia: 'Insights LIA / IA',
                      status: 'Status e Workflow',
                      comunicacao: 'Comunicação',
                      cadastro: 'Status de Cadastro',
                      adicional: 'Informações Adicionais',
                      datas: 'Datas e Timestamps'
                    }

                    const filteredColumns = tableColumns.filter(col =>
                      col.id !== 'acoes' && col.id !== 'feedback' && (
                      col.label.toLowerCase().includes(columnSearchTerm.toLowerCase()) ||
                      col.id.toLowerCase().includes(columnSearchTerm.toLowerCase()))
                    )

                    const groupedColumns = filteredColumns.reduce((acc, col) => {
                      const category = col.category || 'adicional'
                      if (!acc[category]) acc[category] = []
                      acc[category].push(col)
                      return acc
                    }, {} as Record<string, typeof tableColumns>)

                    const categoryOrder = ['basico', 'contato', 'pessoal', 'profissional', 'competencias', 'localizacao', 'endereco', 'preferencias', 'salario', 'documentos', 'origem', 'busca_global', 'ia', 'status', 'comunicacao', 'cadastro', 'adicional', 'datas']

                    return categoryOrder.map(category => {
                      const columns = groupedColumns[category]
                      if (!columns || columns.length === 0) return null

                      const visibleCount = columns.filter(c => c.visible).length

                      return (
                        <div key={category} className="mb-5">
                          <div className="flex items-center justify-between mb-2 px-1">
                            <h4
                              className="text-xs font-semibold uppercase tracking-wider text-gray-800"

                            >
                              {categoryLabels[category] || category}
                            </h4>
                            <span
                              className="text-xs px-2 py-0.5 rounded-full"
                              style={{
                                backgroundColor: visibleCount > 0 ? 'var(--gray-100)' : 'var(--gray-100)',
                                color: visibleCount > 0 ? 'var(--gray-600)' : 'var(--gray-400)',
                              }}
                            >
                              {visibleCount}/{columns.length}
                            </span>
                          </div>
                          <div className="space-y-1">
                            {columns.map((col) => (
                              <div
                                key={col.id}
                                onClick={() => {
                                  setTableColumns(prev => prev.map(c =>
                                    c.id === col.id ? { ...c, visible: !c.visible } : c
                                  ))
                                }}
                                className="flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-all hover:bg-gray-100"
                                style={{
                                  backgroundColor: col.visible ? 'var(--gray-50)' : 'var(--gray-50)',
                                  border: col.visible ? '1px solid var(--gray-300)' : '1px solid var(--gray-200)'
                                }}
                              >
                                {/* Custom Checkbox - Monocromático */}
                                <div
                                  className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-all"
                                  style={{
                                    backgroundColor: col.visible ? 'var(--gray-600)' : 'transparent',
                                    border: col.visible ? 'none' : '2px solid var(--gray-300)'
                                  }}
                                >
                                  {col.visible && (
                                    <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                  )}
                                </div>
                                <span
                                  className="text-xs flex-1 flex items-center gap-1.5"
                                  style={{
                                    color: col.visible ? 'var(--gray-800)' : 'var(--gray-500)',
                                    fontWeight: col.visible ? 500 : 400
                                  }}
                                >
                                  {col.isGlobalSearch && (
                                    <Globe className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                  )}
                                  {col.label}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    })
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* Candidate Preview - Painel lateral direito */}
          {showCandidatePreview && previewCandidate && (
            <div className="flex-shrink-0 relative" style={{ width: `${previewWidth}px` }}>
              {/* Resize Handle */}
              <div
                className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors z-10 group"
                onMouseDown={onPreviewResize}
                title="Arraste para redimensionar"
              >
                <div className="absolute inset-0 -left-1 -right-1"></div>
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-gray-600 group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors"></div>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 h-[calc(100vh-6rem)] overflow-hidden">
                <CandidatePreview
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
                    setSelectedCandidateForAction(candidate)
                    setShowScheduleModal(true)
                  }}
                  onAddToVacancy={(candidate) => {
                    setSelectedCandidatesForBatch(new Set([candidate.id]))
                    setShowAddToVacancyModal(true)
                  }}
                  onToggleFavorite={(candidateId) => onToggleFavorite(candidateId)}
                  onWSIScreening={(candidate) => onStartWSITextScreening(candidate)}
                  isFavorite={favorites.has(previewCandidate.id)}
                  onSendEmail={(candidate) => onSendEmail(candidate)}
                  onSendWhatsApp={(candidate) => onSendWhatsApp(candidate)}
                  onSendTriagem={(candidate) => onSendTriagem(candidate)}
                  onSendAgendamento={(candidate) => onSendAgendamento(candidate)}
                  onSendFeedback={(candidate) => onSendFeedback(candidate)}
                />
              </div>
            </div>
          )}
        </div>
    </div>
  )
}
