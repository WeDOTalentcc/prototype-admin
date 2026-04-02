"use client"

import { useState, useEffect } from "react"
import { Progress } from "@/components/ui/progress"
import {
  X, Brain, MessageSquare, Target, TrendingUp, Award, AlertCircle,
  CheckCircle, Clock, FileText, BarChart3, User,
  ChevronDown, ChevronUp, ThumbsUp,
  ThumbsDown, Mic, Phone,
  Code, BookOpen, Zap, Trophy,
  Download, Share2, Loader2, Star,
  ShieldAlert, AlertTriangle, Layers, Info, Mic2, Copy
} from "lucide-react"
import { liaApi, WSIResultDetails, WSICandidateRanking, WSIVacancyRanking } from "@/services/lia-api"
import { cn } from "@/lib/utils"
import type { Candidate } from "@/components/pages/candidates/types"
import { TriagemScoresPanel, TriagemComparativoTab } from "./triagem-details"
import { TriagemSummaryBar } from "./triagem-details/triagem-summary-bar"

interface TriagemDetailsModalProps {
  candidate: Candidate
  isOpen: boolean
  onClose: () => void
  jobVacancyId?: string
  onApprove?: (candidate: Candidate) => void
  onReject?: (candidate: Candidate) => void
}

const WSI_CLASSIFICATION_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  excepcional:     { bg: 'var(--status-success-bg)',  text: 'var(--status-success)', label: 'Excepcional' },
  excelente:       { bg: 'var(--status-success-bg)',  text: 'var(--status-success)', label: 'Excelente' },
  alto:            { bg: 'var(--lia-bg-tertiary)',            text: 'var(--lia-text-primary)',        label: 'Alto' },
  medio:           { bg: 'var(--status-warning-bg)',  text: 'var(--status-warning)',  label: 'Médio' },
  abaixo_da_media: { bg: 'var(--status-error-bg)',    text: 'var(--status-error)',    label: 'Abaixo da média' },
  regular:         { bg: 'var(--status-error-bg)',    text: 'var(--status-error)',    label: 'Regular / Baixo' },
}

const getClassificationColor = (classification: string) =>
  WSI_CLASSIFICATION_COLORS[classification] ?? { bg: 'var(--wedo-cyan-bg-12)', text: 'var(--lia-text-secondary)', label: classification }

const getClassificationLabel = (classification: string) =>
  WSI_CLASSIFICATION_COLORS[classification]?.label ?? classification

const getDecisionDisplay = (decision?: string) => {
  // Normalizar: API retorna APROVADO/EM_AVALIACAO/REPROVADO; legado usa aprovado/aguardando/nao_aprovado
  const normalized = (decision ?? '').toUpperCase().replace('NAO_APROVADO', 'REPROVADO').replace('AGUARDANDO', 'EM_AVALIACAO')
  switch (normalized) {
    case 'APROVADO':
    case 'aprovado':
      return { label: 'Aprovado', icon: ThumbsUp, color: 'var(--status-success)', bg: 'var(--status-success-bg)' }
    case 'EM_AVALIACAO':
    case 'aguardando':
      return { label: 'Em Avaliação', icon: Clock, color: 'var(--status-warning)', bg: 'var(--status-warning-bg)' }
    case 'REPROVADO':
    case 'nao_aprovado':
      return { label: 'Não Aprovado', icon: ThumbsDown, color: 'var(--status-error)', bg: 'var(--status-error-bg)' }
    default: return { label: 'Pendente', icon: Clock, color: 'var(--lia-text-tertiary)', bg: 'var(--lia-bg-secondary)' }
  }
}

const wsiToPercent = (score: number) => Math.round((score / 5) * 100)

const bloomLabel = (n: number) =>
  (["", "Recordar", "Compreender", "Aplicar", "Analisar", "Avaliar", "Criar"] as const)[n] ?? `Nível ${n}`

const dreyfusLabel = (n: number) =>
  (["", "Iniciante", "Básico", "Intermediário", "Avançado", "Especialista"] as const)[n] ?? `Nível ${n}`

const getScoreColor = (score: number) =>
  score >= 4.5 ? "text-status-success" :
  score >= 4.0 ? "text-status-success" :
  score >= 3.5 ? "text-wedo-cyan-dark" :
  score >= 3.0 ? "text-status-warning" :
  score >= 2.25 ? "text-wedo-orange" :
  "text-status-error"

const getScoreColor3Tier = (score: number) =>
  score >= 4.5 ? "text-status-success" :
  score >= 3.5 ? "text-status-warning" :
  "text-status-error"

const gapConfig = {
  ok:    { label: "Alinhado",          icon: CheckCircle,   color: "text-status-success", bg: "bg-status-success/10", border: "border-status-success/30" },
  acima: { label: "Acima do esperado", icon: Star,          color: "text-wedo-cyan-dark",  bg: "bg-wedo-cyan/10",     border: "border-wedo-cyan/30"       },
  gap:   { label: "Gap identificado",  icon: AlertTriangle, color: "text-status-warning",  bg: "bg-status-warning/10",border: "border-status-warning/30"  },
}

const starComponents = [
  { key: "S" as const, label: "Situação", desc: "Contexto descrito" },
  { key: "T" as const, label: "Tarefa", desc: "Objetivo claro" },
  { key: "A" as const, label: "Ação", desc: "O que foi feito" },
  { key: "R" as const, label: "Resultado", desc: "Impacto mensurável" },
]

const sevConfig = {
  alta:  { label: "ALTA",  color: "text-status-error",   bg: "bg-status-error/10",   border: "border-status-error/30",   dot: "bg-status-error"   },
  media: { label: "MÉDIA", color: "text-status-warning",  bg: "bg-status-warning/10", border: "border-status-warning/30", dot: "bg-status-warning" },
  baixa: { label: "BAIXA", color: "lia-text-secondary",        bg: "bg-lia-bg-secondary",           border: "border-lia-border-subtle",          dot: "bg-lia-border-medium"       },
}

