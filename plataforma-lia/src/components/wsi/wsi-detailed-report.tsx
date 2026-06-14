"use client"

import { useState, useEffect, useMemo } from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  ChevronDown, ChevronUp, CheckCircle, AlertTriangle, XCircle,
  Target, Clock, Trophy, BarChart3, Star, ShieldAlert, Layers,
  Mic, Mic2, BookOpen, Zap, Info, AlertCircle, Loader2
} from"lucide-react"
import { liaApi } from"@/services/lia-api"
import type { WSIResultDetails } from"@/services/lia-api/types/wsi.types"
import { useTranslations } from "next-intl"
import { useLocale } from "next-intl"
import {
  WSI_DISPLAY_SCALE,
  WSI_DISPLAY_FORMATTED,
  getWsiVisualState,
  wsiPercent,
  wsiClassificationI18nKey,
} from "@/lib/wsi/visual"

interface WSIDetailedReportProps {
  resultId: string
  candidateName?: string
  candidateTitle?: string
  onApprove?: (resultId: string) => void
  onReject?: (resultId: string) => void
  onRequestReview?: (resultId: string) => void
}

type TabKey ="respostas" |"parecer" |"ranking"

function ReportHeader({ data, candidateName, candidateTitle }: { data: WSIResultDetails; candidateName?: string; candidateTitle?: string }) {
  const t = useTranslations('screening.wsi')
  const scores = data.scores
  const session = data.session

  // Escala WSI 0-10 (Task #512). Cutoffs canônicos em `lib/wsi/visual.ts`.
  const getClassificacao = (score: number): { label: string; color: string } => {
    const v = getWsiVisualState(score)
    return { label: t(`classification.${wsiClassificationI18nKey(v.classification)}` as never), color: v.text }
  }

  const getDecisionConfig = (decision?: string) => {
    switch (decision) {
      case"approve":
      case"approved":
        return { label: t('report.approved'), badge:"", confidence: t('report.highConfidence') }
      case"reject":
      case"rejected":
        return { label: t('report.rejected'), badge:"", confidence:"" }
      default:
        return { label: t('report.reviewNeeded'), badge:"", confidence: t('report.reviewRecommended') }
    }
  }

  const classificacao = getClassificacao(scores.overall_wsi)
  const decision = getDecisionConfig(scores.decision)

  return (
    <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-wedo-cyan/15 flex items-center justify-center">
            <Target className="w-5 h-5 text-wedo-cyan" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-lia-text-primary">
              {t('report.detailsTitle', { name: candidateName || t('report.candidate') })}
            </h1>
            {candidateTitle && (
              <p className="text-xs text-lia-text-tertiary">{candidateTitle}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Chip variant="neutral" muted className={`${decision.badge} text-micro font-medium px-1.5 py-0 rounded-full`}>
            {scores.decision ==="approve" || scores.decision ==="approved" ? (
              <><CheckCircle className="w-3.5 h-3.5 mr-1" />{decision.label}</>
            ) : (
              <><Clock className="w-3.5 h-3.5 mr-1" />{decision.label}</>
            )}
          </Chip>
          {decision.confidence && (
            <span className="text-[10px] font-medium text-lia-text-tertiary bg-lia-bg-secondary border border-lia-border-subtle px-2 py-0.5 rounded-full">
              {decision.confidence}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-6 text-sm flex-wrap">
        <div>
          <p className="text-xs text-lia-text-tertiary">{t('report.scoreWSI')}</p>
          <p className="font-bold text-lia-text-primary">
            {scores.overall_wsi.toFixed(1)}
            <span className="text-lia-text-tertiary font-normal">/{WSI_DISPLAY_FORMATTED}</span>
          </p>
        </div>
        {scores.percentile != null && (
          <div>
            <p className="text-xs text-lia-text-tertiary">{t('report.ranking')}</p>
            <p className="font-semibold text-lia-text-primary flex items-center gap-1">
              <Trophy className="w-3.5 h-3.5 text-status-warning" />
              Top {scores.percentile}%
            </p>
          </div>
        )}
        <div>
          <p className="text-xs text-lia-text-tertiary">{t('report.classification')}</p>
          <p className={`font-semibold ${classificacao.color}`}>{classificacao.label}</p>
        </div>
        {session.duration_minutes != null && (
          <div>
            <p className="text-xs text-lia-text-tertiary">{t('report.durationLabel')}</p>
            <p className="font-semibold text-lia-text-primary flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />{t('report.min', { minutes: session.duration_minutes })}
            </p>
          </div>
        )}
        <div>
          <p className="text-xs text-lia-text-tertiary">{t('report.screeningMode')}</p>
          <p className="font-semibold text-lia-text-secondary flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-lia-text-tertiary" />
            {session.screening_type ==="voice" ? t('report.voice') : t('report.text')} · {session.mode ==="compact" ? t('report.compact') : t('report.compactPlus')} · {t('report.questions', { count: data.responses.length })}
          </p>
        </div>
      </div>
    </div>
  )
}

function ScoresByDimension({ data }: { data: WSIResultDetails }) {
  const t = useTranslations('screening.wsi')
  const locale = useLocale()
  const scores = data.scores
  const session = data.session
  const dims = [
    { label: t('report.general'), value: scores.overall_wsi, pct: wsiPercent(scores.overall_wsi) },
    { label: t('report.technicalComp'), value: scores.technical_wsi, pct: wsiPercent(scores.technical_wsi) },
    { label: t('report.behavioralComp'), value: scores.behavioral_wsi, pct: wsiPercent(scores.behavioral_wsi) },
  ]

  return (
    <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
      <h2 className="text-sm font-semibold text-lia-text-secondary flex items-center gap-2 mb-4">
        <BarChart3 className="w-4 h-4" /> {t('report.scoresByDimension')}
      </h2>
      <div className="grid grid-cols-3 gap-4">
        {dims.map((s) => (
          <div key={s.label} className="text-center">
            <p className="text-3xl font-semibold text-lia-text-primary">{s.value.toFixed(1)}</p>
            <p className="text-xs text-lia-text-tertiary mb-2">{s.label} ({s.pct}%)</p>
            <div className="h-1.5 bg-lia-bg-secondary rounded-full overflow-hidden">
              <div className="h-full bg-lia-text-primary rounded-full transition-[width]" style={{ width: `${s.pct}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-3 border-t border-lia-border-subtle space-y-2">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-micro text-lia-text-tertiary bg-lia-bg-secondary px-2 py-1 rounded-full">
            {session.screening_type ==="voice" ? <Mic className="w-3 h-3" /> : <Target className="w-3 h-3" />}
            {session.screening_type ==="voice" ? t('report.voiceScreening') : t('report.textScreening')}
          </span>
          {scores.percentile != null && (
            <span className="text-xs text-lia-text-tertiary">Top {scores.percentile}%</span>
          )}
          {session.completed_at && (
            <span className="text-xs text-lia-text-tertiary">
              {new Date(session.completed_at).toLocaleDateString(locale)}
            </span>
          )}
        </div>
        {session.seniority_label && (
          <div className="flex items-center gap-1.5 text-[11px] text-lia-text-tertiary bg-lia-bg-secondary border border-lia-border-subtle rounded-lg px-3 py-2">
            <BarChart3 className="w-3 h-3 text-lia-text-tertiary shrink-0" />
            <span>
              {t('report.forSeniority', { seniority: session.seniority_label })}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function ResponseCard({ response, index, isOpen, onToggle }: {
  response: WSIResultDetails["responses"][0]
  index: number
  isOpen: boolean
  onToggle: () => void
}) {
  const t = useTranslations('screening.wsi')

  const gapConfigMap = {
    ok: { label: t('report.gapAligned'), icon: CheckCircle, color:"text-status-success", bg:"bg-status-success/10", border:"border-status-success/30" },
    aligned: { label: t('report.gapAligned'), icon: CheckCircle, color:"text-status-success", bg:"bg-status-success/10", border:"border-status-success/30" },
    acima: { label: t('report.gapAboveExpected'), icon: Star, color:"text-wedo-cyan-text", bg:"bg-wedo-cyan/10", border:"border-wedo-cyan/30" },
    above: { label: t('report.gapAboveExpected'), icon: Star, color:"text-wedo-cyan-text", bg:"bg-wedo-cyan/10", border:"border-wedo-cyan/30" },
    gap: { label: t('report.gapIdentified'), icon: AlertTriangle, color:"text-status-warning", bg:"bg-status-warning/10", border:"border-status-warning/30" },
    below: { label: t('report.gapIdentified'), icon: AlertTriangle, color:"text-status-warning", bg:"bg-status-warning/10", border:"border-status-warning/30" },
    critical_gap: { label: t('report.gapCritical'), icon: XCircle, color:"text-status-error", bg:"bg-status-error/10", border:"border-status-error/30" },
  }

  const severidadeConfig = {
    alta: { label: t('report.severityHigh'), color:"text-status-error", bg:"bg-status-error/10", border:"border-status-error/30", dot:"bg-status-error" },
    media: { label: t('report.severityMedium'), color:"text-status-warning", bg:"bg-status-warning/10", border:"border-status-warning/30", dot:"bg-status-warning" },
    baixa: { label: t('report.severityLow'), color:"text-lia-text-tertiary", bg:"bg-lia-bg-secondary", border:"border-lia-border-subtle", dot:"bg-lia-text-tertiary" },
  }

  const dreyfusLabel = (n?: number) => {
    if (n == null) return"—"
    const key = String(n) as "1" | "2" | "3" | "4" | "5"
    return t.has(`report.dreyfusLevels.${key}`) ? t(`report.dreyfusLevels.${key}`) : String(n)
  }

  const bloomLabel = (n?: number) => {
    if (n == null) return"—"
    const key = String(n) as "1" | "2" | "3" | "4" | "5"
    return t.has(`report.bloomLevels.${key}`) ? t(`report.bloomLevels.${key}`) : String(n)
  }

  const starComponents = [
    { key:"S", label: t('report.situation'), desc: t('report.situationDesc') },
    { key:"T", label: t('report.task'), desc: t('report.taskDesc') },
    { key:"A", label: t('report.action'), desc: t('report.actionDesc') },
    { key:"R", label: t('report.result'), desc: t('report.resultDesc') },
  ]

  const gapKey = (response.gap_status ||"ok") as keyof typeof gapConfigMap
  const gap = gapConfigMap[gapKey] || gapConfigMap.ok
  const GapIcon = gap.icon
  const starData = (response.star || response.scores.star || {}) as Record<string, boolean>
  // Escala WSI 0-10 (Task #512).
  const scoreColor = getWsiVisualState(response.scores.final_score).text

  return (
    <div>
      <button
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-bg-secondary transition-colors text-left"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-lia-text-primary">{response.competency}</span>
          <span className="text-[10px] bg-lia-bg-secondary text-lia-text-tertiary px-2 py-0.5 rounded-full">
            {response.question.framework}
          </span>
          {response.is_critical && (
            <span className="flex items-center gap-0.5 text-[10px] font-bold text-status-error bg-status-error/10 border border-status-error/30 px-1.5 py-0.5 rounded-full">
              <ShieldAlert className="w-2.5 h-2.5" /> {t('report.critical')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold ${scoreColor}`}>
            {response.scores.final_score.toFixed(1)}/{WSI_DISPLAY_FORMATTED}
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" /> : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-4 pb-4 space-y-4 bg-lia-bg-secondary/50">
          <div className="space-y-2">
            <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3">
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-1">{t('report.questionLabel')}</p>
              <p className="text-xs text-lia-text-secondary leading-relaxed">{response.question.text}</p>
            </div>
            <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3">
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-1">{t('report.candidateResponse')}</p>
              <p className="text-xs text-lia-text-primary leading-relaxed">{response.response_text}</p>
            </div>
          </div>

          {Object.keys(starData).length > 0 && (
            <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3">
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-2">{t('report.responseQuality')}</p>
              <div className="flex items-center gap-2 flex-wrap">
                {starComponents.map(({ key, label, desc }) => {
                  const present = !!starData[key]
                  return (
                    <div
                      key={key}
                      title={desc}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                        present
                          ?"bg-status-success/10 border-status-success/30 text-status-success"
                          :"bg-lia-bg-secondary border-lia-border-subtle text-lia-text-tertiary"
                      }`}
                    >
                      {present
                        ? <CheckCircle className="w-3 h-3" />
                        : <span className="w-3 h-3 flex items-center justify-center text-lia-text-tertiary font-bold text-[10px]">–</span>}
                      <span>{label}</span>
                    </div>
                  )
                })}
                {!starData.R && (
                  <span className="text-[10px] text-status-warning bg-status-warning/10 border border-status-warning/30 px-2 py-0.5 rounded-full">
                    {t('report.resultNotEvidenced')}
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-4 gap-2">
            {[
              { label: t('report.selfDeclaration'), value: response.scores.autodeclaration?.toFixed(1) ??"—" },
              { label: t('report.context'), value: response.scores.context?.toFixed(1) ??"—" },
              { label: t('report.bloom'), value: bloomLabel(response.scores.bloom_level), sub: response.scores.bloom_level ? t('report.level', { level: response.scores.bloom_level }) : undefined },
              { label: t('report.dreyfus'), value: dreyfusLabel(response.scores.dreyfus_level), sub: response.scores.dreyfus_level ? t('report.level', { level: response.scores.dreyfus_level }) : undefined },
            ].map((s) => (
              <div key={s.label} className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-2 text-center">
                <p className="text-[9px] text-lia-text-tertiary mb-1">{s.label}</p>
                <p className="text-sm font-bold text-lia-text-primary">{s.value}</p>
              </div>
            ))}
          </div>

          <div className={`flex items-center justify-between rounded-lg border px-3 py-2.5 ${gap.bg} ${gap.border}`}>
            <div className="flex items-center gap-2">
              <GapIcon className={`w-3.5 h-3.5 ${gap.color}`} />
              <span className={`text-xs font-medium ${gap.color}`}>{t('report.expectedByJob')}</span>
            </div>
            <div className="flex items-center gap-4 text-xs">
              {response.bloom_expected != null && (
                <div className="text-right">
                  <p className="text-[9px] text-lia-text-tertiary">{t('report.bloom')}</p>
                  <p className={`font-semibold ${gap.color}`}>{bloomLabel(response.bloom_expected)}</p>
                </div>
              )}
              <span className={`text-micro font-medium px-2 py-0.5 rounded-full ${gap.bg} ${gap.color} border ${gap.border}`}>
                {gap.label}
              </span>
            </div>
          </div>

          {response.evidences.length > 0 && (
            <div>
              <p className="text-[10px] text-lia-text-tertiary uppercase tracking-wide mb-2">{t('report.evidences')}</p>
              <div className="flex flex-wrap gap-2">
                {response.evidences.map((e, j) => (
                  <span key={j} className="flex items-center gap-1 text-[11px] bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle text-lia-text-secondary px-2 py-1 rounded-full">
                    <CheckCircle className="w-3 h-3 text-status-success" /> {e}
                  </span>
                ))}
              </div>
              <p className="text-xs text-lia-text-tertiary italic mt-2">{response.justification}</p>
            </div>
          )}

          {response.red_flags.length > 0 && (
            <div>
              <p className="text-[10px] text-status-error uppercase tracking-wide mb-2">{t('report.redFlags')}</p>
              <div className="flex flex-wrap gap-2">
                {response.red_flags.map((rf, j) => (
                  <span key={j} className="flex items-center gap-1 text-[11px] bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1 rounded-full">
                    <AlertTriangle className="w-3 h-3" /> {rf}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TabRespostas({ data }: { data: WSIResultDetails }) {
  const t = useTranslations('screening.wsi')
  const [expanded, setExpanded] = useState<number | null>(0)

  return (
    <div className="space-y-4">
      <ScoresByDimension data={data} />

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl shadow-lia-sm overflow-hidden">
        <div className="flex items-center justify-between p-4">
          <h2 className="text-sm font-semibold text-lia-text-secondary">{t('report.responsesByCompetency', { count: data.responses.length })}</h2>
          <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
        </div>

        <div className="divide-y divide-lia-border-subtle">
          {data.responses.map((r, i) => (
            <ResponseCard
              key={i}
              response={r}
              index={i}
              isOpen={expanded === i}
              onToggle={() => setExpanded(expanded === i ? null : i)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function TabParecer({ data }: { data: WSIResultDetails }) {
  const t = useTranslations('screening.wsi')
  const report = data.report
  const feedback = data.feedback
  const isApproved = data.scores.decision ==="approve" || data.scores.decision ==="approved"
  const isPending = !isApproved && data.scores.decision !=="reject" && data.scores.decision !=="rejected"

  const strengths = (report?.technical_analysis as { strengths?: string[] })?.strengths || feedback?.technical_strengths || []
  const gaps = (report?.technical_analysis as { gaps?: { text: string; severity: string }[] })?.gaps || []
  const concerns = (report?.recommendation as { concerns?: string[] })?.concerns || []

  const severidadeConfig = {
    alta: { label: t('report.severityHigh'), color:"text-status-error", bg:"bg-status-error/10", border:"border-status-error/30", dot:"bg-status-error" },
    media: { label: t('report.severityMedium'), color:"text-status-warning", bg:"bg-status-warning/10", border:"border-status-warning/30", dot:"bg-status-warning" },
    baixa: { label: t('report.severityLow'), color:"text-lia-text-tertiary", bg:"bg-lia-bg-secondary", border:"border-lia-border-subtle", dot:"bg-lia-text-tertiary" },
  }

  return (
    <div className="space-y-4">
      {report?.executive_summary && (
        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
          <h2 className="text-sm font-semibold text-lia-text-secondary mb-3 flex items-center gap-2">
            <Star className="w-4 h-4 text-status-warning" /> {t('report.executiveSummary')}
          </h2>
          <p className="text-sm text-lia-text-secondary leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {concerns.length > 0 && isPending && (
        <div className="bg-status-warning/10 border border-status-warning/30 rounded-xl p-4 shadow-lia-sm">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-status-warning" />
            <h2 className="text-sm font-semibold text-status-warning">{t('report.attentionPoints')}</h2>
            <span className="ml-auto text-[10px]  px-2 py-0.5 rounded-full font-medium border border-status-warning/30">
              {t('report.humanReviewRecommended')}
            </span>
          </div>
          <ul className="space-y-1.5">
            {concerns.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                <AlertTriangle className="w-3.5 h-3.5 text-status-warning mt-0.5 shrink-0" /> {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm space-y-4">
        <h2 className="text-sm font-semibold text-lia-text-secondary">{t('report.technicalAnalysis')}</h2>

        {strengths.length > 0 && (
          <div>
            <p className="text-xs font-medium text-status-success mb-2 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> {t('report.strengths')}
            </p>
            <ul className="space-y-1.5">
              {strengths.map((s: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-xs text-lia-text-secondary">
                  <CheckCircle className="w-3.5 h-3.5 text-status-success mt-0.5 shrink-0" /> {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {gaps.length > 0 && (
          <div>
            <p className="text-xs font-medium text-lia-text-secondary mb-2 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-status-warning" /> {t('report.identifiedGaps')}
            </p>
            <ul className="space-y-2">
              {gaps.map((g: { text: string; severity: string }, i: number) => {
                const sev = severidadeConfig[(g.severity ||"baixa") as keyof typeof severidadeConfig] || severidadeConfig.baixa
                return (
                  <li key={i} className={`flex items-start gap-2.5 text-xs text-lia-text-secondary rounded-lg border px-3 py-2 ${sev.bg} ${sev.border}`}>
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sev.dot}`} />
                    <span className="flex-1">{g.text}</span>
                    <span className={`text-[9px] font-bold tracking-wider shrink-0 ${sev.color}`}>{sev.label}</span>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </div>

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm">
        <h2 className="text-sm font-semibold text-lia-text-secondary mb-3">{t('report.recommendation')}</h2>
        {isApproved ? (
          <div className="bg-status-success/10 border border-status-success/30 rounded-lg p-4">
            <p className="text-sm font-semibold text-status-success mb-1">{t('report.stronglyRecommended')}</p>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {(report?.recommendation as { text?: string })?.text || t('report.defaultApprovalText')}
            </p>
          </div>
        ) : (
          <div className="bg-status-warning/10 border border-status-warning/30 rounded-lg p-4">
            <p className="text-sm font-semibold text-status-warning mb-1">{t('report.humanReviewTitle')}</p>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {(report?.recommendation as { text?: string })?.text || t('report.defaultReviewText')}
            </p>
          </div>
        )}
      </div>

      {feedback && (
        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-5 shadow-lia-sm space-y-4">
          <h2 className="text-sm font-semibold text-lia-text-secondary flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-wedo-cyan-text" /> {t('report.candidateFeedback')}
          </h2>
          {feedback.main_message && (
            <p className="text-xs text-lia-text-secondary leading-relaxed">{feedback.main_message}</p>
          )}
          {feedback.technical_strengths.length > 0 && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1.5">{t('report.technicalStrengths')}</p>
              {feedback.technical_strengths.map((s, i) => (
                <p key={i} className="flex items-center gap-1.5 text-xs text-lia-text-secondary mb-1">
                  <CheckCircle className="w-3 h-3 text-status-success shrink-0" /> {s}
                </p>
              ))}
            </div>
          )}
          {feedback.development_opportunities.length > 0 && (
            <div>
              <p className="text-xs font-medium text-lia-text-secondary mb-1.5">{t('report.developmentOpportunities')}</p>
              {feedback.development_opportunities.map((s, i) => (
                <p key={i} className="flex items-center gap-1.5 text-xs text-lia-text-secondary mb-1">
                  <BookOpen className="w-3 h-3 text-wedo-cyan-text shrink-0" /> {s}
                </p>
              ))}
            </div>
          )}
          {feedback.personalized_tip && (
            <div className="bg-wedo-cyan/10 border border-wedo-cyan/30 rounded-lg p-3">
              <p className="text-[10px] text-wedo-cyan-text font-medium mb-0.5">{t('report.personalizedTip')}</p>
              <p className="text-xs text-lia-text-secondary">{feedback.personalized_tip}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TabRanking() {
  const t = useTranslations('screening.wsi')
  return (
    <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-8 shadow-lia-sm text-center">
      <BarChart3 className="w-10 h-10 text-lia-text-tertiary mx-auto mb-3" />
      <h3 className="text-sm font-semibold text-lia-text-secondary mb-1">{t('report.rankingAndComparison')}</h3>
      <p className="text-xs text-lia-text-tertiary">
        {t('report.rankingDescription')}
      </p>
    </div>
  )
}

export function WSIDetailedReport({
  resultId,
  candidateName,
  candidateTitle,
  onApprove,
  onReject,
  onRequestReview,
}: WSIDetailedReportProps) {
  const t = useTranslations('screening.wsi')
  const [activeTab, setActiveTab] = useState<TabKey>("respostas")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<WSIResultDetails | null>(null)

  const TABS: { key: TabKey; label: string }[] = [
    { key:"respostas", label: t('report.tabs.responses') },
    { key:"parecer", label: t('report.tabs.opinion') },
    { key:"ranking", label: t('report.tabs.ranking') },
  ]

   
  useEffect(() => {
    loadDetails()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resultId])

  const loadDetails = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await liaApi.wsiGetResultDetails(resultId)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('report.errorLoadingDetails'))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        <span className="ml-2 text-sm text-lia-text-tertiary">{t('report.loadingReport')}</span>
      </div>
    )
  }

  if (error || !data) {
    return (
      <Card className="border-status-error/30">
        <CardContent className="py-6 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-status-error" />
          <span className="ml-2 text-sm text-status-error">{error || t('report.dataNotFound')}</span>
        </CardContent>
      </Card>
    )
  }

  const isApproved = data.scores.decision ==="approve" || data.scores.decision ==="approved"
  const isRejected = data.scores.decision ==="reject" || data.scores.decision ==="rejected"

  return (
    <div className="max-w-[820px] mx-auto space-y-4">
      <ReportHeader data={data} candidateName={candidateName} candidateTitle={candidateTitle} />

      <div className="flex gap-1 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`flex-1 py-2 text-xs font-medium rounded-md transition-colors ${
              activeTab === tab.key
                ?"bg-lia-text-primary text-lia-bg-primary"
                :"text-lia-text-tertiary hover:bg-lia-bg-secondary"
            }`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab ==="respostas" && <TabRespostas data={data} />}
      {activeTab ==="parecer" && <TabParecer data={data} />}
      {activeTab ==="ranking" && <TabRanking />}

      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle rounded-xl p-4 flex items-center justify-between shadow-lia-sm">
        <span className="text-xs text-lia-text-tertiary">{t('report.recruiterDecision')}</span>
        <div className="flex gap-2">
          {onReject && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs border-status-error/30 text-status-error hover:bg-status-error/10"
              onClick={() => onReject(resultId)}
            >
              <XCircle className="w-3.5 h-3.5 mr-1" /> {t('report.reject')}
            </Button>
          )}
          {onRequestReview && !isApproved && !isRejected && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs border-status-warning/30 text-status-warning hover:bg-status-warning/10"
              onClick={() => onRequestReview(resultId)}
            >
              <AlertTriangle className="w-3.5 h-3.5 mr-1" /> {t('report.requestReview')}
            </Button>
          )}
          {onApprove && (
            <Button
              size="sm"
              className="text-xs bg-lia-text-primary text-lia-bg-primary hover:bg-lia-text-secondary"
              onClick={() => onApprove(resultId)}
            >
              <CheckCircle className="w-3.5 h-3.5 mr-1" /> {t('report.approveForInterview')}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
