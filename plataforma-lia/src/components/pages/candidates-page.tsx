"use client"

/**
 * CandidatesPage — canonical Funil de Talentos canvas (T002, fork_spa_switch).
 *
 * History
 * -------
 * The 719L "candidates-page" that lived here was the legacy implementation
 * (`CandidatesPageHeader` + `CandidatesPageModals` + `useCandidatesPageCore`).
 * The fork-of-truth chosen by the user shipped a leaner canvas in
 * `app/[locale]/(dashboard)/funil-de-talentos/FunilDeTalentosClient.tsx` —
 * "Compartilhar Busca" + 6 abas + ExpandableAIPrompt. We graduate that
 * canvas to be the SPA-switch canonical: `dashboard-app.tsx` keeps using
 * `setCurrentPage("Funil de Talentos")` and renders THIS component.
 *
 * Compatibility
 * -------------
 * `dashboard-app.tsx` calls this both with props
 * (`<CandidatesPage onAddRecentItem pendingCandidateOpen onCandidateOpened/>`)
 * and without (`<CandidatesPage />` as the default fallback case). We keep
 * the named export and accept the legacy prop bag — the props are routed
 * to the legacy session/recents/deep-link integrations that the new canvas
 * does not yet wire (left as TODOs below). They are safe to ignore for now;
 * dropping them from the signature would crash the existing caller.
 *
 * The legacy URL `/pt/funil-de-talentos` now redirects to `/` (server-side
 * `redirect`) so any back-compat link still lands on the SPA shell.
 */

import { useState, useMemo, useCallback, useEffect } from "react"
import dynamic from "next/dynamic"
import { useTranslations, useLocale } from "next-intl"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BulkActionsBar } from "@/components/ui/bulk-actions-bar"
import { ExpandableAIPrompt } from "@/components/expandable-ai-prompt"
import { useCandidatesList } from "@/hooks/candidates/use-candidates-list"
import { useBulkSelection } from "@/hooks/candidates/use-bulk-selection"
import { useTalentFunnel } from "@/hooks/candidates/use-talent-funnel"
import { Brain, Heart, Share2, Users, AlertCircle, List, Bookmark, Database, Clock, LogIn } from "lucide-react"
import type { Candidate } from "@/components/pages/candidates/types"
import type { TableCandidate } from "@/components/tables"
import type { CandidateLocal } from "@/services/lia-api"
import { LoadingFallback } from "@/components/ui/loading"

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
  const city = c.location_city ?? ""
  const state = c.location_state ?? ""
  const locationStr = [city, state].filter(Boolean).join(",") || "—"
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
    position: c.current_title ?? "—",
    monthlySalary: c.current_salary ?? 0,
    location: locationStr,
    workModel: ((c.work_model_preference || "remoto") as "presencial" | "remoto" | "híbrido"),
    score: c.lia_score ?? 0,
    contractType: ((c.contract_type_preference || "CLT") as "CLT" | "PJ" | "Freelancer"),
    linkedin: c.linkedin_url ?? "",
    skills: [] as string[],
    experience: 0,
    education: [] as Array<{ school?: string; degree?: string }>,
  }
}

// ── Props (legacy compat with dashboard-app.tsx) ─────────────────────────────
type CandidatesPageProps = {
  onAddRecentItem?: (item: {
    id: string
    type: 'vaga' | 'chat' | 'candidato'
    title: string
    subtitle?: string
    meta?: Record<string, string | undefined>
  }) => void
  pendingCandidateOpen?: { candidateId: string; candidateName: string } | null
  onCandidateOpened?: () => void
}

