// @ts-nocheck
"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
  Brain, Target, FileText, Clock, X, Copy, Check, ChevronUp, ChevronDown,
  CheckCircle, AlertCircle, TrendingUp, BarChart3, Briefcase, Trash2,
} from "lucide-react"

interface CandidatePageOpinionsTabProps {
  opinionsSubTab: "pareceres" | "analises"
  setOpinionsSubTab: (v: "pareceres" | "analises") => void
  opinionsHistory: Record<string, unknown>[]
  isLoadingHistory: boolean
  expandedOpinionId: string | null
  setExpandedOpinionId: (id: string | null) => void
  savedAnalyses: unknown
  isLoadingAnalyses: boolean
  expandedAnalysisId: string | null
  setExpandedAnalysisId: (id: string | null) => void
  copiedItemId: string | null
  analysisToDelete: Record<string, unknown> | null
  setAnalysisToDelete: (v: Record<string, unknown> | null) => void
  textStyles: Record<string, string>
  badgeStyles: Record<string, string>
  cleanTextForCopy: (text: string) => string
  handleCopyOpinion: (opinion: Record<string, unknown>, type: string) => void
  handleCopyAnalysis: (analysis: Record<string, unknown>) => void
  handleDeleteAnalysis: () => void
}

export function CandidatePageOpinionsTab({
  opinionsSubTab,
  setOpinionsSubTab,
  opinionsHistory,
  isLoadingHistory,
  expandedOpinionId,
  setExpandedOpinionId,
  savedAnalyses,
  isLoadingAnalyses,
  expandedAnalysisId,
  setExpandedAnalysisId,
  copiedItemId,
  analysisToDelete,
  setAnalysisToDelete,
  textStyles,
  badgeStyles,
  cleanTextForCopy,
  handleCopyOpinion,
  handleCopyAnalysis,
  handleDeleteAnalysis,
}: CandidatePageOpinionsTabProps) {
  const getOpinionScoreColor = (score: number, isWsi: boolean) => {
    if (isWsi) {
      if (score >= 4) return "text-status-success"
      if (score >= 3) return "text-status-warning"
      return "text-status-error"
    } else {
      if (score >= 80) return "text-status-success"
      if (score >= 60) return "text-status-warning"
      return "text-status-error"
    }
  }

  const getRecommendationBadge = (rec: string | null) => {
    if (!rec) return null
    if (rec === "approved") {
      return (
        <Badge className={`${badgeStyles.success} flex items-center gap-0.5`}>
          <CheckCircle className="w-2.5 h-2.5" />
          APROVADO
        </Badge>
      )
    }
    if (rec === "pending_review") {
      return (
        <Badge className={`${badgeStyles.warning} flex items-center gap-0.5`}>
          <Clock className="w-2.5 h-2.5" />
          PENDENTE
        </Badge>
      )
    }
    if (rec === "not_approved") {
      return (
        <Badge className={`${badgeStyles.error} flex items-center gap-0.5`}>
          <X className="w-2.5 h-2.5" />
          NÃO APROVADO
        </Badge>
      )
    }
    return null
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">
        {/* Subtabs Header */}
        <div className="flex items-center gap-1 border-b border-lia-border-subtle dark:border-lia-border-subtle pb-2">
          <button
            onClick={() => setOpinionsSubTab("pareceres")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
              opinionsSubTab === "pareceres"
                ? "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                : "text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled hover:bg-gray-50 dark:hover:bg-gray-800"
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
            onClick={() => setOpinionsSubTab("analises")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors motion-reduce:transition-none ${
              opinionsSubTab === "analises"
                ? "bg-wedo-purple/10 dark:bg-wedo-purple/20 text-wedo-purple dark:text-wedo-purple border-b-2 border-wedo-purple/30"
                : "text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-disabled hover:bg-gray-50 dark:hover:bg-gray-800"
            }`}
          >
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Análises
            {savedAnalyses && (savedAnalyses as unknown as { total_analyses: number }).total_analyses > 0 && (
              <Badge className="text-micro px-1.5 py-0 h-4 ml-1 bg-wedo-purple/15 text-wedo-purple">
                {(savedAnalyses as unknown as { total_analyses: number }).total_analyses}
              </Badge>
            )}
          </button>
        </div>

        {/* Subtab: Pareceres da LIA */}
        {opinionsSubTab === "pareceres" && (
          <div className="space-y-3">
            {isLoadingHistory && (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <Card key={i} className="animate-pulse motion-reduce:animate-none">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                        <div className="flex-1">
                          <div className="w-32 h-4 bg-gray-200 rounded-md mb-1"></div>
                          <div className="w-24 h-3 bg-gray-200 rounded-md"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="w-full h-3 bg-gray-200 rounded-md"></div>
                        <div className="w-3/4 h-3 bg-gray-200 rounded-md"></div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {!isLoadingHistory && opinionsHistory.length === 0 && (
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-lia-bg-elevated flex items-center justify-center mx-auto mb-3">
                    <FileText className="w-6 h-6 lia-text-secondary" />
                  </div>
                  <p className={`${textStyles.subtitle} mb-1`}>Nenhum parecer disponível</p>
                  <p className={textStyles.description}>
                    Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
                  </p>
                </CardContent>
              </Card>
            )}

            {!isLoadingHistory && opinionsHistory.length > 0 && (
              <div className="space-y-3">
                {opinionsHistory.map((opinion: Record<string, unknown>) => {
                  const isExpanded = expandedOpinionId === opinion.id
                  const isWsiOpinion = opinion.opinion_type === "wsi"
                  const displayScore = isWsiOpinion
                    ? (opinion.wsi_score as number | null | undefined)
                    : (opinion.score as number | null | undefined)

                  return (
                    <Card key={opinion.id as string} className="overflow-hidden">
                      <div
                        onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id as string | null)}
                        className="p-3 flex items-center justify-between hover:bg-gray-50 transition-colors motion-reduce:transition-none cursor-pointer"
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            isWsiOpinion ? "bg-wedo-purple/15" : "bg-gray-100 dark:bg-lia-bg-secondary"
                          }`}>
                            {isWsiOpinion ? (
                              <Target className="w-4 h-4 text-wedo-purple" />
                            ) : (
                              <Brain className="w-4 h-4 text-wedo-cyan" />
                            )}
                          </div>
                          <div className="text-left">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={textStyles.label}>
                                {isWsiOpinion ? "Parecer WSI" : (opinion.job_vacancy_id ? "Parecer de Vaga" : "Parecer Geral")}
                              </span>
                              {opinion.job_vacancy_id && opinion.job_vacancy_title ? (
                                <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default flex items-center gap-1">
                                  <Briefcase className="w-2.5 h-2.5" />
                                  #{String(opinion.job_vacancy_id).slice(0, 6)} - {opinion.job_vacancy_title as string}
                                </Badge>
                              ) : !opinion.job_vacancy_id ? (
                                <Badge className="text-micro px-1.5 py-0 h-4 bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-subtle dark:border-lia-border-subtle">
                                  Sem vaga vinculada
                                </Badge>
                              ) : null}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                              {displayScore !== null && displayScore !== undefined && (
                                <span className={`text-micro font-semibold ${getOpinionScoreColor(displayScore, isWsiOpinion)}`}>
                                  {isWsiOpinion ? `WSI: ${(displayScore as number).toFixed(1)}/5` : `Score: ${Math.round(displayScore as number)}/100`}
                                </span>
                              )}
                              {opinion.archetype && (
                                <>
                                  <span className="lia-text-muted">•</span>
                                  <span className={textStyles.caption}>{opinion.archetype as string}</span>
                                </>
                              )}
                              {getRecommendationBadge(opinion.recommendation as string | null)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {!!(opinion.created_at) && (
                            <span className="text-micro lia-text-secondary">
                              {new Date(opinion.created_at as string).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })}
                            </span>
                          )}
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleCopyOpinion(opinion, (opinion.opinion_type as string | undefined) || "general")
                                }}
                                className="p-1 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
                              >
                                {copiedItemId === `opinion-${opinion.id as string}` ? (
                                  <Check className="w-3.5 h-3.5 text-status-success" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5 lia-text-secondary hover:lia-text-base" />
                                )}
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-micro">Copiar parecer</TooltipContent>
                          </Tooltip>
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 lia-text-secondary" />
                          ) : (
                            <ChevronDown className="w-4 h-4 lia-text-secondary" />
                          )}
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="px-3 pb-3 pt-0 border-t border-lia-border-subtle space-y-3">
                          {!!(opinion.summary) && (
                            <div className="pt-3">
                              <p className="text-xs text-lia-text-primary dark:text-lia-text-primary leading-relaxed">
                                {opinion.summary as string}
                              </p>
                            </div>
                          )}
                          {!!(opinion.score_breakdown) && Object.keys(opinion.score_breakdown as Record<string, unknown>).length > 0 && (
                            <div>
                              <h5 className={`${textStyles.label} mb-1.5 flex items-center gap-1`}>
                                <BarChart3 className="w-3 h-3" />
                                Score Breakdown
                              </h5>
                              <div className="grid grid-cols-2 gap-1.5">
                                {Object.entries(opinion.score_breakdown as Record<string, unknown>).map(([key, value]: [string, unknown]) => (
                                  value !== null && value !== undefined && (
                                    <div key={key} className="flex items-center justify-between text-micro bg-gray-50 dark:bg-lia-bg-elevated rounded-full px-2 py-1">
                                      <span className="lia-text-base capitalize">{key.replace(/_/g, ' ')}</span>
                                      <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">{typeof value === "number" ? `${Math.round(value)}%` : value}</span>
                                    </div>
                                  )
                                ))}
                              </div>
                            </div>
                          )}
                          {opinion.strengths && (opinion.strengths as string[]).length > 0 && (
                            <div>
                              <h5 className={`${textStyles.label} text-status-success mb-1 flex items-center gap-1`}>
                                <CheckCircle className="w-3 h-3" />
                                Pontos Fortes
                              </h5>
                              <ul className="space-y-0.5">
                                {(opinion.strengths as string[]).map((s: string, i: number) => (
                                  <li key={i} className={`${textStyles.caption} lia-text-base flex items-start gap-1`}>
                                    <span className="text-status-success mt-0.5">•</span>
                                    {s}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {opinion.concerns && (opinion.concerns as string[]).length > 0 && (
                            <div>
                              <h5 className={`${textStyles.label} text-status-warning mb-1 flex items-center gap-1`}>
                                <AlertCircle className="w-3 h-3" />
                                Pontos de Atenção
                              </h5>
                              <ul className="space-y-0.5">
                                {(opinion.concerns as string[]).map((c: string, i: number) => (
                                  <li key={i} className={`${textStyles.caption} lia-text-base flex items-start gap-1`}>
                                    <span className="text-status-warning mt-0.5">•</span>
                                    {c}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {!!(opinion.next_steps) && (
                            <div>
                              <h5 className={`${textStyles.label} mb-1 flex items-center gap-1`}>
                                <TrendingUp className="w-3 h-3" />
                                Próximos Passos
                              </h5>
                              <p className={`${textStyles.caption} lia-text-base`}>{opinion.next_steps as string}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </Card>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Subtab: Análises */}
        {opinionsSubTab === "analises" && (
          <div className="space-y-3">
            {isLoadingAnalyses && (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <Card key={i} className="animate-pulse motion-reduce:animate-none">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                        <div className="flex-1">
                          <div className="w-32 h-4 bg-gray-200 rounded-md mb-1"></div>
                          <div className="w-24 h-3 bg-gray-200 rounded-md"></div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="w-full h-3 bg-gray-200 rounded-md"></div>
                        <div className="w-3/4 h-3 bg-gray-200 rounded-md"></div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {!isLoadingAnalyses && (!savedAnalyses || (savedAnalyses as unknown as { total_analyses: number }).total_analyses === 0) && (
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-3">
                    <Brain className="w-6 h-6 text-wedo-purple" />
                  </div>
                  <p className={`${textStyles.subtitle} mb-1`}>Nenhuma análise disponível</p>
                  <p className={textStyles.description}>
                    Use o ícone no header para gerar análises de perfil e salvá-las aqui.
                  </p>
                </CardContent>
              </Card>
            )}

            {!isLoadingAnalyses && savedAnalyses && (savedAnalyses as unknown as { total_analyses: number }).total_analyses > 0 && (
              <div className="space-y-3">
                {(savedAnalyses as unknown as { analyses: Record<string, unknown>[] }).analyses.map((analysis: Record<string, unknown>) => {
                  const analysisLabels: Record<string, string> = {
                    bullet_points: "Pontos-chave",
                    short_paragraph: "Resumo",
                    detailed_bullets: "Análise Detalhada",
                  }
                  const isExpanded = expandedAnalysisId === analysis.id

                  return (
                    <Card key={analysis.id as string} className="overflow-hidden hover:transition-shadow">
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
                              <Badge className="text-micro px-1.5 py-0 h-4 bg-wedo-purple/15 text-wedo-purple">
                                {analysisLabels[analysis.analysis_type as string] || analysis.analysis_type as string}
                              </Badge>
                            </div>
                            <span className={`${textStyles.caption} lia-text-secondary`}>
                              {analysis.created_at ? new Date(analysis.created_at as string).toLocaleDateString("pt-BR", {
                                day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
                              }) : "Data não disponível"}
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
                                {copiedItemId === `analysis-${analysis.id}` ? (
                                  <Check className="w-3.5 h-3.5 text-status-success" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5 lia-text-secondary hover:lia-text-base" />
                                )}
                              </button>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="text-micro">Copiar análise</TooltipContent>
                          </Tooltip>
                          <ChevronDown className={`w-4 h-4 lia-text-secondary transition-transform motion-reduce:transition-none ${isExpanded ? "rotate-180" : ""}`} />
                        </div>
                      </div>

                      {isExpanded && (
                        <div className="px-3 pb-3 border-t border-gray-50">
                          <div className={`${textStyles.description} text-lia-text-primary dark:text-lia-text-primary leading-relaxed whitespace-pre-wrap bg-gray-50 rounded-md p-3 mt-2`}>
                            {cleanTextForCopy(analysis.content as string)}
                          </div>
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
                    </Card>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Delete Analysis AlertDialog */}
      <AlertDialog open={!!analysisToDelete} onOpenChange={(open: boolean) => !open && setAnalysisToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover Análise</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja remover esta análise? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteAnalysis} className="bg-status-error hover:bg-status-error text-white">
              Remover Definitivamente
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </TooltipProvider>
  )
}
