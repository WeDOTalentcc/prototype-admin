"use client"

import { useState, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  X, CheckCircle, AlertTriangle, Clock, TrendingUp, TrendingDown,
  Activity, BarChart3, Target, Gauge, Zap, Users, Settings,
  Calendar, Timer, Award, RefreshCw, Download, Share2,
  ArrowUp, ArrowDown, Info, Lightbulb, AlertCircle
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles, colors } from '@/lib/design-tokens'

interface SettingsSection {
  id: string
  title: string
  description: string
  icon: any
  status: 'completed' | 'incomplete' | 'pending'
  priority: 'high' | 'medium' | 'low'
  category: 'basic' | 'advanced' | 'integrations'
  estimatedTime: number
  dependencies?: string[]
}

interface ProgressMetrics {
  overall: number
  byCategory: {
    basic: number
    advanced: number
    integrations: number
  }
  sectionsCompleted: number
  totalSections: number
  estimatedTimeRemaining: number
  criticalSectionsCompleted: number
  totalCriticalSections: number
  lastUpdated: string
  trend: 'up' | 'down' | 'stable'
  velocity: number // sections per day
}

interface ProgressDashboardProps {
  sections: SettingsSection[]
  onClose: () => void
  onSectionSelect: (sectionId: string) => void
}

