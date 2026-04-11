"use client"

import React, { useMemo } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Plus, Users, Clock, AlertTriangle, CheckCircle2, Briefcase, Zap, Pause, CheckCircle, XCircle } from "lucide-react"
import { JobKanbanPage } from "./job-kanban-page"
import { LoadingModal as JobsLoadingModal } from "@/components/ui/loading"
import { toast } from "sonner"
import { liaApi } from "@/services/lia-api"
import { useJobsPageCore } from "./jobs/hooks/useJobsPageCore"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { JobsListContent } from "./JobsListContent"
import type { Job } from "@/components/jobs"

const JobsModalsSection = dynamic(() => import("@/components/pages/jobs/JobsModalsSection").then(m => ({ default: m.JobsModalsSection })), { ssr: false, loading: () => null })
const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false, loading: () => <JobsLoadingModal /> })

interface JobsPageProps {
  onNavigate?: (page: string) => void
  onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  pendingChatOpen?: { mode: 'general' | 'job-creation' } | null
  onChatOpened?: () => void
  pendingJobOpen?: { jobId: string; jobTitle: string } | null
  onJobOpened?: () => void
}

export function JobsPage(props: JobsPageProps) {
  const { onAddRecentItem } = props
  const state = useJobsPageCore(props)

  const { statusOrder, groupedJobs } = useMemo(() => {
    const order = [
      'Ativa', 'Aprovada', 'Aguardando aprovação', 'Reaberta', 'Paralisada', 'Interna',
      'Rascunho', 'Fechada (preenchida)', 'Fechada (expirada)', 'Cancelada', 'Concluída', 'Arquivada'
    ] as const
    const grouped: Record<string, Job[]> = {}
    order.forEach(s => { grouped[s] = [] })
    ;(state.filteredJobs || []).forEach((job: Job) => { if (grouped[job.status]) grouped[job.status].push(job) })
    return { statusOrder: order, groupedJobs: grouped }
  }, [state.filteredJobs])

  if (state.showKanban) {
    if (!state.selectedJob) {
      return (
        <div className="h-full flex items-center justify-center bg-lia-bg-primary dark:bg-lia-bg-primary">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-lia-border-default border-t-lia-border-medium rounded-full animate-spin motion-reduce:animate-none mx-auto mb-3" />
            <p className="text-base-ui text-lia-text-tertiary">Carregando vaga...</p>
          </div>
        </div>
      )
    }
    return <JobKanbanPage key={`kanban-${state.selectedJob.id}`} job={state.selectedJob as unknown as Record<string, unknown>} onBack={state.handleBackToJobs} />
  }

  const {
    hasMounted, activeFilter, allJobs, chatMode, closeChat,
    deselectAllJobs, filteredJobs, isChatFullscreen, isLoadingJobs,
    inlineChatInitialMessage, liaInlineMessages, navigationFilters,
    openGeneralChat, openJobCreationChat, returnToGeneralChat,
    returnToLateralPrompt, setActiveFilter, setIsChatFullscreen,
    setLiaInlineMessages, setLiaPromptValue, liaPromptValue,
    showInlineChat, setShowCreateJobModal,
    orchestratorSuggestions, getContextualSuggestions,
    showReport, reportJob, handleCloseReport,
    showCompareModal, setShowCompareModal, showPublishModal, setShowPublishModal,
    showUnpublishModal, setShowUnpublishModal, showInsightsModal, setShowInsightsModal,
    showDuplicateModal, setShowDuplicateModal, showStatusModal, setShowStatusModal,
    statusModalMode, showAssignRecruiterModal, setShowAssignRecruiterModal,
    showCreateJobModal, showEditJobModal, setShowEditJobModal, editingJob,
    showScreeningChannelsModal, setShowScreeningChannelsModal,
    showScreeningSettingsModal, setShowScreeningSettingsModal,
    showScreeningSchedulingModal, setShowScreeningSchedulingModal,
    screeningConfig, updateScreeningConfig,
    showReactivateScreeningDialog, setShowReactivateScreeningDialog,
    reactivateScreeningJobs, setReactivateScreeningJobs,
    reactivateEndDate, setReactivateEndDate,
    showWSITutorialModal, setShowWSITutorialModal,
    companyRecruiters, selectedJobsForBatch, dashboardStats,
    setBackendJobs, setSelectedJob, setPreviewJob, setEditingJob,
    setPendingNavigateJobId, loadBackendJobs, setActivePreviewTab,
    selectedJob, navigateToCreatedJob,
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
      {chatMode === 'job-creation' && isChatFullscreen && showInlineChat && (
        <div className="absolute inset-0 z-50 bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col">
          <ExpandedChatModal
            isOpen={true}
            onClose={closeChat}
            initialMessage={inlineChatInitialMessage}
            initialMessages={liaInlineMessages}
            contextTitle="Criação de Vaga"
            inline={true}
            mode="job-creation"
            onJobCreated={() => { returnToGeneralChat() }}
            onReturnToLateral={returnToLateralPrompt}
            onFullscreenChange={setIsChatFullscreen}
            onMessagesUpdate={(msgs) => setLiaInlineMessages(msgs)}
          />
        </div>
      )}

      <div className={`flex-shrink-0 px-4 pt-3 pb-2 bg-lia-bg-primary dark:bg-lia-bg-primary ${chatMode === 'job-creation' && isChatFullscreen ? 'hidden' : ''}`}>
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-lg font-semibold text-lia-text-primary">
                Gestão de Vagas
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              className="gap-2 h-8 px-3 bg-lia-btn-primary-hover"
              onClick={() => setShowCreateJobModal(true)}
            >
              <Plus className="w-4 h-4" />
              Nova Vaga
            </Button>
          </div>
        </div>

        {/* Stats Bar — metrics that complement the tabs */}
        {!isLoadingJobs && dashboardStats && (
          <div className="flex items-center gap-6 mt-1 mb-2">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{(dashboardStats as Record<string, number>).noFunil || 0}</span> no funil
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-wedo-cyan" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">{(dashboardStats as Record<string, number>).entrevistasRecentes || 0}</span> entrevistas
              </span>
            </div>
            {((dashboardStats as Record<string, number>).taxaConversao || 0) > 0 && (
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-xs text-lia-text-secondary">
                  <span className="font-semibold text-lia-text-primary">{(dashboardStats as Record<string, number>).taxaConversao}%</span> conversão
                </span>
              </div>
            )}
            {((dashboardStats as Record<string, number>).atRisco || 0) > 0 && (
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
                <span className="text-xs text-lia-text-secondary">
                  <span className="font-semibold text-rose-600">{(dashboardStats as Record<string, number>).atRisco}</span> em risco
                </span>
              </div>
            )}
          </div>
        )}
        <div className="mb-0">
          <div className="flex gap-1 p-1 bg-lia-bg-secondary rounded-lg w-fit" role="tablist" aria-label="Tabs">
            {navigationFilters.map((filter) => {
              const TAB_ICONS: Record<string, React.ComponentType<{className?: string}>> = {
                'todas': Briefcase,
                'ativas': Zap,
                'urgentes': AlertTriangle,
                'paralisadas': Pause,
                'concluidas': CheckCircle,
                'canceladas': XCircle,
              }
              const TabIcon = TAB_ICONS[filter.id] || Briefcase
              return (
              <button
                key={filter.id}
                onClick={() => { setActiveFilter(filter.id) }}
                role="tab"
                aria-selected={activeFilter === filter.id}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  activeFilter === filter.id
                    ? 'bg-lia-bg-primary text-lia-text-primary shadow-sm'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <TabIcon className="w-3.5 h-3.5" />
                <span>{filter.label}</span>
                {!filter.isDashboard && (
                  <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${
                    activeFilter === filter.id
                      ? 'bg-lia-interactive-active text-lia-text-primary'
                      : 'bg-lia-bg-tertiary text-lia-text-disabled'
                  }`}>
                    {isLoadingJobs ? (
                      <span className="inline-block w-4 h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded animate-pulse motion-reduce:animate-none" />
                    ) : (
                      filter.count
                    )}
                  </span>
                )}
              </button>
              )
            })}
          </div>
        </div>
      </div>

      <div className={`flex-1 flex flex-col overflow-hidden px-4 pt-2 pb-2 ${chatMode === 'job-creation' && isChatFullscreen ? 'hidden' : ''}`}>
        <JobsListContent
          {...state}
          setLiaPromptValue={state.setLiaPromptValue as (value: string | ((prev: string) => string)) => void}
          toggleJobFilter={state.toggleJobFilter as (category: string, key: string, value: unknown) => void}
          activePreviewTab={state.activePreviewTab as "screening" | "pipeline"}
          statusOrder={statusOrder}
          groupedJobs={groupedJobs}
          onAddRecentItem={onAddRecentItem}
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
          showEditJobModal={showEditJobModal}
          onCloseEditJobModal={() => setShowEditJobModal(false)}
          editingJob={editingJob}
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
          onSetEditingJob={setEditingJob}
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
                  try { const r = await liaApi.publishToLinkedIn(job.backendId); if ((r as Record<string, unknown>)?.mock) toast.info("Publicação simulada no LinkedIn") } catch {}
                }
                if (channels.includes("indeed")) {
                  try { const r = await liaApi.publishToIndeed(job.backendId); if ((r as Record<string, unknown>)?.note) toast.info("Publicação simulada no Indeed") } catch {}
                }
              }
              toast.success("Vagas publicadas com sucesso")
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch { toast.error("Erro ao publicar vagas. Tente novamente.") }
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
              toast.success("Vagas despublicadas com sucesso")
              setShowPublishModal(false)
              deselectAllJobs()
              loadBackendJobs()
            } catch { toast.error("Erro ao despublicar vagas. Tente novamente.") }
          }}
          onOpenCommunicationModal={(jobIds, templateCategory) => {
            const titles = allJobs.filter(job => jobIds.includes(String(job.id))).map(j => j.title).join(", ")
            toast.info(`Comunicação para: ${titles}`, { duration: 8000 })
          }}
        />
      </div>
    </div>
    </ErrorBoundarySection>
  )
}
