"use client"

import React from"react"
import { useTranslations } from"next-intl"
import {
  Popover, PopoverContent, PopoverTrigger,
} from"@/components/ui/popover"
import { SCREENING_STATUS_LABELS } from"@/types/screening"
import { liaApi } from"@/services/lia-api"
import {
  ArrowLeft, Settings, Share2, FileText, Layers3, ListChecks, Lightbulb,
  PauseCircle, PlayCircle, Archive, Calendar, Link2, RotateCcw, Brain,
} from"lucide-react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { toast } from"sonner"
import { JobAgentBadge } from "@/components/jobs/JobAgentBadge"

interface KanbanJobHeaderProps {
  onBack?: () => void
  router: { back: () => void }
  currentJob: Record<string, unknown>
  jobEditForm: Record<string, unknown>
  setJobEditForm: (fn: (prev: Record<string, unknown>) => Record<string, unknown>) => void
  setJobStatusModalMode: (mode: string) => void
  setShowJobStatusModal: (show: boolean) => void
  setShowCloseVacancyModal: (show: boolean) => void
  setActiveTab: (tab: string) => void
  computedSuggestions: unknown[]
  setShowLiaSuggestionsPanel: (show: boolean) => void
  allTableCandidates: unknown[]
  selectedCandidates: Set<string>
  setSelectedCandidates: (s: Set<string>) => void
  setShowShareGestorModal: (show: boolean) => void
  handleShowReport: () => void
  activeTab: string
  setShowJobEditor: (show: boolean) => void
  pipelineInheritance: { isCustomized: boolean; isLoading: boolean; resetToCompanyDefault: () => Promise<boolean> }
  setJobLocalOverrides: (fn: (prev: Record<string, unknown>) => Record<string, unknown>) => void
}

