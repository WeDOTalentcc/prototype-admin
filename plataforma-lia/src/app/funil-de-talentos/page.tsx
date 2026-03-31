// @ts-nocheck
"use client"

import { useState, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BulkSelectionBar } from "@/components/ui/bulk-selection-bar"
import { CandidatesTable } from "@/components/pages/candidates/CandidatesTable"
import { ShareSearchModal } from "@/components/modals/share-search-modal"
import { FavoritesTab } from "@/components/talent-funnel-tabs/favorites-tab"
import { ListsTab } from "@/components/talent-funnel-tabs/lists-tab"
import { SavedSearchesTab } from "@/components/talent-funnel-tabs/saved-searches-tab"
import { useCandidatesList } from "@/hooks/use-candidates-list"
import { useBulkSelection } from "@/hooks/use-bulk-selection"
import { useTalentFunnel } from "@/hooks/use-talent-funnel"
import { textStyles } from "@/lib/design-tokens"
import { Search, Share2, Users, ChevronLeft, ChevronRight, AlertCircle } from "lucide-react"
import type { Candidate, SortConfig } from "@/components/pages/candidates/types"
import type { CandidateLocal } from "@/services/lia-api"
import { cn } from "@/lib/utils"

// ── Mapper: CandidateLocal → Candidate (para reutilizar CandidatesTable) ──────
function toCandidateTableRow(c: CandidateLocal): Candidate {
  const city = c.location_city ?? ""
  const state = c.location_state ?? ""
  const locationStr = [city, state].filter(Boolean).join(", ") || "—"
  return {
    id: c.id,
    candidateId: c.id,
    name: c.name ?? "—",
    email: c.email ?? "",
    phone: c.phone ?? "",
    current_title: c.current_title,
    current_company: c.current_company,
    location_city: c.location_city,
    location_state: c.location_state,
    lia_score: c.lia_score,
    status: c.status,
    tags: c.tags,
    seniority_level: c.seniority_level,
    created_at: c.created_at,
    updated_at: c.updated_at,
    linkedin_url: c.linkedin_url,
    // Required table display fields with defaults
    position: c.current_title ?? "—",
    monthlySalary: c.current_salary ?? 0,
    location: locationStr,
    workModel: (c.work_model_preference as string) ?? "",
    score: c.lia_score ?? 0,
    contractType: (c.contract_type_preference as string) ?? "",
    linkedin: c.linkedin_url ?? "",
  }
}

