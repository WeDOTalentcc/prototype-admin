"use client"

import React, { useCallback, useMemo } from "react"
import { useTranslations } from "next-intl"
import { useKanbanPageCore } from "@/components/pages/job-kanban/hooks/useKanbanPageCore"
import { KanbanJobHeader } from "@/components/pages/job-kanban/KanbanJobHeader"
import { KanbanPageModals } from "@/components/pages/job-kanban/KanbanPageModals"
import { KanbanPageContent } from "@/components/pages/job-kanban/KanbanPageContent"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { useVacancySearch } from "@/hooks/search/useVacancySearch"
import dynamic from "next/dynamic"

const VacancySearchModal = dynamic(
  () => import("@/components/pages/job-kanban/VacancySearchModal").then(m => ({ default: m.VacancySearchModal })),
  { ssr: false, loading: () => null }
)
const VacancyCandidateSearchResults = dynamic(
  () => import("@/components/pages/job-kanban/VacancyCandidateSearchResults").then(m => ({ default: m.VacancyCandidateSearchResults })),
  { ssr: false, loading: () => null }
)
import VagaProgressBar from "@/components/jobs/VagaProgressBar"
import "@/components/pages/job-kanban-page.css"

export function JobKanbanPage({ job, onBack }: { job?: Record<string, unknown>, onBack?: () => void }) {
  const t = useTranslations('kanban')
  const state = useKanbanPageCore({ job, onBack })
  const vacancyId = String(state.currentJob?.backendId || state.currentJob?.id || "")
  const enrichedJD = (() => {
    const ej = state.currentJob?.enriched_jd
    if (!ej) return (state.currentJob?.description as string) || ""
    if (typeof ej === "string") return ej
    return (ej as Record<string, unknown>)?.content as string || JSON.stringify(ej)
  })()
  const handleCandidatesAdded = useCallback(() => {
    state.router?.refresh()
  }, [state.router])
  const initialQuery = useMemo(() => {
    const title = (state.currentJob?.title as string) || ""
    const level = (state.currentJob?.level as string) || ""
    const skills = (state.currentJob?.required_skills as string[] | undefined) || []
    const parts: string[] = []
    if (title) parts.push(title)
    if (level) parts.push(level)
    if (skills.length > 0) parts.push(skills.slice(0, 4).join(", "))
    return parts.join(", ")
  }, [state.currentJob?.title, state.currentJob?.level, state.currentJob?.required_skills])
  const vs = useVacancySearch(vacancyId, enrichedJD, handleCandidatesAdded)

  if (!state.isClient) {
    return (
      <div className="flex items-center justify-center h-screen bg-lia-bg-primary" role="status" aria-live="polite" aria-label={t('loading')}>
        <div className="flex flex-col items-center gap-4" role="status" aria-live="polite" aria-label={t('loading')}>
          <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-lia-border-medium" role="status" aria-live="polite" aria-label={t('loading')}></div>
          <span className="text-sm text-lia-text-tertiary">{t('loading')}</span>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundarySection>
    <div className="h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col overflow-hidden">
      <div className="flex-shrink-0">
      <KanbanJobHeader
        onBack={onBack}
        router={state.router}
        currentJob={state.currentJob}
        jobEditForm={state.jobEditForm}
        setJobEditForm={state.setJobEditForm}
        setJobStatusModalMode={state.setJobStatusModalMode as any}
        setShowJobStatusModal={state.setShowJobStatusModal}
        setShowCloseVacancyModal={state.setShowCloseVacancyModal}
        setActiveTab={state.setActiveTab as any}
        computedSuggestions={state.computedSuggestions}
        setShowLiaSuggestionsPanel={state.setShowLiaSuggestionsPanel}
        allTableCandidates={state.allTableCandidates}
        selectedCandidates={state.selectedCandidates}
        setSelectedCandidates={state.setSelectedCandidates}
        setShowShareGestorModal={state.setShowShareGestorModal}
        handleShowReport={state.handleShowReport}
        activeTab={state.activeTab}
        setShowJobEditor={state.setShowJobEditor}
        pipelineInheritance={state.pipelineInheritance}
        setJobLocalOverrides={state.setJobLocalOverrides}
        onOpenVacancySearch={vs.openModal}
      />
      </div>

      {/* Workflow Rail — Campaign progress bar */}
      <div className="flex-shrink-0">
      <VagaProgressBar jobId={String(state.currentJob?.id || "")} onNavigateToStage={(stage) => state.setActiveTab?.(stage as any)} />
      </div>

      {state.proactiveInsights.length > 0 && state.activeTab === 'management' && (
        <div className="px-4 py-2 space-y-1.5">
          {state.proactiveInsights.slice(0, 3).map(insight => (
            <div
              key={insight.id}
              className={`flex items-start gap-2 px-3 py-2 rounded-xl border text-xs ${
                insight.urgency === 'urgent' ? 'bg-status-error/10 border-status-error/30 text-status-error' :
                insight.urgency === 'high' ? 'bg-status-warning/10 border-status-warning/30 text-status-warning' :
                'bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary'
              }`}
            >
              <span className="font-medium flex-shrink-0">{insight.title}</span>
              <span className="flex-1">{insight.message}</span>
              <button
                onClick={() => state.dismissInsight(insight.id)}
                className="flex-shrink-0 opacity-50 hover:opacity-100"
                aria-label={t('dismiss')}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <KanbanPageContent state={state} />

      <KanbanPageModals {...state} />

      <VacancySearchModal
        isOpen={vs.showModal}
        onClose={vs.closeModal}
        vacancyTitle={(state.currentJob?.title as string) || ""}
        enrichedJD={enrichedJD}
        searchSource={vs.searchSource}
        onSearchSourceChange={vs.setSearchSource}
        requireEmails={vs.requireEmails}
        onRequireEmailsChange={vs.setRequireEmails}
        requirePhoneNumbers={vs.requirePhoneNumbers}
        onRequirePhoneNumbersChange={vs.setRequirePhoneNumbers}
        mode={vs.mode}
        onModeChange={vs.setMode}
        autoConfig={vs.autoConfig}
        onAutoConfigChange={vs.setAutoConfig}
        onSubmit={vs.handleSearchSubmit}
        creditEstimate={vs.creditEstimate}
        initialQuery={initialQuery}
        initialJdContent={enrichedJD}
      />

      <VacancyCandidateSearchResults
        isOpen={vs.showResults}
        vacancyId={vacancyId}
        onClose={vs.closeResults}
        vacancyTitle={(state.currentJob?.title as string) || ""}
        mode={vs.mode}
        autoConfig={vs.autoConfig}
        isSearching={vs.isSearching}
        searchResults={vs.searchResults}
        totalResults={vs.totalResults}
        selectedIds={vs.selectedIds}
        searchFeedbacks={vs.searchFeedbacks}
        onToggleSelect={vs.toggleSelect}
        onSelectAll={vs.selectAll}
        onClearSelection={vs.clearSelection}
        onFeedback={vs.handleFeedback}
        onAddToVacancy={vs.addSelectedToVacancy}
        onAddAuto={vs.addAutoCandidates}
        onLoadMore={vs.handleLoadMore}
        onEditSearch={vs.handleEditSearch}
        searchProgress={vs.searchProgress}
        lastSearchQuery={vs.lastSearchParams?.query || ""}
        lastSearchEntities={vs.lastSearchParams?.entities || null}
        showAutoConfirm={vs.showAutoConfirm}
        autoQualifyingPreview={vs.autoQualifyingPreview}
        onConfirmAutoAdd={vs.confirmAutoAdd}
        onCancelAutoAdd={vs.cancelAutoAdd}
        revealedContacts={vs.revealedContacts}
        isRevealing={vs.isRevealing}
        onRevealContact={vs.handleRevealContact}
      />

    </div>
    </ErrorBoundarySection>
  )
}
