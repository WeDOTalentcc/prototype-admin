'use client'

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
  low: 'bg-gray-100 text-gray-600 border-gray-200'
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
        <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center animate-pulse">
          <Brain className="w-6 h-6 text-wedo-cyan" />
        </div>
        <div className="text-center">
          <p className={cn(textStyles.body, "text-gray-600 dark:text-gray-300")}>
            Analisando e enriquecendo a descrição...
          </p>
          <p className={cn(textStyles.caption, "text-gray-400 dark:text-gray-500 mt-1")}>
            Consultando mercado, histórico e catálogos
          </p>
        </div>
      </div>
    )
  }

  if (!enrichedData) {
    return (
      <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
            <FileText className="w-4 h-4 text-gray-500" />
          </div>
          <div>
            <p className={cn(textStyles.body, "text-gray-600 dark:text-gray-300")}>
              Dados detectados aguardando enriquecimento
            </p>
            <p className={cn(textStyles.caption, "text-gray-400 dark:text-gray-500")}>
              Continue conversando com a LIA para gerar sugestões
            </p>
          </div>
        </div>
        
        {detectedCriteria?.cargo && (
          <div className="mt-4 p-3 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-600">
            <h4 className={cn(textStyles.label, "text-gray-700 dark:text-gray-200 mb-2")}>
              Dados Detectados
            </h4>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Cargo:</span>
                <span className="font-medium text-gray-800 dark:text-gray-200">{detectedCriteria.cargo}</span>
              </div>
              {detectedCriteria.senioridade && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Senioridade:</span>
                  <span className="font-medium text-gray-800 dark:text-gray-200">{detectedCriteria.senioridade}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between p-3 bg-gradient-to-r from-gray-100 dark:from-gray-800 to-green-500/10 rounded-md border border-gray-300 dark:border-gray-600">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <div>
            <p className={cn(textStyles.label, "text-gray-800 dark:text-gray-200")}>
              Qualidade WSI: {enrichedData.wsiQualityScore}%
            </p>
            <p className={cn(textStyles.caption, "text-gray-500 dark:text-gray-400")}>
              {enrichedData.totalSuggestions} sugestões para melhorar
            </p>
          </div>
        </div>
        {enrichedData.totalSuggestions > 0 && (
          <button
            onClick={handleAcceptAll}
            className="px-3 py-1.5 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
           
          >
            Aceitar todas
          </button>
        )}
      </div>

      {enrichedData.wsiQualityScore < 70 && (
        <div className="p-3 bg-status-warning/10 dark:bg-status-warning/20 rounded-md border border-status-warning/30 dark:border-status-warning/30">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-status-warning mt-0.5" />
            <div>
              <p className={cn(textStyles.bodySmall, "text-status-warning dark:text-status-warning font-medium")}>
                Qualidade abaixo do ideal para triagem WSI
              </p>
              <p className={cn(textStyles.caption, "text-status-warning dark:text-status-warning mt-0.5")}>
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
            className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 overflow-hidden"
          >
            <button
              onClick={() => toggleSection(sectionKey)}
              className="w-full flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className={cn(textStyles.label, "text-gray-800 dark:text-gray-200")}>
                  {section.sectionName}
                </span>
                {section.suggestions.length > 0 && (
                  <span className="px-1.5 py-0.5 text-micro font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full">
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
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </button>

            {isExpanded && (
              <div className="border-t border-gray-200 dark:border-gray-700">
                {section.detectedItems.length > 0 && (
                  <div className="p-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                    <p className={cn(textStyles.caption, "text-gray-500 dark:text-gray-400 mb-2")}>
                      Já detectados:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {section.detectedItems.map((item, idx) => (
                        <span 
                          key={idx}
                          className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md"
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
                            "p-3 rounded-md border transition-all",
                            state === 'accepted' && "bg-status-success/10 dark:bg-status-success/20 border-status-success/30 dark:border-status-success/30",
                            state === 'rejected' && "bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-600 opacity-50",
                            state === 'pending' && "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 hover:border-gray-900 dark:hover:border-gray-50"
                          )}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={cn(textStyles.body, "font-medium text-gray-800 dark:text-gray-200")}>
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
                              
                              <p className={cn(textStyles.caption, "text-gray-500 dark:text-gray-400")}>
                                {suggestion.justification}
                              </p>
                              
                              {suggestion.wsiQualityNote && (
                                <div className="mt-1.5 flex items-center gap-1 text-gray-600 dark:text-gray-400">
                                  <Brain className="w-3 h-3 text-wedo-cyan" />
                                  <span className="text-micro font-medium">
                                    {suggestion.wsiQualityNote}
                                  </span>
                                </div>
                              )}

                              {suggestion.metrics && Object.keys(suggestion.metrics).length > 0 && (
                                <div className="mt-1.5 flex flex-wrap gap-2">
                                  {suggestion.metrics.market_percentage && (
                                    <span className="text-micro text-gray-500 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded-full">
                                      {suggestion.metrics.market_percentage}% do mercado
                                    </span>
                                  )}
                                  {suggestion.metrics.company_history_percentage && (
                                    <span className="text-micro text-gray-500 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded-full">
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
                                  className="w-7 h-7 rounded-md bg-status-success/15 hover:bg-status-success/20 dark:bg-status-success/30 dark:hover:bg-status-success/50 flex items-center justify-center transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
                                  title="Aceitar sugestão"
                                  aria-label="Aceitar sugestão"
                                >
                                  <Check className="w-3.5 h-3.5 text-status-success" />
                                </button>
                                <button
                                  onClick={() => handleReject(suggestion.id)}
                                  className="w-7 h-7 rounded-md bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 flex items-center justify-center transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
                                  title="Rejeitar sugestão"
                                  aria-label="Rejeitar sugestão"
                                >
                                  <X className="w-3.5 h-3.5 text-gray-500" />
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
                    <p className={cn(textStyles.caption, "text-gray-400")}>
                      Sem sugestões para esta seção
                    </p>
                  </div>
                )}

                {section.wsiQualityNote && (
                  <div className="p-2 mx-3 mb-3 bg-gray-100 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-600">
                    <div className="flex items-center gap-2">
                      <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                      <span className={cn(textStyles.caption, "text-gray-600 dark:text-gray-400 font-medium")}>
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
        <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 p-3">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <span className={cn(textStyles.label, "text-gray-800 dark:text-gray-200")}>
              Remuneração
            </span>
          </div>
          
          {enrichedData.compensation.marketRange && enrichedData.compensation.currentRange && (
            <div className="space-y-2">
              <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-md">
                <span className="text-sm text-gray-500">Sua proposta:</span>
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  R$ {enrichedData.compensation.currentRange.min.toLocaleString()} - R$ {enrichedData.compensation.currentRange.max.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center p-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                <span className="text-sm text-gray-500">Benchmark:</span>
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  R$ {enrichedData.compensation.marketRange.min.toLocaleString()} - R$ {enrichedData.compensation.marketRange.max.toLocaleString()}
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