// ── Componente ─────────────────────────────────────────────────────────────────
export default function FunilDeTalentosPage() {
  const {
    candidates: rawCandidates,
    loading,
    error,
    total,
    currentPage,
    totalPages,
    filters,
    updateFilter,
    goToPage,
  } = useCandidatesList()

  const {
    selectedCandidates,
    selectedCount,
    toggleCandidate,
    selectAll,
    clearSelection,
  } = useBulkSelection()

  const {
    savedSearches,
    addSavedSearch,
    updateSavedSearch,
    removeSavedSearch,
    toggleSavedSearchFavorite,
    getFavoriteIds,
    getPinnedIds,
    getFavoriteNotes,
    toggleFavoriteCandidate,
    togglePinnedCandidate,
    favoriteCandidatesData,
  } = useTalentFunnel()

  const [sortConfig, setSortConfig] = useState<SortConfig>({ column: "created_at", direction: "desc" })
  const [activeTab, setActiveTab] = useState("todos")
  const [shareModalOpen, setShareModalOpen] = useState(false)
  const [shareBulkOpen, setShareBulkOpen] = useState(false)

  const candidates = useMemo(() => rawCandidates.map(toCandidateTableRow), [rawCandidates])
  const selectedIds = useMemo(() => selectedCandidates, [selectedCandidates])
  const selectedIdsArray = useMemo(() => Array.from(selectedCandidates), [selectedCandidates])

  // Candidates filtered by favorites (for FavoritesTab)
  const favoriteIds = useMemo(() => getFavoriteIds(), [getFavoriteIds])
  const pinnedIds = useMemo(() => getPinnedIds(), [getPinnedIds])
  const favoriteNotes = useMemo(() => getFavoriteNotes(), [getFavoriteNotes])
  const favoriteCandidates = useMemo(
    () => favoriteCandidatesData.map(toCandidateTableRow),
    [favoriteCandidatesData]
  )

  const handleSort = (column: string) => {
    setSortConfig(prev =>
      prev.column === column
        ? { column, direction: prev.direction === "asc" ? "desc" : "asc" }
        : { column, direction: "asc" }
    )
  }

  const handleSelectAll = () => {
    selectAll(candidates.map(c => c.id))
  }

  const handleBulkAction = (actionId: string) => {
    if (actionId === "share_search") {
      setShareBulkOpen(true)
    }
  }

  const handleCandidateClick = (candidate: Candidate) => {
    window.open(`/funil-de-talentos/candidato/${candidate.id}`, "_blank")
  }

  // Filtros rápidos
  const STATUS_OPTIONS = ["Novo", "Em triagem", "Aprovado", "Reprovado"]
  const SENIORITY_OPTIONS = ["Júnior", "Pleno", "Sênior", "Especialista"]

  return (
    <div className="min-h-screen bg-gray-50 dark:lia-bg-950">
      {/* Bulk selection bar — fixa no topo quando há seleção */}
      {selectedCount > 0 && (
        <BulkSelectionBar
          selectedCount={selectedCount}
          totalCount={total}
          isAllSelected={selectedCount === candidates.length && candidates.length > 0}
          onSelectAll={handleSelectAll}
          onClearSelection={clearSelection}
          onAction={handleBulkAction}
          actions={[
            { id: "move_stage", label: "Mover Etapa", icon: <Users className="w-4 h-4" /> },
            { id: "send_message", label: "Mensagem", icon: <Share2 className="w-4 h-4" /> },
            { id: "share_search", label: "Compartilhar Seleção", icon: <Share2 className="w-4 h-4" /> },
          ]}
        />
      )}

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-6 space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className={cn(textStyles.title, "text-xl font-semibold")}>
              Funil de Talentos
            </h1>
            <p className={cn(textStyles.secondary, "text-xs mt-0.5")} aria-live="polite">
              {total > 0 ? `${total.toLocaleString("pt-BR")} candidatos` : "Busque candidatos na base"}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="rounded-md border-lia-border-default dark:border-lia-border-subtle self-start sm:self-auto"
            onClick={() => setShareModalOpen(true)}
            disabled={candidates.length === 0}
          >
            <Share2 className="w-4 h-4 mr-1.5" />
            Compartilhar Busca
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:lia-border-800 rounded-md">
            <TabsTrigger value="todos" className="rounded-md text-xs">
              Todos
              {activeTab === "todos" && total > 0 && (
                <Badge className="ml-1.5 h-4 px-1.5 text-micro bg-gray-900 dark:lia-bg-100 text-white dark:lia-text-900">
                  {total}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="favoritos" className="rounded-md text-xs">Favoritos</TabsTrigger>
            <TabsTrigger value="listas" className="rounded-md text-xs">Listas</TabsTrigger>
            <TabsTrigger value="buscas" className="rounded-md text-xs">Buscas Salvas</TabsTrigger>
          </TabsList>

          {/* Tab: Todos */}
          <TabsContent value="todos" className="mt-4 space-y-3">
            {/* SearchBar + filtros rápidos */}
            <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:lia-border-800 rounded-md p-3 space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 lia-text-400" aria-hidden="true" />
                <Input
                  id="funil-search"
                  aria-label="Buscar candidatos"
                  placeholder="Buscar por nome, cargo, empresa ou habilidade..."
                  value={filters.search ?? ""}
                  onChange={e => updateFilter("search", e.target.value)}
                  className="pl-9 text-xs rounded-md border-lia-border-subtle dark:border-lia-border-subtle bg-transparent"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {STATUS_OPTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => updateFilter("status", filters.status === s ? undefined : s)}
                    className={cn(
                      "px-2.5 py-1 text-xs rounded-md border transition-colors",
                      filters.status === s
                        ? "bg-gray-900 dark:lia-bg-50 text-white dark:lia-text-900 border-gray-900 dark:lia-border-50"
                        : "bg-white dark:bg-lia-bg-primary lia-text-600 dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400"
                    )}
                  >
                    {s}
                  </button>
                ))}
                <div className="w-px h-5 bg-gray-200 dark:bg-lia-bg-elevated self-center" />
                {SENIORITY_OPTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => updateFilter("seniority", filters.seniority === s ? undefined : s)}
                    className={cn(
                      "px-2.5 py-1 text-xs rounded-md border transition-colors",
                      filters.seniority === s
                        ? "bg-gray-900 dark:lia-bg-50 text-white dark:lia-text-900 border-gray-900 dark:lia-border-50"
                        : "bg-white dark:bg-lia-bg-primary lia-text-600 dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400"
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Error state */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-status-error/10 dark:bg-status-error/10 border border-status-error/30 dark:border-status-error/30 rounded-md text-xs text-status-error dark:text-status-error">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
              </div>
            )}

            {/* Table */}
            <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:lia-border-800 rounded-md overflow-hidden">
              {!loading && candidates.length === 0 && !error ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-4">
                  <Users className="h-10 w-10 lia-text-300 dark:lia-text-600 mb-3" />
                  <p className="text-sm font-medium lia-text-600 dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                    {filters.search || filters.status || filters.seniority
                      ? "Nenhum candidato encontrado. Tente outros filtros."
                      : "Busque candidatos por nome, habilidade ou cargo"}
                  </p>
                </div>
              ) : (
                <CandidatesTable
                  candidates={candidates}
                  selectedIds={selectedIds}
                  onToggleSelect={toggleCandidate}
                  onSelectAll={handleSelectAll}
                  onCandidateClick={handleCandidateClick}
                  sortConfig={sortConfig}
                  onSort={handleSort}
                  isLoading={loading}
                />
              )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:lia-border-800 rounded-md px-4 py-2.5">
                <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                  Página {currentPage} de {totalPages}
                </span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                    aria-label="Página anterior"
                    className="h-7 w-7 p-0 rounded-md border-lia-border-subtle dark:border-lia-border-subtle"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const start = Math.max(1, currentPage - 2)
                    const page = start + i
                    if (page > totalPages) return null
                    return (
                      <Button
                        key={page}
                        variant={page === currentPage ? "default" : "outline"}
                        size="sm"
                        onClick={() => goToPage(page)}
                        className={cn(
                          "h-7 w-7 p-0 rounded-md text-xs",
                          page === currentPage
                            ? "bg-gray-900 dark:lia-bg-50 text-white dark:lia-text-900"
                            : "border-lia-border-subtle dark:border-lia-border-subtle"
                        )}
                      >
                        {page}
                      </Button>
                    )
                  })}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToPage(currentPage + 1)}
                    disabled={currentPage >= totalPages}
                    aria-label="Próxima página"
                    className="h-7 w-7 p-0 rounded-md border-lia-border-subtle dark:border-lia-border-subtle"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Tab: Favoritos */}
          <TabsContent value="favoritos" className="mt-4">
            <FavoritesTab
              candidates={favoriteCandidates}
              pinnedCandidates={pinnedIds}
              favoriteCandidates={favoriteIds}
              favoriteNotes={favoriteNotes}
              onTogglePin={togglePinnedCandidate}
              onToggleFavorite={toggleFavoriteCandidate}
              onCandidateClick={handleCandidateClick}
              onLIAClick={handleCandidateClick}
            />
          </TabsContent>

          {/* Tab: Listas */}
          <TabsContent value="listas" className="mt-4">
            <ListsTab
              onListSelect={() => undefined}
              onAddToJobs={() => undefined}
              onGoToSearch={() => setActiveTab("todos")}
            />
          </TabsContent>

          {/* Tab: Buscas Salvas */}
          <TabsContent value="buscas" className="mt-4">
            <SavedSearchesTab
              savedSearches={savedSearches}
              onExecuteSearch={search => {
                updateFilter("search", search.query)
                setActiveTab("todos")
              }}
              onAddSearch={addSavedSearch}
              onUpdateSearch={updateSavedSearch}
              onDeleteSearch={removeSavedSearch}
              onToggleFavorite={toggleSavedSearchFavorite}
              onNavigateToSearch={() => setActiveTab("todos")}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Modal: Compartilhar Busca (H.4) */}
      <ShareSearchModal
        open={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        shareType="search"
        title={`Busca — ${filters.search || "Todos os candidatos"}`}
        candidateIds={candidates.map(c => c.id)}
        candidateCount={candidates.length}
        sourceQuery={JSON.stringify(filters)}
      />

      {/* Modal: Compartilhar Seleção (H.3b via bulk) */}
      <ShareSearchModal
        open={shareBulkOpen}
        onClose={() => {
          setShareBulkOpen(false)
          clearSelection()
        }}
        shareType="list"
        title={`Seleção de ${selectedCount} candidatos`}
        candidateIds={selectedIdsArray}
        candidateCount={selectedCount}
      />
    </div>
  )
}