export const KanbanJobHeader = React.memo(function KanbanJobHeader(props: KanbanJobHeaderProps) {
  const t = useTranslations('kanban')
  const tJobs = useTranslations('jobs')
  const {
    onBack, router, currentJob, jobEditForm, setJobEditForm,
    setJobStatusModalMode, setShowJobStatusModal, setShowCloseVacancyModal,
    setActiveTab, computedSuggestions, setShowLiaSuggestionsPanel,
    allTableCandidates, selectedCandidates, setSelectedCandidates, setShowShareGestorModal,
    handleShowReport, activeTab, setShowJobEditor, pipelineInheritance,
  } = props

  return (
      <div className="bg-lia-bg-primary">
        <div className="w-full px-4">
          <div className="flex flex-col lg:flex-row items-start justify-between gap-4 mb-4">
            {/* Left: Título e Informações Principais */}
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <Button variant="ghost" size="sm" onClick={() => onBack ? onBack() : router.back()} className="gap-2 mt-1 flex-shrink-0">
                <ArrowLeft className="w-4 h-4" />
                {t('back')}
              </Button>
              <div className="h-8 w-px bg-lia-border-default mt-1 flex-shrink-0"></div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-semibold text-lia-text-primary whitespace-nowrap">
                    {currentJob.title as string}
                  </h1>
                  {!!(currentJob.jobId) && (
                    <span className="text-micro font-mono text-lia-text-secondary bg-lia-bg-tertiary border border-lia-border-subtle px-1.5 py-0.5 rounded-xl whitespace-nowrap">
                      {currentJob.jobId as string}
                    </span>
                  )}
                  {/* Onda 2 F5 — pingo cyan + tooltip quando ha agentes acoplados a esta vaga. */}
                  <JobAgentBadge jobId={(currentJob.backendId || currentJob.id) as string | undefined} />

                  <Popover>
                    <PopoverTrigger asChild>
                      <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap px-2 py-0.5 cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none select-none">
                        {(((jobEditForm.status || currentJob.status) as string) as string) as string}
                      </Chip>
                    </PopoverTrigger>
                    <PopoverContent className="w-44 p-1" align="start">
                      {(() => { const st = ((jobEditForm.status || currentJob.status) as string) as string; return st === 'Ativa' || st === 'active' })() ? (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                            onClick={() => { setJobStatusModalMode('pause'); setShowJobStatusModal(true) }}
                          >
                            <PauseCircle className="w-3.5 h-3.5 text-status-warning" />
                            {t('pauseJob')}
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-error hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            {t('closeJob')}
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors motion-reduce:transition-none"
                            onClick={() => { setJobStatusModalMode('activate'); setShowJobStatusModal(true) }}
                          >
                            <PlayCircle className="w-3.5 h-3.5" />
                            {t('reactivateJob')}
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-error hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            {t('closeJob')}
                          </button>
                        </>
                      )}
                    </PopoverContent>
                  </Popover>
                  {(() => {
                    const scrStatus = currentJob.screeningStatus || 'not_configured'
                    const scrLabels = Object.fromEntries(
                      Object.entries(SCREENING_STATUS_LABELS).map(([k, v]) => [k, `${t('screeningPrefix')}: ${v}`])
                    ) as Record<string, string>
                    const scrStyles: Record<string, string> = {
                      not_configured: 'bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-default',
                      not_started: ' border border-status-warning/30',
                      active: ' border border-status-success/30',
                      paused: ' border border-wedo-orange/30',
                      completed: ' border border-wedo-cyan/30',
                    }
                    const handleScreeningStatusChange = async (newStatus: string) => {
                      const jobId = (currentJob.backendId || currentJob.jobId || currentJob.id) as string
                      try {
                        await liaApi.updateJobVacancy(jobId, { screeningStatus: newStatus } as Record<string, unknown>)
                        setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, screeningStatus: newStatus }))
                        toast.success(newStatus === 'active' ? t('screeningActivated') : newStatus === 'paused' ? t('screeningPaused') : t('screeningUpdated'))
                      } catch {
                        toast.error(t('screeningUpdateError'))
                      }
                    }
                    const badge = (
                      <Chip variant="neutral" muted className={`whitespace-nowrap text-xs px-2 py-0.5 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none select-none ${(scrStyles as Record<string, string>)[scrStatus as string] || scrStyles.not_configured}`}>
                        {(scrLabels as Record<string, string>)[scrStatus as string] || t('screeningNA')}
                      </Chip>
                    )
                    if ((scrStatus as string) === 'completed') return badge
                    return (
                      <Popover>
                        <PopoverTrigger asChild>{badge}</PopoverTrigger>
                        <PopoverContent className="w-48 p-1" align="start">
                          {scrStatus === 'not_configured' && (
                            <button
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                              onClick={() => setActiveTab('edit')}
                            >
                              <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
                              {t('configureScreening')}
                            </button>
                          )}
                          {scrStatus === 'not_started' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors motion-reduce:transition-none"
                                onClick={() => handleScreeningStatusChange('active')}
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                {t('startScreening')}
                              </button>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                                onClick={() => setActiveTab('edit')}
                              >
                                <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
                                {t('configure')}
                              </button>
                            </>
                          )}
                          {scrStatus === 'active' && (
                            <button
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-warning hover:bg-status-warning/10 transition-colors motion-reduce:transition-none"
                              onClick={() => handleScreeningStatusChange('paused')}
                            >
                              <PauseCircle className="w-3.5 h-3.5" />
                              {t('pauseScreening')}
                            </button>
                          )}
                          {scrStatus === 'paused' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors motion-reduce:transition-none"
                                onClick={() => handleScreeningStatusChange('active')}
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                {t('resumeScreening')}
                              </button>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                                onClick={() => setActiveTab('edit')}
                              >
                                <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
                                {t('configure')}
                              </button>
                            </>
                          )}
                        </PopoverContent>
                      </Popover>
                    )
                  })()}
                </div>
                <div className="flex items-center gap-1.5 flex-wrap mt-1">
                  {(currentJob.status as string) === 'Rascunho' && (
                    <Chip variant="warning" muted className="bg-status-warning/10 dark:bg-status-warning/20 whitespace-nowrap text-micro px-1.5 py-0">
                      {t('draft')}
                    </Chip>
                  )}
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.level as string}
                  </Chip>
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium capitalize whitespace-nowrap text-micro px-1.5 py-0">
                    {(currentJob.workModel as string | undefined) || '—'}
                  </Chip>
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {(currentJob.type as string | undefined) || '—'}
                  </Chip>
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.department as string}
                  </Chip>
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.location as string}
                  </Chip>
                  {!!(currentJob.salary) && (currentJob.salary as string) !== 'A combinar' && (
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      {currentJob.salary as string}
                    </Chip>
                  )}
                  {!!(currentJob.publishedLinkedIn) && (
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      {t('published')}
                    </Chip>
                  )}
                  <span className="text-micro text-lia-text-muted mx-0.5">|</span>
                  {!!(currentJob.openDate) && (
                    <span className="text-micro text-lia-text-secondary whitespace-nowrap">
                      <Calendar className="w-3 h-3 inline mr-0.5 -mt-0.5" />
                      {new Date(currentJob.openDate as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  )}
                  {!!(currentJob.openDate) && (() => {
                    const days = Math.floor((Date.now() - new Date(currentJob.openDate as string).getTime()) / (1000 * 60 * 60 * 24))
                    if (days <= 0) return null
                    const isLate = days > 30
                    return (
                      <span className={`text-micro font-semibold whitespace-nowrap ${isLate ? 'text-status-error' : 'text-lia-text-secondary'}`}>
                        {days}d {isLate ? t('late') : t('open')}
                      </span>
                    )
                  })()}
                  {!!(currentJob.updatedAt) && (
                    <span className="text-micro text-lia-text-secondary whitespace-nowrap">
                      {t('updated')}: {new Date(currentJob.updatedAt as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </span>
                  )}
                  {!!(currentJob.deadlineScreening) && (
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      {t('screeningDeadline')}: {new Date(currentJob.deadlineScreening as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Chip>
                  )}
                  {!!(currentJob.deadlineShortlist) && (
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      {t('shortlistDeadline')}: {new Date(currentJob.deadlineShortlist as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Chip>
                  )}
                  {!!(currentJob.deadlineClosing) && (
                    <Chip variant="neutral" muted className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      {t('closing')}: {new Date(currentJob.deadlineClosing as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Chip>
                  )}
                  {computedSuggestions.length > 0 && (
                    <Chip variant="neutral" muted 
                      className="bg-wedo-cyan text-white border-0 font-semibold whitespace-nowrap text-micro px-1.5 py-0 cursor-pointer hover:bg-wedo-cyan-dark transition-colors motion-reduce:transition-none"
                      onClick={() => {
                        setShowLiaSuggestionsPanel(true)
                      }}
                    >
                      <Lightbulb className="w-3 h-3 mr-1" />
                      {t('liaSuggestions', { count: computedSuggestions.length })}
                    </Chip>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Action Buttons */}
            <div className="flex items-center gap-2 pt-1 flex-shrink-0">
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={handleShowReport}>
                <FileText className="w-3.5 h-3.5" />
                {t('report')}
              </Button>
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={() => {
                if (selectedCandidates.size > 0) {
                  setShowShareGestorModal(true)
                } else {
                  setSelectedCandidates(new Set((allTableCandidates as Array<Record<string, unknown>>).map(c => String(c.id))))
                  toast.success(t('shareMode'), { description: t('shareModeDescription') })
                }
              }}>
                <Share2 className="w-3.5 h-3.5" />
                {t('share')}
              </Button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 px-4 mt-2">
            <button
              onClick={() => { setActiveTab('management'); setShowJobEditor(false); }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                activeTab === 'management'
                  ? 'bg-lia-bg-tertiary text-lia-text-primary'
                  : 'text-lia-text-secondary hover:bg-lia-interactive-hover'
              }`}
            >
              <Layers3 className="w-3.5 h-3.5" />
              {t('jobManagement')}
              <Chip variant="neutral" muted className={`text-micro px-1.5 py-0 ml-1 ${
                activeTab === 'management'
                  ? 'bg-lia-interactive-active text-lia-text-secondary'
                  : 'bg-lia-interactive-active text-lia-text-secondary'
              }`}>
                {allTableCandidates?.length || 0}
              </Chip>
            </button>
            <button
              onClick={() => { setActiveTab('edit'); setShowJobEditor(true); }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                activeTab === 'edit'
                  ? 'bg-lia-bg-tertiary text-lia-text-primary'
                  : 'text-lia-text-secondary hover:bg-lia-interactive-hover'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              {t('settings')}
            </button>
            {/* Onda 3 F4 — aba Agentes (acoplar agentes a esta vaga). */}
            <button
              onClick={() => { setActiveTab('agents'); setShowJobEditor(false); }}
              data-testid="job-tab-agents"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                activeTab === 'agents'
                  ? 'bg-lia-bg-tertiary text-lia-text-primary'
                  : 'text-lia-text-secondary hover:bg-lia-interactive-hover'
              }`}
            >
              <Brain className="w-3.5 h-3.5 text-lia-cyan" />
              {tJobs('tabs.agents')}
            </button>
            <div className="ml-auto flex items-center gap-2">
              {pipelineInheritance.isCustomized ? (
                <>
                  <span className="inline-flex items-center gap-1 text-micro text-status-warning dark:text-status-warning">
                    <Settings className="w-3 h-3" />
                    {t('customPipeline')}
                  </span>
                  <button
                    onClick={async () => {
                      const success = await pipelineInheritance.resetToCompanyDefault()
                      if (success) {
                        toast.success(t('pipelineReset'), { description: t('pipelineResetDescription') })
                        window.location.reload()
                      }
                    }}
                    disabled={pipelineInheritance.isLoading}
                    className="inline-flex items-center gap-1 px-2 py-1 text-micro font-medium text-lia-text-tertiary hover:text-lia-text-secondary bg-lia-bg-tertiary hover:bg-lia-interactive-active rounded-md transition-colors motion-reduce:transition-none"
                   
                  >
                    <RotateCcw className="w-3 h-3" />
                    {t('resetToDefault')}
                  </button>
                </>
              ) : (
                <span className="inline-flex items-center gap-1 text-micro text-lia-text-muted">
                  <Link2 className="w-3 h-3" />
                  {t('inheritedFromCompany')}
                </span>
              )}
            </div>
          </div>

        </div>
      </div>
  )
})
KanbanJobHeader.displayName = 'KanbanJobHeader'
