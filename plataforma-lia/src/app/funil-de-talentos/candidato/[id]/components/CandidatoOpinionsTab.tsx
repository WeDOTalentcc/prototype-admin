"use client"

import React from "react"
import { getPercentageScoreColorClass } from "@/lib/score-utils"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import {
  Brain, FileText, Target, Briefcase, CheckCircle, Clock, X,
  BarChart3, TrendingUp, AlertCircle, ChevronDown, ChevronUp, Copy
} from "lucide-react"
import { TabsContent } from "@/components/ui/tabs"
import { ANALYSIS_TYPE_LABELS } from "../candidato-page.constants"
import type { OpinionsSubTab } from "../candidato-page.types"

interface CandidatoOpinionsTabProps {
  opinionsSubTab: OpinionsSubTab
  opinionsHistory: Record<string, unknown>[]
  savedAnalyses: Record<string, unknown> | null
  isLoadingOpinions: boolean
  isLoadingAnalyses: boolean
  expandedOpinionId: string | null
  expandedAnalysisId: string | null
  setOpinionsSubTab: (v: OpinionsSubTab) => void
  setExpandedOpinionId: (v: string | null) => void
  setExpandedAnalysisId: (v: string | null) => void
  formatDate: (dateStr: string | null | undefined) => string | null
  copyToClipboard: (text: string, label?: string) => Promise<void>
  cleanMarkdown: (text: string) => string
}

function getScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "text-lia-text-secondary"
  return getPercentageScoreColorClass(score)
}

function RecommendationBadge({ rec }: { rec: unknown }) {
  if (!rec) return null
  if (rec === "approved") return <Badge className="bg-status-success/15 text-status-success text-xs flex items-center gap-0.5"><CheckCircle className="w-2.5 h-2.5" />APROVADO</Badge>
  if (rec === "pending_review") return <Badge className="bg-status-warning/15 text-status-warning text-xs flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />PENDENTE</Badge>
  if (rec === "not_approved") return <Badge className="bg-status-error/15 text-status-error text-xs flex items-center gap-0.5"><X className="w-2.5 h-2.5" />NÃO APROVADO</Badge>
  return null
}

function OpinionSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2].map((i) => (
        <div key={i} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-md p-4 animate-pulse motion-reduce:animate-none">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full" />
            <div className="flex-1">
              <div className="w-32 h-4 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md mb-1" />
              <div className="w-24 h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md" />
            </div>
          </div>
          <div className="space-y-2">
            <div className="w-full h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md" />
            <div className="w-3/4 h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-md" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function CandidatoOpinionsTab({
  opinionsSubTab,
  opinionsHistory,
  savedAnalyses,
  isLoadingOpinions,
  isLoadingAnalyses,
  expandedOpinionId,
  expandedAnalysisId,
  setOpinionsSubTab,
  setExpandedOpinionId,
  setExpandedAnalysisId,
  formatDate,
  copyToClipboard,
  cleanMarkdown,
}: CandidatoOpinionsTabProps) {
  const analyses = (savedAnalyses?.analyses as Record<string, unknown>[] | undefined) ?? []

  return (
    <TabsContent value="opinions" className="mt-4">
      <Card className="border-lia-border-subtle">
        <CardContent className="p-4 space-y-4">
          {/* SubTabs */}
          <div className="flex items-center gap-4 border-b border-lia-border-subtle pb-3">
            <button
              onClick={() => setOpinionsSubTab("pareceres")}
              className={`flex items-center gap-2 pb-2 text-sm font-medium transition-colors motion-reduce:transition-none ${
                opinionsSubTab === "pareceres"
                  ? "text-lia-text-secondary border-b-2 border-lia-btn-primary-bg dark:border-lia-border-subtle"
                  : "text-lia-text-secondary hover:text-lia-text-primary"
              }`}
            >
              <Brain className="w-4 h-4 text-wedo-cyan" />
              Pareceres da LIA
              {opinionsHistory.length > 0 && (
                <Badge className="text-xs px-1.5 py-0 h-4 bg-lia-btn-primary-bg text-lia-btn-primary-text">{opinionsHistory.length}</Badge>
              )}
            </button>
            <button
              onClick={() => setOpinionsSubTab("analises")}
              className={`flex items-center gap-2 pb-2 text-sm font-medium transition-colors motion-reduce:transition-none ${
                opinionsSubTab === "analises"
                  ? "text-wedo-purple border-b-2 border-wedo-purple/30"
                  : "text-lia-text-secondary hover:text-lia-text-primary"
              }`}
            >
              <Brain className="w-4 h-4 text-wedo-cyan" />
              Análises
              {(savedAnalyses?.total_analyses as number || 0) > 0 && (
                <Badge className="text-xs px-1.5 py-0 h-4 bg-wedo-purple text-white">{savedAnalyses?.total_analyses as number}</Badge>
              )}
            </button>
          </div>

          {/* PARECERES */}
          {opinionsSubTab === "pareceres" && (
            <>
              {isLoadingOpinions && <OpinionSkeleton />}

              {!isLoadingOpinions && opinionsHistory.length === 0 && (
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-md p-8 text-center">
                  <div className="w-14 h-14 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center mx-auto mb-4">
                    <FileText className="w-7 h-7 text-lia-text-secondary" />
                  </div>
                  <p className="text-sm font-semibold text-lia-text-primary mb-1">Nenhum parecer disponível</p>
                  <p className="text-xs text-lia-text-secondary">
                    Os pareceres serão gerados automaticamente após triagens ou análises da LIA.
                  </p>
                </div>
              )}

              {!isLoadingOpinions && opinionsHistory.length > 0 && (
                <div className="space-y-3">
                  {opinionsHistory.map((opinion) => {
                    const isExpanded = expandedOpinionId === opinion.id
                    const isWsi = opinion.opinion_type === "wsi"
                    const displayScore = isWsi ? opinion.wsi_score : opinion.score
                    const strengthsList = opinion.strengths as string[] | undefined
                    const gapsList = opinion.gaps as string[] | undefined
                    const scoreBreakdown = opinion.score_breakdown as Record<string, unknown> | undefined

                    return (
                      <div key={opinion.id as string} className="relative">
                        {!opinion.is_current && (
                          <Badge className="absolute top-2 right-2 text-xs px-1.5 py-0 h-4 bg-lia-bg-tertiary text-lia-text-secondary z-10">
                            v{opinion.version as number} - Histórico
                          </Badge>
                        )}
                        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-md overflow-hidden">
                          <button
                            onClick={() => setExpandedOpinionId(isExpanded ? null : opinion.id as string)}
                            className="w-full p-4 flex items-center justify-between hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                          >
                            <div className="flex items-center gap-3">
                              <div className={`w-9 h-9 rounded-full flex items-center justify-center ${isWsi ? "bg-wedo-purple/15" : "bg-lia-bg-tertiary dark:bg-lia-bg-secondary"}`}>
                                {isWsi ? <Target className="w-4 h-4 text-wedo-purple" /> : <Brain className="w-4 h-4 text-wedo-cyan" />}
                              </div>
                              <div className="text-left">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-sm font-semibold text-lia-text-primary">{isWsi ? "Parecer WSI" : "Parecer Geral"}</span>
                                  {opinion.job_vacancy_id && opinion.job_vacancy_title ? (
                                    <Badge className="text-xs px-1.5 py-0 h-4 bg-lia-bg-secondary dark:bg-lia-bg-primary text-lia-text-primary border-lia-border-default flex items-center gap-1">
                                      <Briefcase className="w-2.5 h-2.5" />
                                      {`#${String(opinion.job_vacancy_id).slice(0, 6)} - ${String(opinion.job_vacancy_title)}`}
                                    </Badge>
                                  ) : opinion.job_vacancy_title ? (
                                    <Badge className="text-xs px-1.5 py-0 h-4 bg-lia-bg-secondary dark:bg-lia-bg-primary text-lia-text-primary border-lia-border-default flex items-center gap-1">
                                      <Briefcase className="w-2.5 h-2.5" />
                                      {String(opinion.job_vacancy_title)}
                                    </Badge>
                                  ) : null}
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                  {displayScore !== null && displayScore !== undefined && (
                                    <span className={`text-xs font-semibold ${getScoreColor(displayScore as number)}`}>
                                      {isWsi
                                        ? `WSI: ${(displayScore as number).toFixed(1)}/5`
                                        : `Score: ${Math.round(displayScore as number)}/100`}
                                    </span>
                                  )}
                                  {!!opinion.archetype && <><span className="text-lia-text-secondary">•</span><span className="text-xs text-lia-text-secondary">{String(opinion.archetype)}</span></>}
                                  <RecommendationBadge rec={opinion.recommendation} />
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      const text = [
                                        String(opinion.summary || ""),
                                        strengthsList?.length ? `Pontos Fortes:\n${strengthsList.join("\n")}` : "",
                                        gapsList?.length ? `Gaps:\n${gapsList.join("\n")}` : "",
                                        opinion.next_steps ? `Próximos Passos: ${String(opinion.next_steps)}` : "",
                                      ].filter(Boolean).join("\n\n")
                                      void copyToClipboard(text, "Parecer")
                                    }}
                                    className="p-1.5 rounded-md hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                                  >
                                    <Copy className="w-4 h-4 text-lia-text-secondary" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent>Copiar Parecer</TooltipContent>
                              </Tooltip>
                              {!!opinion.created_at && <span className="text-xs text-lia-text-secondary">{formatDate(String(opinion.created_at))}</span>}
                              {isExpanded ? <ChevronUp className="w-4 h-4 text-lia-text-secondary" /> : <ChevronDown className="w-4 h-4 text-lia-text-secondary" />}
                            </div>
                          </button>

                          {isExpanded && (
                            <div className="px-4 pb-4 pt-0 border-t border-lia-border-subtle space-y-4">
                              {!!opinion.summary && (
                                <div className="pt-4">
                                  <p className="text-sm text-lia-text-primary leading-relaxed">{String(opinion.summary)}</p>
                                </div>
                              )}
                              {scoreBreakdown && Object.keys(scoreBreakdown).length > 0 && (
                                <div>
                                  <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                                    <BarChart3 className="w-3.5 h-3.5" />
                                    Score Breakdown
                                  </h5>
                                  <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(scoreBreakdown).map(([key, value]) =>
                                      value !== null && value !== undefined ? (
                                        <div key={key} className="flex items-center justify-between text-xs bg-lia-bg-secondary dark:bg-lia-bg-elevated rounded-md px-3 py-2">
                                          <span className="text-lia-text-secondary capitalize">{key.replace(/_/g, " ")}</span>
                                          <span className="font-semibold text-lia-text-primary">{typeof value === "number" ? `${Math.round(value)}%` : String(value)}</span>
                                        </div>
                                      ) : null
                                    )}
                                  </div>
                                </div>
                              )}
                              {strengthsList && strengthsList.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-semibold text-status-success mb-2 flex items-center gap-1">
                                    <CheckCircle className="w-3.5 h-3.5" />Pontos Fortes
                                  </h5>
                                  <ul className="space-y-1">
                                    {strengthsList.map((s, i) => (
                                      <li key={i} className="text-xs text-lia-text-secondary flex items-start gap-1.5">
                                        <span className="text-status-success mt-0.5">•</span>{s}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {gapsList && gapsList.length > 0 && (
                                <div>
                                  <h5 className="text-xs font-semibold text-status-error mb-2 flex items-center gap-1">
                                    <AlertCircle className="w-3.5 h-3.5" />Gaps Identificados
                                  </h5>
                                  <ul className="space-y-1">
                                    {gapsList.map((g, i) => (
                                      <li key={i} className="text-xs text-lia-text-secondary flex items-start gap-1.5">
                                        <span className="text-status-error mt-0.5">•</span>{g}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {!!opinion.next_steps && (
                                <div>
                                  <h5 className="text-xs font-semibold text-lia-text-primary mb-2 flex items-center gap-1">
                                    <TrendingUp className="w-3.5 h-3.5" />Próximos Passos
                                  </h5>
                                  <p className="text-xs text-lia-text-secondary">{String(opinion.next_steps)}</p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* ANALYSES */}
          {opinionsSubTab === "analises" && (
            <>
              {isLoadingAnalyses && <OpinionSkeleton />}

              {!isLoadingAnalyses && analyses.length === 0 && (
                <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-md p-8 text-center">
                  <div className="w-14 h-14 rounded-full bg-wedo-purple/10 flex items-center justify-center mx-auto mb-4">
                    <Brain className="w-7 h-7 text-wedo-purple" />
                  </div>
                  <p className="text-sm font-semibold text-lia-text-primary mb-1">Nenhuma análise salva</p>
                  <p className="text-xs text-lia-text-secondary">Use o ícone 🧠 no perfil do candidato para gerar análises.</p>
                </div>
              )}

              {!isLoadingAnalyses && analyses.length > 0 && (
                <div className="space-y-3">
                  {analyses.map((analysis) => {
                    const isExpanded = expandedAnalysisId === analysis.id
                    return (
                      <div key={analysis.id as string} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-md overflow-hidden">
                        <button
                          onClick={() => setExpandedAnalysisId(isExpanded ? null : analysis.id as string)}
                          className="w-full p-4 flex items-center justify-between hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-full bg-wedo-purple/15 flex items-center justify-center">
                              <Brain className="w-4 h-4 text-wedo-purple" />
                            </div>
                            <div className="text-left">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-lia-text-primary">
                                  {ANALYSIS_TYPE_LABELS[analysis.analysis_type as string] || String(analysis.analysis_type)}
                                </span>
                                <Badge className="text-xs px-1.5 py-0 h-4 bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                                  Análise LIA
                                </Badge>
                              </div>
                              <span className="text-xs text-lia-text-secondary mt-0.5">
                                {analysis.created_at
                                  ? new Date(analysis.created_at as string).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
                                  : "Data não disponível"}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  onClick={(e) => { e.stopPropagation(); void copyToClipboard(String(analysis.content ?? ""), "Análise") }}
                                  className="p-1.5 rounded-md hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                                >
                                  <Copy className="w-4 h-4 text-lia-text-secondary" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>Copiar Análise</TooltipContent>
                            </Tooltip>
                            {isExpanded ? <ChevronUp className="w-4 h-4 text-lia-text-secondary" /> : <ChevronDown className="w-4 h-4 text-lia-text-secondary" />}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="px-4 pb-4 border-t border-lia-border-subtle pt-4">
                            <div className="text-sm text-lia-text-primary leading-relaxed whitespace-pre-wrap">
                              {cleanMarkdown(String(analysis.content || ""))}
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
        </CardContent>
      </Card>
    </TabsContent>
  )
}
