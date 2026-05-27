"use client"

import React from"react"
import { textStyles } from"@/lib/design-tokens"
import { Chip } from "@/components/ui/chip"
import { Brain, FileText, ChevronDown, Check, Copy, Trash2 } from"lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from"@/components/ui/tooltip"
import { OpinionCard } from"@/components/candidate-preview/OpinionCard"

interface CandidateOpinionsTabProps {
  opinionsSubTab: string
  setOpinionsSubTab: (tab: string) => void
  opinionsHistory: Record<string, any>[]
  isLoadingHistory: boolean
  savedAnalyses: { total_analyses: number; analyses: Record<string, unknown>[] } | null | undefined
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
      <div className="flex items-center gap-1 pb-2">
        <button
          onClick={() => setOpinionsSubTab('pareceres')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
opinionsSubTab === 'pareceres'
              ? 'bg-lia-bg-tertiary text-lia-text-primary rounded-lg bg-lia-bg-tertiary'
: 'text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover'
          }`}
        >
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Pareceres IA
          {opinionsHistory.length > 0 && (
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center ml-1 bg-wedo-cyan/15">
              {opinionsHistory.length}
            </Chip>
          )}
        </button>
        <button
          onClick={() => setOpinionsSubTab('analises')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
opinionsSubTab === 'analises'
              ? ' rounded-lg bg-wedo-purple/10'
: 'text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-interactive-hover'
          }`}
        >
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Análises
          {savedAnalyses && savedAnalyses.total_analyses > 0 && (
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center ml-1">
              {savedAnalyses.total_analyses}
            </Chip>
          )}
        </button>
      </div>

      {/* Subtab: Pareceres IA */}
      {opinionsSubTab === 'pareceres' && (
        <>
          {/* Loading State */}
          {isLoadingHistory && (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-4 animate-pulse motion-reduce:animate-none">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 bg-lia-interactive-active rounded-full"></div>
                    <div className="flex-1">
                      <div className="w-32 h-4 bg-lia-interactive-active rounded-md mb-1"></div>
                      <div className="w-24 h-3 bg-lia-interactive-active rounded-md"></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="w-full h-3 bg-lia-interactive-active rounded-md"></div>
                    <div className="w-3/4 h-3 bg-lia-interactive-active rounded-md"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoadingHistory && opinionsHistory.length === 0 && (
            <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-lia-text-disabled" />
              </div>
              <p className={`${textStyles.subtitle} mb-1`}>Nenhum parecer disponível</p>
              <p className={textStyles.description}>
                Os pareceres serão gerados automaticamente após triagens ou análises da IA.
              </p>
            </div>
          )}

          {/* Opinions List - Full History */}
          {!isLoadingHistory && opinionsHistory.length > 0 && (
            <div className="space-y-3">
              {opinionsHistory.map((opinion: Record<string, any>) => (
                <div key={opinion.id as string} className="relative">
                  {!opinion.is_current && (
                    <Chip variant="neutral" muted className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-tertiary z-10">
                      v{(opinion.version as React.ReactNode)} - Histórico
                    </Chip>
                  )}
                  <OpinionCard
                    opinion={opinion}
                    isExpanded={expandedOpinionId === (opinion.id as string)}
                    onToggle={() => setExpandedOpinionId(
                      expandedOpinionId === opinion.id ? null : opinion.id as string
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
                <div key={i} className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-4 animate-pulse motion-reduce:animate-none">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 bg-lia-interactive-active rounded-full"></div>
                    <div className="flex-1">
                      <div className="w-32 h-4 bg-lia-interactive-active rounded-md mb-1"></div>
                      <div className="w-24 h-3 bg-lia-interactive-active rounded-md"></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="w-full h-3 bg-lia-interactive-active rounded-md"></div>
                    <div className="w-3/4 h-3 bg-lia-interactive-active rounded-md"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoadingAnalyses && (!savedAnalyses || savedAnalyses.total_analyses === 0) && (
            <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-6 text-center">
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
          {!isLoadingAnalyses && savedAnalyses && savedAnalyses.total_analyses > 0 && (
            <div className="space-y-3">
              {savedAnalyses.analyses.map((analysis: Record<string, any>) => {
                const analysisLabels: Record<string, string> = {
                  'bullet_points': 'Pontos-chave',
                  'short_paragraph': 'Resumo',
                  'detailed_bullets': 'Análise Detalhada'
                }
                const isExpanded = expandedAnalysisId === analysis.id

                return (
                  <div
                    key={analysis.id as string}
                    className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl overflow-hidden hover:transition-shadow"
                  >
                    {/* Card Header - Always Visible */}
                    <div
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-lia-interactive-hover/50 transition-colors motion-reduce:transition-none"
                      onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id as string | null)}
                    >
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-wedo-purple/15 flex items-center justify-center flex-shrink-0">
                          <Brain className="w-4 h-4 text-wedo-purple" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`${textStyles.bodySmall} font-medium`}>Análise IA</span>
                            <Chip variant="neutral" muted
                              className="text-micro px-1.5 py-0 h-4 flex items-center"
                             
                            >
                              {(analysisLabels[analysis.analysis_type as string] || analysis.analysis_type as React.ReactNode)}
                            </Chip>
                          </div>
                          <span className={`${textStyles.caption} text-lia-text-secondary`}>
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
                              className="p-1 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
                            >
                              {copiedItemId === `analysis-${analysis.id as string}` ? (
                                <Check className="w-3.5 h-3.5 text-status-success" />
                              ) : (
                                <Copy className="w-3.5 h-3.5 text-lia-text-disabled hover:text-lia-text-secondary" />
                              )}
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                        </Tooltip>
                        <ChevronDown className={`w-4 h-4 text-lia-text-secondary transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </div>

                    {/* Card Content - Expandable */}
                    {isExpanded && (
                      <div className="px-3 pb-3 border-t border-lia-border-subtle">
                        <div className={`${textStyles.description} text-lia-text-primary leading-relaxed whitespace-pre-wrap bg-lia-bg-secondary rounded-md p-3 mt-2`}>
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
                                <Trash2 className="w-4 h-4 text-lia-text-secondary group-hover:text-status-error" />
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