export function ProgressDashboard({ sections, onClose, onSectionSelect }: ProgressDashboardProps) {
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week')
  const [showDetails, setShowDetails] = useState(false)

  // Calcular métricas de progresso
  const progressMetrics = useMemo<ProgressMetrics>(() => {
    const completedSections = sections.filter(s => s.status === 'completed')
    const pendingSections = sections.filter(s => s.status === 'pending')
    const incompleteSections = sections.filter(s => s.status === 'incomplete')

    const basicSections = sections.filter(s => s.category === 'basic')
    const advancedSections = sections.filter(s => s.category === 'advanced')
    const integrationSections = sections.filter(s => s.category === 'integrations')

    const basicCompleted = basicSections.filter(s => s.status === 'completed').length
    const advancedCompleted = advancedSections.filter(s => s.status === 'completed').length
    const integrationsCompleted = integrationSections.filter(s => s.status === 'completed').length

    const criticalSections = sections.filter(s => s.priority === 'high')
    const criticalCompleted = criticalSections.filter(s => s.status === 'completed')

    const overallProgress = (completedSections.length / sections.length) * 100

    const estimatedTimeRemaining = sections
      .filter(s => s.status !== 'completed')
      .reduce((acc, section) => acc + section.estimatedTime, 0)

    return {
      overall: overallProgress,
      byCategory: {
        basic: (basicCompleted / basicSections.length) * 100,
        advanced: advancedSections.length > 0 ? (advancedCompleted / advancedSections.length) * 100 : 0,
        integrations: integrationSections.length > 0 ? (integrationsCompleted / integrationSections.length) * 100 : 0
      },
      sectionsCompleted: completedSections.length,
      totalSections: sections.length,
      estimatedTimeRemaining,
      criticalSectionsCompleted: criticalCompleted.length,
      totalCriticalSections: criticalSections.length,
      lastUpdated: new Date().toISOString(),
      trend: overallProgress > 50 ? 'up' : overallProgress > 25 ? 'stable' : 'down',
      velocity: 2.3 // Mock data - sections per day
    }
  }, [sections])

  // Próximas ações recomendadas
  const nextActions = useMemo(() => {
    const incompleteSections = sections.filter(s => s.status !== 'completed')

    // Priorizar seções de alta prioridade sem dependências ou com dependências já completadas
    const readySections = incompleteSections.filter(section => {
      if (!section.dependencies) return true
      return section.dependencies.every(depId =>
        sections.find(s => s.id === depId)?.status === 'completed'
      )
    })

    // Ordenar por prioridade e tempo estimado
    return readySections
      .sort((a, b) => {
        const priorityWeight = { high: 3, medium: 2, low: 1 }
        const priorityDiff = priorityWeight[b.priority] - priorityWeight[a.priority]
        if (priorityDiff !== 0) return priorityDiff
        return a.estimatedTime - b.estimatedTime
      })
      .slice(0, 3)
  }, [sections])

  // v4: Cores de categoria em grayscale (90% gray + 10% accent apenas para contexto LIA)
  const categoryColors = {
    basic: { bg: 'bg-gray-100 dark:bg-lia-bg-secondary', text: 'lia-text-700 dark:text-lia-text-secondary', border: 'border-lia-border-subtle dark:border-lia-border-subtle' },
    advanced: { bg: 'bg-gray-100 dark:bg-lia-bg-secondary', text: 'lia-text-700 dark:text-lia-text-secondary', border: 'border-lia-border-subtle dark:border-lia-border-subtle' },
    integrations: { bg: 'bg-gray-100 dark:bg-lia-bg-secondary', text: 'lia-text-700 dark:text-lia-text-secondary', border: 'border-lia-border-subtle dark:border-lia-border-subtle' }
  }

  // v4: Cores de prioridade semânticas
  const priorityColors = {
    high: { bg: 'bg-status-error/10 dark:bg-status-error/20', text: 'text-status-error dark:text-status-error', icon: AlertTriangle },
    medium: { bg: 'bg-status-warning/10 dark:bg-status-warning/20', text: 'text-status-warning dark:text-status-warning', icon: Clock },
    low: { bg: 'bg-gray-100 dark:bg-lia-bg-secondary', text: 'lia-text-700 dark:text-lia-text-secondary', icon: Info }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-lia-bg-primary rounded-md w-full max-w-6xl h-[90vh] overflow-y-auto border border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className={`${textStyles.h3} mb-1`}>
                Dashboard de Progresso
              </h2>
              <p className={textStyles.description}>
                Acompanhe o progresso da configuração da plataforma em tempo real
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Exportar
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="w-4 h-4 mr-2" />
                Compartilhar
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Métricas Principais - v4: Cards com grayscale, métricas com Inter */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-gray-100 dark:bg-lia-bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
                  <Gauge className="w-8 h-8 lia-text-700 dark:text-lia-text-secondary" />
                </div>
                <div className={`${textStyles.metricLarge} mb-1`}>
                  {Math.round(progressMetrics.overall)}%
                </div>
                <div className={`${textStyles.labelSmall} mb-2`}>
                  Progresso Geral
                </div>
                <div className="flex items-center justify-center gap-1">
                  {progressMetrics.trend === 'up' ? (
                    <TrendingUp className="w-4 h-4 text-status-success dark:text-status-success" />
                  ) : progressMetrics.trend === 'down' ? (
                    <TrendingDown className="w-4 h-4 text-status-error dark:text-status-error" />
                  ) : (
                    <Activity className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  )}
                  <span className={textStyles.metricSmall}>
                    {progressMetrics.velocity} seções/dia
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-status-success/10 dark:bg-status-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-status-success dark:text-status-success" />
                </div>
                <div className={`${textStyles.metricLarge} mb-1`}>
                  {progressMetrics.sectionsCompleted}
                </div>
                <div className={`${textStyles.labelSmall} mb-2`}>
                  Seções Concluídas
                </div>
                <div className={textStyles.metricSmall}>
                  de {progressMetrics.totalSections} total
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-status-warning/10 dark:bg-status-warning/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Timer className="w-8 h-8 text-status-warning dark:text-status-warning" />
                </div>
                <div className={`${textStyles.metricLarge} mb-1`}>
                  {Math.round(progressMetrics.estimatedTimeRemaining / 60 * 10) / 10}h
                </div>
                <div className={`${textStyles.labelSmall} mb-2`}>
                  Tempo Restante
                </div>
                <div className={textStyles.metricSmall}>
                  estimativa baseada nas seções pendentes
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
              <CardContent className="p-6 text-center">
                <div className="w-16 h-16 bg-status-error/10 dark:bg-status-error/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertTriangle className="w-8 h-8 text-status-error dark:text-status-error" />
                </div>
                <div className={`${textStyles.metricLarge} mb-1`}>
                  {progressMetrics.criticalSectionsCompleted}
                </div>
                <div className={`${textStyles.labelSmall} mb-2`}>
                  Críticas Concluídas
                </div>
                <div className={textStyles.metricSmall}>
                  de {progressMetrics.totalCriticalSections} prioritárias
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Progresso por Categoria - v4: Barras em gray-900 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {Object.entries(progressMetrics.byCategory).map(([category, progress]) => {
              const catColors = categoryColors[category as keyof typeof categoryColors]
              const sectionsInCategory = sections.filter(s => s.category === category)
              const completedInCategory = sectionsInCategory.filter(s => s.status === 'completed').length

              return (
                <Card key={category} className="rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className={textStyles.subtitle}>
                        {category === 'basic' ? 'Básico' : category === 'advanced' ? 'Avançado' : 'Integrações'}
                      </h3>
                      <Badge className={`${catColors.bg} ${catColors.text} ${catColors.border} border`}>
                        {Math.round(progress)}%
                      </Badge>
                    </div>

                    <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3 mb-3">
                      <div
                        className="h-3 rounded-full transition-[width,height] duration-500 bg-gray-900 dark:lia-bg-100"
                        style={{width: `${progress}%`}}
                      />
                    </div>

                    <div className={`flex items-center justify-between ${textStyles.description}`}>
                      <span>{completedInCategory} / {sectionsInCategory.length} seções</span>
                      <span>
                        {sectionsInCategory
                          .filter(s => s.status !== 'completed')
                          .reduce((acc, s) => acc + s.estimatedTime, 0)} min restante
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>

          {/* Próximas Ações Recomendadas - v4 */}
          <Card className="mb-8 rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
            <CardHeader>
              <CardTitle className={`flex items-center gap-2 ${textStyles.subtitle}`}>
                <Lightbulb className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                Próximas Ações Recomendadas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {nextActions.map((section, index) => {
                  const SectionIcon = section.icon
                  const priorityColor = priorityColors[section.priority]
                  const PriorityIcon = priorityColor.icon

                  return (
                    <div
                      key={section.id}
                      className="flex items-center gap-4 p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                      onClick={() => onSectionSelect(section.id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-md flex items-center justify-center">
                          <span className={textStyles.metricSmall}>
                            {index + 1}
                          </span>
                        </div>
                        <div className="w-10 h-10 bg-gray-100 dark:bg-lia-bg-secondary rounded-md flex items-center justify-center">
                          <SectionIcon className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                        </div>
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className={textStyles.subtitle}>
                            {section.title}
                          </h4>
                          <Badge className={`${priorityColor.bg} ${priorityColor.text} text-xs`}>
                            <PriorityIcon className="w-3 h-3 mr-1" />
                            {section.priority === 'high' ? 'Alta' : section.priority === 'medium' ? 'Média' : 'Baixa'}
                          </Badge>
                        </div>
                        <p className={textStyles.description}>
                          {section.description}
                        </p>
                      </div>

                      <div className="text-right">
                        <div className={textStyles.metricSmall}>
                          {section.estimatedTime} min
                        </div>
                        <div className={textStyles.labelSmall}>estimado</div>
                      </div>

                      <Button variant="outline" size="sm" className="rounded-md">
                        Configurar
                      </Button>
                    </div>
                  )
                })}

                {nextActions.length === 0 && (
                  <div className="text-center py-8">
                    <Award className="w-12 h-12 mx-auto mb-4 text-status-success dark:text-status-success" />
                    <h3 className={`${textStyles.subtitle} mb-2`}>
                      Parabéns! Setup Completo
                    </h3>
                    <p className={textStyles.description}>
                      Todas as seções críticas foram configuradas com sucesso.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Lista Detalhada de Seções - v4 */}
          <Card className="rounded-md border-lia-border-subtle dark:border-lia-border-subtle">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className={`flex items-center gap-2 ${textStyles.subtitle}`}>
                  <BarChart3 className="w-5 h-5" />
                  Status Detalhado das Seções
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDetails(!showDetails)}
                >
                  {showDetails ? 'Ocultar' : 'Mostrar'} Detalhes
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {sections.map((section) => {
                  const SectionIcon = section.icon
                  // v4: Status colors semânticas com dark mode
                  const statusColors = {
                    completed: { bg: 'bg-status-success/10 dark:bg-status-success/20', text: 'text-status-success dark:text-status-success', icon: CheckCircle },
                    pending: { bg: 'bg-status-warning/10 dark:bg-status-warning/20', text: 'text-status-warning dark:text-status-warning', icon: Clock },
                    incomplete: { bg: 'bg-status-error/10 dark:bg-status-error/20', text: 'text-status-error dark:text-status-error', icon: AlertCircle }
                  }
                  const statusColor = statusColors[section.status]
                  const StatusIcon = statusColor.icon
                  const categoryColor = categoryColors[section.category]
                  const priorityColor = priorityColors[section.priority]

                  return (
                    <div
                      key={section.id}
                      className="flex items-center gap-4 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                      onClick={() => onSectionSelect(section.id)}
                    >
                      <div className="w-10 h-10 bg-gray-100 dark:bg-lia-bg-secondary rounded-md flex items-center justify-center">
                        <SectionIcon className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className={textStyles.subtitle}>
                            {section.title}
                          </h4>
                          <Badge className={`${statusColor.bg} ${statusColor.text} text-xs`}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {section.status === 'completed' ? 'Concluído' :
                             section.status === 'pending' ? 'Pendente' : 'Incompleto'}
                          </Badge>
                          <Badge className={`${categoryColor.bg} ${categoryColor.text} ${categoryColor.border} border text-xs`}>
                            {section.category === 'basic' ? 'Básico' :
                             section.category === 'advanced' ? 'Avançado' : 'Integração'}
                          </Badge>
                          <Badge className={`${priorityColor.bg} ${priorityColor.text} text-xs`}>
                            {section.priority === 'high' ? 'Alta' :
                             section.priority === 'medium' ? 'Média' : 'Baixa'}
                          </Badge>
                        </div>

                        {showDetails && (
                          <div>
                            <p className={`${textStyles.description} mb-2`}>
                              {section.description}
                            </p>
                            {section.dependencies && section.dependencies.length > 0 && (
                              <div className={`flex items-center gap-2 ${textStyles.labelSmall}`}>
                                <span>Depende de:</span>
                                {section.dependencies.map((depId, idx) => {
                                  const depSection = sections.find(s => s.id === depId)
                                  return (
                                    <Badge key={depId} variant="outline" className="text-xs">
                                      {depSection?.title}
                                    </Badge>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="text-right">
                        <div className={textStyles.metricSmall}>
                          {section.estimatedTime} min
                        </div>
                        <div className={textStyles.labelSmall}>estimado</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Footer - v4 */}
          <div className="mt-6 pt-6 border-t border-lia-border-subtle dark:border-lia-border-subtle flex items-center justify-between">
            <div className={textStyles.description}>
              Última atualização: {new Date(progressMetrics.lastUpdated).toLocaleString('pt-BR')}
            </div>
            <Button variant="outline" size="sm" className="rounded-md">
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar Dados
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
