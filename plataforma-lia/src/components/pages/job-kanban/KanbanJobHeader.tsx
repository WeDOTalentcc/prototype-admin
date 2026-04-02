"use client"

import React from "react"
import {
  Popover, PopoverContent, PopoverTrigger,
} from "@/components/ui/popover"
import { SCREENING_STATUS_LABELS } from "@/types/screening"
import { liaApi } from "@/services/lia-api"
import {
  ArrowLeft, Settings, Share2, FileText, Layers3, ListChecks, Lightbulb,
  PauseCircle, PlayCircle, Archive, Calendar, Link2, RotateCcw,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

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
  setShowExpandedLIA: (show: boolean) => void
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
  const {
    onBack, router, currentJob, jobEditForm, setJobEditForm,
    setJobStatusModalMode, setShowJobStatusModal, setShowCloseVacancyModal,
    setActiveTab, computedSuggestions, setShowExpandedLIA, setShowLiaSuggestionsPanel,
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
                Voltar
              </Button>
              <div className="h-8 w-px bg-lia-border-default mt-1 flex-shrink-0"></div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-semibold text-lia-text-primary whitespace-nowrap">
                    {currentJob.title as string}
                  </h1>
                  {!!(currentJob.jobId) && (
                    <span className="text-micro font-mono text-lia-text-secondary bg-lia-bg-tertiary border border-lia-border-subtle px-1.5 py-0.5 rounded-md whitespace-nowrap">
                      {currentJob.jobId as string}
                    </span>
                  )}
                  <Popover>
                    <PopoverTrigger asChild>
                      <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-xs px-2 py-0.5 cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none select-none">
                        {(((jobEditForm.status || currentJob.status) as string) as string) as string}
                      </Badge>
                    </PopoverTrigger>
                    <PopoverContent className="w-44 p-1" align="start">
                      {(() => { const st = ((jobEditForm.status || currentJob.status) as string) as string; return st === 'Ativa' || st === 'active' })() ? (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                            onClick={() => { setJobStatusModalMode('pause'); setShowJobStatusModal(true) }}
                          >
                            <PauseCircle className="w-3.5 h-3.5 text-status-warning" />
                            Pausar vaga
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-error hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            Fechar vaga
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors motion-reduce:transition-none"
                            onClick={() => { setJobStatusModalMode('activate'); setShowJobStatusModal(true) }}
                          >
                            <PlayCircle className="w-3.5 h-3.5" />
                            Reativar vaga
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-error hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            Fechar vaga
                          </button>
                        </>
                      )}
                    </PopoverContent>
                  </Popover>
                  {(() => {
                    const scrStatus = currentJob.screeningStatus || 'not_configured'
                    const scrLabels = Object.fromEntries(
                      Object.entries(SCREENING_STATUS_LABELS).map(([k, v]) => [k, `Triagem: ${v}`])
                    ) as Record<string, string>
                    const scrStyles: Record<string, string> = {
                      not_configured: 'bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-default',
                      not_started: 'bg-status-warning/10 text-status-warning border border-status-warning/30',
                      active: 'bg-status-success/10 text-status-success border border-status-success/30',
                      paused: 'bg-wedo-orange/10 text-wedo-orange border border-wedo-orange/30',
                      completed: 'bg-wedo-cyan/10 text-wedo-cyan border border-wedo-cyan/30',
                    }
                    const handleScreeningStatusChange = async (newStatus: string) => {
                      const jobId = (currentJob.backendId || currentJob.jobId || currentJob.id) as string
                      try {
                        await liaApi.updateJobVacancy(jobId, { screeningStatus: newStatus } as Record<string, unknown>)
                        setJobEditForm((prev: Record<string, unknown>) => ({ ...prev, screeningStatus: newStatus }))
                        toast.success(`Triagem ${newStatus === 'active' ? 'ativada' : newStatus === 'paused' ? 'pausada' : 'atualizada'}`)
                      } catch {
                        // @ts-ignore TODO: fix type
                        toast.error('Erro ao atualizar triagem')
                      }
                    }
                    const badge = (
                      <Badge className={`font-semibold whitespace-nowrap text-xs px-2 py-0.5 cursor-pointer hover:opacity-80 transition-opacity motion-reduce:transition-none select-none ${(scrStyles as Record<string, string>)[scrStatus as string] || scrStyles.not_configured}`}>
                        {(scrLabels as Record<string, string>)[scrStatus as string] || 'Triagem: N/C'}
                      </Badge>
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
                              Configurar Triagem
                            </button>
                          )}
                          {scrStatus === 'not_started' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors motion-reduce:transition-none"
                                onClick={() => handleScreeningStatusChange('active')}
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                Iniciar Triagem
                              </button>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                                onClick={() => setActiveTab('edit')}
                              >
                                <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
                                Configurar
                              </button>
                            </>
                          )}
                          {scrStatus === 'active' && (
                            <button
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-warning hover:bg-status-warning/10 transition-colors motion-reduce:transition-none"
                              onClick={() => handleScreeningStatusChange('paused')}
                            >
                              <PauseCircle className="w-3.5 h-3.5" />
                              Pausar Triagem
                            </button>
                          )}
                          {scrStatus === 'paused' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors motion-reduce:transition-none"
                                onClick={() => handleScreeningStatusChange('active')}
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                Retomar Triagem
                              </button>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                                onClick={() => setActiveTab('edit')}
                              >
                                <Settings className="w-3.5 h-3.5 text-lia-text-tertiary" />
                                Configurar
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
                    <Badge className="bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 text-status-warning dark:text-status-warning font-semibold whitespace-nowrap text-micro px-1.5 py-0">
                      Rascunho
                    </Badge>
                  )}
                  <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-semibold whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.level as string}
                  </Badge>
                  <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium capitalize whitespace-nowrap text-micro px-1.5 py-0">
                    {(currentJob.workModel as string | undefined) || '—'}
                  </Badge>
                  <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {(currentJob.type as string | undefined) || '—'}
                  </Badge>
                  <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.department as string}
                  </Badge>
                  <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.location as string}
                  </Badge>
                  {!!(currentJob.salary) && (currentJob.salary as string) !== 'A combinar' && (
                    <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      {currentJob.salary as string}
                    </Badge>
                  )}
                  {!!(currentJob.publishedLinkedIn) && (
                    <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      Publicada
                    </Badge>
                  )}
                  <span className="text-micro text-lia-text-disabled mx-0.5">|</span>
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
                        {days}d {isLate ? 'de atraso' : 'aberta'}
                      </span>
                    )
                  })()}
                  {!!(currentJob.updatedAt) && (
                    <span className="text-micro text-lia-text-secondary whitespace-nowrap">
                      Atualizada: {new Date(currentJob.updatedAt as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </span>
                  )}
                  {!!(currentJob.deadlineScreening) && (
                    <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Prazo triagem: {new Date(currentJob.deadlineScreening as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {!!(currentJob.deadlineShortlist) && (
                    <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Prazo short: {new Date(currentJob.deadlineShortlist as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {!!(currentJob.deadlineClosing) && (
                    <Badge className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Encerramento: {new Date(currentJob.deadlineClosing as string).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {computedSuggestions.length > 0 && (
                    <Badge 
                      className="bg-wedo-cyan text-white border-0 font-semibold whitespace-nowrap text-micro px-1.5 py-0 cursor-pointer hover:bg-wedo-cyan-dark transition-colors motion-reduce:transition-none"
                      onClick={() => {
                        setShowExpandedLIA(true)
                        setShowLiaSuggestionsPanel(true)
                      }}
                    >
                      <Lightbulb className="w-3 h-3 mr-1" />
                      {computedSuggestions.length} sugestão{computedSuggestions.length > 1 ? 'ões' : ''} da LIA
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Action Buttons */}
            <div className="flex items-center gap-2 pt-1 flex-shrink-0">
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={() => {
                toast.success("Em breve", { description: "Em breve: Configuração de etapas do pipeline" })
              }}>
                <Settings className="w-3.5 h-3.5" />
                Configurar Etapas
              </Button>
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={handleShowReport}>
                <FileText className="w-3.5 h-3.5" />
                Relatório
              </Button>
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={() => {
                if (selectedCandidates.size > 0) {
                  setShowShareGestorModal(true)
                } else {
                  // @ts-ignore TODO: fix type
                  setSelectedCandidates(new Set(allTableCandidates.map(c => c.id as string)))
                  toast.success("Modo Compartilhamento", { description: "Todos os candidatos foram selecionados. Ajuste a seleção e clique em Compartilhar na barra de ações." })
                }
              }}>
                <Share2 className="w-3.5 h-3.5" />
                Compartilhar
              </Button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 px-4 mt-2">
            <button
              onClick={() => { setActiveTab('management'); setShowJobEditor(false); }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] ${
                activeTab === 'management'
                  ? 'bg-lia-bg-tertiary text-lia-text-primary'
                  : 'text-lia-text-secondary hover:bg-lia-interactive-hover'
              }`}
            >
              <Layers3 className="w-3.5 h-3.5" />
              Gestão da Vaga
              <Badge className={`text-micro px-1.5 py-0 ml-1 ${
                activeTab === 'management'
                  ? 'bg-lia-interactive-active text-lia-text-secondary'
                  : 'bg-lia-interactive-active text-lia-text-secondary'
              }`}>
                {allTableCandidates?.length || 0}
              </Badge>
            </button>
            <button
              onClick={() => { setActiveTab('edit'); setShowJobEditor(true); }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] ${
                activeTab === 'edit'
                  ? 'bg-lia-bg-tertiary text-lia-text-primary'
                  : 'text-lia-text-secondary hover:bg-lia-interactive-hover'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              Configurações
            </button>
            <div className="ml-auto flex items-center gap-2">
              {pipelineInheritance.isCustomized ? (
                <>
                  <span className="inline-flex items-center gap-1 text-micro text-status-warning dark:text-status-warning">
                    <Settings className="w-3 h-3" />
                    Pipeline personalizado
                  </span>
                  <button
                    onClick={async () => {
                      const success = await pipelineInheritance.resetToCompanyDefault()
                      if (success) {
                        toast.success('Pipeline resetado', { description: 'Pipeline restaurado para o padrão da empresa.' })
                        window.location.reload()
                      }
                    }}
                    disabled={pipelineInheritance.isLoading}
                    className="inline-flex items-center gap-1 px-2 py-1 text-micro font-medium text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled bg-lia-bg-tertiary hover:bg-lia-interactive-active rounded-md transition-colors motion-reduce:transition-none"
                   
                  >
                    <RotateCcw className="w-3 h-3" />
                    Resetar para padrão
                  </button>
                </>
              ) : (
                <span className="inline-flex items-center gap-1 text-micro text-lia-text-disabled">
                  <Link2 className="w-3 h-3" />
                  Herdado da empresa
                </span>
              )}
            </div>
          </div>

        </div>
      </div>
  )
})
KanbanJobHeader.displayName = 'KanbanJobHeader'
