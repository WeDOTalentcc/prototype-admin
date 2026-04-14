"use client"

import { useState, useMemo } from"react"
import dynamic from "next/dynamic"
import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Badge } from"@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { BulkActionsBar } from"@/components/ui/bulk-actions-bar"
import { CandidatesTable } from"@/components/pages/candidates/CandidatesTable"
import { useCandidatesList } from"@/hooks/candidates/use-candidates-list"
import { useBulkSelection } from"@/hooks/candidates/use-bulk-selection"
import { useTalentFunnel } from"@/hooks/candidates/use-talent-funnel"
import { textStyles } from"@/lib/design-tokens"
import { Search, Heart, Share2, Users, ChevronLeft, ChevronRight, AlertCircle, List, Bookmark, Database, Clock } from"lucide-react"
import type { Candidate, SortConfig } from"@/components/pages/candidates/types"
import type { TableCandidate } from"@/components/tables"
import type { CandidateLocal } from"@/services/lia-api"
import { cn } from"@/lib/utils"
import { LoadingFallback } from"@/components/ui/loading"

function DynamicLoadingFallback({ textKey }: { textKey: string }) {
  const t = useTranslations('pipeline')
  return <LoadingFallback height="h-40" text={t(textKey)} />
}

const FavoritesTab = dynamic(
  () => import("@/components/talent-funnel-tabs/favorites-tab").then(m => ({ default: m.FavoritesTab })),
  { ssr: false, loading: () => <DynamicLoadingFallback textKey="loading.favorites" /> }
)

const ListsTab = dynamic(
  () => import("@/components/talent-funnel-tabs/lists-tab").then(m => ({ default: m.ListsTab })),
  { ssr: false, loading: () => <DynamicLoadingFallback textKey="loading.lists" /> }
)

const SavedSearchesTab = dynamic(
  () => import("@/components/talent-funnel-tabs/saved-searches-tab").then(m => ({ default: m.SavedSearchesTab })),
  { ssr: false, loading: () => <DynamicLoadingFallback textKey="loading.savedSearches" /> }
)

const HistoryTab = dynamic(
  () => import("@/components/talent-funnel-tabs/history-tab").then(m => ({ default: m.HistoryTab })),
  { ssr: false, loading: () => <DynamicLoadingFallback textKey="loading.history" /> }
)

const TalentPoolsTab = dynamic(
  () => import("@/components/pages-candidates/TalentPoolsTab"),
  { ssr: false, loading: () => <DynamicLoadingFallback textKey="loading.talentPools" /> }
)

const ShareSearchModal = dynamic(
  () => import("@/components/modals/share-search-modal").then(m => ({ default: m.ShareSearchModal })),
  { ssr: false }
)

// ── Mapper: CandidateLocal → Candidate (para reutilizar CandidatesTable) ──────
function toCandidateTableRow(c: CandidateLocal): Candidate {
  const city = c.location_city ??""
  const state = c.location_state ??""
  const locationStr = [city, state].filter(Boolean).join(",") ||"—"
  return {
    id: c.id,
    candidateId: c.id,
    name: c.name ??"—",
    email: c.email ??"",
    phone: c.phone ??"",
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
    position: c.current_title ??"—",
    monthlySalary: c.current_salary ?? 0,
    location: locationStr,
    workModel: ((c.work_model_preference ||"remoto") as"presencial" |"remoto" |"híbrido"),
    score: c.lia_score ?? 0,
    contractType: ((c.contract_type_preference ||"CLT") as"CLT" |"PJ" |"Freelancer"),
    linkedin: c.linkedin_url ??"",
    skills: [] as string[],
    experience: 0,
    education: [] as Array<{ school?: string; degree?: string }>,
  }
}

// ── Componente ─────────────────────────────────────────────────────────────────
export default function FunilDeTalentosPage() {
  const t = useTranslations('pipeline')
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

  const [sortConfig, setSortConfig] = useState<SortConfig>({ column:"created_at", direction:"desc" })
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
        ? { column, direction: prev.direction ==="asc" ?"desc" :"asc" }
        : { column, direction:"asc" }
    )
  }

  const handleSelectAll = () => {
    selectAll(candidates.map(c => c.id))
  }

  const handleBulkAction = (actionId: string) => {
    if (actionId ==="share_search") {
      setShareBulkOpen(true)
    }
  }

  const handleCandidateClick = (candidate: Candidate) => {
    window.open(`/funil-de-talentos/candidato/${candidate.id}`,"_blank")
  }

  // Filtros rápidos
  
const STATUS_COLORS: Record<string, { active: string; inactive: string }> = {
  "Novo": { active:"bg-cyan-50 dark:bg-cyan-950/30 text-cyan-700 dark:text-cyan-400 border-cyan-200 dark:border-cyan-800", inactive:"bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-cyan-300" },
  "Em triagem": { active:"bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800", inactive:"bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-amber-300" },
  "Aprovado": { active:"bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800", inactive:"bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-emerald-300" },
  "Reprovado": { active:"bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800", inactive:"bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-rose-300" },
}

