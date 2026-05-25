"use client"

import { formatBRL } from "@/lib/pricing"

import { getJobDimensionColorClass } from "@/lib/score-utils"
import {
  Users,
  CheckCircle,
  Clock,
  XCircle,
  Filter,
  TrendingUp,
  Target,
  Brain,
  BarChart3,
  ArrowRight,
  ArrowDownRight,
  CheckCircle as CheckCircleIcon,
  AlertTriangle,
  AlertCircle,
  Lightbulb,
  Eye,
  DollarSign,
  Star,
  Award,
  AlertOctagon,
  Calendar,
} from "lucide-react"
import type {
  JobInsightData,
  ConversionRate,
  StageBottleneck,
  InsightCategory,
  WSIScore,
  DemographicDistribution,
} from "../job-insights.types"
import { CONVERSION_STATUS_COLORS, INSIGHT_TYPE_STYLES } from "../job-insights.constants"

interface AggregateMetrics {
  totalCandidates: number
  totalApproved: number
  totalScreening: number
  totalRejected: number
  avgTimePerStage: number
  conversionRate: string
  screeningConversionRate: string
}

interface SalaryData {
  vagaMin: number
  vagaMax: number
  mediaInscritos: number
  dentroFaixa: number
  percentualDentro: number
}

interface QualityMetrics {
  avgScoreTodos: number
  avgScoreTriados: number
  avgScoreAprovados: number
  taxaTriagem: string
  taxaAprovacao: string
}

interface WSIMetrics {
  dimensions: WSIScore[]
  avgWSI: number
}

interface LiaTextualAnalysis {
  summary: string
  performance: string
  volumeInsight: string
  conversionNote: string
  avgDaysOpen: number
}

interface TrendData {
  weeks: readonly string[]
  candidatesTrend: number[]
  conversionTrend: number[]
  maxCandidates: number
}

interface FunnelStage {
  name: string
  value: number
  color: string
  percentage: number
  rate: string
}

interface InsightsOverviewSectionProps {
  jobs: JobInsightData[]
  aggregateMetrics: AggregateMetrics
  funnelData: FunnelStage[]
  salaryData: SalaryData
  qualityMetrics: QualityMetrics
  wsiMetrics: WSIMetrics
  liaTextualAnalysis: LiaTextualAnalysis
  trendData: TrendData
  calculatedConversionRates: ConversionRate[]
  categorizedInsights: InsightCategory[]
  bottlenecks?: StageBottleneck[]
  getScoreColor: (score?: number) => string
  getDaysRemaining: (deadline?: string) => number | null
}

function DemographicBar({ name: label, count, percentage }: DemographicDistribution) {
  return (
    <div data-testid="insights-overview-section" className="flex items-center justify-between">
      <span className="text-xs text-lia-text-secondary">{label}</span>
      <div className="flex items-center gap-2">
        <div className="w-16 h-2 bg-lia-interactive-active rounded-full overflow-hidden">
          <div className="h-full bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg" style={{ width: `${percentage}%` }} />
        </div>
        <span className="text-micro text-lia-text-secondary w-8 text-right">{count}</span>
      </div>
    </div>
  )
}

