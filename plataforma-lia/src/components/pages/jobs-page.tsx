"use client"

import React, { useMemo } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Plus, Users, Clock, AlertTriangle, CheckCircle2, Briefcase, Zap, Pause, CheckCircle, XCircle, WifiOff } from "lucide-react"
import { PageTabNavigation } from "@/components/ui/page-tab-navigation"
import type { PageTab } from "@/components/ui/page-tab-navigation"
import { JobKanbanPage } from "./job-kanban-page"
import { LoadingModal as JobsLoadingModal } from "@/components/ui/loading"
import { toast } from "sonner"
import { liaApi } from "@/services/lia-api"
import { useJobsPageCore } from "./jobs/hooks/useJobsPageCore"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { JobsListContent } from "./JobsListContent"
import type { Job } from "@/components/jobs"
import { useTranslations } from 'next-intl'
import { sortJobsByColumn } from "./jobs/utils/jobsPageUtils"

const JobsModalsSection = dynamic(() => import("@/components/pages/jobs/JobsModalsSection").then(m => ({ default: m.JobsModalsSection })), { ssr: false, loading: () => null })
// Phase 4H — Bulk import from ATS
const BulkImportModal = dynamic(() => import("@/components/jobs/BulkImportModal").then(m => ({ default: m.BulkImportModal })), { ssr: false })

interface JobsPageProps {
  onNavigate?: (page: string) => void
  onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  pendingChatOpen?: { mode: 'general' | 'job-creation' } | null
  onChatOpened?: () => void
  pendingJobOpen?: { jobId: string; jobTitle: string } | null
  onJobOpened?: () => void
}