const STATUS_OPTIONS = [
  { value: "Novo", labelKey: "filters.statusNew" },
  { value: "Em triagem", labelKey: "filters.statusScreening" },
  { value: "Aprovado", labelKey: "filters.statusApproved" },
  { value: "Reprovado", labelKey: "filters.statusRejected" },
] as const
const SENIORITY_OPTIONS = [
  { value: "Júnior", labelKey: "filters.seniorityJunior" },
  { value: "Pleno", labelKey: "filters.seniorityMid" },
  { value: "Sênior", labelKey: "filters.senioritySenior" },
  { value: "Especialista", labelKey: "filters.senioritySpecialist" },
] as const

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary">
      {/* Bulk selection bar — fixa no topo quando há seleção */}
      {selectedCount > 0 && (
        <BulkActionsBar
          selectedCount={selectedCount}
          totalCount={total}
          layout="fixed"
          showSelectAll
          isAllSelected={selectedCount === candidates.length && candidates.length > 0}
          onSelectAll={handleSelectAll}
          onDeselectAll={clearSelection}
          actions={[
            { id:"move_stage", label: t('bulkActions.moveStage'), icon: <Users className="w-3.5 h-3.5" />, onClick: () => handleBulkAction("move_stage") },
            { id:"send_message", label: t('bulkActions.message'), icon: <Share2 className="w-3.5 h-3.5" />, onClick: () => handleBulkAction("send_message") },
            { id:"share_search", label: t('bulkActions.shareSelection'), icon: <Share2 className="w-3.5 h-3.5" />, onClick: () => handleBulkAction("share_search") },
          ]}
        />
      )}

      <div className="max-w-screen-2xl mx-auto px-4 pt-3 pb-0 space-y-0">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-lg font-semibold text-lia-text-primary">
            {t('title')}
          </h1>
          <Button
            variant="outline"
            size="sm"
            className="rounded-xl border-lia-border-default dark:border-lia-border-subtle"
            onClick={() => setShareModalOpen(true)}
            disabled={candidates.length === 0}
          >
            <Share2 className="w-4 h-4 mr-1.5" />
            {t('shareSearch')}
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-lg">
            <TabsTrigger value="todos" className="rounded-lg text-xs">
              <Search className="w-3.5 h-3.5 mr-1" />
              {t('tabs.search')}
              {activeTab ==="todos" && total > 0 && (
                <Badge className="ml-1.5 h-4 px-1.5 text-micro  dark:bg-wedo-cyan/20 dark:text-wedo-cyan">
                  {total}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="favoritos" className="rounded-lg text-xs"><Heart className="w-3.5 h-3.5 mr-1" />{t('tabs.favorites')}</TabsTrigger>
            <TabsTrigger value="listas" className="rounded-lg text-xs"><List className="w-3.5 h-3.5 mr-1" />{t('tabs.lists')}</TabsTrigger>
            <TabsTrigger value="buscas" className="rounded-lg text-xs"><Bookmark className="w-3.5 h-3.5 mr-1" />{t('tabs.savedSearches')}</TabsTrigger>
            <TabsTrigger value="bancos-vivos" className="rounded-lg text-xs"><Database className="w-3.5 h-3.5 mr-1" />{t('tabs.talentPools')}</TabsTrigger>
            <TabsTrigger value="historico" className="rounded-lg text-xs"><Clock className="w-3.5 h-3.5 mr-1" />{t('tabs.history')}</TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-6 mt-2 mb-1">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-wedo-cyan animate-pulse" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{total.toLocaleString()}</span> {t('stats.candidates')}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Heart className="w-3.5 h-3.5 text-rose-500" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{favoriteIds.size}</span> {t('stats.favorites')}
              </span>
            </div>
          </div>

          {/* Tab: Todos */}
          <TabsContent value="todos" className="mt-4 space-y-3">
            {/* SearchBar + filtros rápidos */}
            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-3 space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-lia-text-tertiary" aria-hidden="true" />
                <Input
                  id="funil-search"
                  aria-label={t('searchAriaLabel')}
                  placeholder={t('searchPlaceholder')}
                  value={filters.search ??""}
                  onChange={e => updateFilter("search", e.target.value)}
                  className="pl-9 text-xs rounded-xl border-lia-border-subtle dark:border-lia-border-subtle bg-transparent focus:border-wedo-cyan/40 transition-colors"
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {STATUS_OPTIONS.map(s => (
                  <button
                    key={s.value}
                    onClick={() => updateFilter("status", filters.status === s.value ? undefined : s.value)}
                    className={cn("px-2.5 py-1 text-xs rounded-md border transition-colors",
                      filters.status === s.value
                        ? (STATUS_COLORS[s.value]?.active ||"bg-lia-btn-primary-bg dark:bg-lia-bg-secondary text-white dark:text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-subtle")
                        : (STATUS_COLORS[s.value]?.inactive ||"bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium")
                    )}
                  >
                    {t(s.labelKey)}
                  </button>
                ))}
                <div className="w-px h-5 bg-lia-border-subtle self-center" />
                {SENIORITY_OPTIONS.map(s => (
                  <button
                    key={s.value}
                    onClick={() => updateFilter("seniority", filters.seniority === s.value ? undefined : s.value)}
                    className={cn("px-2.5 py-1 text-xs rounded-md border transition-colors",
                      filters.seniority === s.value
                        ?"bg-lia-btn-primary-bg dark:bg-lia-bg-secondary text-white dark:text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-subtle"
                        :"bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium"
                    )}
                  >
                    {t(s.labelKey)}
                  </button>
                ))}
              </div>
            </div>

            {/* Error state */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-status-error/10 dark:bg-status-error/10 border border-status-error/30 dark:border-status-error/30 rounded-xl text-xs text-status-error dark:text-status-error">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
              </div>
            )}

            {/* Table */}
            <div className="bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden">
              {!loading && candidates.length === 0 && !error ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-4">
                  <Users className="h-10 w-10 text-lia-text-disabled dark:text-lia-text-secondary mb-3" />
                  <p className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                    {filters.search || filters.status || filters.seniority
                      ? t('emptyState.noResults')
                      : t('emptyState.searchPrompt')}
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
              <div className="flex items-center justify-between bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl px-4 py-2.5">
                <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                  {t('pagination.page', { current: currentPage, total: totalPages })}
                </span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => goToPage(currentPage - 1)}
                    disabled={currentPage <= 1}
                    aria-label={t('pagination.previousPage')}
                    className="h-7 w-7 p-0 rounded-xl border-lia-border-subtle dark:border-lia-border-subtle"
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
                        variant={page === currentPage ?"primary" :"outline"}
                        size="sm"
                        onClick={() => goToPage(page)}
                        className={cn("h-7 w-7 p-0 rounded-md text-xs",
                          page === currentPage
                            ?"bg-lia-btn-primary-bg dark:bg-lia-bg-secondary text-white dark:text-lia-text-primary"
                            :"border-lia-border-subtle dark:border-lia-border-subtle"
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
                    aria-label={t('pagination.nextPage')}
                    className="h-7 w-7 p-0 rounded-xl border-lia-border-subtle dark:border-lia-border-subtle"
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

              candidates={favoriteCandidates as unknown as TableCandidate[]}

              pinnedCandidates={pinnedIds}

              favoriteCandidates={favoriteIds}
              favoriteNotes={favoriteNotes}
              onTogglePin={togglePinnedCandidate}
              onToggleFavorite={toggleFavoriteCandidate}
              onCandidateClick={handleCandidateClick as any}
              onLIAClick={handleCandidateClick as any}
            />
          </TabsContent>

          {/* Tab: Listas */}
          <TabsContent value="listas" className="mt-4" forceMount={undefined}>
            {activeTab === "listas" && (
              <ListsTab
                onListSelect={() => undefined}
                onAddToJobs={() => undefined}
                onGoToSearch={() => setActiveTab("todos")}
              />
            )}
          </TabsContent>

          {/* Tab: Buscas Salvas */}
          <TabsContent value="buscas" className="mt-4" forceMount={undefined}>
            {activeTab === "buscas" && (
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
            )}
          </TabsContent>

          <TabsContent value="bancos-vivos" className="mt-4" forceMount={undefined}>
            {activeTab === "bancos-vivos" && (
              <TalentPoolsTab onSelectPool={(id) => { window.location.href = `/bancos-de-talentos/${id}` }} />
            )}
          </TabsContent>

          <TabsContent value="historico" className="mt-4" forceMount={undefined}>
            {activeTab === "historico" && (
              <HistoryTab
                history={[]}
                onReExecuteSearch={() => {}}
                onSaveAsSearch={() => {}}
                onDeleteItem={() => {}}
                onClearAll={() => {}}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Modal: Compartilhar Busca (H.4) */}
      {shareModalOpen && (
        <ShareSearchModal
          open={shareModalOpen}
          onClose={() => setShareModalOpen(false)}
          shareType="search"
          title={t('shareModal.searchTitle', { query: filters.search || t('shareModal.allCandidates') })}
          candidateIds={candidates.map(c => c.id)}
          candidateCount={candidates.length}
          sourceQuery={JSON.stringify(filters)}
        />
      )}

      {/* Modal: Compartilhar Seleção (H.3b via bulk) */}
      {shareBulkOpen && (
        <ShareSearchModal
          open={shareBulkOpen}
          onClose={() => {
            setShareBulkOpen(false)
            clearSelection()
          }}
          shareType="list"
          title={t('shareModal.selectionTitle', { count: selectedCount })}
          candidateIds={selectedIdsArray}
          candidateCount={selectedCount}
        />
      )}
    </div>
  )
}