export function InsightsOverviewSection({
  jobs,
  aggregateMetrics,
  funnelData,
  salaryData,
  qualityMetrics,
  wsiMetrics,
  liaTextualAnalysis,
  trendData,
  calculatedConversionRates,
  categorizedInsights,
  bottlenecks,
  getScoreColor,
  getDaysRemaining,
}: InsightsOverviewSectionProps) {
  return (
    <div className="space-y-4">
      {/* ── Resumo Agregado ─────────────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <Target className="w-3.5 h-3.5 text-lia-text-tertiary" />
          Resumo Agregado
        </h3>
        <div className="grid grid-cols-6 gap-3">
          {[
            { Icon: Users, label: "Total Candidatos", value: aggregateMetrics.totalCandidates, color: "text-lia-text-primary" },
            { Icon: Filter, label: "Em Triagem", value: aggregateMetrics.totalScreening, color: "text-lia-text-primary" },
            { Icon: CheckCircle, label: "Aprovados", value: aggregateMetrics.totalApproved, color: "text-status-success" },
            { Icon: XCircle, label: "Rejeitados", value: aggregateMetrics.totalRejected, color: "text-lia-text-secondary" },
            { Icon: Clock, label: "Tempo/Etapa", value: `${aggregateMetrics.avgTimePerStage}d`, color: "text-lia-text-primary" },
            { Icon: TrendingUp, label: "Conversão", value: `${aggregateMetrics.conversionRate}%`, color: "text-lia-text-primary" },
          ].map(({ Icon, label, value, color }) => (
            <div key={label} className="bg-lia-bg-primary rounded-xl p-3 border border-lia-border-subtle">
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className="w-3.5 h-3.5 text-lia-text-tertiary" />
                <span className="text-xs text-lia-text-secondary">{label}</span>
              </div>
              <p className={`text-xl font-semibold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Análise LIA Textual ─────────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-default">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0">
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide mb-2">
              Análise LIA
            </h3>
            <p className="text-sm text-lia-text-primary leading-relaxed">
              {liaTextualAnalysis.summary} {liaTextualAnalysis.performance}
              {liaTextualAnalysis.volumeInsight && ` ${liaTextualAnalysis.volumeInsight}`}
              {liaTextualAnalysis.conversionNote && ` ${liaTextualAnalysis.conversionNote}`}
              {liaTextualAnalysis.avgDaysOpen > 0 &&
                ` Tempo médio de abertura: ${liaTextualAnalysis.avgDaysOpen} dias.`}
            </p>
          </div>
        </div>
      </div>

      {/* ── Taxa de Conversão por Etapa ─────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <ArrowDownRight className="w-3.5 h-3.5 text-lia-text-tertiary" />
          Taxa de Conversão por Etapa
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {calculatedConversionRates.map((rate) => {
            const colors = CONVERSION_STATUS_COLORS[rate.status]
            return (
              <div key={(rate as unknown as Record<string, unknown>).stage as string || rate.from} className={`rounded-md p-3 border ${colors.bg} ${colors.border}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-lia-text-secondary">{rate.from}</span>
                    <ArrowRight className="w-3 h-3 text-lia-text-disabled" />
                    <span className="text-xs text-lia-text-secondary">{rate.to}</span>
                  </div>
                  <span className={colors.icon}>
                    {rate.status === "good" && <CheckCircleIcon className="w-3.5 h-3.5" />}
                    {rate.status === "warning" && <AlertTriangle className="w-3.5 h-3.5" />}
                    {rate.status === "critical" && <AlertCircle className="w-3.5 h-3.5" />}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-lia-bg-primary/50 rounded-full overflow-hidden">
                    <div className={`h-full ${colors.bar}`} style={{ width: `${Math.min(rate.rate, 100)}%` }} />
                  </div>
                  <span className={`text-sm font-bold ${colors.text}`}>{rate.rate}%</span>
                </div>
                <p className="text-xs text-lia-text-tertiary mt-1">{colors.label}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Tendência Temporal ──────────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-lia-text-tertiary" />
          Tendência Temporal
          <span className="text-xs text-lia-text-disabled font-normal ml-1">(estimativa)</span>
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-lia-bg-primary rounded-xl p-3 border border-lia-border-subtle">
            <h4 className="text-xs font-medium text-lia-text-tertiary mb-3">Candidatos Acumulados</h4>
            <div className="flex items-end justify-between h-20 gap-1">
              {trendData.candidatesTrend.map((val, i) => (
                <div key={i} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-lia-btn-primary-bg dark:bg-lia-btn-primary-bg rounded-t transition-colors motion-reduce:transition-none"
                    style={{ height: `${(val / trendData.maxCandidates) * 100}%` }}
                  />
                  <span className="text-xs text-lia-text-tertiary mt-1">{trendData.weeks[i]}</span>
                  <span className="text-xs font-medium text-lia-text-secondary">{val}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-lia-bg-primary rounded-xl p-3 border border-lia-border-subtle">
            <h4 className="text-xs font-medium text-lia-text-tertiary mb-3">Taxa de Conversão (%)</h4>
            <div className="flex items-end justify-between h-20 gap-1">
              {trendData.conversionTrend.map((val, i) => (
                <div key={i} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-status-success rounded-t transition-colors motion-reduce:transition-none"
                    style={{ height: `${val}%` }}
                  />
                  <span className="text-xs text-lia-text-tertiary mt-1">{trendData.weeks[i]}</span>
                  <span className="text-xs font-medium text-lia-text-secondary">{val}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Funil de Recrutamento ───────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <BarChart3 className="w-3.5 h-3.5 text-lia-text-tertiary" />
          Funil de Recrutamento
        </h3>
        <div className="space-y-2">
          {funnelData.map((stage, index) => (
            <div key={stage.name} className="flex items-center gap-3">
              <div className="w-24 text-xs font-medium text-lia-text-secondary text-right">{stage.name}</div>
              <div className="flex-1 h-7 bg-lia-bg-tertiary rounded-xl overflow-hidden relative">
                <div
                  className={`h-full ${stage.color} transition-[width] duration-500`}
                  style={{ width: `${stage.percentage}%` }}
                />
                <div className="absolute inset-0 flex items-center px-2">
                  <span className="text-xs font-semibold text-lia-text-primary">{stage.value}</span>
                </div>
              </div>
              <div className="w-12 text-xs text-lia-text-secondary">{stage.rate}%</div>
              {index < funnelData.length - 1 && <ArrowRight className="w-3 h-3 text-lia-text-disabled" />}
            </div>
          ))}
        </div>
      </div>

      {/* ── Salary + Quality ────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Análise Salarial
          </h3>
          <div className="space-y-3">
            {[
              { label: "Faixa da Vaga", value: `${formatBRL(salaryData.vagaMin)} - ${formatBRL(salaryData.vagaMax)}` },
              { label: "Média Pretensão Candidatos", value: `${formatBRL(salaryData.mediaInscritos)}` },
              { label: "Candidatos Dentro da Faixa", value: `${salaryData.dentroFaixa} (${salaryData.percentualDentro}%)` },
            ].map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between bg-lia-bg-primary rounded-xl p-2.5 border border-lia-border-subtle">
                <span className="text-xs text-lia-text-secondary">{label}</span>
                <span className="text-xs font-semibold text-lia-text-primary">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <Star className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Indicadores de Qualidade
          </h3>
          <div className="space-y-3">
            {[
              { label: "Nota Média (Todos)", value: `${qualityMetrics.avgScoreTodos}%`, score: qualityMetrics.avgScoreTodos },
              { label: "Nota Média (Triados)", value: `${qualityMetrics.avgScoreTriados}%`, score: qualityMetrics.avgScoreTriados },
              { label: "Taxa Triagem → Aprovação", value: `${qualityMetrics.taxaAprovacao}%`, score: undefined },
            ].map(({ label, value, score }) => (
              <div key={label} className="flex items-center justify-between bg-lia-bg-primary rounded-xl p-2.5 border border-lia-border-subtle">
                <span className="text-xs text-lia-text-secondary">{label}</span>
                <span className={`text-xs font-semibold ${score !== undefined ? getScoreColor(score) : "text-lia-text-primary"}`}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── WSI Metrics ─────────────────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Métricas WSI
            <span className="text-xs text-lia-text-disabled font-normal ml-1">(estimativa baseada em performance)</span>
          </h3>
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-lia-text-tertiary">Nota Média:</span>
            <span className="text-sm font-bold text-lia-text-primary">{wsiMetrics.avgWSI}%</span>
          </div>
        </div>
        <div className="space-y-2">
          {wsiMetrics.dimensions.map((dim) => (
            <div key={dim.dimension} className="flex items-center gap-3">
              <div className="w-24">
                <span className="text-xs font-medium text-lia-text-secondary">{dim.dimension}</span>
                <span className="text-xs text-lia-text-tertiary block">{dim.label}</span>
              </div>
              <div className="flex-1 h-4 bg-lia-interactive-active rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-[width] ${getJobDimensionColorClass(dim.score).bar}`}
                  style={{ width: `${dim.score}%` }}
                />
              </div>
              <span className={`text-xs font-semibold w-10 text-right ${getJobDimensionColorClass(dim.score).text}`}>
                {dim.score}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Insights Categorizados ──────────────────────────────────────── */}
      <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
        <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <Lightbulb className="w-3.5 h-3.5 text-lia-text-tertiary" />
          Insights Categorizados
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {categorizedInsights.map((insight, index) => {
            const styles = INSIGHT_TYPE_STYLES[insight.type]
            const IconComponent = insight.type === "action" ? Lightbulb : insight.type === "attention" ? AlertCircle : Eye
            return (
              <div key={`insight-${insight.type}-${insight.title || index}`} className={`rounded-md p-3 border ${styles.bg} ${styles.border}`}>
                <div className="flex items-start gap-2">
                  <IconComponent className={`w-4 h-4 mt-0.5 ${styles.iconColor}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-xs font-semibold text-lia-text-primary">{insight.title}</h4>
                      {insight.badge && (
                        <span className={`text-micro font-medium px-1.5 py-0.5 rounded-full ${insight.type === "attention" ? "bg-status-error/20 text-status-error" : "bg-status-warning/20 text-status-warning"}`}>
                          {insight.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-lia-text-secondary leading-relaxed">{insight.description}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Gargalos ────────────────────────────────────────────────────── */}
      {bottlenecks && bottlenecks.length > 0 && (
        <div className="bg-status-warning/10 rounded-xl p-4 border border-status-warning/30" aria-live="polite">
          <h3 className="text-xs font-semibold text-status-warning uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <AlertOctagon className="w-3.5 h-3.5" />
            Gargalos Identificados
          </h3>
          <div className="space-y-2">
            {bottlenecks.map((b) => (
              <div key={b.stage || (b as unknown as Record<string, unknown>).title as string} className="bg-lia-bg-primary rounded-xl p-3 border border-status-warning/30">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-lia-text-primary">{b.stage}</span>
                  {b.stuckCount > 0 && (
                    <span className="text-micro px-2 py-0.5 rounded-full bg-status-warning/15 text-status-warning">
                      {b.stuckCount} parados
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-lia-text-tertiary" />
                    <span className="text-lia-text-secondary">Tempo médio:</span>
                    <span className="font-medium text-lia-text-primary">{b.avgDays}d</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className="w-3 h-3 text-lia-text-tertiary rotate-180" />
                    <span className="text-lia-text-secondary">Taxa desistência:</span>
                    <span className={`font-medium ${b.dropRate > 30 ? "text-status-error" : b.dropRate > 15 ? "text-status-warning" : "text-status-success"}`}>
                      {b.dropRate}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Vagas Sem Aprovação ─────────────────────────────────────────── */}
      {jobs.some((job) => (job.days_open || 0) > 30 && (job.approved_count || 0) === 0) && (
        <div className="bg-status-error/10 rounded-xl p-4 border border-status-error/30" aria-live="polite">
          <h3 className="text-xs font-semibold text-status-error uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            Vagas Sem Aprovação
          </h3>
          <div className="space-y-2">
            {jobs
              .filter((job) => (job.days_open || 0) > 30 && (job.approved_count || 0) === 0)
              .map((job) => (
                <div key={job.id} className="bg-lia-bg-primary rounded-xl p-3 border border-status-error/30">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {job.code && (
                        <span className="text-micro font-medium text-status-error bg-status-error/15 px-1.5 py-0.5 rounded-full">
                          {job.code}
                        </span>
                      )}
                      <span className="text-xs font-semibold text-lia-text-primary">{job.title}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-status-error" />
                      <span className="text-xs font-medium text-status-error">{job.days_open} dias aberta</span>
                    </div>
                  </div>
                  <p className="text-xs text-lia-text-tertiary mt-1">
                    {job.candidates_count || 0} candidatos • {job.screening_count || 0} em triagem • Nenhum aprovado
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* ── Detalhamento por Vaga ───────────────────────────────────────── */}
      {jobs.length > 0 && (
        <div className="bg-lia-bg-secondary/50 rounded-xl p-4 border border-lia-border-subtle">
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-lia-text-tertiary" />
            Detalhamento por Vaga
          </h3>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {jobs.map((job) => {
              const daysRemaining = getDaysRemaining(job.deadline)
              return (
                <div key={job.id} className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {job.code && (
                          <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full">
                            {job.code}
                          </span>
                        )}
                        <span className="text-xs font-semibold text-lia-text-primary truncate">{job.title}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-lia-text-secondary">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {job.candidates_count || 0} cand.
                        </span>
                        <span className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          {job.approved_count || 0} aprov.
                        </span>
                        <span className="flex items-center gap-1">
                          <Filter className="w-3 h-3" />
                          {job.screening_count || 0} triagem
                        </span>
                        {daysRemaining !== null && (
                          <span className={`flex items-center gap-1 ${daysRemaining <= 7 ? "text-status-warning font-medium" : ""}`}>
                            <Clock className="w-3 h-3" />
                            {daysRemaining > 0 ? `${daysRemaining}d restantes` : "Expirado"}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right ml-3">
                      <div className="flex items-center gap-1">
                        <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                        <span className={`text-sm font-bold ${getScoreColor(job.performance_score)}`}>
                          {job.performance_score || "--"}%
                        </span>
                      </div>
                      <span className="text-xs text-lia-text-tertiary">Score LIA</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