function DreyfusRow({
  dreyfusEsperado, dreyfusDemonstrado, senioridade
}: { dreyfusEsperado: number; dreyfusDemonstrado: number; senioridade?: string }) {
  const delta = dreyfusDemonstrado - dreyfusEsperado
  const isCritical = delta <= -2
  const isAtencao  = delta === -1
  const isAcima    = delta > 0
  const color = isCritical ? "text-status-error" : isAtencao ? "text-status-warning" : isAcima ? "text-wedo-cyan-dark" : "text-status-success"
  const bg    = isCritical ? "bg-status-error/10 border-status-error/30" : isAtencao ? "bg-status-warning/10 border-status-warning/30" : isAcima ? "bg-wedo-cyan/10 border-wedo-cyan/30" : "bg-status-success/10 border-status-success/30"
  const lbl   = isCritical ? "Gap crítico" : isAtencao ? "Atenção" : isAcima ? "Acima" : "Alinhado"
  return (
    <div className={`flex items-center justify-between text-micro rounded-md border px-2.5 py-1.5 mt-1 ${bg}`}>
      <span className="lia-text-secondary">Maturidade comportamental</span>
      <div className="flex items-center gap-2">
        <span className="lia-text-secondary">
          Esperado{senioridade ? ` para ${senioridade}` : ""}: <span className="font-medium text-lia-text-secondary">{dreyfusLabel(dreyfusEsperado)}</span>
        </span>
        <span className="lia-text-muted">·</span>
        <span className="lia-text-secondary">
          Demonstrado: <span className={`font-semibold ${color}`}>{dreyfusLabel(dreyfusDemonstrado)}</span>
        </span>
        <span className={`text-micro font-bold px-1.5 py-0.5 rounded-full border ${bg} ${color}`}>{lbl}</span>
      </div>
    </div>
  )
}

const getFrameworkLabel = (framework: string) => {
  switch (framework) {
    case 'CBI': return 'Competency-Based'
    case 'Bloom': return "Bloom's Taxonomy"
    case 'Dreyfus': return 'Dreyfus Model'
    case 'BigFive': return 'Big Five (OCEAN)'
    default: return framework
  }
}

interface F11ReportData {
  seniority?: string
  seniority_weights?: { technical: number; behavioral: number }
  mode?: string
  question_count?: number
  cbi_questions?: Array<{ severity?: string; question?: string; texto?: string; focus?: string; foco?: string }>
  response_analyses?: Array<{ feedback?: string }>
  [key: string]: unknown
}

