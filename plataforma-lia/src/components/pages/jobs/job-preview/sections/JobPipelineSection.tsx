"use client"


import { CURRENCY_SYMBOL, formatBRLCompact } from"@/lib/pricing"
import React from"react"
import { Chip } from "@/components/ui/chip"
import {
  Clock, Shield, Target, TrendingUp, Lightbulb, BarChart3, AlertCircle,
  Share2, Linkedin, Briefcase, Brain, Globe
} from"lucide-react"
import { type Job } from"@/components/jobs"
import { type JobVacancyMetrics } from"@/services/lia-api"
import { textStyles } from"@/lib/design-tokens"

interface JobPipelineSectionProps {
  previewJob: Job
  jobMetrics: JobVacancyMetrics | null
  isLoadingJobMetrics: boolean
}

export function JobPipelineSection({
  previewJob,
  jobMetrics,
  isLoadingJobMetrics,
}: JobPipelineSectionProps) {
  return (
    <div data-testid="job-pipeline-section" className="space-y-4">
                      {/* Cards de Métricas Preditivas Principais */}
                      <div className="grid grid-cols-2 gap-2">
                        {/* Score de Sucesso */}
                        <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary">Sucesso de Fechamento</span>
                            <Target className="w-3 h-3 text-lia-text-primary" />
                          </div>
                          <div className="text-base-ui font-semibold text-lia-text-primary">
                            {previewJob.funnel.total > 20 ? '85%' : previewJob.funnel.total > 10 ? '60%' : '35%'}
                          </div>
                          <div className="mt-0.5 text-xs text-lia-text-primary">
                            Pipeline: {previewJob.funnel.total} candidatos
                          </div>
                        </div>

                        {/* Tempo de Preenchimento */}
                        <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary">Tempo de Preenchimento</span>
                            <Clock className="w-3 h-3 text-lia-text-primary" />
                          </div>
                          <div className="text-base-ui font-semibold text-lia-text-primary">
                            {previewJob.urgencyLevel > 3 ? '15' : previewJob.urgencyLevel > 2 ? '25' : '35'}d
                          </div>
                          <div className="mt-0.5 text-xs text-lia-text-primary">
                            Velocidade: {previewJob.funnel.interview > 0 ? '3.2' : '1.5'} cv/dia
                          </div>
                        </div>

                        {/* Qualidade Pipeline */}
                        <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary">Qualidade Pipeline</span>
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                          </div>
                          <div className="text-base-ui font-semibold text-lia-text-primary">
                            {previewJob.funnel.final > 3 ? 'A+' : previewJob.funnel.interview > 5 ? 'B+' : 'C'}
                          </div>
 <div className="mt-0.5 text-xs text-lia-text-primary">
                            Conversão: {previewJob.funnel.interview > 0 ? Math.round((previewJob.funnel.interview / previewJob.funnel.total) * 100) : 0}%
                          </div>
                        </div>

                        {/* Risco de Recusa */}
                        <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-2.5">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-lia-text-primary">Risco de Recusa</span>
                            <AlertCircle className="w-3 h-3 text-status-error" />
                          </div>
                          <div className="text-base-ui font-semibold text-status-error dark:text-status-error">
                            {previewJob.seniority === 'Sênior' ? '45%' : previewJob.seniority === 'Pleno' ? '25%' : '15%'}
                          </div>
                          <div className="mt-0.5 text-xs text-status-error dark:text-status-error">
                            Gap salarial: {previewJob.seniority === 'Sênior' ? '±18%' : '±8%'}
                          </div>
                        </div>
                      </div>

                      {/* Funil de Recrutamento Visual */}
                      <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-3">
                        <h4 className={`${textStyles.title} mb-3 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary" />
                          Funil de Recrutamento
                        </h4>

                        {/* Visualização do Funil */}
                        <div className="space-y-2">
                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-lia-text-primary w-20">Total</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-3">
                                  <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated h-3 rounded-full flex items-center justify-end pr-1 w-full">
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.total}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-lia-text-primary w-20">Triagem</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-3">
                                  <div className="bg-lia-border-medium dark:bg-lia-bg-elevated h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: `${(previewJob.funnel.screening / previewJob.funnel.total) * 100}%`}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.screening}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-lia-text-primary w-10 text-right">
                                {Math.round((previewJob.funnel.screening / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-lia-text-primary w-20">Entrevistas</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-3">
                                  <div className="bg-lia-border-medium dark:bg-lia-bg-elevated h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: `${(previewJob.funnel.interview / previewJob.funnel.total) * 100}%`}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.interview}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-lia-text-primary w-10 text-right">
                                {Math.round((previewJob.funnel.interview / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-lia-text-primary w-20">Finalistas</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-3">
                                  <div className="bg-lia-border-medium dark:bg-lia-bg-elevated h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: `${(previewJob.funnel.final / previewJob.funnel.total) * 100}%`}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.final}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-lia-text-primary w-10 text-right">
                                {Math.round((previewJob.funnel.final / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>

                          <div className="relative">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-lia-text-primary w-20">Contratados</span>
                              <div className="flex-1 mx-2">
                                <div className="bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-3">
                                  <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated h-3 rounded-full flex items-center justify-end pr-1"
                                       style={{width: previewJob.funnel.hired > 0 ? `${(previewJob.funnel.hired / previewJob.funnel.total) * 100}%` : '5%'}}>
                                    <span className="text-xs text-white font-medium">{previewJob.funnel.hired}</span>
                                  </div>
                                </div>
                              </div>
                              <span className="text-xs text-lia-text-primary w-10 text-right">
                                {Math.round((previewJob.funnel.hired / previewJob.funnel.total) * 100)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Métricas de Conversão */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-2">
                          <p className={`${textStyles.bodySmall}`}>CV → Triagem</p>
                          <p className="text-sm font-bold text-lia-text-primary">
                            {Math.round((previewJob.funnel.screening / previewJob.funnel.total) * 100)}%
                          </p>
                        </div>
                        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-2">
                          <p className={`${textStyles.bodySmall}`}>Triagem → Entrevista</p>
                          <p className="text-sm font-bold text-lia-text-primary">
                            {previewJob.funnel.screening > 0 ? Math.round((previewJob.funnel.interview / previewJob.funnel.screening) * 100) : 0}%
                          </p>
                        </div>
                        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-2">
                          <p className={`${textStyles.bodySmall}`}>Entrevista → Final</p>
                          <p className="text-sm font-bold text-lia-text-primary">
                            {previewJob.funnel.interview > 0 ? Math.round((previewJob.funnel.final / previewJob.funnel.interview) * 100) : 0}%
                          </p>
                        </div>
                        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-2">
                          <p className={`${textStyles.bodySmall}`}>Final → Contratação</p>
                          <p className="text-sm font-bold text-lia-text-primary">
                            {previewJob.funnel.final > 0 ? Math.round((previewJob.funnel.hired / previewJob.funnel.final) * 100) : 0}%
                          </p>
                        </div>
                      </div>

                      {/* Insights e Recomendações da LIA */}
                      <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-3">
                        <div className="flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-lia-text-primary mt-0.5" />
                          <div className="flex-1">
                            <p className="text-xs font-medium text-lia-text-primary font-semibold mb-1">
                              Insights de IA
                            </p>
                            <ul className="space-y-1 text-xs text-lia-text-primary">
                              {previewJob.funnel.total < 10 && (
                                <li>• Pipeline baixo: Ampliar divulgação ou revisar requisitos</li>
                              )}
                              {previewJob.seniority === 'Sênior' && (
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
                      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl p-3">
                        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
                          <BarChart3 className="w-3.5 h-3.5 text-lia-text-primary" />
                          Comparativo com Mercado
                        </h4>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-elevated/50 rounded-xl">
                            <p className={`${textStyles.bodySmall}`}>Salário</p>
                            <p className="text-sm font-bold text-lia-text-primary">
                              {previewJob.salary > `${CURRENCY_SYMBOL} 10.000` ? '+15%' : '-5%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. mercado</p>
                          </div>
                          <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-elevated/50 rounded-xl">
                            <p className={`${textStyles.bodySmall}`}>Candidatos</p>
                            <p className="text-sm font-bold text-lia-text-primary">
                              {previewJob.funnel.total > 30 ? '+45%' : '-20%'}
                            </p>
                            <p className={textStyles.bodySmall}>vs. média</p>
                          </div>
                          <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-elevated/50 rounded-xl">
                            <p className={`${textStyles.bodySmall}`}>Atratividade</p>
                            <p className="text-sm font-bold text-lia-text-primary">
                              #—
                            </p>
                            <p className={textStyles.bodySmall}>ranking</p>
                          </div>
                        </div>
                      </div>

                      {/* KPIs da Vaga com Budget */}
                      <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated/30 rounded-xl p-3">
                        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
                          <TrendingUp className="w-3.5 h-3.5 text-lia-text-primary" />
                          KPIs e Orçamento
                        </h4>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="flex items-center justify-between">
                            <span className={`${textStyles.bodySmall}`}>Urgência</span>
                            <div className="flex gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < previewJob.urgencyLevel ? 'bg-status-error' : 'bg-lia-border-default'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          {previewJob.budget && (
                            <>
                              <div className="flex items-center justify-between">
                                <span className={`${textStyles.bodySmall}`}>Budget</span>
                                <span className="text-xs font-bold text-lia-text-primary">
                                  {formatBRLCompact(previewJob.budget)}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className={`${textStyles.bodySmall}`}>Usado</span>
                                <span className="text-xs font-bold text-lia-text-primary">
                                  {previewJob.budgetUsed ? Math.round((previewJob.budgetUsed / previewJob.budget) * 100) : 0}%
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Fatores de Risco */}
                      <div className="bg-status-error/10 dark:bg-status-error/20 rounded-md p-3">
                        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
                          <Shield className="w-3.5 h-3.5 text-status-error" />
                          Fatores de Risco
                        </h4>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-lia-text-primary">Competitividade salarial</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.seniority === 'Sênior' ? 4 : 2) ? 'bg-status-error' : 'bg-lia-border-default'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-lia-text-primary">Escassez de talentos</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.seniority === 'Sênior' ? 3 : 1) ? 'bg-wedo-orange' : 'bg-lia-border-default'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-lia-text-primary">Tempo de processo</span>
                            <div className="flex items-center gap-0.5">
                              {[...Array(5)].map((_, i) => (
                                <div
                                  key={i}
                                  className={`w-1.5 h-2.5 rounded-full ${
                                    i < (previewJob.urgencyLevel > 3 ? 4 : 2) ? 'bg-lia-bg-secondary dark:bg-lia-bg-elevated' : 'bg-lia-border-default'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Canais de Divulgação */}
                      <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-3">
                        <h4 className={`${textStyles.title} mb-2 flex items-center gap-1`}>
                          <Share2 className="w-3.5 h-3.5 text-lia-text-primary" />
                          Canais de Divulgação
                        </h4>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Linkedin className="w-3 h-3 text-lia-text-primary" />
                              <span className={`${textStyles.bodySmall}`}>LinkedIn</span>
                            </div>
                            {previewJob.publishedLinkedIn ? (
                              <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated">Publicado</Chip>
                            ) : (
                              <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">Não publicado</Chip>
                            )}
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Globe className="w-3 h-3 text-lia-text-primary" />
                              <span className={`${textStyles.bodySmall}`}>Site</span>
                            </div>
                            {previewJob.publishedWebsite ? (
                              <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated">Publicado</Chip>
                            ) : (
                              <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">Não publicado</Chip>
                            )}
                          </div>
                          {previewJob.publishedIndeed !== undefined && (
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-1">
                                <Briefcase className="w-3 h-3 text-lia-text-primary" />
                                <span className={`${textStyles.bodySmall}`}>Indeed</span>
                              </div>
                              {previewJob.publishedIndeed ? (
                                <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated">Publicado</Chip>
                              ) : (
                                <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary">Não publicado</Chip>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
    </div>
  )
}