export function JobsPage(props: JobsPageProps) {
  const state = useJobsPageCore(props)
  // Phase 4H — Bulk import modal state
  const [showBulkImportModal, setShowBulkImportModal] = React.useState(false)
  const t = useTranslations('jobs')

  const { statusOrder, groupedJobs } = useMemo(() => {
    const order = [
      'Ativa', 'Aprovada', 'Aguardando aprovação', 'Reaberta', 'Paralisada', 'Interna',
      'Rascunho', 'Fechada (preenchida)', 'Fechada (expirada)', 'Cancelada', 'Concluída', 'Arquivada'
    ] as const
    const grouped: Record<string, Job[]> = {}
    order.forEach(s => { grouped[s] = [] })
    const sorted = sortJobsByColumn(state.filteredJobs || [], state.jobsSortColumn, state.jobsSortDirection)
    sorted.forEach((job: Job) => { if (grouped[job.status]) grouped[job.status].push(job) })
    return { statusOrder: order, groupedJobs: grouped }
  }, [state.filteredJobs, state.jobsSortColumn, state.jobsSortDirection])

  if (state.showKanban) {
    if (!state.selectedJob) {
      return (
        <div className="h-full flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-primary">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-lia-border-default border-t-lia-border-medium rounded-full animate-spin motion-reduce:animate-none mx-auto mb-3" />
            <p className="text-base-ui text-lia-text-tertiary">{t("loadingJob")}</p>
          </div>
        </div>
      )
    }
    return <JobKanbanPage key={`kanban-${state.selectedJob.id}`} job={state.selectedJob as unknown as Record<string, unknown>} onBack={state.handleBackToJobs} />
  }

  const {
    hasMounted, activeFilter, allJobs,
    deselectAllJobs, filteredJobs, isLoadingJobs, jobsError,
    navigationFilters,
    openJobCreationChat, setActiveFilter,
    setShowCreateJobModal,
    showReport, reportJob, handleCloseReport,
    showCompareModal, setShowCompareModal, showPublishModal, setShowPublishModal,
    showUnpublishModal, setShowUnpublishModal, showInsightsModal, setShowInsightsModal,
    showDuplicateModal, setShowDuplicateModal, showStatusModal, setShowStatusModal,
    statusModalMode, showAssignRecruiterModal, setShowAssignRecruiterModal,
    showCreateJobModal,
    showScreeningChannelsModal, setShowScreeningChannelsModal,
    showScreeningSettingsModal, setShowScreeningSettingsModal,
    showScreeningSchedulingModal, setShowScreeningSchedulingModal,
    screeningConfig, updateScreeningConfig,
    showReactivateScreeningDialog, setShowReactivateScreeningDialog,
    reactivateScreeningJobs, setReactivateScreeningJobs,
    reactivateEndDate, setReactivateEndDate,
    showWSITutorialModal, setShowWSITutorialModal,
    companyRecruiters, selectedJobsForBatch, dashboardStats,
    setBackendJobs, setSelectedJob, setPreviewJob,
    setPendingNavigateJobId, loadBackendJobs, setActivePreviewTab,
    selectedJob, navigateToCreatedJob,
    isExternalSourceFallback,
  } = state

  if (!hasMounted) {
    return (
      <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <div className="p-2.5 max-w-full overflow-x-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="h-6 w-48 bg-lia-interactive-active dark:bg-lia-bg-secondary rounded-lg animate-pulse motion-reduce:animate-none" />
                <div className="h-4 w-64 bg-lia-interactive-active dark:bg-lia-bg-secondary rounded-lg animate-pulse motion-reduce:animate-none mt-2" />
              </div>
              <div className="h-8 w-24 bg-lia-interactive-active dark:bg-lia-bg-secondary rounded-lg animate-pulse motion-reduce:animate-none" />
            </div>
            <div className="space-y-2 mt-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-12 bg-lia-interactive-active dark:bg-lia-bg-secondary rounded-lg animate-pulse motion-reduce:animate-none" />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ErrorBoundarySection>
    <div className="h-full flex flex-col bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden relative">
      <div className="flex-shrink-0 px-4 pt-3 pb-0 bg-lia-bg-primary dark:bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-lg font-semibold text-lia-text-primary">
            {t("title")}
          </h1>
          <div className="flex items-center gap-2">
            <Button
              className="gap-2 h-8 px-3 bg-lia-btn-primary-hover"
              onClick={() => setShowCreateJobModal(true)}
            >
              <Plus className="w-4 h-4" />
              {t("newJob")}
            </Button>
          </div>
        </div>

        <PageTabNavigation
          tabs={navigationFilters.map((filter) => {
            const TAB_ICONS: Record<string, React.ComponentType<{className?: string}>> = {
              'todas': Briefcase,
              'ativas': Zap,
              'urgentes': AlertTriangle,
              'paralisadas': Pause,
              'concluidas': CheckCircle,
              'canceladas': XCircle,
            }
            return {
              id: filter.id,
              label: filter.label,
              icon: TAB_ICONS[filter.id] || Briefcase,
              count: (filter as Record<string, unknown>).isDashboard ? null : filter.count,
            } satisfies PageTab
          })}
          activeTab={activeFilter}
          onTabChange={setActiveFilter}
          isLoading={isLoadingJobs}
        />

        {!isLoadingJobs && dashboardStats && (
          <div className="flex items-center gap-6 mt-2 mb-1">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{(dashboardStats as Record<string, number>).noFunil || 0}</span> {t("inFunnel")}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-wedo-cyan" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{(dashboardStats as Record<string, number>).entrevistasRecentes || 0}</span> {t("interviews")}
              </span>
            </div>
            {((dashboardStats as Record<string, number>).taxaConversao || 0) > 0 && (
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-xs text-lia-text-secondary">
                  <span className="font-semibold text-lia-text-primary">{(dashboardStats as Record<string, number>).taxaConversao}%</span> {t("conversion")}
                </span>
              </div>
            )}
            {((dashboardStats as Record<string, number>).atRisco || 0) > 0 && (
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
                <span className="text-xs text-lia-text-secondary">
                  <span className="font-semibold text-rose-600">{(dashboardStats as Record<string, number>).atRisco}</span> {t("atRisk")}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col overflow-hidden px-4 pt-2 pb-2">
        {isExternalSourceFallback && !isLoadingJobs && (
          <div className="flex items-center gap-2 px-3 py-2 mb-2 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 text-amber-700 dark:text-amber-400">
            <WifiOff className="w-3.5 h-3.5 shrink-0" />
            <span className="text-xs">{t("externalSourceUnavailable")}</span>
          </div>
        )}
        <JobsListContent
          {...(state as unknown as React.ComponentProps<typeof JobsListContent>)}
          setShowBulkImportModal={setShowBulkImportModal}
          toggleJobFilter={state.toggleJobFilter as (category: string, key: string, value: unknown) => void}
          activePreviewTab={state.activePreviewTab as "screening" | "pipeline"}
          statusOrder={statusOrder}
          groupedJobs={groupedJobs}
        />

        <JobsModalsSection
          allJobs={allJobs}
          selectedJobsForBatch={selectedJobsForBatch}
          showReport={showReport}
          reportJob={reportJob}
          onCloseReport={handleCloseReport}
          showCompareModal={showCompareModal}
          onCloseCompareModal={() => setShowCompareModal(false)}
          showPublishModal={showPublishModal}
          onClosePublishModal={() => setShowPublishModal(false)}
          showUnpublishModal={showUnpublishModal}
          onCloseUnpublishModal={() => setShowUnpublishModal(false)}
          showInsightsModal={showInsightsModal}
          onCloseInsightsModal={() => setShowInsightsModal(false)}
          showDuplicateModal={showDuplicateModal}
          onCloseDuplicateModal={() => setShowDuplicateModal(false)}
          showStatusModal={showStatusModal}
          onCloseStatusModal={() => setShowStatusModal(false)}
          statusModalMode={statusModalMode}
          showAssignRecruiterModal={showAssignRecruiterModal}
          onCloseAssignRecruiterModal={() => setShowAssignRecruiterModal(false)}
          showCreateJobModal={showCreateJobModal}
          onCloseCreateJobModal={() => setShowCreateJobModal(false)}
          showScreeningChannelsModal={showScreeningChannelsModal}
          onCloseScreeningChannelsModal={() => setShowScreeningChannelsModal(false)}
          showScreeningSettingsModal={showScreeningSettingsModal}
          onCloseScreeningSettingsModal={() => setShowScreeningSettingsModal(false)}
          showScreeningSchedulingModal={showScreeningSchedulingModal}
          onCloseScreeningSchedulingModal={() => setShowScreeningSchedulingModal(false)}
          screeningConfig={screeningConfig}
          updateScreeningConfig={updateScreeningConfig}
          showReactivateScreeningDialog={showReactivateScreeningDialog}
          reactivateScreeningJobs={reactivateScreeningJobs as unknown as Job[]}
          reactivateEndDate={reactivateEndDate}
          showWSITutorialModal={showWSITutorialModal}
          onCloseWSITutorialModal={() => setShowWSITutorialModal(false)}
          companyRecruiters={companyRecruiters}
          activeFilter={activeFilter}
          onDeselectAll={deselectAllJobs}
          onRefreshJobs={loadBackendJobs}
          onSetBackendJobs={setBackendJobs}
          onSetSelectedJob={setSelectedJob}
          onSetPreviewJob={setPreviewJob}
          onSetActiveFilter={setActiveFilter}
          onOpenJobCreationChat={openJobCreationChat}
          onSetPendingNavigateJobId={setPendingNavigateJobId}
          onNavigateToCreatedJob={navigateToCreatedJob}
          onSetReactivateScreeningDialog={setShowReactivateScreeningDialog}
          onSetReactivateScreeningJobs={setReactivateScreeningJobs as unknown as (jobs: Job[]) => void}
          onSetReactivateEndDate={setReactivateEndDate}
          jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
            id: String(job.id),
            code: job.jobId,
            title: job.title,
            status: job.status,
            is_published: job.status === "Ativa",
            published_channels: []
          })) as unknown as Job[]}
          onPublish={async (jobIds, channels, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                await liaApi.updateJobVacancy(job.backendId, { status: "Ativa", published_website: channels.includes("portal") })
                if (channels.includes("linkedin")) {
                  try { const r = await liaApi.publishToLinkedIn(job.backendId); if ((r as Record<string, unknown>)?.mock) toast.info(t("linkedinSimulated")) } catch {}
                }
                if (channels.includes("indeed")) {
                  try { const r = await liaApi.publishToIndeed(job.backendId); if ((r as Record<string, unknown>)?.note) toast.info(t("indeedSimulated")) } catch {}
                }
              }
              toast.success(t("publishedSuccess"))
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch { toast.error(t("publishError")) }
          }}
          onUnpublish={async (jobIds, options) => {
            try {
              const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
              for (const job of selectedJobs) {
                if (!job.backendId) continue
                if (job.publishedLinkedIn) { try { await liaApi.unpublishFromPlatform(job.backendId, "linkedin") } catch {} }
                if (job.publishedIndeed) { try { await liaApi.unpublishFromPlatform(job.backendId, "indeed") } catch {} }
                if (options?.freezeJob) { try { await liaApi.updateJobVacancy(job.backendId, { status: "Paralisada" }) } catch {} }
              }
              toast.success(t("unpublishedSuccess"))
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch { toast.error(t("unpublishError")) }
          }}
          onOpenCommunicationModal={(jobIds, templateCategory) => {
            const titles = allJobs.filter(job => jobIds.includes(String(job.id))).map(j => j.title).join(", ")
            toast.info(t("communicationFor", { titles }), { duration: 8000 })
          }}
        />
      </div>
      {/* Phase 4H — Bulk import modal */}
      <BulkImportModal
        isOpen={showBulkImportModal}
        onClose={() => setShowBulkImportModal(false)}
        onSuccess={() => {
          setShowBulkImportModal(false)
          state.loadBackendJobs?.()
        }}
      />
    </div>
    </ErrorBoundarySection>
  )
}
