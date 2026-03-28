"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, Clock, MapPin, DollarSign, Heart, Shield, Building, Lock, Globe,
  Expand, X, ChevronRight, ClipboardList, Target, TrendingUp, Lightbulb,
  BarChart3, Brain, AlertCircle, CheckCircle, Share2, Linkedin, Briefcase,
  FileText, Layers3, CalendarCheck, Settings, MessageSquare, Phone,
  ChevronDown, ChevronUp, Star, Zap
} from "lucide-react"
import { type Job } from "@/components/jobs"
import { type ScreeningConfig } from "@/hooks/useScreeningConfig"
import { type JobVacancyMetrics } from "@/services/lia-api"
import { WSI_BLOCKS, WSI_AUTOMATIC_MESSAGES, formatMessageWithVariables, getStatusColor } from "@/components/jobs/jobsPageConstants"
import { textStyles } from "@/lib/design-tokens"

interface JobPreviewPanelProps {
  showJobPreview: boolean
  previewJob: Job | null
  activePreviewTab: 'screening' | 'pipeline'
  onTabChange: (tab: 'screening' | 'pipeline') => void
  previewWidth: number
  onResize: (width: number) => void
  onResizeStart: () => void
  onResizeEnd: () => void
  onClose: () => void
  onJobClick: (job: Job) => void
  screeningConfig: ScreeningConfig | undefined
  isLoadingScreeningConfig: boolean
  jobMetrics: JobVacancyMetrics | null
  isLoadingJobMetrics: boolean
}

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

  if (!showJobPreview || !previewJob) return null

  return (
              <div 
                className="flex-shrink-0 bg-white dark:bg-gray-800 rounded-md overflow-hidden animate-slide-in flex flex-col h-full max-h-[calc(100vh-180px)] relative group"
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
                <div className="bg-white dark:bg-gray-800 border-b border-gray-100">
                  {/* Linha 1: Título + Código + Ações */}
                  <div className="px-3 pt-3 pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        {/* Row 1: Título + Código (lado direito) */}
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-base-ui font-semibold text-gray-950 dark:text-gray-50 truncate">
                            {previewJob.title}
                          </h3>
                          <Badge className="text-micro px-1.5 py-0 h-4 flex-shrink-0 font-mono font-medium" style={{backgroundColor: 'rgba(107, 114, 128, 0.15)', border: '1px solid rgba(107, 114, 128, 0.3)'}}>
                            {previewJob.jobId}
                          </Badge>
                          {previewJob.isAffirmative && (
                            <span title="Vaga Afirmativa">
                              <Heart className="w-3 h-3 text-wedo-magenta" />
                            </span>
                          )}
                        </div>

                        {/* Row 2: Datas em texto simples (como no candidato) */}
                        <div className="flex items-center gap-3 mb-1 text-micro text-gray-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3 text-gray-400" />
                            {previewJob.openDate ? new Date(previewJob.openDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                          </span>
                          {previewJob.deadline && (
                            <span className={`flex items-center gap-1 ${
                              new Date(previewJob.deadline) < new Date() ? 'text-status-error' : 'text-gray-500'
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
                        <div className="flex items-center gap-3 mb-1.5 text-micro text-gray-400">
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
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 border border-gray-200">
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
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 border border-gray-200">
                              {previewJob.workModel === 'remoto' ? 'Remoto' : previewJob.workModel === 'híbrido' ? 'Híbrido' : 'Presencial'}
                            </Badge>
                          )}
                          {previewJob.type && (
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-700 border border-gray-200">
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
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-800 border-gray-200">
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
                            <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-gray-500 border-gray-200 flex items-center gap-0.5">
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
                            const scrLabels: Record<string, string> = {
                              not_configured: 'Triagem: N/C',
                              not_started: 'Triagem: Não Iniciada',
                              active: 'Triagem: Ativa',
                              paused: 'Triagem: Pausada',
                              completed: 'Triagem: Concluída',
                            }
                            const scrColors: Record<string, string> = {
                              not_configured: 'var(--gray-200)',
                              not_started: 'var(--gray-100)',
                              active: 'var(--status-success)',
                              paused: 'var(--gray-300)',
                              completed: 'var(--gray-400)',
                            }
                            return (
                              <Badge 
                                className="text-micro px-1.5 py-0 h-4 font-medium text-gray-800"
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
                    <div className="px-3 pb-2 border-t border-gray-100 dark:border-gray-700/50 pt-2">
                      <div className="flex items-center gap-0.5 overflow-x-auto">
                        {previewJob.hiringProcess.map((step, idx) => (
                          <React.Fragment key={idx}>
                            <div className={`px-1.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                              idx === 0 ? 'bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200 font-semibold' :
                              idx === (previewJob.hiringProcess?.length || 0) - 1 ? 'bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200 font-semibold' :
                              'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                            }`}>
                              {step}
                            </div>
                            {idx < (previewJob.hiringProcess?.length || 0) - 1 && (
                              <ChevronRight className="w-2 h-2 text-gray-800 flex-shrink-0" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Tabs de Navegação - Tamanho Reduzido */}
                <div className="border-b border-gray-100">
                  <div className="flex items-center px-3">
                    <button
                      onClick={() => onTabChange('screening')}
                      className={`px-2 py-2 text-micro font-medium border-b transition-colors ${
                        activePreviewTab === 'screening'
                          ? 'border-gray-900 text-gray-700 font-semibold'
                          : 'border-transparent text-gray-500 hover:text-gray-700'
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
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Sucesso de Fechamento</span>
                            <Target className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-xl font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.performance?.conversion_rate != null 
                              ? `${Math.round(jobMetrics.performance.conversion_rate)}%` 
                              : previewJob.funnel.hired > 0 
                                ? `${Math.round((previewJob.funnel.hired / Math.max(previewJob.funnel.total, 1)) * 100)}%`
                                : '—'}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            Pipeline: {jobMetrics?.funnel.total ?? previewJob.funnel.total} candidatos
                          </div>
                        </div>

                        {/* Atividade 7d */}
                        <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Atividade 7d</span>
                            <TrendingUp className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                          </div>
                          <div className="text-xl font-bold text-gray-900 dark:text-gray-50">
                            {isLoadingJobMetrics ? '...' : jobMetrics ? jobMetrics.activity.applications_7d : 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                            {isLoadingJobMetrics ? '...' : jobMetrics ? `${jobMetrics.activity.views_7d} visualizações` : 'Sem dados'}
                          </div>
                        </div>

                        {/* Time to Fill */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Time to Fill</span>
                            <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-xl font-bold text-gray-950 dark:text-gray-50 font-semibold">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.performance.time_to_fill_days != null ? `${jobMetrics.performance.time_to_fill_days}d` : (previewJob.urgencyLevel > 3 ? '15d' : previewJob.urgencyLevel > 2 ? '25d' : '35d')}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            {isLoadingJobMetrics ? '...' : jobMetrics?.activity.interviews_scheduled ? `${jobMetrics.activity.interviews_scheduled} entrevistas agendadas` : 'Sem entrevistas'}
                          </div>
                        </div>

                        {/* SLA Status */}
                        <div className={`rounded-md p-3 ${jobMetrics?.sla.within_sla === false ? 'bg-status-error/10 dark:bg-status-error/20' : 'bg-gray-50 dark:bg-gray-800'}`}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Status SLA</span>
                            <Shield className={`w-3 h-3 ${jobMetrics?.sla.within_sla === false ? 'text-status-error' : 'text-gray-800 dark:text-gray-200'}`} />
                          </div>
                          <div className={`text-xl font-bold font-semibold ${jobMetrics?.sla.within_sla === false ? 'text-status-error dark:text-status-error' : 'text-gray-950 dark:text-gray-50'}`}>
                            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.within_sla ? 'OK' : 'Atrasado'}
                          </div>
                          <div className={`mt-1 text-xs ${jobMetrics?.sla.within_sla === false ? 'text-status-error dark:text-status-error' : 'text-gray-800 dark:text-gray-200'}`}>
                            {isLoadingJobMetrics ? '...' : jobMetrics?.sla.days_remaining != null ? `${jobMetrics.sla.days_remaining} dias restantes` : 'Sem prazo definido'}
                          </div>
                        </div>
                      </div>

                      {/* Insights e Recomendações da LIA */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-950 dark:text-gray-200 font-semibold mb-1">
                              Insights da LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
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
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Comparativo com Mercado
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Salário</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.salary > 'R$ 10.000' ? '+15%' : '-5%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. mercado</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Candidatos</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. média</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Atratividade</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              #—
                            </p>
                            <p className={textStyles.bodySmall}>ranking</p>
                          </div>
                        </div>
                      </div>

                      {/* Fatores de Risco */}
                      <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <Shield className="w-3.5 h-3.5 text-status-error" />
                          Fatores de Risco
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Competitividade salarial</span>
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
                            <span className="text-gray-800 dark:text-gray-200">Escassez de talentos</span>
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
                            <span className="text-gray-800 dark:text-gray-200">Tempo de processo</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-gray-500 dark:bg-gray-600' : 'bg-gray-300'
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
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Brain className="w-4 h-4 text-wedo-cyan mt-0.5" />
                          <div className="flex-1">
                            <h4 className={`${textStyles.title} dark:text-gray-50 mb-1`}>
                              Performance LIA - Triagens Automatizadas
                            </h4>
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>
                              Análise detalhada do impacto da inteligência artificial no processo de triagem desta vaga
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Métricas Principais - Grid 2x2 */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Horas Economizadas */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Triagens Realizadas</span>
                            <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.liaMetrics?.triagens_realizadas ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
                          </div>
                        </div>

                        {/* Pipeline LIA */}
                        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-gray-300 dark:border-gray-600">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Pipeline LIA</span>
                            <TrendingUp className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.liaMetrics?.pipeline_lia ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            candidatos em triagem
                          </div>
                        </div>

                        {/* Sem Resposta */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Sem Resposta</span>
                            <Zap className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.liaMetrics?.sem_resposta ?? 0}
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            candidatos
                          </div>
                        </div>

                        {/* Taxa de Conclusão */}
                        <div className="bg-gray-100 dark:bg-gray-750 rounded-md p-3 border border-gray-300 dark:border-gray-600">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Taxa de Conclusão</span>
                            <CheckCircle className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                            {(() => {
                              const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                              const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                              return agendadas > 0 ? Math.round((realizadas / agendadas) * 100) : 0
                            })()}%
                          </div>
                          <div className="mt-1 text-xs text-gray-800 dark:text-gray-200">
                            {previewJob.liaMetrics?.triagens_realizadas ?? 0} de {previewJob.liaMetrics?.triagens_agendadas ?? 0} agendadas
                          </div>
                        </div>
                      </div>

                      {/* Funil LIA Detalhado */}
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Funil de Triagem LIA
                        </h4>

                        <div className="space-y-2">
                          {/* Pipeline LIA */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Pipeline LIA</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1" style={{width: '100%'}}>
                                  <span className="text-xs text-white font-medium">{previewJob.liaMetrics?.pipeline_lia ?? 0}</span>
                                </div>
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">100%</span>
                          </div>

                          {/* Agendadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Agendadas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
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
                            <span className="text-xs text-gray-800 w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const triagensAgendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                return pipelineLia > 0 ? Math.round((triagensAgendadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>

                          {/* Realizadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Realizadas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (triagensRealizadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-600 dark:bg-gray-300 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                                      <span className="text-xs text-white dark:text-gray-50 font-medium">{triagensRealizadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const triagensRealizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                return pipelineLia > 0 ? Math.round((triagensRealizadas / pipelineLia) * 100) : 0
                              })()}%
                            </span>
                          </div>

                          {/* Entrevistas Agendadas */}
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-800 dark:text-gray-200 w-24">Entrevistas</span>
                            <div className="flex-1 mx-2">
                              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                {(() => {
                                  const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                  const entrevistasAgendadas = previewJob.liaMetrics?.entrevistas_agendadas ?? 0
                                  const widthPercent = pipelineLia > 0 ? (entrevistasAgendadas / pipelineLia) * 100 : 0
                                  return (
                                    <div className="bg-gray-900 dark:bg-gray-100 h-3 rounded-full flex items-center justify-end pr-1"
                                         style={{width: `${Math.min(widthPercent, 100)}%`}}>
                                      <span className="text-xs text-white dark:text-gray-50 font-bold">{entrevistasAgendadas}</span>
                                    </div>
                                  )
                                })()}
                              </div>
                            </div>
                            <span className="text-xs text-gray-800 w-10 text-right">
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
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <Star className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Média de Notas por Critério
                        </h4>

                        <div className="text-center py-4">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Sem dados disponíveis
                          </p>
                          <p className="text-micro text-gray-400 dark:text-gray-500 mt-1">
                            As médias serão exibidas após as triagens serem concluídas
                          </p>
                        </div>
                      </div>

                      {/* Comparação com Outras Vagas */}
                      <div className="bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md p-3 border border-wedo-purple/30 dark:border-wedo-purple/30">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Resumo do Funil
                        </h4>

                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded-md">
                            <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Total no Funil</p>
                            <p className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.total}
                            </p>
                            <p className="text-micro text-gray-500 mt-1">candidatos</p>
                          </div>

                          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded-md">
                            <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Em Triagem</p>
                            <p className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.screening}
                            </p>
                            <p className="text-micro text-gray-500 mt-1">candidatos</p>
                          </div>

                          <div className="text-center p-2 bg-white dark:bg-gray-800 rounded-md">
                            <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Em Entrevista</p>
                            <p className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.interview}
                            </p>
                            <p className="text-micro text-gray-500 mt-1">candidatos</p>
                          </div>
                        </div>
                      </div>

                      {/* Candidatos Sem Resposta */}
                      <div className="bg-status-warning/10 dark:bg-status-warning/20 rounded-md p-3 border border-status-warning/30 dark:border-status-warning/30">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
                          Candidatos Sem Resposta
                        </h4>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Sem Resposta</span>
                              <span className="text-xs font-bold text-status-warning dark:text-status-warning">
                                {previewJob.liaMetrics?.sem_resposta ?? 0}
                              </span>
                            </div>
                            <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                                const percent = pipelineLia > 0 ? (semResposta / pipelineLia) * 100 : 0
                                return <div className="bg-status-warning h-1.5 rounded-full" style={{width: `${percent}%`}}></div>
                              })()}
                            </div>
                            <p className="text-xs text-gray-800 mt-1">
                              {(() => {
                                const pipelineLia = previewJob.liaMetrics?.pipeline_lia ?? 0
                                const semResposta = previewJob.liaMetrics?.sem_resposta ?? 0
                                return pipelineLia > 0 ? `${Math.round((semResposta / pipelineLia) * 100)}% do pipeline` : 'N/A'
                              })()}
                            </p>
                          </div>

                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Aguardando</span>
                              <span className="text-xs font-bold text-wedo-cyan-dark dark:text-wedo-cyan-dark">
                                {(() => {
                                  const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                  const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                  return Math.max(0, agendadas - realizadas)
                                })()}
                              </span>
                            </div>
                            <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              {(() => {
                                const agendadas = previewJob.liaMetrics?.triagens_agendadas ?? 0
                                const realizadas = previewJob.liaMetrics?.triagens_realizadas ?? 0
                                const percent = agendadas > 0 ? ((agendadas - realizadas) / agendadas) * 100 : 0
                                return <div className="bg-gray-900 dark:bg-gray-50 h-1.5 rounded-full" style={{width: `${Math.max(0, percent)}%`}}></div>
                              })()}
                            </div>
                            <p className="text-xs text-gray-800 mt-1">triagens pendentes</p>
                          </div>
                        </div>
                      </div>

                      {/* Resumo LIA */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-950 dark:text-gray-200 font-semibold mb-1">
                              Resumo da Triagem LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
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

                  {/* Tab: Roteiro de Triagem */}
                  {activePreviewTab === 'screening' && (
                    <div className="space-y-4">
                      {/* Loading State Guard */}
                      {isLoadingScreeningConfig ? (
                        <div className="space-y-4">
                          {/* Skeleton for Performance Card */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                            <div className="h-4 bg-gray-200 rounded-md w-32 mb-3"></div>
                            <div className="grid grid-cols-4 gap-2">
                              {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="text-center">
                                  <div className="h-6 bg-gray-200 rounded-md mb-1"></div>
                                  <div className="h-3 bg-gray-100 rounded-md w-12 mx-auto"></div>
                                </div>
                              ))}
                            </div>
                            <div className="grid grid-cols-4 gap-2 mt-2 pt-2 border-t border-gray-100">
                              {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="text-center">
                                  <div className="h-6 bg-gray-200 rounded-md mb-1"></div>
                                  <div className="h-3 bg-gray-100 rounded-md w-12 mx-auto"></div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Skeleton for Skills Card */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                            <div className="h-4 bg-gray-200 rounded-md w-32 mb-3"></div>
                            <div className="flex flex-wrap gap-1.5">
                              {[1, 2, 3, 4, 5, 6].map((i) => (
                                <div key={i} className="h-6 bg-gray-200 rounded-md px-2 w-24"></div>
                              ))}
                            </div>
                          </div>

                          {/* Skeleton for Questions Card */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                            <div className="h-4 bg-gray-200 rounded-md w-40 mb-3"></div>
                            <div className="space-y-3">
                              {[1, 2, 3].map((i) => (
                                <div key={i} className="p-2 bg-gray-50 rounded-md border border-gray-100">
                                  <div className="h-4 bg-gray-200 rounded-md w-3/4 mb-2"></div>
                                  <div className="h-3 bg-gray-100 rounded-md w-1/2"></div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                      {/* 4. Descrição da Vaga */}
                      {previewJob.description && (
                        <div className="p-3 bg-white border border-gray-100 rounded-md">
                          <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('descricao')}>
                            <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                              <FileText className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                              Descrição da Vaga
                            </h5>
                            {collapsedPreviewSections.includes('descricao') ? (
                              <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            ) : (
                              <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            )}
                          </div>
                          {!collapsedPreviewSections.includes('descricao') && (
                            <p className="text-micro text-gray-600 dark:text-gray-300 leading-relaxed whitespace-pre-line line-clamp-6 mt-2">
                              {previewJob.description}
                            </p>
                          )}
                        </div>
                      )}

                      {/* 3. Competências Avaliadas */}
                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('competencias')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                            Competências Avaliadas
                          </h5>
                          {collapsedPreviewSections.includes('competencias') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('competencias') && (<>
                        {(() => {
                          const technicalSkills = (previewJob.technicalRequirements || []).map((tr: any) => typeof tr === 'string' ? tr : tr.technology || tr.name).filter(Boolean)
                          const behavioralSkills = (previewJob.behavioralCompetencies || []).map((bc: any) => typeof bc === 'string' ? bc : bc.competency || bc.name).filter(Boolean)
                          const responsibilitySkills = (previewJob.requirements || []).map((r: any) => typeof r === 'string' ? r : r.requirement || r.text || r.name).filter(Boolean)
                          const hasData = technicalSkills.length > 0 || behavioralSkills.length > 0 || responsibilitySkills.length > 0

                          if (!hasData) {
                            const fallbackSkills = screeningConfig?.wsi_skills || ['Comunicação', 'Resolução de Problemas', 'Adaptabilidade', 'Trabalho em Equipe']
                            return (
                              <div className="flex flex-wrap gap-1.5">
                                {fallbackSkills.slice(0, 6).map((skill: string, idx: number) => (
                                  <Badge key={idx} className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-micro px-1.5 py-0.5 h-[18px] font-medium">
                                    {skill}
                                  </Badge>
                                ))}
                              </div>
                            )
                          }

                          return (
                            <div className="space-y-2">
                              {technicalSkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-gray-500 uppercase tracking-wide">Técnicas</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {technicalSkills.map((skill: string, idx: number) => (
                                      <Badge key={idx} className="bg-wedo-cyan/10 dark:bg-wedo-cyan/30 text-wedo-cyan-dark dark:text-wedo-cyan-dark text-micro px-1.5 py-0.5 h-[18px] font-medium border border-wedo-cyan/30">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {behavioralSkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-gray-500 uppercase tracking-wide">Comportamentais</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {behavioralSkills.map((skill: string, idx: number) => (
                                      <Badge key={idx} className="bg-wedo-purple/10 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple text-micro px-1.5 py-0.5 h-[18px] font-medium border border-wedo-purple/30">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {responsibilitySkills.length > 0 && (
                                <div>
                                  <span className="text-micro font-medium text-gray-500 uppercase tracking-wide">Responsabilidades</span>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {responsibilitySkills.slice(0, 8).map((skill: string, idx: number) => (
                                      <Badge key={idx} className="bg-status-warning/10 dark:bg-status-warning/30 text-status-warning dark:text-status-warning text-micro px-1.5 py-0.5 h-[18px] font-medium border border-status-warning/30">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })()}
                        <p className="text-micro text-gray-400 mt-2 flex items-center gap-1">
                          <Lightbulb className="w-3 h-3" />
                          Extraídas automaticamente do perfil da vaga via metodologia WSI
                        </p>
                        </>)}
                      </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('idiomas')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Idiomas
                          </h5>
                          {collapsedPreviewSections.includes('idiomas') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('idiomas') && (
                          previewJob.languages && previewJob.languages.length > 0 ? (
                            <div className="space-y-1.5 mt-2">
                              {previewJob.languages.map((lang: any, idx: number) => (
                                <div key={idx} className="flex items-center gap-2">
                                  <span className="text-micro text-gray-600 dark:text-gray-400 font-medium">
                                    {lang.language}
                                  </span>
                                  {lang.level && (
                                    <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                                      {lang.level}
                                    </Badge>
                                  )}
                                  {lang.required && (
                                    <Badge className="text-micro px-1.5 py-0 h-4 bg-status-error/10 text-status-error border border-status-error/30">
                                      Obrigatório
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-micro text-gray-500 dark:text-gray-400 italic mt-2">
                              Nenhum idioma configurado
                            </p>
                          )
                        )}
                      </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('remuneracao')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <DollarSign className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Remuneração e Benefícios
                          </h5>
                          {collapsedPreviewSections.includes('remuneracao') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('remuneracao') && (
                          <div className="space-y-2 mt-2">
                            {(() => {
                              const salaryMin = previewJob.salaryRange?.min ?? previewJob.salaryMin
                              const salaryMax = previewJob.salaryRange?.max ?? previewJob.salaryMax
                              const hasSalary = salaryMin || salaryMax
                              const bonusMin = previewJob.bonusRange?.min ?? previewJob.bonus_range?.min ?? previewJob.bonusMin
                              const bonusMax = previewJob.bonusRange?.max ?? previewJob.bonus_range?.max ?? previewJob.bonusMax
                              const hasBonus = bonusMin || bonusMax
                              const benefits = previewJob.benefits || []
                              const fmt = (v: any) => {
                                if (!v) return ''
                                const n = typeof v === 'string' ? parseFloat(v) : v
                                return isNaN(n) ? '' : `R$ ${n.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                              }
                              return (
                                <>
                                  {hasSalary ? (
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-micro text-gray-500 dark:text-gray-400">Salário:</span>
                                      <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                                        {fmt(salaryMin)}{salaryMax ? ` - ${fmt(salaryMax)}` : ''}
                                      </span>
                                    </div>
                                  ) : (
                                    <p className="text-micro text-gray-500 dark:text-gray-400 italic">
                                      Faixa salarial não informada
                                    </p>
                                  )}
                                  {hasBonus && (
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-micro text-gray-500 dark:text-gray-400">Bônus:</span>
                                      <span className="text-micro font-medium text-gray-950 dark:text-gray-50">
                                        {fmt(bonusMin)}{bonusMax ? ` - ${fmt(bonusMax)}` : ''}
                                      </span>
                                    </div>
                                  )}
                                  {benefits.length > 0 && (
                                    <div>
                                      <span className="text-micro text-gray-500 dark:text-gray-400 block mb-1">Benefícios:</span>
                                      <div className="flex flex-wrap gap-1.5">
                                        {benefits.map((b: any, idx: number) => (
                                          <Badge key={idx} className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                                            {typeof b === 'string' ? b : b.name}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </>
                              )
                            })()}
                          </div>
                        )}
                      </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('etapas')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Layers3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Etapas do Processo
                          </h5>
                          {collapsedPreviewSections.includes('etapas') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('etapas') && (
                          <div className="mt-2">
                            {previewJob.hiringProcess && previewJob.hiringProcess.length > 0 ? (
                              <div className="flex items-center gap-1 overflow-x-auto pb-1">
                                {previewJob.hiringProcess.map((step: string, idx: number) => (
                                  <React.Fragment key={idx}>
                                    {idx > 0 && (
                                      <ChevronRight className="w-3 h-3 text-gray-300 flex-shrink-0" />
                                    )}
                                    <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-md flex-shrink-0">
                                      <span className="text-micro font-medium text-gray-700">{step}</span>
                                    </div>
                                  </React.Fragment>
                                ))}
                              </div>
                            ) : previewJob.interviewStages && previewJob.interviewStages.length > 0 ? (
                              <div className="flex items-center gap-1 overflow-x-auto pb-1">
                                {previewJob.interviewStages
                                  .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
                                  .map((stage: any, idx: number) => (
                                    <React.Fragment key={idx}>
                                      {idx > 0 && (
                                        <ChevronRight className="w-3 h-3 text-gray-300 flex-shrink-0" />
                                      )}
                                      <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 border border-gray-200 rounded-md flex-shrink-0">
                                        {stage.liaAssisted && (
                                          <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" />
                                        )}
                                        <span className="text-micro font-medium text-gray-700">{stage.stageName}</span>
                                      </div>
                                    </React.Fragment>
                                  ))}
                              </div>
                            ) : (
                              <p className="text-micro text-gray-500 dark:text-gray-400 italic">
                                Nenhuma etapa configurada
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                          <div className="border-t border-gray-200 dark:border-gray-700" />

                          {/* Roteiro de Triagem Automática */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <ClipboardList className="w-4 h-4 text-gray-600" />
                              <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Roteiro de Triagem Automática</h4>
                              <Badge 
                                className={`text-micro px-1.5 py-0 h-4 text-gray-950 ${(screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-gray-200'}`}
                              >
                                {(screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
                              </Badge>
                            </div>
                          </div>

                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('fluxo-resumido')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <ClipboardList className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            Resumo da Triagem
                            <Badge
                              className={`text-micro px-1.5 py-0 h-4 text-gray-800 ${(screeningConfig?.status?.enabled ?? true) ? 'bg-wedo-green-pastel' : 'bg-gray-200'}`}
                            >
                              {(screeningConfig?.status?.enabled ?? true) ? 'Ativo' : 'Pausado'}
                            </Badge>
                          </h5>
                          {collapsedPreviewSections.includes('fluxo-resumido') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>
                        {!collapsedPreviewSections.includes('fluxo-resumido') && (
                          <div className="mt-2">
                            <div className="grid grid-cols-2 gap-2">
                              <div className="text-center p-2 bg-gray-50 rounded-md">
                                <div className="text-base-ui font-semibold text-gray-800">{(previewJob.screeningQuestions || []).length}</div>
                                <p className="text-micro text-gray-500">Perguntas</p>
                              </div>
                              <div className="text-center p-2 bg-gray-50 rounded-md">
                                <div className="text-base-ui font-semibold text-gray-800">{Math.ceil((previewJob.screeningQuestions || []).reduce((acc: number, q: any) => acc + (q.time_limit || 120), 0) / 60)}min</div>
                                <p className="text-micro text-gray-500">Tempo Est.</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* 5. Blocos WSI do Roteiro de Triagem */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('fluxo-wsi')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Layers3 className="w-3.5 h-3.5 text-gray-600" />
                            Fluxo de Triagem WSI
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-200 text-gray-800">
                              6 Blocos
                            </Badge>
                          </h5>
                          {collapsedPreviewSections.includes('fluxo-wsi') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>

                        {!collapsedPreviewSections.includes('fluxo-wsi') && (
                        <div className="space-y-2">
                          {WSI_BLOCKS.map((block) => {
                            const isExpanded = expandedBlocks.includes(block.id)
                            
                            const allQuestions = previewJob.screeningQuestions || []
                            const cat = (q: any) => (q.category || '').toLowerCase()
                            const typ = (q: any) => (q.type || '').toLowerCase()
                            
                            const isBlock2 = (q: any) => {
                              if (typ(q) === 'eliminatory' || q.required) return true
                              if (cat(q).includes('elegib') || cat(q).includes('elimin')) return true
                              if (cat(q).includes('fit') && cat(q).includes('básico')) return true
                              if (cat(q).includes('disponib') || cat(q).includes('eligib')) return true
                              return false
                            }
                            
                            const isBlock3 = (q: any) => {
                              if (isBlock2(q)) return false
                              return cat(q).includes('tecn') || cat(q).includes('tech') ||
                                cat(q).includes('skill') || cat(q).includes('técnica') ||
                                typ(q).includes('tech')
                            }
                            
                            const isBlock4 = (q: any) => {
                              if (isBlock2(q) || isBlock3(q)) return false
                              return true
                            }
                            
                            const blockQuestions = allQuestions.filter((q: any) => {
                              if (q.block_id !== undefined && q.block_id !== null) {
                                return q.block_id === block.id
                              }
                              if (block.id === 2) return isBlock2(q)
                              if (block.id === 3) return isBlock3(q)
                              if (block.id === 4) return isBlock4(q)
                              return false
                            })
                            
                            const eliminatoryCount = blockQuestions.filter((q: any) => q.type === 'eliminatory' || q.required).length
                            const informativeCount = blockQuestions.length - eliminatoryCount
                            
                            return (
                              <div 
                                key={block.id} 
                                className={`border rounded-md overflow-hidden ${
                                  block.editable ? 'border-gray-200' : 'border-gray-100 bg-gray-50/50'
                                }`}
                              >
                                {/* Block Header */}
                                <div 
                                  className={`flex items-center justify-between p-2.5 cursor-pointer transition-colors ${
                                    block.editable 
                                      ? 'bg-gray-50 hover:bg-gray-100' 
                                      : 'bg-gray-100/80'
                                  }`}
                                  onClick={() => {
                                    if (isExpanded) {
                                      setExpandedBlocks(prev => prev.filter(id => id !== block.id))
                                    } else {
                                      setExpandedBlocks(prev => [...prev, block.id])
                                    }
                                  }}
                                >
                                  <div className="flex items-center gap-2">
                                    <span className={`w-5 h-5 rounded-full text-white text-micro font-bold flex items-center justify-center ${
                                      block.editable ? 'bg-gray-700' : 'bg-gray-400'
                                    }`}>
                                      {block.id}
                                    </span>
                                    <div>
                                      <span className={`text-xs font-semibold ${block.editable ? 'text-gray-950' : 'text-gray-600'}`}>
                                        {block.name}
                                      </span>
                                      <span className="text-micro text-gray-500 ml-1.5">({block.duration})</span>
                                    </div>
                                    {!block.editable && (
                                      <Badge className="text-micro px-1 py-0 h-3.5 bg-gray-200 text-gray-500">
                                        Auto
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-1.5">
                                    {block.editable && blockQuestions.length > 0 && (
                                      <>
                                        {eliminatoryCount > 0 && (
                                          <Badge className="text-micro px-1.5 py-0 bg-status-error/10 text-status-error border border-status-error/30">
                                            {eliminatoryCount} Elim.
                                          </Badge>
                                        )}
                                        {informativeCount > 0 && (
                                          <Badge className="text-micro px-1.5 py-0 bg-gray-100 text-gray-600">
                                            {informativeCount} Info.
                                          </Badge>
                                        )}
                                      </>
                                    )}
                                    {isExpanded ? (
                                      <ChevronUp className="w-3.5 h-3.5 text-gray-500" />
                                    ) : (
                                      <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                                    )}
                                  </div>
                                </div>
                                
                                {/* Block Content */}
                                {isExpanded && (
                                  <div className={`p-2.5 space-y-1.5 ${!block.editable ? 'bg-gray-50/30' : ''}`}>
                                    {/* Non-editable blocks show automatic WSI messages */}
                                    {!block.editable ? (
                                      WSI_AUTOMATIC_MESSAGES[block.id] ? (
                                        <div className="rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 overflow-hidden">
                                          <div className="px-2.5 py-2 border-b border-gray-900 dark:border-gray-50/10 bg-gray-100 dark:bg-gray-800">
                                            <p className="text-xs font-medium text-gray-800">
                                              {WSI_AUTOMATIC_MESSAGES[block.id].title}
                                            </p>
                                          </div>
                                          <div className="p-2.5">
                                            <div className="text-micro text-gray-800 leading-relaxed whitespace-pre-line">
                                              {formatMessageWithVariables(WSI_AUTOMATIC_MESSAGES[block.id].message)}
                                            </div>
                                          </div>
                                          <div className="px-2.5 py-2 border-t border-gray-900 dark:border-gray-50/10 bg-gray-50">
                                            <p className="text-micro text-gray-500 italic">
                                              {WSI_AUTOMATIC_MESSAGES[block.id].note}
                                            </p>
                                          </div>
                                        </div>
                                      ) : (
                                        <div className="p-2.5 bg-white/60 border border-gray-100 rounded-md">
                                          <p className="text-micro text-gray-600 italic">
                                            {block.description}
                                          </p>
                                          <p className="text-micro text-gray-400 mt-1">
                                            Gerenciado automaticamente pela LIA
                                          </p>
                                        </div>
                                      )
                                    ) : (
                                      <>
                                        {blockQuestions.length === 0 ? (
                                          <div className="p-3 bg-gray-50 border border-gray-200 border-dashed rounded-md text-center">
                                            <p className="text-micro text-gray-500">
                                              Nenhuma pergunta neste bloco
                                            </p>
                                          </div>
                                        ) : (
                                          blockQuestions.map((item: any, idx: number) => (
                                            <div 
                                              key={item.id || idx} 
                                              className="p-2.5 bg-white border border-gray-200 rounded-md"
                                            >
                                              <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                                                <Badge className={`text-micro px-1.5 py-0 h-4 rounded-full ${
                                                  item.category === 'behavioral' || item.category === 'Comportamental'
                                                    ? 'bg-wedo-purple/15 text-wedo-purple border border-wedo-purple/30'
                                                    : item.category === 'technical' || item.category === 'Técnica'
                                                    ? 'bg-wedo-cyan/10 text-wedo-cyan-dark border border-wedo-cyan/30'
                                                    : item.category === 'eligibility' || item.category === 'Elegibilidade'
                                                    ? 'bg-status-success/15 text-status-success border border-status-success/30'
                                                    : 'bg-gray-100 text-gray-700 border border-gray-200'
                                                }`}>
                                                  {item.category === 'behavioral' ? 'Comport.' 
                                                    : item.category === 'technical' ? 'Técnica' 
                                                    : item.category === 'eligibility' ? 'Elegibilidade'
                                                    : item.category === 'cultural' ? 'Cultural'
                                                    : item.category || 'Geral'}
                                                </Badge>
                                                {(item.type === 'eliminatory' || item.required) && (
                                                  <Badge className="text-micro px-1.5 py-0 h-4 rounded-full bg-status-error/10 text-status-error border border-status-error/30">
                                                    Eliminatória
                                                  </Badge>
                                                )}
                                              </div>
                                              <p className="text-micro text-gray-950 leading-relaxed mb-1.5">
                                                {item.question}
                                              </p>
                                              <div className="flex items-center gap-2 flex-wrap">
                                                {item.skill_targeted && (
                                                  <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                    <Target className="w-2.5 h-2.5 text-gray-400" />
                                                    {item.skill_targeted}
                                                  </span>
                                                )}
                                                <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                  <MessageSquare className="w-2.5 h-2.5 text-gray-400" />
                                                  {item.type === 'eliminatory' ? 'Sim/Não' 
                                                    : item.options?.length ? 'Múltipla escolha'
                                                    : 'Texto livre'}
                                                </span>
                                                {item.weight != null && (
                                                  <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                    <BarChart3 className="w-2.5 h-2.5 text-gray-400" />
                                                    Peso {typeof item.weight === 'number' ? item.weight.toFixed(2) : item.weight}
                                                  </span>
                                                )}
                                                <span className="inline-flex items-center gap-0.5 text-micro text-gray-500">
                                                  <Clock className="w-2.5 h-2.5 text-gray-400" />
                                                  {item.type === 'eliminatory' ? '30s' : '2 min'}
                                                </span>
                                              </div>
                                            </div>
                                          ))
                                        )}
                                      </>
                                    )}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                        )}
                      </div>

                      {/* 2. Agendamento Automático */}
                      <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('agendamento')}>
                          <div className="flex items-center gap-2">
                            <CalendarCheck className="w-3.5 h-3.5 text-gray-600" />
                            <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50">Agendamento Automático</h5>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Badge className={`${(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'bg-gray-700 text-white dark:bg-gray-600' : 'bg-gray-400 text-white'} text-micro px-1.5 py-0 h-4`}>
                              {(screeningConfig?.scheduling?.auto_enabled ?? true) ? 'Ativo' : 'Inativo'}
                            </Badge>
                            {collapsedPreviewSections.includes('agendamento') ? (
                              <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            ) : (
                              <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                            )}
                          </div>
                        </div>
                        {!collapsedPreviewSections.includes('agendamento') && (<>
                        <p className="text-micro text-gray-500 mb-2 mt-2">Aprovados na triagem são agendados automaticamente para entrevista</p>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded-md">
                            <span className="text-micro text-gray-500">Score Mínimo</span>
                            <span className="text-micro font-medium text-gray-700">{(() => {
                              const preset = screeningConfig?.scheduling?.min_score_for_auto_preset
                              switch(preset) {
                                case 'rigorous': return 'Rigoroso'
                                case 'flexible': return 'Flexível'
                                default: return 'Recomendado'
                              }
                            })()}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded-md">
                            <span className="text-micro text-gray-500">Calendário</span>
                            <span className="text-micro font-medium text-gray-700">{screeningConfig?.scheduling?.calendar_provider || 'Microsoft'}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded-md">
                            <span className="text-micro text-gray-500">Horários</span>
                            <span className="text-micro font-medium text-gray-700">{screeningConfig?.scheduling?.available_hours || '9h-18h'}</span>
                          </div>
                          <div className="flex items-center justify-between p-1.5 bg-gray-50 rounded-md">
                            <span className="text-micro text-gray-500">Duração</span>
                            <span className="text-micro font-medium text-gray-700">{screeningConfig?.scheduling?.interview_duration_min ?? 45}min</span>
                          </div>
                        </div>
                        </>)}
                      </div>

                          {/* 1. Canais + Configurações Agrupados */}
                          <div className="p-3 bg-white border border-gray-100 rounded-md">
                        <div className="flex items-center justify-between cursor-pointer" onClick={() => togglePreviewSection('canais')}>
                          <h5 className="text-xs font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-1.5">
                            <Settings className="w-3.5 h-3.5 text-gray-600" />
                            Canais de Comunicação
                          </h5>
                          {collapsedPreviewSections.includes('canais') ? (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          ) : (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-400 transition-transform" />
                          )}
                        </div>

                        {!collapsedPreviewSections.includes('canais') && (<>
                        {/* Canais em linha */}
                        <div className="flex items-center gap-3 mb-3 mt-3 pb-3 border-b border-gray-100">
                          <span className="text-micro text-gray-500">Canais:</span>
                          <div className="flex items-center gap-2">
                            <div className={`flex items-center gap-1 px-2 py-1 rounded-md ${(screeningConfig?.channels?.whatsapp?.enabled ?? true) ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-600'}`}>
                              <MessageSquare className="w-3 h-3" />
                              <span className="text-micro font-medium">WhatsApp</span>
                              {(screeningConfig?.channels?.whatsapp?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
                            </div>
                            <div className={`flex items-center gap-1 px-2 py-1 rounded-md ${(screeningConfig?.channels?.chat_web?.enabled ?? true) ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-600'}`}>
                              <Globe className="w-3 h-3" />
                              <span className="text-micro font-medium">Chat Web</span>
                              {(screeningConfig?.channels?.chat_web?.enabled ?? true) && <CheckCircle className="w-3 h-3" />}
                            </div>
                            <div className={`flex items-center gap-1 px-2 py-1 rounded-md ${(screeningConfig?.channels?.phone?.enabled ?? false) ? 'bg-status-success/10 text-status-success' : 'bg-gray-100 text-gray-600'}`}>
                              <Phone className="w-3 h-3" />
                              <span className="text-micro font-medium">Ligação</span>
                              {(screeningConfig?.channels?.phone?.enabled ?? false) && <CheckCircle className="w-3 h-3" />}
                            </div>
                          </div>
                        </div>

                        {/* Configurações em grid */}
                        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Score Mínimo Aprovação</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-700 text-white">{(() => {
                              const preset = screeningConfig?.settings?.min_score_preset
                              switch(preset) {
                                case 'rigorous': return 'Rigoroso'
                                case 'flexible': return 'Flexível'
                                default: return 'Recomendado'
                              }
                            })()}</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Timeout Resposta</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800">{screeningConfig?.settings?.response_timeout_hours ?? 48}h</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Re-tentativas</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 text-gray-800">{screeningConfig?.settings?.max_retries ?? 2}x</Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-micro text-gray-500">Fallback</span>
                            <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-orange/15 text-wedo-orange">Revisão Manual</Badge>
                          </div>
                        </div>

                      </>)}
                      </div>

                      
                      </div>
                      )}
                    </div>
                  )}

                  {/* Tab: Funil & Analytics Unificado */}
                  {activePreviewTab === 'pipeline' && (
                    <div className="space-y-4">
                      {/* Cards de Métricas Preditivas Principais */}
                      <div className="grid grid-cols-2 gap-2">
                        {/* Score de Sucesso */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Sucesso de Fechamento</span>
                            <Target className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.total > 20 ? '85%' : previewJob.funnel.total > 10 ? '60%' : '35%'}
                          </div>
                          <div className="mt-0.5 text-xs text-gray-800 dark:text-gray-200">
                            Pipeline: {previewJob.funnel.total} candidatos
                          </div>
                        </div>

                        {/* Time to Fill */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Time to Fill</span>
                            <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          </div>
                          <div className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                            {previewJob.urgencyLevel > 3 ? '15' : previewJob.urgencyLevel > 2 ? '25' : '35'}d
                          </div>
                          <div className="mt-0.5 text-xs text-gray-800 dark:text-gray-200">
                            Velocidade: {previewJob.funnel.interview > 0 ? '3.2' : '1.5'} cv/dia
                          </div>
                        </div>

                        {/* Qualidade Pipeline */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Qualidade Pipeline</span>
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                          </div>
                          <div className="text-base-ui font-semibold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.final > 3 ? 'A+' : previewJob.funnel.interview > 5 ? 'B+' : 'C'}
                          </div>
 <div className="mt-0.5 text-xs text-gray-800">
                            Conversão: {previewJob.funnel.interview > 0 ? Math.round((previewJob.funnel.interview / previewJob.funnel.total) * 100) : 0}%
                          </div>
                        </div>

                        {/* Risco de Recusa */}
                        <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200">Risco de Recusa</span>
                            <AlertCircle className="w-3 h-3 text-status-error" />
                          </div>
                          <div className="text-base-ui font-semibold text-status-error dark:text-status-error">
                            {previewJob.level === 'Sênior' ? '45%' : previewJob.level === 'Pleno' ? '25%' : '15%'}
                          </div>
                          <div className="mt-0.5 text-xs text-status-error dark:text-status-error">
                            Gap salarial: {previewJob.level === 'Sênior' ? '±18%' : '±8%'}
                          </div>
                        </div>
                      </div>

                      {/* Funil de Recrutamento Visual */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Funil de Recrutamento
                        </h4>

                        {/* Visualização do Funil */}
                        <div className="space-y-2">
                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Total</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-500 dark:bg-gray-600 h-3 rounded-full flex items-center justify-end pr-1" style={{width: '100%'}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.total}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Triagem</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: `${(previewJob.funnel.screening / previewJob.funnel.total) * 100}%`}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.screening}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.screening / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Entrevistas</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: `${(previewJob.funnel.interview / previewJob.funnel.total) * 100}%`}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.interview}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.interview / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Finalistas</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-400 dark:bg-gray-500 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: `${(previewJob.funnel.final / previewJob.funnel.total) * 100}%`}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.final}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.final / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-800 dark:text-gray-200 w-20">Contratados</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                                  <div className="bg-gray-500 dark:bg-gray-600 h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: previewJob.funnel.hired > 0 ? `${(previewJob.funnel.hired / previewJob.funnel.total) * 100}%` : '5%'}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.hired}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-gray-800 w-10 text-right">
                                {Math.round((previewJob.funnel.hired / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Métricas de Conversão */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>CV → Triagem</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {Math.round((previewJob.funnel.screening / previewJob.funnel.total) * 100)}%
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Triagem → Entrevista</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.screening > 0 ? Math.round((previewJob.funnel.interview / previewJob.funnel.screening) * 100) : 0}%
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Entrevista → Final</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.interview > 0 ? Math.round((previewJob.funnel.final / previewJob.funnel.interview) * 100) : 0}%
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-md p-2">
                          <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Final → Contratação</p>
                          <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                            {previewJob.funnel.final > 0 ? Math.round((previewJob.funnel.hired / previewJob.funnel.final) * 100) : 0}%
                          </p>
                        </div>
                      </div>

                      {/* Insights e Recomendações da LIA */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200 mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-gray-950 dark:text-gray-200 font-semibold mb-1">
                              Insights da LIA
                            </p>
                            <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
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
                      <div className="bg-white dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Comparativo com Mercado
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Salário</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.salary > 'R$ 10.000' ? '+15%' : '-5%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. mercado</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Candidatos</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. média</p>
                          </div>
                          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                            <p className={`${textStyles.bodySmall} dark:text-gray-200`}>Atratividade</p>
                            <p className="text-sm font-bold text-gray-950 dark:text-gray-50">
                              #—
                            </p>
                            <p className={textStyles.bodySmall}>ranking</p>
                          </div>
                        </div>
                      </div>

                      {/* KPIs da Vaga com Budget */}
                      <div className="bg-gray-50 dark:bg-gray-700/30 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <TrendingUp className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          KPIs e Orçamento
                        </h4>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center justify-between">
                            <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Urgência</span>
                            <div className="flex gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < previewJob.urgencyLevel ? 'bg-status-error' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          {previewJob.budget && (
                            <>
                              <div className="flex items-center justify-between">
                                <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Budget</span>
                                <span className="text-xs font-bold text-gray-950 dark:text-gray-50">
                                  R$ {(previewJob.budget / 1000).toFixed(0)}k
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Usado</span>
                                <span className="text-xs font-bold text-gray-950 dark:text-gray-50">
                                  {previewJob.budgetUsed ? Math.round((previewJob.budgetUsed / previewJob.budget) * 100) : 0}%
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Fatores de Risco */}
                      <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <Shield className="w-3.5 h-3.5 text-status-error" />
                          Fatores de Risco
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-800 dark:text-gray-200">Competitividade salarial</span>
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
                            <span className="text-gray-800 dark:text-gray-200">Escassez de talentos</span>
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
                            <span className="text-gray-800 dark:text-gray-200">Tempo de processo</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-gray-500 dark:bg-gray-600' : 'bg-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Canais de Divulgação */}
                      <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                        <h4 className={`${textStyles.title} dark:text-gray-50 mb-2 flex items-center gap-1`}>
                          <Share2 className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                          Canais de Divulgação
                        </h4>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Linkedin className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>LinkedIn</span>
                            </div>
                            {previewJob.publishedLinkedIn ? (
                              <Badge className="text-xs bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200">Publicado</Badge>
                            ) : (
                              <Badge className="text-xs bg-gray-100 text-gray-800">Não publicado</Badge>
                            )}
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Globe className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                              <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Site</span>
                            </div>
                            {previewJob.publishedWebsite ? (
                              <Badge className="text-xs bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200">Publicado</Badge>
                            ) : (
                              <Badge className="text-xs bg-gray-100 text-gray-800">Não publicado</Badge>
                            )}
                          </div>
                          {previewJob.publishedIndeed !== undefined && (
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-1">
                                <Briefcase className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                                <span className={`${textStyles.bodySmall} dark:text-gray-200`}>Indeed</span>
                              </div>
                              {previewJob.publishedIndeed ? (
                                <Badge className="text-xs bg-gray-100 text-gray-950 dark:bg-gray-700 dark:text-gray-200">Publicado</Badge>
                              ) : (
                                <Badge className="text-xs bg-gray-100 text-gray-800">Não publicado</Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Ações Rápidas - Aparecem em todas as tabs */}
                  <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
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