// ── Componente ────────────────────────────────────────────────────────────────
export function CandidatesPage({
  onAddRecentItem,
  pendingCandidateOpen,
  onCandidateOpened,
}: CandidatesPageProps = {}) {
  const t = useTranslations('pipeline')
  const locale = useLocale()
  const {
    candidates: rawCandidates,
    error,
    errorKind,
    total,
    filters,
    updateFilter,
    refresh,
  } = useCandidatesList()

  const {
    selectedCandidates,
    selectedCount,
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

  const [activeTab, setActiveTab] = useState("todos")
  const [shareModalOpen, setShareModalOpen] = useState(false)
  const [shareBulkOpen, setShareBulkOpen] = useState(false)

  const candidates = useMemo(() => rawCandidates.map(toCandidateTableRow), [rawCandidates])
  const selectedIdsArray = useMemo(() => Array.from(selectedCandidates), [selectedCandidates])

  // Candidates filtered by favorites (for FavoritesTab)
  const favoriteIds = useMemo(() => getFavoriteIds(), [getFavoriteIds])
  const pinnedIds = useMemo(() => getPinnedIds(), [getPinnedIds])
  const favoriteNotes = useMemo(() => getFavoriteNotes(), [getFavoriteNotes])
  const favoriteCandidates = useMemo(
    () => favoriteCandidatesData.map(toCandidateTableRow),
    [favoriteCandidatesData]
  )

  const handleSelectAll = () => {
    selectAll(candidates.map(c => c.id))
  }

  const handleBulkAction = (actionId: string) => {
    if (actionId === "share_search") {
      setShareBulkOpen(true)
    }
  }

  const handleCandidateClick = useCallback((candidate: Candidate) => {
    // Surface the click in the recents rail (if the host wired it).
    onAddRecentItem?.({
      id: candidate.id,
      type: 'candidato',
      title: candidate.name,
      subtitle: candidate.current_title ?? undefined,
    })
    window.open(`/funil-de-talentos/candidato/${candidate.id}`, "_blank")
  }, [onAddRecentItem])

  // Deep-link integration: dashboard-app passes `pendingCandidateOpen` when the
  // user navigated here from a notification or recent item. We acknowledge it
  // immediately so the host clears the pending state — actual modal wiring is
  // a TODO that will land alongside the unified candidate-detail drawer.
  useEffect(() => {
    if (pendingCandidateOpen?.candidateId) {
      onCandidateOpened?.()
    }
  }, [pendingCandidateOpen?.candidateId, onCandidateOpened])

  // Redireciona ao login locale-aware preservando `next` para retornar aqui
  // após a reautenticação.
  const handleRelogin = useCallback(() => {
    const next = typeof window !== "undefined"
      ? `${window.location.pathname}${window.location.search}`
      : `/${locale}/funil-de-talentos`
    window.location.href = `/${locale}/login?next=${encodeURIComponent(next)}`
  }, [locale])

  const isAuthError = errorKind === "unauthorized" || errorKind === "forbidden"

  // Mensagem localizada derivada de errorKind (o hook só classifica).
  const errorMessage = (() => {
    if (!errorKind) return error
    const key =
      errorKind === "unauthorized" ? "auth.unauthorizedMessage" :
      errorKind === "forbidden"    ? "auth.forbiddenMessage"    :
      errorKind === "server"       ? "auth.serverErrorMessage"  :
                                     "auth.networkErrorMessage"
    return t(key)
  })()

  // Wrapper para o EAP — registra comandos disparados pelo canvas de busca
  // canônico (Linguagem Natural / Boolean / Job Description / Filtros).
  // TODO: Wirar o command->updateFilter do useCandidatesList numa próxima
  // iteração quando o contrato for definido com produto.
  const handleSearchCommand = useCallback((command: string, _action: string) => {
    if (process.env.NODE_ENV !== "production") {
      console.log("[FunilDeTalentos.EAP] command", { command })
    }
  }, [])

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
            { id: "move_stage", label: t('bulkActions.moveStage'), icon: <Users className="w-3.5 h-3.5" />, onClick: () => handleBulkAction("move_stage") },
            { id: "send_message", label: t('bulkActions.message'), icon: <Share2 className="w-3.5 h-3.5" />, onClick: () => handleBulkAction("send_message") },
            { id: "share_search", label: t('bulkActions.shareSelection'), icon: <Share2 className="w-3.5 h-3.5" />, onClick: () => handleBulkAction("share_search") },
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
              <Brain className="w-3.5 h-3.5 mr-1" />
              {t('tabs.search')}
            </TabsTrigger>
            <TabsTrigger value="favoritos" className="rounded-lg text-xs"><Heart className="w-3.5 h-3.5 mr-1" />{t('tabs.favorites')}</TabsTrigger>
            <TabsTrigger value="listas" className="rounded-lg text-xs"><List className="w-3.5 h-3.5 mr-1" />{t('tabs.lists')}</TabsTrigger>
            <TabsTrigger value="bancos-vivos" className="rounded-lg text-xs"><Database className="w-3.5 h-3.5 mr-1" />{t('tabs.talentPools')}</TabsTrigger>
            <TabsTrigger value="buscas" className="rounded-lg text-xs"><Bookmark className="w-3.5 h-3.5 mr-1" />{t('tabs.savedSearches')}</TabsTrigger>
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
          <TabsContent value="todos" className="mt-4">
            {isAuthError ? (
              <div
                role="alert"
                aria-live="assertive"
                data-testid="funil-relogin-state"
                className="flex flex-col items-center justify-center text-center gap-3 py-14 px-6 bg-lia-bg-primary dark:bg-lia-bg-primary border border-status-error/30 rounded-xl"
              >
                <div className="h-10 w-10 rounded-full bg-status-error/10 flex items-center justify-center">
                  <LogIn className="h-5 w-5 text-status-error" aria-hidden="true" />
                </div>
                <div className="space-y-1">
                  <h2 className="text-sm font-semibold text-lia-text-primary">
                    {t('auth.reloginTitle')}
                  </h2>
                  <p className="text-xs text-lia-text-secondary max-w-sm">{errorMessage}</p>
                </div>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleRelogin}
                  className="h-8 rounded-xl text-xs"
                >
                  <LogIn className="h-3.5 w-3.5 mr-1.5" />
                  {t('auth.reloginCta')}
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-6 py-12">
                <div className="flex items-center gap-2 text-lia-text-primary">
                  <Brain className="h-5 w-5 text-wedo-cyan" />
                  <h2 className="text-base font-medium">Vamos buscar de forma inteligente?</h2>
                </div>
                {error && (
                  <div
                    role="alert"
                    aria-live="polite"
                    data-testid="funil-error-state"
                    className="flex items-start gap-2 p-3 max-w-2xl w-full bg-status-error/10 dark:bg-status-error/10 border border-status-error/30 dark:border-status-error/30 rounded-xl text-xs text-status-error dark:text-status-error"
                  >
                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 flex items-center justify-between gap-3">
                      <span>{errorMessage}</span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => refresh()}
                        className="h-7 rounded-lg text-xs border-status-error/40"
                      >
                        {t('auth.retryCta')}
                      </Button>
                    </div>
                  </div>
                )}
                <ExpandableAIPrompt
                  selectedCandidates={selectedIdsArray}
                  onCommand={handleSearchCommand}
                  filteredCount={candidates.length}
                  totalCount={total}
                  pageContext="candidates"
                />
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