export function TriagemDetailsModal({
  candidate,
  isOpen,
  onClose,
  jobVacancyId,
  onApprove,
  onReject
}: TriagemDetailsModalProps) {
  const [activeTab, setActiveTab] = useState<'triagem' | 'parecer' | 'comparativo'>('triagem')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['responses']))
  const [loading, setLoading] = useState(true)
  const [details, setDetails] = useState<WSIResultDetails | null>(null)
  const [ranking, setRanking] = useState<WSICandidateRanking | null>(null)
  const [vacancyRanking, setVacancyRanking] = useState<WSIVacancyRanking | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [feedbackStatus, setFeedbackStatus] = useState<Record<string, unknown> | null>(null)
  const [sendingFeedback, setSendingFeedback] = useState(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState(false)
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [confirmReject, setConfirmReject] = useState(false)
  const [f11Report, setF11Report] = useState<F11ReportData | null>(null)
  const [bigFiveHint, setBigFiveHint] = useState<string | null>(null)
  const [copiedFeedback, setCopiedFeedback] = useState(false)

  useEffect(() => {
    if (isOpen && candidate?.id) {
      loadData()
    }
  }, [isOpen, candidate?.id])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      const resultsData = await liaApi.wsiGetCandidateResults(candidate.id, 1)

      if (resultsData.total_screenings === 0) {
        setError('Nenhuma triagem WSI encontrada para este candidato.')
        return
      }

      const latestResult = resultsData.results[0]
      const detailsData = await liaApi.wsiGetResultDetails(latestResult.result_id)
      setDetails(detailsData)

      try {
        const fbStatus = await liaApi.wsiGetFeedbackStatus(latestResult.result_id)
        setFeedbackStatus(fbStatus)
      } catch (e) {
      }

      const vacId = jobVacancyId || detailsData.job_vacancy_id
      if (vacId) {
        try {
          const [rankData, vacRankData] = await Promise.all([
            liaApi.wsiGetCandidateRanking(candidate.id, vacId),
            liaApi.wsiGetVacancyRanking(vacId)
          ])
          setRanking(rankData)
          setVacancyRanking(vacRankData)
        } catch (e) {
        }
      }

      const sessionId = detailsData.session?.session_id || detailsData.session_id
      if (sessionId) {
        try {
          const f11 = await fetch(`/api/backend-proxy/wsi/f11-report/${sessionId}`)
          if (f11.ok) setF11Report(await f11.json())
        } catch (e) {
        }
      }
    } catch (err) {
      setError('Erro ao carregar dados da triagem.')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const handleSendFeedback = async () => {
    if (!details) return
    const resultId = details.result_id || (details as WSIResultDetails & { id?: string }).id
    if (!resultId) return
    setSendingFeedback(true)
    setFeedbackError(null)
    try {
      const result = await liaApi.wsiTriggerFeedback(resultId)
      setFeedbackSuccess(true)
      setFeedbackStatus({ ...feedbackStatus, feedback_sent: true })
      setTimeout(() => setFeedbackSuccess(false), 5000)
    } catch (err: unknown) {
      setFeedbackError(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao enviar feedback')
    } finally {
      setSendingFeedback(false)
    }
  }

  const decision = (details?.scores as any)?.decision || (details as any)?.decision
  const decisionNormalized = (decision ?? '').toUpperCase()
  const isPendingDecision = !decision || decisionNormalized === 'AGUARDANDO' || decisionNormalized === 'EM_AVALIACAO'
  // canTriggerFeedback: disponível para todos os estados de decisão quando há dados de triagem
  const canTriggerFeedback = !!details && !!details.scores
  const feedbackAlreadySent = feedbackStatus?.feedback_sent === true

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="w-full max-w-3xl p-8 flex flex-col items-center gap-3 rounded-md bg-lia-bg-primary"  role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-wedo-cyan" />
          <p className="text-sm lia-text-secondary">Carregando dados da triagem...</p>
        </div>
      </div>
    )
  }

  if (error || !details) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay">
        <div className="w-full max-w-3xl p-8 flex flex-col items-center gap-3 rounded-md bg-lia-bg-primary" >
          <AlertCircle className="w-8 h-8 lia-text-secondary" />
          <p className="text-sm lia-text-secondary">{error || 'Dados não disponíveis.'}</p>
          <button onClick={onClose} className="mt-2 px-4 py-2 text-sm rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover">Fechar</button>
        </div>
      </div>
    )
  }

  const { scores, session: sessionInfo, responses, report, feedback } = details
  const classColors = getClassificationColor(scores.classification)
  const decisionDisplay = getDecisionDisplay(feedback?.decision)
  const DecisionIcon = decisionDisplay.icon

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay">
      <div className="w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col rounded-md border border-lia-border-subtle bg-lia-bg-secondary">
        <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/[0.12]">
              <Brain className="w-4 h-4 text-wedo-cyan" />
            </div>
            <div>
              <h2 className="text-base-ui font-semibold text-lia-text-primary">
                Detalhes da Triagem WSI - {candidate.name}
              </h2>
              <p className="text-xs lia-text-secondary">
                {candidate.role || candidate.current_title} {candidate.location ? `• ${candidate.location}` : ''}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => {
                if (!details) return
                const printWindow = window.open('', '_blank')
                if (!printWindow) return
                const respHtml = details.responses.map((resp, idx) => `
                  <div style="margin-bottom:16px;padding:12px;border:1px solid #F3F4F6;border-radius:8px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                      <strong>${resp.competency}</strong>
                      <span style="font-weight:bold;color:${resp.scores.final_score >= 4 ? '#166534' : resp.scores.final_score >= 3 ? '#854D0E' : '#991B1B'}">${resp.scores.final_score.toFixed(1)}/5.0</span>
                    </div>
                    <p style="color:var(--lia-text-secondary);font-size:12px;margin-bottom:4px;"><strong>Pergunta:</strong> ${resp.question.text}</p>
                    <p style="font-size:12px;margin-bottom:4px;"><strong>Resposta:</strong> ${resp.response_text}</p>
                    <p style="font-size:11px;color:var(--lia-text-secondary);font-style:italic;">${resp.justification || ''}</p>
                  </div>
                `).join('')
                printWindow.document.write(`
                  <html><head><title>Triagem WSI - ${candidate.name}</title>
                  <style>body{font-family:'Open Sans',sans-serif;padding:32px;color:var(--lia-text-primary);max-width:800px;margin:0 auto;}
                  h1{font-size:20px;margin-bottom:4px;}h2{font-size:16px;margin-top:24px;margin-bottom:12px;color:var(--lia-text-primary);}
                  .scores{display:flex;gap:24px;margin:16px 0;}.score-box{text-align:center;padding:12px 20px;border:1px solid #F3F4F6;border-radius:8px;}
                  .score-box .value{font-size:24px;font-weight:bold;}.score-box .label{font-size:11px;color:var(--lia-text-secondary);}
                  .meta{font-size:12px;color:var(--lia-text-secondary);margin-bottom:16px;}
                  @media print{body{padding:16px;}}</style></head><body>
                  <h1>Triagem WSI - ${candidate.name}</h1>
                  <p class="meta">${candidate.role || candidate.current_title || ''} ${candidate.location ? '• ' + candidate.location : ''}</p>
                  <div class="scores">
                    <div class="score-box"><div class="value">${details.scores.overall_wsi.toFixed(1)}</div><div class="label">Score Geral</div></div>
                    <div class="score-box"><div class="value">${details.scores.technical_wsi.toFixed(1)}</div><div class="label">Comp. Técnicas</div></div>
                    <div class="score-box"><div class="value">${details.scores.behavioral_wsi.toFixed(1)}</div><div class="label">Comp. Comportamentais</div></div>
                  </div>
                  <p style="font-size:13px;"><strong>Classificação:</strong> ${getClassificationLabel(details.scores.classification)}
                  ${ranking?.ranked ? ` | <strong>Ranking:</strong> #${ranking.rank} de ${ranking.total}` : ''}</p>
                  <h2>Respostas por Competência</h2>${respHtml}
                  ${details.report?.executive_summary ? '<h2>Sumário Executivo</h2><p style="font-size:13px;">' + details.report.executive_summary + '</p>' : ''}
                  </body></html>
                `)
                printWindow.document.close()
                printWindow.print()
              }}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium transition-colors motion-reduce:transition-none hover:bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle bg-lia-bg-secondary rounded-md"
            >
              <Download className="w-3 h-3" />
              Exportar
            </button>
            <button onClick={onClose} className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover rounded-full lia-text-secondary">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Score summary bar + tab nav — extracted to TriagemSummaryBar */}
        <TriagemSummaryBar
          scores={scores}
          sessionInfo={sessionInfo}
          ranking={ranking}
          classColors={classColors}
          decisionDisplay={decisionDisplay}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          getClassificationLabel={getClassificationLabel}
          getScoreColor={getScoreColor}
        />

        <div className="flex-1 overflow-y-auto p-4 bg-lia-bg-secondary">
          {activeTab === 'triagem' && (
            <div className="space-y-4">
              <TriagemScoresPanel
                scores={scores}
                sessionInfo={sessionInfo}
                f11Report={f11Report}
                details={details}
              />

              <div className="border border-lia-border-subtle bg-lia-bg-secondary rounded-lg overflow-hidden">
                <div className={cn("cursor-pointer p-3 flex items-center justify-between hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none", expandedSections.has('responses') && "border-b border-lia-border-subtle")} onClick={() => toggleSection('responses')}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
                    <MessageSquare className="w-4 h-4 text-lia-text-secondary" />
                    Respostas por Competência ({responses.length})
                  </h3>
                  {expandedSections.has('responses') ? <ChevronUp className="w-4 h-4 lia-text-secondary" /> : <ChevronDown className="w-4 h-4 lia-text-secondary" />}
                </div>
                {expandedSections.has('responses') && (() => {
                  const f11Analyses = f11Report?.response_analyses || []
                  const f11Map: Record<string, { competency: string; score?: number; analysis?: string }> = {}
                  // @ts-ignore
                  f11Analyses.forEach((a: { competency?: string; score?: number; analysis?: string }) => { if (a.competency) f11Map[a.competency] = a as { competency: string; score?: number; analysis?: string } })

                  return (
                  <div className="divide-y divide-lia-border-subtle">
                    {responses.map((resp, idx) => {
                      const f11 = (f11Map[resp.competency] || {}) as any
                      const starData = f11.star || { S: false, T: false, A: false, R: false }
                      const gapStatus = (f11.gap_status || 'ok') as keyof typeof gapConfig
                      const gap = gapConfig[gapStatus] || gapConfig.ok
                      const GapIcon = gap.icon
                  // @ts-ignore
                      const isCritical = f11.is_critical || resp.question?.is_critical || false
                      const bloomExpected = f11.bloom_expected || resp.scores.bloom_level || 3
                      const bloomExpLabel = f11.bloom_expected_label || bloomLabel(bloomExpected)
                      const dreyfusExpected = f11.dreyfus_expected || resp.scores.dreyfus_level || 3
                      const dreyfusExpLabel = f11.dreyfus_expected_label || dreyfusLabel(dreyfusExpected)
                      const demonstrated_bloom = f11.bloom_level || resp.scores.bloom_level || 3
                      const demonstrated_dreyfus = f11.dreyfus_level || resp.scores.dreyfus_level || 3
                      const finalScore = f11.final_score ?? resp.scores.final_score
                      const isOpen = expandedSections.has(`resp-${idx}`)
                      return (
                        <div key={`resp-${idx}`}>
                          <button
                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none text-left"
                            onClick={() => toggleSection(`resp-${idx}`)}
                          >
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-sm font-medium text-lia-text-primary">{resp.competency}</span>
                              <span className="text-micro bg-lia-bg-tertiary lia-text-secondary px-2 py-0.5 rounded-full">{getFrameworkLabel(resp.question?.framework || f11.framework || '')}</span>
                              {isCritical && (
                                <span className="flex items-center gap-0.5 text-micro font-bold text-status-error bg-status-error/10 border border-status-error/30 px-1.5 py-0.5 rounded-full">
                                  <ShieldAlert className="w-2.5 h-2.5" /> Crítica
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-bold ${getScoreColor3Tier(finalScore)}`}>
                                {finalScore.toFixed(1)}/5.0
                              </span>
                              {isOpen ? <ChevronUp className="w-4 h-4 lia-text-secondary" /> : <ChevronDown className="w-4 h-4 lia-text-secondary" />}
                            </div>
                          </button>

                          {isOpen && (
                            <div className="px-4 pb-4 space-y-4 bg-lia-bg-secondary/50">
                              <div className="space-y-2">
                                <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-3">
                                  <p className="text-micro lia-text-secondary uppercase tracking-wide mb-1">Pergunta</p>
                                  <p className="text-xs text-lia-text-secondary leading-relaxed">{resp.question?.text || f11.question_text}</p>
                                </div>
                                <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-3">
                                  <p className="text-micro lia-text-secondary uppercase tracking-wide mb-1" aria-live="polite" aria-atomic="true">Resposta do Candidato</p>
                                  <p className="text-xs text-lia-text-primary leading-relaxed">{resp.response_text}</p>
                                </div>
                              </div>

                              <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-3">
                                <p className="text-micro lia-text-secondary uppercase tracking-wide mb-2">Qualidade da resposta (STAR)</p>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {starComponents.map(({ key, label, desc }) => {
                                    const present = starData[key]
                                    return (
                                      <div
                                        key={key}
                                        title={desc}
                                        className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${
 present
                                            ? "bg-status-success/10 border-status-success/30 text-status-success"
                                            : "bg-lia-bg-tertiary border-lia-border-subtle lia-text-secondary"
                                        }`}
                                      >
                                        {present
                                          ? <CheckCircle className="w-3 h-3" />
                                          : <span className="w-3 h-3 flex items-center justify-center lia-text-muted font-bold text-micro">–</span>
                                        }
                                        <span>{label}</span>
                                      </div>
                                    )
                                  })}
                                  {!starData.R && (
                                    <span className="text-micro text-status-warning bg-status-warning/10 border border-status-warning/20 px-2 py-0.5 rounded-full" aria-live="polite" aria-atomic="true">
                                      Resultado não evidenciado
                                    </span>
                                  )}
                                </div>
                              </div>

                              <div className="grid grid-cols-4 gap-2">
                                {[
                                  { label: "Autodeclaração", value: (f11.autodeclaration_score ?? resp.scores.autodeclaration)?.toFixed(1) },
                                  { label: "Contexto", value: (f11.context_score ?? resp.scores.context)?.toFixed(1) },
                                  { label: "Bloom", value: bloomLabel(demonstrated_bloom), sub: `Nível ${demonstrated_bloom}` },
                                  { label: "Dreyfus", value: dreyfusLabel(demonstrated_dreyfus), sub: `Nível ${demonstrated_dreyfus}` },
                                ].map((s) => (
                                  <div key={s.label} className="bg-lia-bg-primary border border-lia-border-subtle rounded-lg p-2 text-center">
                                    <p className="text-micro lia-text-secondary mb-1">{s.label}</p>
                                    <p className="text-sm font-bold text-lia-text-primary">{s.value}</p>
                                  </div>
                                ))}
                              </div>

                              <div className={`flex items-center justify-between rounded-lg border px-3 py-2.5 ${gap.bg} ${gap.border}`}>
                                <div className="flex items-center gap-2">
                                  <GapIcon className={`w-3.5 h-3.5 ${gap.color}`} />
                                  <span className={`text-xs font-medium ${gap.color}`} aria-live="polite" aria-atomic="true">Esperado pela vaga</span>
                                </div>
                                <div className="flex items-center gap-4 text-xs">
                                  <div className="text-right">
                                    <p className="text-micro lia-text-secondary">Bloom</p>
                                    <p className={`font-semibold ${gap.color}`}>{bloomLabel(bloomExpected)}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-micro lia-text-secondary">Dreyfus</p>
                                    <p className={`font-semibold ${gap.color}`}>{dreyfusLabel(dreyfusExpected)}</p>
                                  </div>
                                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gap.bg} ${gap.color} border ${gap.border}`}>
                                    {gap.label}
                                  </span>
                                </div>
                              </div>

                              {resp.evidences && resp.evidences.length > 0 && (
                                <div>
                                  <p className="text-micro lia-text-secondary uppercase tracking-wide mb-2">Evidências</p>
                                  <div className="flex flex-wrap gap-2">
                                    {resp.evidences.map((ev, i) => (
                                      <span key={`ev-${i}`} className="flex items-center gap-1 text-xs bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary px-2 py-1 rounded-full">
                                        <CheckCircle className="w-3 h-3 text-status-success" /> {ev}
                                      </span>
                                    ))}
                                  </div>
                                  <p className="text-xs lia-text-secondary italic mt-2">{resp.justification || f11.justification}</p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                  )
                })()}
              </div>
            </div>
          )}

          {activeTab === 'parecer' && (
            <div className="space-y-3">

              {/* Alertas de atenção — inline (small block) */}
              {(scores.overall_wsi >= 3.0 && scores.overall_wsi < 3.75) && (
                <div className="rounded-xl border border-status-warning/30 bg-status-warning/10 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="w-4 h-4 text-status-warning" />
                    <h3 className="text-sm font-semibold text-status-warning">Pontos de Atenção</h3>
                    <span className="ml-auto text-micro bg-status-warning/10 text-status-warning px-2 py-0.5 rounded-full font-medium border border-status-warning/30">Revisão humana recomendada</span>
                  </div>
                  <ul className="space-y-1.5">{(f11Report?.attention_flags || (report as any)?.flags || ["Score WSI dentro da zona de revisão — decisão requer análise do recrutador responsável."]).map((a: string, i: number) => (<li key={`flag-${i}`} className="flex items-start gap-2 text-xs text-status-warning/90"><AlertTriangle className="w-3.5 h-3.5 text-status-warning mt-0.5 shrink-0" /> {a}</li>))}</ul>
                </div>
              )}

              {report && (
                <>
                  <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                    <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Sumário Executivo
                    </h3>
                    <p className="text-xs text-lia-text-secondary leading-relaxed">{report.executive_summary}</p>
                  </div>

                  {report.technical_analysis && Object.keys(report.technical_analysis).length > 0 && (
                    <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                      <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                        <Target className="w-4 h-4 text-lia-text-secondary" />
                        Análise Técnica
        
                      </h3>
                      {(report.technical_analysis as any).pontos_fortes && (
                        <div className="mb-2">
        
                          <p className="text-micro font-medium text-status-success mb-1 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Pontos Fortes:</p>
                          {(report.technical_analysis as any).pontos_fortes.map((p: string, i: number) => (
                            <div key={`pf-${i}`} className="flex items-start gap-1.5 mb-1">
                              <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0 text-status-success" />
                              <p className="text-xs text-lia-text-secondary">{p}</p>
                            </div>
                          ))}
                        </div>
        
                      )}
                      {(report.technical_analysis as any).gaps && (report.technical_analysis as any).gaps.length > 0 && (
                        <div className="mb-2">
                          <p className="text-micro font-medium text-lia-text-secondary mb-1 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5 text-status-warning" /> Gaps Identificados:</p>
        
                          <ul className="space-y-2">
                            {(report.technical_analysis as any).gaps.map((g: unknown, i: number) => {
                              const gs = typeof g === 'string' ? { texto: g, severidade: 'baixa' } : (g as { texto?: string; severidade?: string })
                              const sc = sevConfig[(gs.severidade as keyof typeof sevConfig) || 'baixa']
                              return (
                                <li key={`gap-${i}`} className={`flex items-start gap-2.5 text-xs text-lia-text-secondary rounded-lg border px-3 py-2 ${sc.bg} ${sc.border}`}>
        
                                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sc.dot}`} />
                                  <span className="flex-1">{gs.texto || String(gs)}</span>
                                  <span className={`text-micro font-bold tracking-wider shrink-0 ${sc.color}`}>{sc.label}</span>
                                </li>
                              )
                            })}
                          </ul>
                        </div>
        
                      )}
                      {(report.technical_analysis as any).evidencias && (
                        <div>
                          <p className="text-micro font-medium lia-text-secondary mb-1">Evidências:</p>
                          {(report.technical_analysis as any).evidencias.map((e: string, i: number) => (
                            <div key={`ev-${i}`} className="flex items-start gap-1.5 mb-1">
                              <Zap className="w-3 h-3 mt-0.5 flex-shrink-0 lia-text-secondary" />
                              <p className="text-xs text-lia-text-secondary">{e}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Big Five — Perfil de Personalidade */}
                  {report.behavioral_analysis && Object.keys(report.behavioral_analysis).length > 0 && (() => {
                    const BIG_FIVE_MAP: Record<string, string> = {
                      openness:          "Abertura a mudanças",
                      conscientiousness: "Organização e disciplina",
                      extraversion:      "Sociabilidade",
                      agreeableness:     "Cooperação",
                      neuroticism:       "Estabilidade emocional",
                    }
                    const BIG_FIVE_HINT: Record<string, string> = {
                      openness:          "Adapta-se a novidades, aprende rápido e lida bem com ambiguidade",
                      conscientiousness: "Planejamento, atenção a prazos e execução sistemática",
                      extraversion:      "Facilidade para interagir, comunicar e construir relacionamentos",
                      agreeableness:     "Disposição para colaborar, ceder e trabalhar bem em equipe",
                      neuroticism:       "Mantém calma sob pressão e lida bem com críticas e frustrações",
                    }
                    const entries = Object.entries(report.behavioral_analysis)
                    const isBigFive = entries.some(([k]) => Object.keys(BIG_FIVE_MAP).includes(k))
                    if (!isBigFive) {
                      return (
                        <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                          <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                            <User className="w-4 h-4 text-lia-text-secondary" />
                            Análise Comportamental
                          </h3>
                          <div className="space-y-2">
                            {entries.map(([key, val]: [string, any]) => (
                              <div key={key}>
                                <div className="flex items-center justify-between mb-0.5">
                                  <span className="text-xs text-lia-text-primary capitalize">{key}</span>
                                  <span className="text-xs font-bold">{val.score?.toFixed(1)}/5.0</span>
                                </div>
                                <Progress value={((val.score || 0) / 5) * 100} className="h-1.5 mb-1" />
                                <p className="text-micro lia-text-secondary">{val.descricao}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    }
                    const seniority = sessionInfo?.seniority_label || "Sênior"
                    return (
                      <div className="p-3 border border-lia-border-subtle space-y-4 bg-lia-bg-secondary rounded-lg">
                        <div>
                          <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
                            <User className="w-4 h-4 text-lia-text-secondary" />
                            Perfil de Personalidade
                          </h3>
                          <p className="text-micro lia-text-secondary mt-0.5">
                            Dimensões <span className="text-wedo-purple font-medium">críticas</span> determinam fit de performance e cultura.
                          </p>
                        </div>
                        <div className="flex items-center gap-4 text-micro lia-text-secondary">
                          <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-lia-btn-primary-bg rounded-sm inline-block" /> Candidato</span>
                          <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-lia-interactive-active rounded-sm inline-block border border-lia-border-default" /> Esperado</span>
                        </div>
                        <div className="space-y-5">
                          {entries.map(([key, val]: [string, any]) => {
                            const traitName = BIG_FIVE_MAP[key] || key
                            const hint = BIG_FIVE_HINT[key] || ""
                            const candidato = Math.round((val.score || 0) / 5 * 100)
                            const vagaEsperado = val.expected_pct ?? 70
                            const dreyfusEsperado = val.dreyfus_esperado ?? 4
                            const dreyfusDemonstrado = Math.round((val.score || 0) * 5 / 5)
                            const status = candidato < vagaEsperado - 20 ? "gap" : candidato > vagaEsperado + 10 ? "acima" : "ok"
                            const showHint = bigFiveHint === key
                            return (
                              <div key={key} className="space-y-1">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-xs font-medium text-lia-text-primary">{traitName}</span>
                                  {val.is_critical && (
                                    <span className="text-micro font-semibold px-1.5 py-0.5 rounded-full border text-wedo-purple bg-wedo-purple/10 border-wedo-purple/30" aria-live="polite" aria-atomic="true">Crítica para esta vaga</span>
                                  )}
                                  {status === "gap"   && <span className="text-micro font-bold text-status-warning bg-status-warning/10 px-1.5 py-0.5 rounded-full border border-status-warning/30">⚠️ Diferença</span>}
                                  {status === "acima" && <span className="text-micro font-bold text-wedo-cyan-dark bg-wedo-cyan/10 px-1.5 py-0.5 rounded-full border border-wedo-cyan/30">↑ Acima</span>}
                                  {status === "ok"    && <span className="text-micro font-bold text-status-success bg-status-success/10 px-1.5 py-0.5 rounded-full border border-status-success/30">✓ Alinhado</span>}
                                  {hint && (
                                    <button className="ml-auto" onClick={() => setBigFiveHint(showHint ? null : key)}>
                                      <Info className="w-3 h-3 lia-text-muted hover:lia-text-secondary transition-colors motion-reduce:transition-none" />
                                    </button>
                                  )}
                                </div>
                                {showHint && hint && (
                                  <p className="text-xs lia-text-secondary bg-lia-bg-secondary border border-lia-border-subtle rounded-md px-2.5 py-1.5">{hint}</p>
                                )}
                                <div className="relative h-3">
                                  <div className="absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full bg-lia-interactive-active border border-lia-border-default" style={{width: `${vagaEsperado}%`}} />
                                  <div className={`absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full ${status === "gap" ? "bg-status-warning" : status === "acima" ? "bg-wedo-cyan" : "bg-lia-btn-primary-bg"}`} style={{width: `${candidato}%`}} />
                                </div>
                                <div className="flex items-center justify-between text-micro lia-text-secondary">
                                  <span>Candidato: <span className="font-semibold text-lia-text-secondary" aria-live="polite" aria-atomic="true">{candidato}%</span></span>
                                  <span>Vaga espera: <span className="font-semibold text-lia-text-secondary" aria-live="polite" aria-atomic="true">{vagaEsperado}%</span></span>
                                </div>
                                <DreyfusRow dreyfusEsperado={dreyfusEsperado} dreyfusDemonstrado={dreyfusDemonstrado} senioridade={seniority} />
                              </div>
                            )
                          })}
                        </div>
                        <p className="text-micro lia-text-secondary pt-1 border-t border-lia-border-subtle">
                          Clique em <Info className="w-2.5 h-2.5 inline" /> para entender o que cada dimensão mede.
                        </p>
                      </div>
                    )
                  })()}

                  {report.recommendation && Object.keys(report.recommendation).length > 0 && (
                    <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                      <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                        <Award className="w-4 h-4 text-lia-text-secondary" />
                        Recomendação
                      </h3>
        
                      <div className="p-2.5 rounded-lg mb-2" style={{backgroundColor: decisionDisplay.bg}}>
                        <p className="text-xs font-semibold" style={{color: decisionDisplay.color}}>{(report.recommendation as any).decisao}</p>
                        <p className="text-xs mt-1 text-lia-text-secondary">{(report.recommendation as any).justificativa}</p>
        
                      </div>
                      {(report.recommendation as any).proximos_passos && (
                        <div>
        
                          <p className="text-micro font-medium lia-text-secondary mb-1">Próximos Passos:</p>
                          {(report.recommendation as any).proximos_passos.map((step: string, i: number) => (
                            <div key={`step-${i}`} className="flex items-center gap-1.5 mb-1">
                              <span className="w-4 h-4 rounded-full bg-lia-interactive-active flex items-center justify-center text-micro font-bold text-lia-text-secondary">{i + 1}</span>
                              <p className="text-xs text-lia-text-secondary">{step}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* Perguntas sugeridas para entrevista — CBI do F11 */}
              {f11Report?.cbi_questions && f11Report.cbi_questions.length > 0 && (
                <div className="p-3 border border-lia-border-subtle space-y-3 bg-lia-bg-secondary rounded-lg">
                  <div>
                    <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
                      <Mic2 className="w-4 h-4 lia-text-secondary" /> Perguntas sugeridas para a entrevista
                    </h3>
                    <p className="text-micro lia-text-secondary mt-0.5">
                      Geradas com base nos gaps identificados — use na entrevista presencial
                    </p>
                  </div>
                  {f11Report.cbi_questions.map((q: { severity?: string; question?: string; texto?: string; focus?: string; foco?: string }, i: number) => {
                    const sev = sevConfig[(q.severity as keyof typeof sevConfig) ?? 'baixa']
                    return (
                      <div key={`cbi-${i}`} className={`border rounded-lg p-4 space-y-2 ${sev.bg} ${sev.border}`}>
                        <p className="text-xs text-lia-text-primary leading-relaxed">"{q.question || q.texto}"</p>
                        <div className="flex items-center gap-2">
                          <span className="text-micro lia-text-secondary">Foco:</span>
                          <span className="text-micro text-lia-text-secondary font-medium bg-lia-bg-primary border border-lia-border-subtle px-2 py-0.5 rounded-full">{q.focus || q.foco || "Competência comportamental"}</span>
                          <span className={`text-micro font-bold ${sev.color}`}>Gap {sev.label}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {isPendingDecision && !!details && (
                <div className="p-3 border border-lia-border-subtle space-y-3 bg-lia-bg-secondary rounded-lg">
                  <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary"><BookOpen className="w-4 h-4 text-wedo-cyan-dark" /> Feedback para o Candidato</h3>
                  <p className="text-xs lia-text-secondary italic" aria-live="polite" aria-atomic="true">Aguardando decisão do recrutador para liberar feedback ao candidato.</p>
                  <div className="bg-lia-bg-secondary border border-lia-border-subtle rounded-lg p-3"><p className="text-micro lia-text-secondary font-medium mb-0.5">Prévia do feedback (rascunho)</p><p className="text-xs text-lia-text-secondary">Agradecemos sua participação na triagem. Suas respostas foram analisadas e entraremos em contato em breve com o próximo passo do processo.</p></div>
                </div>
              )}

              {canTriggerFeedback && (
                <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-lia-text-primary">
                    <MessageSquare className="w-4 h-4 text-wedo-cyan" />
                    Envio de Feedback Automático
                  </h3>
                  <p className="text-xs text-lia-text-secondary mb-3" aria-live="polite" aria-atomic="true">
                    O candidato obteve classificação "{scores.classification}" e pode receber feedback construtivo automaticamente.
                  </p>
                  {feedbackSuccess && (
                    <div className="flex items-center gap-2 p-2 mb-3 rounded-lg bg-status-success/[0.08] border border-status-success/20">
                      <CheckCircle className="w-4 h-4 text-status-success" />
                      <span className="text-xs font-medium text-status-success">Feedback enviado com sucesso</span>
                    </div>
                  )}
                  {feedbackError && (
                    <div className="flex items-center gap-2 p-2 mb-3 rounded-lg bg-status-error/[0.08] border border-status-error/20">
                      <AlertCircle className="w-4 h-4 text-status-error" />
                      <span className="text-xs font-medium text-status-error">{feedbackError}</span>
                    </div>
                  )}
                  <button
                    onClick={handleSendFeedback}
                    disabled={sendingFeedback || feedbackAlreadySent}
                    className={cn("flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-md transition-colors motion-reduce:transition-none disabled:opacity-50 disabled:cursor-not-allowed", feedbackAlreadySent ? "bg-lia-interactive-active lia-text-secondary" : "bg-lia-btn-primary-bg text-lia-btn-primary-text")}
                  >
                    {sendingFeedback ? (
                      <><Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" /> Enviando...</>
                    ) : feedbackAlreadySent ? (
                      <><CheckCircle className="w-3.5 h-3.5" /> Feedback já Enviado</>
                    ) : (
                      <><MessageSquare className="w-3.5 h-3.5" /> Enviar Feedback ao Candidato</>
                    )}
                  </button>
                </div>
              )}

              {(feedback || (f11Report?.response_analyses && f11Report.response_analyses.length > 0)) && (
                <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold flex items-center gap-2 text-lia-text-primary">
                      <BookOpen className="w-4 h-4 text-wedo-cyan-dark" />
                      Feedback para o Candidato
                    </h3>
                    <button
                      onClick={() => {
                        const f11Feedback = f11Report?.response_analyses?.map((a: { feedback?: string }) => a.feedback).filter(Boolean) || []
                        const text = [
                          ...(feedback ? [
                            feedback.main_message,
                            ...(feedback.technical_strengths || []),
                            ...(feedback.behavioral_strengths || []),
                            ...(feedback.development_opportunities || []),
                            feedback.personalized_tip || '',
                            feedback.next_steps || '',
                          ] : []),
                  
                          ...(f11Feedback.length > 0 ? (feedback ? ['', '--- Avaliação detalhada ---'] : []).concat(f11Feedback.filter((x): x is string => Boolean(x))) : []),
                        ].filter(Boolean).join('\n')
                        navigator.clipboard.writeText(text)
                        setCopiedFeedback(true)
                        setTimeout(() => setCopiedFeedback(false), 2000)
                      }}
                      className="flex items-center gap-1 px-2 py-1 text-micro font-medium lia-text-secondary hover:text-lia-text-secondary border border-lia-border-subtle rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                     
                    >
                      {copiedFeedback ? <CheckCircle className="w-3 h-3 text-status-success" /> : <Copy className="w-3 h-3" />}
                      {copiedFeedback ? "Copiado!" : "Copiar feedback"}
                    </button>
                  </div>
                  {feedback?.main_message && (
                    <p className="text-xs text-lia-text-secondary leading-relaxed mb-3">{feedback.main_message}</p>
                  )}

                  {!feedback && f11Report?.response_analyses && (
                    <div className="mb-3 space-y-1">
                      {f11Report.response_analyses.slice(0, 3).map((a: { feedback?: string }, i: number) => (
                        a.feedback && (
                          <p key={i} className="text-xs text-lia-text-secondary leading-relaxed">{a.feedback}</p>
                        )
                      ))}
                    </div>
                  )}

                  {feedback?.technical_strengths && feedback.technical_strengths.length > 0 && (
                    <div className="mb-2">
                      <p className="text-micro font-medium lia-text-secondary mb-1">Pontos Fortes Técnicos:</p>
                      {feedback.technical_strengths.map((s: string, i: number) => (
                        <div key={`ts-${i}`} className="flex items-start gap-1.5 mb-0.5">
                          <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0 text-status-success" />
                          <p className="text-xs text-lia-text-secondary">{s}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {feedback?.behavioral_strengths && feedback.behavioral_strengths.length > 0 && (
                    <div className="mb-2">
                      <p className="text-micro font-medium lia-text-secondary mb-1">Pontos Fortes Comportamentais:</p>
                      {feedback.behavioral_strengths.map((s: string, i: number) => (
                        <div key={`bs-${i}`} className="flex items-start gap-1.5 mb-0.5">
                          <Star className="w-3 h-3 mt-0.5 flex-shrink-0 lia-text-secondary" />
                          <p className="text-xs text-lia-text-secondary">{s}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {feedback?.development_opportunities && feedback.development_opportunities.length > 0 && (
                    <div className="mb-2">
                      <p className="text-micro font-medium lia-text-secondary mb-1">Oportunidades de Desenvolvimento:</p>
                      {feedback.development_opportunities.map((d: string, i: number) => (
                        <div key={`dev-${i}`} className="flex items-start gap-1.5 mb-0.5">
                          <BookOpen className="w-3 h-3 mt-0.5 flex-shrink-0 text-wedo-cyan-dark" />
                          <p className="text-xs text-lia-text-secondary">{d}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {feedback?.personalized_tip && (
                    <div className="p-2 rounded-lg mt-2 bg-wedo-cyan/[0.08] border border-wedo-cyan/20">
                      <p className="text-micro font-medium mb-0.5 text-wedo-cyan">Dica Personalizada</p>
                      <p className="text-xs text-lia-text-secondary">{feedback.personalized_tip}</p>
                    </div>
                  )}

                  {feedback?.next_steps && (
                    <div className="mt-2 p-2 rounded-lg bg-lia-bg-tertiary">
                      <p className="text-micro font-medium lia-text-secondary mb-0.5">Próximos Passos:</p>
                      <p className="text-xs text-lia-text-secondary">{feedback.next_steps}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'comparativo' && (
            <TriagemComparativoTab
              vacancyRanking={vacancyRanking}
              ranking={ranking}
              candidate={candidate}
            />
          )}

        </div>

        <div className="flex-shrink-0 px-4 py-3 flex items-center justify-between border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex items-center gap-2">
            <span className="text-micro lia-text-secondary">Decisão do Recrutador</span>
          </div>
          <div className="flex items-center gap-2">
            {confirmReject ? (
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-status-error font-medium">Confirmar reprovação?</span>
                <button
                  onClick={async () => {
                    setRejecting(true)
                    await onReject?.(candidate)
                    setRejecting(false)
                    setConfirmReject(false)
                  }}
                  disabled={rejecting}
                  className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none disabled:opacity-50 bg-status-error text-lia-text-tertiary"
                >
                  {rejecting ? <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" /> : <ThumbsDown className="w-3 h-3" />}
                  Sim, reprovar
                </button>
                <button
                  onClick={() => setConfirmReject(false)}
                  className="px-2.5 py-1.5 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover border border-lia-border-subtle bg-lia-bg-secondary"
                >
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmReject(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors motion-reduce:transition-none hover:bg-status-error/10 border border-lia-border-subtle text-status-error"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
                Reprovar
              </button>
            )}
            <button
              onClick={async () => {
                setApproving(true)
                await onApprove?.(candidate)
                setApproving(false)
              }}
              disabled={approving}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md transition-colors motion-reduce:transition-none hover:bg-lia-btn-primary-hover disabled:opacity-50 bg-lia-btn-primary-bg text-lia-text-tertiary"
            >
              {approving ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" /> : <ThumbsUp className="w-3.5 h-3.5" />}
              Aprovar para Entrevista
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
