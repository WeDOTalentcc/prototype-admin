"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { Badge } from "@/components/ui/badge"
import { Brain, FileText, ChevronDown, Check, Copy, Trash2 } from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { OpinionCard } from "@/components/candidate-preview/OpinionCard"

interface CandidateOpinionsTabProps {
  opinionsSubTab: string
  setOpinionsSubTab: (tab: string) => void
  opinionsHistory: Record<string, any>[]
  isLoadingHistory: boolean
  savedAnalyses: unknown
  isLoadingAnalyses: boolean
  expandedOpinionId: unknown
  setExpandedOpinionId: (id: unknown) => void
  expandedAnalysisId: string | null
  setExpandedAnalysisId: (id: string | null) => void
  analysisToDelete: unknown
  setAnalysisToDelete: (analysis: unknown) => void
  copiedItemId: string | null
  handleCopyOpinion: (opinion: Record<string, any>) => void
  handleCopyAnalysis: (analysis: Record<string, any>) => void
  cleanTextForCopy: (text: string) => string
}

export function CandidateOpinionsTab({
  opinionsSubTab,
  setOpinionsSubTab,
  opinionsHistory,
  isLoadingHistory,
  savedAnalyses,
  isLoadingAnalyses,
  expandedOpinionId,
  setExpandedOpinionId,
  expandedAnalysisId,
  setExpandedAnalysisId,
  analysisToDelete,
  setAnalysisToDelete,
  copiedItemId,
  handleCopyOpinion,
  handleCopyAnalysis,
  cleanTextForCopy,
}: CandidateOpinionsTabProps) {
  return (
    <div className="p-3 space-y-3">
      {/* Subtabs Header */}
      <div className="flex items-center gap-1 border-b border-lia-border-subtle dark:border-lia-border-subtle pb-2">
        <button
          onClick={() => setOpinionsSubTab('pareceres')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
opinionsSubTab === 'pareceres'
              ? 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle'
: 'text-lia-text-tertiary hover:text-lia-text-secondary dark:text-lia-text-secondary hover:bg-gray-50'
          }`}
        >
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Pareceres da LIA
          {opinionsHistory.length > 0 && (
            <Badge className="text-micro px-1.5 py-0 h-4 ml-1 bg-wedo-cyan/15">
              {opinionsHistory.length}
            </Badge>
          )}
        </button>
        <button
          onClick={() => setOpinionsSubTab('analises')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
opinionsSubTab === 'analises'
              ? 'bg-wedo-purple/10 text-wedo-purple border-b-2 border-wedo-purple/30'
: 'text-lia-text-tertiary hover:text-lia-text-secondary dark:text-lia-text-secondary hover:bg-gray-50'
          }`}
        >
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Análises
          {/* @ts-ignore TODO: fix type */}
          {(savedAnalyses as any) && (savedAnalyses as any).total_analyses > 0 && (
            <Badge className="text-micro px-1.5 py-0 h-4 ml-1" style={{backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)'}}>
              {(savedAnalyses as unknown as {total_analyses: number}).total_analyses}
            </Badge>
          )}
        </button>
      </div>

      {/* Subtab: Pareceres da LIA */}
      {opinionsSubTab === 'pareceres' && (
        <>
          {/* Loading State */}
          {isLoadingHistory && (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4 animate-pulse motion-reduce:animate-none">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-full"></div>
                    <div className="flex-1">
                      <div className="w-32 h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mb-1"></div>
                      <div className="w-24 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="w-full h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                    <div className="w-3/4 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoadingHistory && opinionsHistory.length === 0 && (
            <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-lia-text-disabled" />
              </div>
              <p className={`${textStyles.subtitle} mb-1`}>Nenhum parecer disponível</p>
              <p className={textStyles.description}>
                Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
              </p>
            </div>
          )}

          {/* Opinions List - Full History */}
          {!isLoadingHistory && opinionsHistory.length > 0 && (
            <div className="space-y-3">
              {opinionsHistory.map((opinion: Record<string, any>) => (
                <div key={opinion.id as string} className="relative">
                  {!opinion.is_current && (
                    // @ts-ignore TODO: fix type
                    <Badge className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 bg-gray-100 text-lia-text-tertiary dark:text-lia-text-tertiary z-10">
                      v{(opinion.version as React.ReactNode)} - Histórico
                    </Badge>
                  )}
                  <OpinionCard
                    opinion={opinion}
                    // @ts-ignore TODO: fix type
                    isExpanded={expandedOpinionId === opinion.id}
                    onToggle={() => setExpandedOpinionId(
                      expandedOpinionId === opinion.id ? null : opinion.id
                    )}
                    type={opinion.opinion_type === 'wsi' ? 'wsi' : 'general'}
                    copiedItemId={copiedItemId}
                    onCopyOpinion={handleCopyOpinion}
                  />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Subtab: Análises */}
      {opinionsSubTab === 'analises' && (
        <>
          {/* Loading State */}
          {isLoadingAnalyses && (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4 animate-pulse motion-reduce:animate-none">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-full"></div>
                    <div className="flex-1">
                      <div className="w-32 h-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mb-1"></div>
                      <div className="w-24 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="w-full h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                    <div className="w-3/4 h-3 bg-gray-200 dark:bg-lia-bg-elevated rounded-md"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoadingAnalyses && (!savedAnalyses || (savedAnalyses as unknown as {total_analyses: number}).total_analyses === 0) && (
            <div className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-3">
                <Brain className="w-6 h-6 text-wedo-purple" />
              </div>
              <p className={`${textStyles.subtitle} mb-1`}>Nenhuma análise disponível</p>
              <p className={textStyles.description}>
                Use o ícone 🧠 no header para gerar análises de perfil e salvá-las aqui.
              </p>
            </div>
          )}

          {/* Analyses List with Expandable Cards */}
          {!isLoadingAnalyses && savedAnalyses && (savedAnalyses as unknown as {total_analyses: number}).total_analyses > 0 && (
            <div className="space-y-3">
              {(savedAnalyses as unknown as {analyses: Record<string, any>[]}).analyses.map((analysis: Record<string, any>) => {
                const analysisLabels: Record<string, string> = {
                  'bullet_points': 'Pontos-chave',
                  'short_paragraph': 'Resumo',
                  'detailed_bullets': 'Análise Detalhada'
                }
                const isExpanded = expandedAnalysisId === analysis.id

                return (
                  <div
                    key={analysis.id as string}
                    className="bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md overflow-hidden hover:transition-shadow"
                  >
                    {/* Card Header - Always Visible */}
                    <div
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50/50 transition-colors motion-reduce:transition-none"
                      onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id as string | null)}
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-wedo-purple/15 flex items-center justify-center flex-shrink-0">
                          <Brain className="w-4 h-4 text-wedo-purple" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>Análise LIA</span>
                            <Badge
                              className="text-micro px-1.5 py-0 h-4"
                              style={{backgroundColor: 'var(--gray-100)', color: 'var(--wedo-purple)'}}
                            >
                              {(analysisLabels[analysis.analysis_type as string] || analysis.analysis_type as React.ReactNode)}
                            </Badge>
                          </div>
                          <span className={`${textStyles.caption} lia-text-secondary`}>
                            {analysis.created_at ? new Date(analysis.created_at as string).toLocaleDateString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            }) : 'Data não disponível'}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleCopyAnalysis(analysis)
                              }}
                              className="p-1 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                            >
                              {copiedItemId === `analysis-${analysis.id as string}` ? (
                                <Check className="w-3.5 h-3.5 text-status-success" />
                              ) : (
                                <Copy className="w-3.5 h-3.5 text-lia-text-disabled hover:text-lia-text-secondary dark:text-lia-text-tertiary" />
                              )}
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                        </Tooltip>
                        <ChevronDown className={`w-4 h-4 lia-text-secondary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </div>

                    {/* Card Content - Expandable */}
                    {isExpanded && (
                      <div className="px-3 pb-3 border-t border-gray-50">
                        <div className={`${textStyles.description} text-lia-text-primary dark:text-lia-text-primary leading-relaxed whitespace-pre-wrap bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-3 mt-2`}>
                          {cleanTextForCopy(analysis.content as string)}
                        </div>
                        {/* Delete button */}
                        <div className="flex justify-end mt-2">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setAnalysisToDelete(analysis)
                                }}
                                className="p-1.5 hover:bg-status-error/10 rounded-md transition-colors motion-reduce:transition-none group"
                              >
                                <Trash2 className="w-4 h-4 lia-text-secondary group-hover:text-status-error" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-micro">Remover análise</TooltipContent>
                          </Tooltip>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
