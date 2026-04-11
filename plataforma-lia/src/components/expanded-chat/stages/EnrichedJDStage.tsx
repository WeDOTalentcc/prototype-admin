'use client'


import { formatBRL } from "@/lib/pricing"
import React, { useState } from 'react'
import { 
  FileText, 
  Lightbulb, 
  Check, 
  X, 
  ChevronDown, 
  ChevronUp,
  TrendingUp,
  BarChart3,
  Building2,
  DollarSign,
  Brain,
  AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'

export type SuggestionSource = 'market_benchmark' | 'company_history' | 'skills_catalog' | 'company_config' | 'ats_integration'
export type SuggestionImpact = 'high' | 'medium' | 'low'
export type SuggestionCategory = 'responsibilities' | 'technical_skills' | 'behavioral_competencies' | 'compensation'

export interface EnrichedSuggestion {
  id: string
  value: string
  source: SuggestionSource
  justification: string
  metrics?: Record<string, number>
  impactDescription?: string
  impactLevel: SuggestionImpact
  wsiQualityNote?: string
  isNew: boolean
  category: SuggestionCategory
  accepted?: boolean
}

export interface SectionSuggestions {
  sectionName: string
  detectedItems: string[]
  suggestions: EnrichedSuggestion[]
  wsiQualityNote?: string
  completenessScore?: number
}

export interface CompensationSuggestions {
  currentRange?: { min: number; max: number }
  marketRange?: { min: number; max: number }
  marketPosition?: 'below' | 'competitive' | 'above'
  salarySuggestion?: EnrichedSuggestion
  bonusSuggestion?: EnrichedSuggestion
  competitivenessScore?: number
}

export interface EnrichedJDData {
  sections: SectionSuggestions[]
  compensation?: CompensationSuggestions
  wsiQualityScore: number
  overallCompleteness: number
  totalSuggestions: number
}

export interface EnrichedJDStageProps {
  enrichedData?: EnrichedJDData | null
  onAcceptSuggestion?: (suggestionId: string) => void
  onRejectSuggestion?: (suggestionId: string) => void
  onAcceptAll?: () => void
  isLoading?: boolean
  detectedCriteria?: {
    cargo?: string
    senioridade?: string
    departamento?: string
    responsabilidades?: string[]
    competenciasTecnicas?: string[]
    competenciasComportamentais?: string[]
  }
}

const sourceIcons: Record<SuggestionSource, React.ReactNode> = {
  market_benchmark: <TrendingUp className="w-3 h-3" />,
  company_history: <Building2 className="w-3 h-3" />,
  skills_catalog: <BarChart3 className="w-3 h-3" />,
  company_config: <Building2 className="w-3 h-3" />,
  ats_integration: <FileText className="w-3 h-3" />
}

const sourceLabels: Record<SuggestionSource, string> = {
  market_benchmark: 'Mercado',
  company_history: 'Histórico',
  skills_catalog: 'Catálogo',
  company_config: 'Empresa',
  ats_integration: 'ATS'
}

const impactColors: Record<SuggestionImpact, string> = {
  high: 'bg-status-success/15 text-status-success border-status-success/30',
  medium: 'bg-status-warning/15 text-status-warning border-status-warning/30',
  low: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle'
}

export function EnrichedJDStage({
  enrichedData,
  onAcceptSuggestion,
  onRejectSuggestion,
  onAcceptAll,
  isLoading = false,
  detectedCriteria
}: EnrichedJDStageProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['responsibilities', 'technical_skills', 'behavioral_competencies']))
  const [acceptedSuggestions, setAcceptedSuggestions] = useState<Set<string>>(new Set())
  const [rejectedSuggestions, setRejectedSuggestions] = useState<Set<string>>(new Set())

  const toggleSection = (sectionName: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionName)) {
      newExpanded.delete(sectionName)
    } else {
      newExpanded.add(sectionName)
    }
    setExpandedSections(newExpanded)
  }

  const handleAccept = (suggestionId: string) => {
    setAcceptedSuggestions(prev => new Set(prev).add(suggestionId))
    setRejectedSuggestions(prev => {
      const next = new Set(prev)
      next.delete(suggestionId)
      return next
    })
    onAcceptSuggestion?.(suggestionId)
  }

  const handleReject = (suggestionId: string) => {
    setRejectedSuggestions(prev => new Set(prev).add(suggestionId))
    setAcceptedSuggestions(prev => {
      const next = new Set(prev)
      next.delete(suggestionId)
      return next
    })
    onRejectSuggestion?.(suggestionId)
  }

  const handleAcceptAll = () => {
    if (!enrichedData) return
    const allSuggestionIds = new Set<string>()
    enrichedData.sections.forEach(section => {
      section.suggestions.forEach(s => allSuggestionIds.add(s.id))
    })
    setAcceptedSuggestions(allSuggestionIds)
    setRejectedSuggestions(new Set())
    onAcceptAll?.()
  }

  const getSuggestionState = (id: string): 'pending' | 'accepted' | 'rejected' => {
    if (acceptedSuggestions.has(id)) return 'accepted'
    if (rejectedSuggestions.has(id)) return 'rejected'
    return 'pending'
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center animate-pulse motion-reduce:animate-none">
          <Brain className="w-6 h-6 text-wedo-cyan" />
        </div>
        <div className="text-center">
          <p className={cn(textStyles.body, "text-lia-text-secondary")}>
            Analisando e enriquecendo a descrição...
          </p>
          <p className={cn(textStyles.caption, "text-lia-text-disabled mt-1")}>
            Consultando mercado, histórico e catálogos
          </p>
        </div>
      </div>
    )
  }

  if (!enrichedData) {
    return (
      <div className="p-4 bg-lia-bg-secondary/50 rounded-xl border border-lia-border-subtle">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-lia-interactive-active flex items-center justify-center">
            <FileText className="w-4 h-4 text-lia-text-secondary" />
          </div>
          <div>
            <p className={cn(textStyles.body, "text-lia-text-secondary")}>
              Dados detectados aguardando enriquecimento
            </p>
            <p className={cn(textStyles.caption, "text-lia-text-disabled")}>
              Continue conversando com a LIA para gerar sugestões
            </p>
          </div>
        </div>
        
        {detectedCriteria?.cargo && (
          <div className="mt-4 p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
            <h4 className={cn(textStyles.label, "text-lia-text-secondary mb-2")}>
              Dados Detectados
            </h4>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="lia-text-secondary">Cargo:</span>
                <span className="font-medium text-lia-text-primary">{detectedCriteria.cargo}</span>
              </div>
              {detectedCriteria.senioridade && (
                <div className="flex justify-between">
                  <span className="lia-text-secondary">Senioridade:</span>
                  <span className="font-medium text-lia-text-primary">{detectedCriteria.senioridade}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div data-testid="enriched-jd-stage" className="space-y-4">
      <div className="flex items-center justify-between p-3 bg-gradient-to-r from-lia-bg-tertiary dark:from-lia-bg-tertiary to-green-500/10 rounded-xl border border-lia-border-default">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <div>
            <p className={cn(textStyles.label, "text-lia-text-primary")}>
              Qualidade WSI: {enrichedData.wsiQualityScore}%
            </p>
            <p className={cn(textStyles.caption, "text-lia-text-tertiary")}>
              {enrichedData.totalSuggestions} sugestões para melhorar
            </p>
          </div>
        </div>
        {enrichedData.totalSuggestions > 0 && (
          <button
            onClick={handleAcceptAll}
            className="px-3 py-1.5 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default"
           
          >
            Aceitar todas
          </button>
        )}
      </div>

      {enrichedData.wsiQualityScore < 70 && (
        <div className="p-3 bg-status-warning/10 dark:bg-status-warning/20 rounded-xl border border-status-warning/30 dark:border-status-warning/30">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-status-warning mt-0.5" />
            <div>
              <p className={cn(textStyles.bodySmall, "text-status-warning font-medium")}>
                Qualidade abaixo do ideal para triagem WSI
              </p>
              <p className={cn(textStyles.caption, "text-status-warning mt-0.5")}>
                Aceite as sugestões destacadas para melhorar as perguntas de triagem
              </p>
            </div>
          </div>
        </div>
      )}

      {enrichedData.sections.map((section) => {
        const sectionKey = section.sectionName.toLowerCase().replace(/\s+/g, '_')
        const isExpanded = expandedSections.has(sectionKey)
        const pendingSuggestions = section.suggestions.filter(s => getSuggestionState(s.id) === 'pending')
        const acceptedCount = section.suggestions.filter(s => getSuggestionState(s.id) === 'accepted').length
        
        return (
          <div 
            key={section.sectionName}
            className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle overflow-hidden"
          >
            <button
              onClick={() => toggleSection(sectionKey)}
              className="w-full flex items-center justify-between p-3 hover:bg-lia-interactive-hover/50 transition-colors motion-reduce:transition-none"
            >
              <div className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-lia-text-secondary" />
                <span className={cn(textStyles.label, "text-lia-text-primary")}>
                  {section.sectionName}
                </span>
                {section.suggestions.length > 0 && (
                  <span className="px-1.5 py-0.5 text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary rounded-full">
                    +{section.suggestions.length}
                  </span>
                )}
                {acceptedCount > 0 && (
                  <span className="px-1.5 py-0.5 text-micro font-medium bg-status-success/15 text-status-success rounded-full flex items-center gap-1">
                    <Check className="w-2.5 h-2.5" />
                    {acceptedCount}
                  </span>
                )}
              </div>
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-lia-text-secondary" />
              ) : (
                <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
              )}
            </button>

            {isExpanded && (
              <div className="border-t border-lia-border-subtle">
                {section.detectedItems.length > 0 && (
                  <div className="p-3 bg-lia-bg-secondary/50">
                    <p className={cn(textStyles.caption, "text-lia-text-tertiary mb-2")}>
                      Já detectados:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {section.detectedItems.map((item, idx) => (
                        <span 
                          key={idx}
                          className="px-2 py-1 text-xs bg-lia-interactive-active text-lia-text-secondary rounded-md"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {section.suggestions.length > 0 ? (
                  <div className="p-3 space-y-2">
                    {section.suggestions.map((suggestion) => {
                      const state = getSuggestionState(suggestion.id)
                      return (
                        <div 
                          key={suggestion.id}
                          className={cn(
 "p-3 rounded-md border transition-colors",
                            state === 'accepted' && "bg-status-success/10 dark:bg-status-success/20 border-status-success/30 dark:border-status-success/30",
                            state === 'rejected' && "bg-lia-bg-secondary/50 border-lia-border-subtle opacity-50",
                            state === 'pending' && "bg-lia-bg-primary border-lia-border-subtle hover:border-lia-btn-primary-bg"
                          )}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={cn(textStyles.body, "font-medium text-lia-text-primary")}>
                                  {suggestion.value}
                                </span>
                                <span className={cn(
 "px-1.5 py-0.5 text-micro font-medium rounded-full border flex items-center gap-1",
                                  impactColors[suggestion.impactLevel]
                                )}>
                                  {sourceIcons[suggestion.source]}
                                  {sourceLabels[suggestion.source]}
                                </span>
                              </div>
                              
                              <p className={cn(textStyles.caption, "text-lia-text-tertiary")}>
                                {suggestion.justification}
                              </p>
                              
                              {suggestion.wsiQualityNote && (
                                <div className="mt-1.5 flex items-center gap-1 text-lia-text-secondary">
                                  <Brain className="w-3 h-3 text-wedo-cyan" />
                                  <span className="text-micro font-medium">
                                    {suggestion.wsiQualityNote}
                                  </span>
                                </div>
                              )}

                              {suggestion.metrics && Object.keys(suggestion.metrics).length > 0 && (
                                <div className="mt-1.5 flex flex-wrap gap-2">
                                  {suggestion.metrics.market_percentage && (
                                    <span className="text-micro text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full">
                                      {suggestion.metrics.market_percentage}% do mercado
                                    </span>
                                  )}
                                  {suggestion.metrics.company_history_percentage && (
                                    <span className="text-micro text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full">
                                      {suggestion.metrics.company_history_percentage}% das suas vagas
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>

                            {state === 'pending' && (
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => handleAccept(suggestion.id)}
                                  className="w-7 h-7 rounded-md bg-status-success/15 hover:bg-status-success/20 dark:bg-status-success/30 dark:hover:bg-status-success/50 flex items-center justify-center transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default"
                                  title="Aceitar sugestão"
                                  aria-label="Aceitar sugestão"
                                >
                                  <Check className="w-3.5 h-3.5 text-status-success" />
                                </button>
                                <button
                                  onClick={() => handleReject(suggestion.id)}
                                  className="w-7 h-7 rounded-xl bg-lia-bg-tertiary hover:bg-lia-interactive-active dark:hover:bg-lia-btn-primary-bg flex items-center justify-center transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-lia-border-default"
                                  title="Rejeitar sugestão"
                                  aria-label="Rejeitar sugestão"
                                >
                                  <X className="w-3.5 h-3.5 text-lia-text-secondary" />
                                </button>
                              </div>
                            )}

                            {state === 'accepted' && (
                              <div className="w-7 h-7 rounded-md bg-status-success flex items-center justify-center">
                                <Check className="w-4 h-4 text-white" />
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="p-4 text-center">
                    <p className={cn(textStyles.caption, "lia-text-secondary")}>
                      Sem sugestões para esta seção
                    </p>
                  </div>
                )}

                {section.wsiQualityNote && (
                  <div className="p-2 mx-3 mb-3 bg-lia-bg-tertiary rounded-xl border border-lia-border-default">
                    <div className="flex items-center gap-2">
                      <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      <span className={cn(textStyles.caption, "text-lia-text-secondary font-medium")}>
                        {section.wsiQualityNote}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}

      {enrichedData.compensation && (
        <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-3">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="w-4 h-4 text-lia-text-secondary" />
            <span className={cn(textStyles.label, "text-lia-text-primary")}>
              Remuneração
            </span>
          </div>
          
          {enrichedData.compensation.marketRange && enrichedData.compensation.currentRange && (
            <div className="space-y-2">
              <div className="flex justify-between items-center p-2 bg-lia-bg-secondary/50 rounded-xl">
                <span className="text-sm text-lia-text-secondary">Sua proposta:</span>
                <span className="text-sm font-medium text-lia-text-primary">
                  {formatBRL(enrichedData.compensation.currentRange.min)} - {formatBRL(enrichedData.compensation.currentRange.max)}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 bg-lia-bg-tertiary rounded-xl">
                <span className="text-sm text-lia-text-secondary">Benchmark:</span>
                <span className="text-sm font-medium text-lia-text-secondary">
                  {formatBRL(enrichedData.compensation.marketRange.min)} - {formatBRL(enrichedData.compensation.marketRange.max)}
                </span>
              </div>
              
              {enrichedData.compensation.marketPosition && (
                <div className={cn(
 "text-xs font-medium text-center py-1.5 rounded-md",
                  enrichedData.compensation.marketPosition === 'competitive' && "bg-status-success/15 text-status-success",
                  enrichedData.compensation.marketPosition === 'below' && "bg-status-warning/15 text-status-warning",
                  enrichedData.compensation.marketPosition === 'above' && "bg-wedo-cyan/15 text-wedo-cyan-dark"
                )}>
                  {enrichedData.compensation.marketPosition === 'competitive' && 'Competitivo com o mercado'}
                  {enrichedData.compensation.marketPosition === 'below' && 'Abaixo do mercado - considere ajustar'}
                  {enrichedData.compensation.marketPosition === 'above' && 'Acima do mercado - atrativo para talentos'}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EnrichedJDStage
