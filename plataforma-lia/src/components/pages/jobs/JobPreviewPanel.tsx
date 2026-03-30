"use client"

import React, { useState } from "react"
import { SCREENING_STATUS_LABELS } from "@/types/screening"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, Clock, MapPin, DollarSign, Heart, Shield, Building, Lock, Globe,
  Expand, X, ChevronRight, ClipboardList,
  ChevronDown, ChevronUp,
} from "lucide-react"
import { type Job } from "@/components/jobs"
import { type ScreeningConfig } from "@/hooks/useScreeningConfig"
import { type JobVacancyMetrics } from "@/services/lia-api"
import { getStatusColor } from "@/components/jobs/jobsPageConstants"
import { JobScreeningSection } from "./job-preview/sections/JobScreeningSection"
import { JobPipelineSection } from "./job-preview/sections/JobPipelineSection"
import { type JobPreviewPanelProps } from "./job-preview/job-preview.types"

export type { JobPreviewPanelProps }

export function JobPreviewPanel({
  showJobPreview,
  previewJob,
  activePreviewTab,
  onTabChange,
  previewWidth,
  onResize,
  onResizeStart,
  onResizeEnd,
  onClose,
  onJobClick,
  screeningConfig,
  isLoadingScreeningConfig,
  jobMetrics,
  isLoadingJobMetrics,
}: JobPreviewPanelProps) {
  const [expandedBlocks, setExpandedBlocks] = useState<number[]>([0, 1, 2, 3, 4, 6])
  const [collapsedPreviewSections, setCollapsedPreviewSections] = useState<string[]>([])

  const togglePreviewSection = (section: string) => {
    setCollapsedPreviewSections(prev =>
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    )
  }

  const toggleBlock = (blockId: number) => {
    setExpandedBlocks(prev =>
      prev.includes(blockId) ? prev.filter(id => id !== blockId) : [...prev, blockId]
    )
  }

  if (!showJobPreview || !previewJob) return null

  return (
              <div 
                className="flex-shrink-0 bg-white dark:bg-lia-bg-secondary rounded-md overflow-hidden animate-slide-in flex flex-col h-full max-h-[calc(100vh-180px)] relative group"
                style={{width: `${previewWidth}px`,
                  minWidth: '320px',
                  maxWidth: '700px'}}
              >
                {/* Resize Handle - Left Side */}
                <div
                  className="absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize bg-gray-400/30 hover:bg-gray-400 transition-colors group-hover:opacity-100 opacity-0 z-10"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    onResizeStart()
                    const startX = e.clientX
                    const startWidth = previewWidth

                    const handleMouseMove = (e: MouseEvent) => {
                      const deltaX = startX - e.clientX
                      const newWidth = Math.max(320, Math.min(700, startWidth + deltaX))
                      onResize(newWidth)
                    }

                    const handleMouseUp = () => {
                      onResizeEnd()
                      document.removeEventListener('mousemove', handleMouseMove)
                      document.removeEventListener('mouseup', handleMouseUp)
                    }

                    document.addEventListener('mousemove', handleMouseMove)
                    document.addEventListener('mouseup', handleMouseUp)
                  }}
                />
                {/* Header Padronizado (Design System Candidato) */}
                <div className="bg-white dark:bg-lia-bg-secondary border-b border-lia-border-subtle">
                  {/* Linha 1: Título + Código + Ações */}
                  <div className="px-3 pt-3 pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        {/* Row 1: Título + Código (lado direito) */}
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary truncate">
                            {previewJob.title}
                          </h3>
                          <Badge className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium" style={{backgroundColor: 'var(--gray-bg-15)', border: '1px solid var(--gray-border)'}}>
                            {previewJob.jobId}
                          </Badge>
                          {previewJob.isAffirmative && (
                            <span title="Vaga Afirmativa">
                              <Heart className="w-3 h-3 text-wedo-magenta" />
                            </span>
                          )}
                        </div>

                        {/* Row 2: Datas em texto simples (como no candidato) */}
                        <div className="flex items-center gap-3 mb-1 text-micro text-lia-text-tertiary">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-lia-text-disabled" />
                            {previewJob.openDate ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                          </span>
                          {previewJob.deadline && (
                            <span className={`flex items-center gap-1 ${
                              new Date(previewJob.deadline) < new Date() ? 'text-status-error' : 'text-lia-text-tertiary'
                            }`}>
                              <Clock className="w-3 h-3" />
                              {(() => {
                                const days = Math.ceil((new Date(previewJob.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                                return days > 0 ? `${days}d restantes` : `${Math.abs(days)}d atraso`
                              })()}
                            </span>
                          )}
                        </div>

                        {/* Row 2b: Histórico inline */}
                        <div className="flex items-center gap-3 mb-1.5 text-micro text-lia-text-disabled">
                          <span>Criado: {previewJob.createdAt 
                            ? new Date(previewJob.createdAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
                            : previewJob.openDate 
                              ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: '2-digit' })
                              : '—'}</span>
                          <span>Atualizado: {previewJob.updatedAt 
                            ? new Date(previewJob.updatedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
                            : '—'}</span>
                          {previewJob.publishedAt && (
                            <span>Publicado: {new Date(previewJob.publishedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</span>
                          )}
                          {previewJob.closedAt && (
                            <span>Fechado: {new Date(previewJob.closedAt).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}</span>
                          )}
                        </div>

                        {/* Row 3: Badges de informação */}
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {previewJob.department && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-lia-text-secondary border border-lia-border-subtle">
                              {previewJob.department}
                            </Badge>
                          )}
                          {previewJob.level && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-status-warning/10 text-status-warning border border-status-warning/30">
                              {previewJob.level}
                            </Badge>
                          )}
                          {previewJob.location && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-cyan/10 text-wedo-cyan-dark border border-wedo-cyan/30 flex items-center gap-0.5">
                              <MapPin className="w-2.5 h-2.5" />
                              {previewJob.location}
                            </Badge>
                          )}
                          {previewJob.workModel && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-lia-text-secondary border border-lia-border-subtle">
                              {previewJob.workModel === 'remoto' ? 'Remoto' : previewJob.workModel === 'híbrido' ? 'Híbrido' : 'Presencial'}
                            </Badge>
                          )}
                          {previewJob.type && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-lia-text-secondary border border-lia-border-subtle">
                              {previewJob.type}
                            </Badge>
                          )}
                          {(previewJob.visibility === 'confidential' || previewJob.isConfidential) && (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30">
                              <Shield className="w-2.5 h-2.5 mr-0.5" />
                              Confidencial
                            </Badge>
                          )}
                          {previewJob.visibility === 'internal' && (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30">
                              <Building className="w-2.5 h-2.5 mr-0.5" />
                              Interna
                            </Badge>
                          )}
                          {previewJob.visibility === 'hidden' && (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-lia-text-primary border-lia-border-subtle">
                              <Lock className="w-2.5 h-2.5 mr-0.5" />
                              Oculta
                            </Badge>
                          )}
                          {/* Badge de publicação */}
                          {(previewJob.publishedLinkedIn || previewJob.publishedWebsite) ? (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-status-success/10 text-status-success border-status-success/30 flex items-center gap-0.5">
                              <Globe className="w-2.5 h-2.5" />
                              Publicada
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-lia-text-tertiary border-lia-border-subtle flex items-center gap-0.5">
                              <Globe className="w-2.5 h-2.5" />
                              Não publicada
                            </Badge>
                          )}
                          {(previewJob.salaryRange?.min || previewJob.salaryRange?.max || previewJob.salaryMin || previewJob.salaryMax) && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-status-success/10 text-status-success border border-status-success/30 flex items-center gap-0.5">
                              <DollarSign className="w-2.5 h-2.5" />
                              {(() => {
                                const min = previewJob.salaryRange?.min || previewJob.salaryMin
                                const max = previewJob.salaryRange?.max || previewJob.salaryMax
                                if (min && max) return `R$ ${(min/1000).toFixed(0)}k - ${(max/1000).toFixed(0)}k`
                                if (min) return `A partir de R$ ${(min/1000).toFixed(0)}k`
                                if (max) return `Até R$ ${(max/1000).toFixed(0)}k`
                                return ''
                              })()}
                            </Badge>
                          )}
                          {/* Badge de status */}
                          <Badge 
                            className="text-micro px-1.5 py-0 h-4 font-medium"
                            style={{backgroundColor: getStatusColor(previewJob.status as Job['status']), color: 'var(--white)'}}
                          >
                            {previewJob.status}
                          </Badge>
                          {(() => {
                            const scrStatus = previewJob.screeningStatus || 'not_configured'
                            const scrLabels = Object.fromEntries(
                              Object.entries(SCREENING_STATUS_LABELS).map(([k, v]) => [k, `Triagem: ${v}`])
                            ) as Record<string, string>
                            const scrColors: Record<string, string> = {
                              not_configured: 'var(--gray-200)',
                              not_started: 'var(--gray-100)',
                              active: 'var(--status-success)',
                              paused: 'var(--gray-300)',
                              completed: 'var(--gray-400)',
                            }
                            return (
                              <Badge 
                                className="text-micro px-1.5 py-0 h-4 font-medium text-lia-text-primary"
                                style={{backgroundColor: scrColors[scrStatus] || 'var(--gray-200)'}}
                              >
                                {scrLabels[scrStatus] || 'Triagem: N/C'}
                              </Badge>
                            )
                          })()}
                        </div>
                      </div>
                      <div className="flex items-center gap-0.5 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onJobClick(previewJob)}
                          className="h-6 w-6 p-0"
                          title="Abrir vaga completa"
                        >
                          <Expand className="w-3 h-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            onClose()
                          }}
                          className="h-6 w-6 p-0"
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Linha 3: Processo Seletivo Inline */}
                  {previewJob.hiringProcess && previewJob.hiringProcess.length > 0 && (
                    <div className="px-3 pb-2 border-t border-lia-border-subtle dark:border-lia-border-subtle/50 pt-2">
                      <div className="flex items-center gap-0.5 overflow-x-auto">
                        {previewJob.hiringProcess.map((step, idx) => (
                          <React.Fragment key={idx}>
                            <div className={`px-1.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                              idx === 0 ? 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary font-semibold' :
                              idx === (previewJob.hiringProcess?.length || 0) - 1 ? 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary font-semibold' :
                              'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary'
                            }`}>
                              {step}
                            </div>
                            {idx < (previewJob.hiringProcess?.length || 0) - 1 && (
                              <ChevronRight className="w-2 h-2 text-lia-text-primary flex-shrink-0" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Tabs de Navegação - Tamanho Reduzido */}
                <div className="border-b border-lia-border-subtle">
                  <div className="flex items-center px-3">
                    <button
                      onClick={() => onTabChange('screening')}
                      className={`px-2 py-2 text-micro font-medium border-b transition-colors ${
                        activePreviewTab === 'screening'
                          ? 'border-gray-900 text-lia-text-secondary font-semibold'
                          : 'border-transparent text-lia-text-tertiary hover:text-lia-text-secondary'
                      }`}
                    >
                      <div className="flex items-center gap-1">
                        <ClipboardList className="w-2.5 h-2.5" />
                        Detalhes da Vaga
                      </div>
                    </button>
                  </div>
                </div>

                {/* Conteúdo das Tabs - Scrollable */}
                <div className="overflow-y-auto flex-1 p-4">

                  {/* Tab: Análise Preditiva - Removida, já está unificada com Pipeline */}

                  {/* Tab: Funil & Analytics Unificado */}
                  {activePreviewTab === 'pipeline' && (
                    <div className="space-y-4">
                      {/* Cards de Métricas Preditivas Principais */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Score de Sucesso */}
                        <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Sucesso de Fechamento</span>
                            <Target className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                          </div>
                          <div className="text-xl font-bold text-lia-text-primary dark:text-lia-text-primary font-semibold">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.performance?.conversion_rate != null 
                              ? `${Math.round(jobMetrics.performance.conversion_rate)}%` 
                              : previewJob.funnel.hired > 0 
                                ? `${Math.round((previewJob.funnel.hired / Math.max(previewJob.funnel.total, 1)) * 100)}%`
                                : '—'}
                          </div>
                          <div className="mt-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                            Pipeline: {jobMetrics?.funnel.total ?? previewJob.funnel.total} candidatos
                          </div>
                        </div>

                        {/* Atividade 7d */}
                        <div className="bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Atividade 7d</span>
                            <TrendingUp className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
                          </div>
                          <div className="text-xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                            {isLoadingJobMetrics ? '...' : jobMetrics ? jobMetrics.activity.applications_7d : 0}
                          </div>
                          <div className="mt-1 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                            {isLoadingJobMetrics ? '...' : jobMetrics ? `${jobMetrics.activity.views_7d} visualizações` : 'Sem dados'}
                          </div>
                        </div>

                        {/* Time to Fill */}
                        <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Time to Fill</span>
                            <Clock className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                          </div>
                          <div className="text-xl font-bold text-lia-text-primary dark:text-lia-text-primary font-semibold">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.performance.time_to_fill_days != null ? `${jobMetrics.performance.time_to_fill_days}d` : (previewJob.urgencyLevel > 3 ? '15d' : previewJob.urgencyLevel > 2 ? '25d' : '35d')}
                          </div>
                          <div className="mt-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.activity.interviews_scheduled ? `${jobMetrics.activity.interviews_scheduled} entrevistas agendadas` : 'Sem entrevistas'}
                          </div>
                        </div>

                        {/* SLA Status */}
                        <div className={`rounded-md p-3 ${jobMetrics?.sla.within_sla === false ? 'bg-status-error/10 dark:bg-status-error/20' : 'bg-gray-50 dark:bg-lia-bg-secondary'}`}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Status SLA</span>
                            <Shield className={`w-3 h-3 ${jobMetrics?.sla.within_sla === false ? 'text-status-error' : 'text-lia-text-primary dark:text-lia-text-primary'}`} />
                          </div>
                          <div className={`text-xl font-bold font-semibold ${jobMetrics?.sla.within_sla === false ? 'text-status-error dark:text-status-error' : 'text-lia-text-primary dark:text-lia-text-primary'}`}>
                            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.within_sla ? 'OK' : 'Atrasado'}
                          </div>
                          <div className={`mt-1 text-xs ${jobMetrics?.sla.within_sla === false ? 'text-status-error dark:text-status-error' : 'text-lia-text-primary dark:text-lia-text-primary'}`}>
                            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.days_remaining != null ? `${jobMetrics.sla.days_remaining} dias restantes` : 'Sem prazo definido'}
                          </div>
                        </div>
                      </div>

                      {/* Insights e Recomendações da LIA */}
                      <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-semibold mb-1">
                              Insights da LIA
                            </p>
                            <ul className="space-y-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                              {previewJob.funnel.total < 10 && (
                                <li>• Pipeline baixo: Ampliar divulgação ou revisar requisitos</li>
                              )}
                              {previewJob.level === 'Sênior' && (
                                <li>• Alto risco de recusa: Prepare margem de negociação de 15-20%</li>
                              )}
                              {previewJob.funnel.screening > previewJob.funnel.interview * 3 && (
                                <li>• Gargalo em entrevistas: Agilize agendamentos</li>
                              )}
                              {previewJob.urgencyLevel > 3 && previewJob.funnel.total < 20 && (
                                <li>• Urgência vs Pipeline: Ative sourcing ativo e headhunting</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>

                      {/* Análise Comparativa */}
                      <div className="bg-white dark:bg-lia-bg-secondary rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-2 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                          Comparativo com Mercado
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-gray-50 dark:bg-lia-bg-elevated/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-lia-text-primary`}>Salário</p>
                            <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">
                              {previewJob.salary > 'R$ 10.000' ? '+15%' : '-5%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. mercado</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-lia-bg-elevated/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-lia-text-primary`}>Candidatos</p>
                            <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">
                              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. média</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-lia-bg-elevated/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-lia-text-primary`}>Atratividade</p>
                            <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">
                              #—
                            </p>
                            <p className={textStyles.bodySmall}>ranking</p>
                          </div>
                        </div>
                      </div>

                      {/* Fatores de Risco */}
                      <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-2 flex items-center gap-1`}>
                          <Shield className="w-3.5 h-3.5 text-status-error" />
                          Fatores de Risco
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-lia-text-primary dark:text-lia-text-primary">Competitividade salarial</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.level === 'Sênior' ? 4 : 2) ? 'bg-status-error' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-lia-text-primary dark:text-lia-text-primary">Escassez de talentos</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.level === 'Sênior' ? 3 : 1) ? 'bg-wedo-orange' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-lia-text-primary dark:text-lia-text-primary">Tempo de processo</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-gray-500 dark:bg-lia-bg-elevated' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab: Métricas LIA Triagens - ARQUIVADO: código preservado mas desabilitado */}
                  {false && (
                    <div className="space-y-4">
                      {/* Header com Resumo */}
                      <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Brain className="w-4 h-4 text-wedo-cyan mt-0.5" />
                          <div className="flex-1">
                            <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-1`}>
                              Performance LIA - Triagens Automatizadas
                            </h4>
                            <p className={`${textStyles.bodySmall} dark:text-lia-text-primary`}>
                              Análise detalhada do impacto da inteligência artificial no processo de triagem desta vaga
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Métricas Principais - Grid 2x2 */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Horas Economizadas */}
                        <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Triagens Realizadas</span>
                            <Clock className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                          </div>
                          <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                            {previewJob.liaMetrics?.triagens_realizadas ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                            de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
                          </div>
                        </div>

                        {/* Pipeline LIA */}
                        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-lia-border-default dark:border-lia-border-default">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Pipeline LIA</span>
                            <TrendingUp className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                          </div>
                          <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                            {previewJob.liaMetrics?.pipeline_lia ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                            candidatos em triagem
                          </div>
                        </div>

                        {/* Sem Resposta */}
                        <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Sem Resposta</span>
                            <Zap className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                          </div>
                          <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                            {previewJob.liaMetrics?.sem_resposta ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                            candidatos
                          </div>
                        </div>

                        {/* Taxa de Conclusão */}
                        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-lia-border-default dark:border-lia-border-default">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Taxa de Conclusão</span>
                            <CheckCircle className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                          </div>
                          <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                            {(() => {
                              const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                              const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                              return agendadas > 0 ? Math.round((realizadas / agendadas) * 100) : 0
                            })()}%
                          </div>
                          <div className="mt-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                            {previewJob.liaMetrics?.triagens_realizadas ?? 0} de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
                          </div>
                        </div>
                      </div>

                      {/* Funil LIA Detalhado */}
                      <div className="bg-white dark:bg-lia-bg-secondary rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                          Funil de Triagem LIA
                        </h4>

                        <div className="space-y-2">
                          {/* Pipeline LIA */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-lia-text-primary dark:text-lia-text-primary w-24">Pipeline LIA</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                                <div className="bg-gray-400 dark:bg-lia-bg-elevated h-3 rounded-full flex items-center justify-end pr-1 w-full">
                                  <span className="text-xs text-white font-medium">{previewJob.liaMetrics?.pipeline_lia ?? 0}</span>
                                </div>
                              </div>
                            </div>
                            <span className="text-xs text-lia-text-primary w-10 text-right">100%</span>
                          </div>

                          {/* Agendadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-lia-text-primary dark:text-lia-text-primary w-24">Agendadas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (triagensAgendadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-500 dark:bg-gray-400 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                                      <span className="text-xs text-white font-medium">{triagensAgendadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-lia-text-primary w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                return pipelineLia > 0 ? Math.round((triagensAgendadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>

                          {/* Realizadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-lia-text-primary dark:text-lia-text-primary w-24">Realizadas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (triagensRealizadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-600 dark:bg-gray-300 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                                      <span className="text-xs text-white dark:text-lia-text-primary font-medium">{triagensRealizadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-lia-text-primary w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                return pipelineLia > 0 ? Math.round((triagensRealizadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>

                          {/* Entrevistas Agendadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-lia-text-primary dark:text-lia-text-primary w-24">Entrevistas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (entrevistasAgendadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-900 dark:bg-gray-100 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                                      <span className="text-xs text-white dark:text-lia-text-primary font-bold">{entrevistasAgendadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-lia-text-primary w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                                return pipelineLia > 0 ? Math.round((entrevistasAgendadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Média de Notas por Pergunta */}
                      <div className="bg-white dark:bg-lia-bg-secondary rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-3 flex items-center gap-1`}>
                          <Star className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                          Média de Notas por Critério
                        </h4>

                        <div className="text-center py-4">
                          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">
                            Sem dados disponíveis
                          </p>
                          <p className="text-micro text-lia-text-disabled dark:text-lia-text-tertiary mt-1">
                            As médias serão exibidas após as triagens serem concluídas
                          </p>
                        </div>
                      </div>

                      {/* Comparação com Outras Vagas */}
                      <div className="bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md p-3 border border-wedo-purple/30 dark:border-wedo-purple/30">
                        <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                          Resumo do Funil
                        </h4>

                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-white dark:bg-lia-bg-secondary rounded-md">
                            <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-1">Total no Funil</p>
                            <p className="text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary">
                              {previewJob.funnel.total}
                            </p>
                            <p className="text-micro text-lia-text-tertiary mt-1">candidatos</p>
                          </div>

                          <div className="text-center p-2 bg-white dark:bg-lia-bg-secondary rounded-md">
                            <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-1">Em Triagem</p>
                            <p className="text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary">
                              {previewJob.funnel.screening}
                            </p>
                            <p className="text-micro text-lia-text-tertiary mt-1">candidatos</p>
                          </div>

                          <div className="text-center p-2 bg-white dark:bg-lia-bg-secondary rounded-md">
                            <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-1">Em Entrevista</p>
                            <p className="text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary">
                              {previewJob.funnel.interview}
                            </p>
                            <p className="text-micro text-lia-text-tertiary mt-1">candidatos</p>
                          </div>
                        </div>
                      </div>

                      {/* Candidatos Sem Resposta */}
                      <div className="bg-status-warning/10 dark:bg-status-warning/20 rounded-md p-3 border border-status-warning/30 dark:border-status-warning/30">
                        <h4 className={`${textStyles.title} dark:text-lia-text-primary mb-2 flex items-center gap-1`}>
                          <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
                          Candidatos Sem Resposta
                        </h4>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className={`${textStyles.bodySmall} dark:text-lia-text-primary`}>Sem Resposta</span>
                              <span className="text-xs font-bold text-status-warning dark:text-status-warning">
                                {previewJob.liaMetrics?.sem_resposta ?? 0}
                              </span>
                            </div>
                            <div className="bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-1.5">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                                const percent = pipelineLia > 0 ? (semResposta / pipelineLia) * 100 : 0
                                return <div className="bg-status-warning h-1.5 rounded-full" style={{width: `${percent}%`}}></div>
                              })()}
                            </div>
                            <p className="text-xs text-lia-text-primary mt-1">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                                return pipelineLia > 0 ? `${Math.round((semResposta / pipelineLia) * 100)}% do pipeline` : 'N/A'
                              })()}
                            </p>
                          </div>

                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className={`${textStyles.bodySmall} dark:text-lia-text-primary`}>Aguardando</span>
                              <span className="text-xs font-bold text-wedo-cyan-dark dark:text-wedo-cyan-dark">
                                {(() => {
                                  const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                  const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                  return Math.max(0, agendadas - realizadas)
                                })()}
                              </span>
                            </div>
                            <div className="bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-1.5">
                              {(() => {
                                const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                const percent = agendadas > 0 ? ((agendadas - realizadas) / agendadas) * 100 : 0
                                return <div className="bg-gray-900 dark:bg-gray-50 h-1.5 rounded-full" style={{width: `${Math.max(0, percent)}%`}}></div>
                              })()}
                            </div>
                            <p className="text-xs text-lia-text-primary mt-1">triagens pendentes</p>
                          </div>
                        </div>
                      </div>

                      {/* Resumo LIA */}
                      <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 border border-lia-border-subtle dark:border-lia-border-subtle">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary font-semibold mb-1">
                              Resumo da Triagem LIA
                            </p>
                            <ul className="space-y-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                              <li>• {previewJob.liaMetrics?.triagens_realizadas ?? 0} triagens realizadas de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas</li>
                              <li>• {previewJob.liaMetrics?.entrevistas_agendadas ?? 0} entrevistas agendadas</li>
                              <li>• {previewJob.liaMetrics?.sem_resposta ?? 0} candidatos sem resposta</li>
                              <li>• {previewJob.liaMetrics?.pipeline_lia ?? 0} candidatos no pipeline LIA</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}


                  {activePreviewTab === 'screening' && (
                    <JobScreeningSection
                      previewJob={previewJob}
                      screeningConfig={screeningConfig}
                      isLoadingScreeningConfig={isLoadingScreeningConfig}
                      collapsedPreviewSections={collapsedPreviewSections}
                      expandedBlocks={expandedBlocks}
                      onToggleSection={togglePreviewSection}
                      onToggleBlock={toggleBlock}
                    />
                  )}

                  {activePreviewTab === 'pipeline' && (
                    <JobPipelineSection
                      previewJob={previewJob}
                      jobMetrics={jobMetrics}
                      isLoadingJobMetrics={isLoadingJobMetrics}
                    />
                  )}

                  {/* Ações Rápidas - Aparecem em todas as tabs */}
                  <div className="mt-4 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle space-y-2">
                    <Button
                      className="w-full text-xs h-8 gap-2"
                      onClick={() => onJobClick(previewJob)}
                    >
                      <ChevronRight className="w-4 h-4" />
                      Abrir Kanban de Candidatos
                    </Button>
                  </div>
                </div>
              </div>
  )
}
