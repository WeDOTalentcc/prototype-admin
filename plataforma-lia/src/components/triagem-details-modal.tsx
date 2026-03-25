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

interface TriagemDetailsModalProps {
  candidate: any
  isOpen: boolean
  onClose: () => void
  jobVacancyId?: string
  onApprove?: (candidate: any) => void
  onReject?: (candidate: any) => void
}

const WSI_CLASSIFICATION_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  excepcional:     { bg: 'rgba(5, 150, 105, 0.12)',  text: '#065F46', label: 'Excepcional' },
  excelente:       { bg: 'rgba(34, 197, 94, 0.12)',  text: '#166534', label: 'Excelente' },
  alto:            { bg: 'rgba(59, 130, 246, 0.12)', text: '#1D4ED8', label: 'Alto' },
  medio:           { bg: 'rgba(234, 179, 8, 0.12)',  text: '#854D0E', label: 'Médio' },
  abaixo_da_media: { bg: 'rgba(249, 115, 22, 0.12)', text: '#9A3412', label: 'Abaixo da média' },
  regular:         { bg: 'rgba(239, 68, 68, 0.12)',  text: '#991B1B', label: 'Regular / Baixo' },
}

const getClassificationColor = (classification: string) =>
  WSI_CLASSIFICATION_COLORS[classification] ?? { bg: 'rgba(96, 190, 209, 0.12)', text: '#374151', label: classification }

const getClassificationLabel = (classification: string) =>
  WSI_CLASSIFICATION_COLORS[classification]?.label ?? classification

const getDecisionDisplay = (decision?: string) => {
  // Normalizar: API retorna APROVADO/EM_AVALIACAO/REPROVADO; legado usa aprovado/aguardando/nao_aprovado
  const normalized = (decision ?? '').toUpperCase().replace('NAO_APROVADO', 'REPROVADO').replace('AGUARDANDO', 'EM_AVALIACAO')
  switch (normalized) {
    case 'APROVADO':
    case 'aprovado':
      return { label: 'Aprovado', icon: ThumbsUp, color: '#166534', bg: 'rgba(34, 197, 94, 0.12)' }
    case 'EM_AVALIACAO':
    case 'aguardando':
      return { label: 'Em Avaliação', icon: Clock, color: '#854D0E', bg: 'rgba(234, 179, 8, 0.12)' }
    case 'REPROVADO':
    case 'nao_aprovado':
      return { label: 'Não Aprovado', icon: ThumbsDown, color: '#991B1B', bg: 'rgba(239, 68, 68, 0.12)' }
    default: return { label: 'Pendente', icon: Clock, color: '#6B7280', bg: '#F3F4F6' }
  }
}

const wsiToPercent = (score: number) => Math.round((score / 5) * 100)

const bloomLabel = (n: number) =>
  (["", "Recordar", "Compreender", "Aplicar", "Analisar", "Avaliar", "Criar"] as const)[n] ?? `Nível ${n}`

const dreyfusLabel = (n: number) =>
  (["", "Iniciante", "Básico", "Intermediário", "Avançado", "Especialista"] as const)[n] ?? `Nível ${n}`

const getScoreColor = (score: number) =>
  score >= 4.5 ? "text-emerald-700" :
  score >= 4.0 ? "text-green-600" :
  score >= 3.5 ? "text-blue-600" :
  score >= 3.0 ? "text-amber-600" :
  score >= 2.25 ? "text-orange-600" :
  "text-red-600"

const getScoreColor3Tier = (score: number) =>
  score >= 4.5 ? "text-emerald-600" :
  score >= 3.5 ? "text-amber-600" :
  "text-red-500"

const gapConfig = {
  ok:    { label: "Alinhado",          icon: CheckCircle, color: "text-emerald-600", bg: "bg-emerald-50",  border: "border-emerald-200" },
  acima: { label: "Acima do esperado", icon: Star,        color: "text-blue-600",    bg: "bg-blue-50",     border: "border-blue-200"    },
  gap:   { label: "Gap identificado",  icon: AlertTriangle, color: "text-amber-600",   bg: "bg-amber-50",    border: "border-amber-200"   },
}

const starComponents = [
  { key: "S" as const, label: "Situação", desc: "Contexto descrito" },
  { key: "T" as const, label: "Tarefa", desc: "Objetivo claro" },
  { key: "A" as const, label: "Ação", desc: "O que foi feito" },
  { key: "R" as const, label: "Resultado", desc: "Impacto mensurável" },
]

const sevConfig = {
  alta:  { label: "ALTA",  color: "text-red-600",   bg: "bg-red-50",   border: "border-red-200",   dot: "bg-red-500"   },
  media: { label: "MÉDIA", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500" },
  baixa: { label: "BAIXA", color: "text-gray-500",  bg: "bg-gray-50",  border: "border-gray-200",  dot: "bg-gray-400"  },
}

function DreyfusRow({
  dreyfusEsperado, dreyfusDemonstrado, senioridade
}: { dreyfusEsperado: number; dreyfusDemonstrado: number; senioridade?: string }) {
  const delta = dreyfusDemonstrado - dreyfusEsperado
  const isCritical = delta <= -2
  const isAtencao  = delta === -1
  const isAcima    = delta > 0
  const color = isCritical ? "text-red-600" : isAtencao ? "text-amber-600" : isAcima ? "text-blue-600" : "text-emerald-600"
  const bg    = isCritical ? "bg-red-50 border-red-200" : isAtencao ? "bg-amber-50 border-amber-200" : isAcima ? "bg-blue-50 border-blue-200" : "bg-emerald-50 border-emerald-200"
  const lbl   = isCritical ? "Gap crítico" : isAtencao ? "Atenção" : isAcima ? "Acima" : "Alinhado"
  return (
    <div className={`flex items-center justify-between text-[10px] rounded-md border px-2.5 py-1.5 mt-1 ${bg}`}>
      <span className="text-gray-500">Maturidade comportamental</span>
      <div className="flex items-center gap-2">
        <span className="text-gray-400">
          Esperado{senioridade ? ` para ${senioridade}` : ""}: <span className="font-medium text-gray-600">{dreyfusLabel(dreyfusEsperado)}</span>
        </span>
        <span className="text-gray-300">·</span>
        <span className="text-gray-400">
          Demonstrado: <span className={`font-semibold ${color}`}>{dreyfusLabel(dreyfusDemonstrado)}</span>
        </span>
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${bg} ${color}`}>{lbl}</span>
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
  const [feedbackStatus, setFeedbackStatus] = useState<any>(null)
  const [sendingFeedback, setSendingFeedback] = useState(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState(false)
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [confirmReject, setConfirmReject] = useState(false)
  const [f11Report, setF11Report] = useState<any>(null)
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
        console.warn('Feedback status not available:', e)
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
          console.warn('Ranking data not available:', e)
        }
      }

      const sessionId = detailsData.session?.session_id || detailsData.session_id
      if (sessionId) {
        try {
          const f11 = await fetch(`/api/backend-proxy/wsi/f11-report/${sessionId}`)
          if (f11.ok) setF11Report(await f11.json())
        } catch (e) {
          console.warn('F11 report not available:', e)
        }
      }
    } catch (err) {
      console.error('Failed to load WSI details:', err)
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
    const resultId = details.result_id || (details as any).id
    if (!resultId) return
    setSendingFeedback(true)
    setFeedbackError(null)
    try {
      const result = await liaApi.wsiTriggerFeedback(resultId)
      setFeedbackSuccess(true)
      setFeedbackStatus({ ...feedbackStatus, feedback_sent: true })
      setTimeout(() => setFeedbackSuccess(false), 5000)
    } catch (err: any) {
      setFeedbackError(err.message || 'Erro ao enviar feedback')
    } finally {
      setSendingFeedback(false)
    }
  }

  const decision = details?.scores?.decision || details?.decision
  const decisionNormalized = (decision ?? '').toUpperCase()
  const isPendingDecision = !decision || decisionNormalized === 'AGUARDANDO' || decisionNormalized === 'EM_AVALIACAO'
  // canTriggerFeedback: disponível para todos os estados de decisão quando há dados de triagem
  const canTriggerFeedback = !!details && !!details.scores
  const feedbackAlreadySent = feedbackStatus?.feedback_sent === true

  const font = { fontFamily: "'Open Sans', sans-serif" }

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)' }}>
        <div className="w-full max-w-3xl p-8 flex flex-col items-center gap-3 rounded-md bg-white dark:bg-gray-800" style={{ boxShadow: '0 16px 32px -8px rgba(0, 0, 0, 0.12)' }}>
          <Loader2 className="w-8 h-8 animate-spin text-wedo-cyan" />
          <p className="text-sm text-gray-500" style={font}>Carregando dados da triagem...</p>
        </div>
      </div>
    )
  }

  if (error || !details) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)' }}>
        <div className="w-full max-w-3xl p-8 flex flex-col items-center gap-3 rounded-md bg-white dark:bg-gray-800" style={{ boxShadow: '0 16px 32px -8px rgba(0, 0, 0, 0.12)' }}>
          <AlertCircle className="w-8 h-8 text-gray-400" />
          <p className="text-sm text-gray-500" style={font}>{error || 'Dados não disponíveis.'}</p>
          <button onClick={onClose} className="mt-2 px-4 py-2 text-sm rounded-md bg-gray-900 text-white hover:bg-gray-800" style={font}>Fechar</button>
        </div>
      </div>
    )
  }

  const { scores, session: sessionInfo, responses, report, feedback } = details
  const classColors = getClassificationColor(scores.classification)
  const decisionDisplay = getDecisionDisplay(feedback?.decision)
  const DecisionIcon = decisionDisplay.icon

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)' }}>
      <div className="w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col rounded-md dark:bg-gray-800 dark:border-gray-700 border border-gray-100" style={{ backgroundColor: '#FFFFFF', boxShadow: '0 16px 32px -8px rgba(0, 0, 0, 0.12)' }}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(96, 190, 209, 0.12)' }}>
              <Brain className="w-4 h-4 text-wedo-cyan" />
            </div>
            <div>
              <h2 className="text-[13px] font-semibold text-gray-950 dark:text-gray-50" style={font}>
                Detalhes da Triagem WSI - {candidate.name}
              </h2>
              <p className="text-[11px] text-gray-500" style={font}>
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
                    <p style="color:#6B7280;font-size:12px;margin-bottom:4px;"><strong>Pergunta:</strong> ${resp.question.text}</p>
                    <p style="font-size:12px;margin-bottom:4px;"><strong>Resposta:</strong> ${resp.response_text}</p>
                    <p style="font-size:11px;color:#6B7280;font-style:italic;">${resp.justification || ''}</p>
                  </div>
                `).join('')
                printWindow.document.write(`
                  <html><head><title>Triagem WSI - ${candidate.name}</title>
                  <style>body{font-family:'Open Sans',sans-serif;padding:32px;color:#111827;max-width:800px;margin:0 auto;}
                  h1{font-size:20px;margin-bottom:4px;}h2{font-size:16px;margin-top:24px;margin-bottom:12px;color:#374151;}
                  .scores{display:flex;gap:24px;margin:16px 0;}.score-box{text-align:center;padding:12px 20px;border:1px solid #F3F4F6;border-radius:8px;}
                  .score-box .value{font-size:24px;font-weight:bold;}.score-box .label{font-size:11px;color:#6B7280;}
                  .meta{font-size:12px;color:#6B7280;margin-bottom:16px;}
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
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium transition-colors hover:bg-gray-100 text-gray-800 dark:text-gray-200 border border-gray-100" style={{ ...font, backgroundColor: '#FFFFFF', borderRadius: '6px' }}
            >
              <Download className="w-3 h-3" />
              Exportar
            </button>
            <button onClick={onClose} className="h-7 w-7 p-0 flex items-center justify-center transition-colors hover:bg-gray-100 rounded-full text-gray-500">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="px-4 py-2.5 border-b border-b-gray-100" style={{ backgroundColor: '#FFFFFF' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-5">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                <div>
                  <p className="text-[10px] text-gray-500" style={font}>Score WSI</p>
                  <p className={`text-base font-bold ${getScoreColor(scores.overall_wsi)}`} style={font}>{scores.overall_wsi.toFixed(1)}<span className="text-gray-400 font-normal">/5.0</span></p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Trophy className="w-4 h-4 text-gray-500" />
                <div>
                  <p className="text-[10px] text-gray-500" style={font}>Ranking</p>
                  <p className="text-sm font-bold text-gray-950 dark:text-gray-50" style={font}>
                    {ranking?.ranked ? `#${ranking.rank} de ${ranking.total}` : 'N/A'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-gray-500" />
                <div>
                  <p className="text-[10px] text-gray-500" style={font}>Classificação</p>
                  <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded-full" style={{ backgroundColor: classColors.bg, color: classColors.text, ...font }}>
                    {getClassificationLabel(scores.classification)}
                  </span>
                </div>
              </div>

              {sessionInfo.duration_minutes && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-[10px] text-gray-500" style={font}>Duração</p>
                    <p className="text-xs font-medium text-gray-950 dark:text-gray-50" style={font}>{sessionInfo.duration_minutes} min</p>
                  </div>
                </div>
              )}
            </div>

            <div className="text-right">
              <span className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium rounded-full" style={{ backgroundColor: decisionDisplay.bg, color: decisionDisplay.color, ...font }}>
                <DecisionIcon className="w-3 h-3" />
                {decisionDisplay.label}
              </span>
            </div>
          </div>
        </div>

        <div className="px-4 py-2 border-b border-b-gray-100">
          <div className="flex gap-1">
            {[
              { key: 'triagem' as const, icon: MessageSquare, label: 'Respostas e Avaliação' },
              { key: 'parecer' as const, icon: FileText, label: 'Parecer e Feedback' },
              { key: 'comparativo' as const, icon: BarChart3, label: 'Ranking e Comparativo' },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className="px-3 py-1.5 text-[11px] font-medium transition-all flex items-center gap-1.5 rounded-full hover:bg-gray-100"
                style={{ ...font, backgroundColor: activeTab === tab.key ? '#1F2937' : 'transparent', color: activeTab === tab.key ? '#FFFFFF' : '#6B7280' }}
              >
                <tab.icon className="w-3 h-3" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {activeTab === 'triagem' && (
            <div className="space-y-4">
              <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                <h3 className="text-xs font-semibold flex items-center gap-2 mb-3 text-gray-950 dark:text-gray-50" style={font}>
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  Scores por Dimensão
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 rounded-lg border border-gray-100">
                    <p className="text-xl font-bold text-gray-950" style={font}>{scores.overall_wsi.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500" style={font}>Geral ({wsiToPercent(scores.overall_wsi)}%)</p>
                    <Progress value={wsiToPercent(scores.overall_wsi)} className="h-1.5 mt-1.5" />
                  </div>
                  <div className="text-center p-3 rounded-lg border border-gray-100">
                    <p className="text-xl font-bold text-gray-950" style={font}>{scores.technical_wsi.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500" style={font}>Comp. Técnicas ({wsiToPercent(scores.technical_wsi)}%)</p>
                    <Progress value={wsiToPercent(scores.technical_wsi)} className="h-1.5 mt-1.5" />
                  </div>
                  <div className="text-center p-3 rounded-lg border border-gray-100">
                    <p className="text-xl font-bold text-gray-950" style={font}>{scores.behavioral_wsi.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500" style={font}>Comp. Comportamentais ({wsiToPercent(scores.behavioral_wsi)}%)</p>
                    <Progress value={wsiToPercent(scores.behavioral_wsi)} className="h-1.5 mt-1.5" />
                  </div>
                </div>
                <div className="flex items-center gap-3 mt-3 flex-wrap">
                  <span className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                    {sessionInfo.screening_type === 'voice' ? <Mic className="w-3 h-3" /> : <MessageSquare className="w-3 h-3" />}
                    {sessionInfo.screening_type === 'voice' ? 'Triagem por Voz' : 'Triagem por Texto'}
                  </span>
                  {scores.percentile && (
                    <span className="text-[10px] text-gray-500 flex items-center gap-1" style={font}>
                      <TrendingUp className="w-3 h-3" />
                      Top {100 - scores.percentile}%
                    </span>
                  )}
                  {sessionInfo.started_at && (
                    <span className="text-[10px] text-gray-400" style={font}>
                      {new Date(sessionInfo.started_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>
                {f11Report?.seniority_weights && (
                  <div className="flex items-center gap-1.5 text-[11px] text-gray-400 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 mt-2">
                    <BarChart3 className="w-3 h-3 text-gray-400 shrink-0" />
                    <span>
                      Para <span className="font-medium text-gray-600">{f11Report.seniority || details?.session?.seniority_label || 'N/A'}</span>: Competências Técnicas valem{' '}
                      <span className="font-semibold text-gray-700">{Math.round(f11Report.seniority_weights.technical * 100)}%</span> e Comportamentais valem{' '}
                      <span className="font-semibold text-gray-700">{Math.round(f11Report.seniority_weights.behavioral * 100)}%</span> do score final
                    </span>
                  </div>
                )}
                {f11Report?.mode && (
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-gray-400" style={font}>Modo de triagem:</span>
                    <span className="text-[10px] font-medium text-gray-700 flex items-center gap-1" style={font}>
                      <Layers className="w-3 h-3 text-gray-400" />
                      {f11Report.mode === 'compact' ? 'Compact' : f11Report.mode === 'full' ? 'Full' : f11Report.mode}
                      {f11Report.question_count ? ` · ${f11Report.question_count} perguntas` : ''}
                    </span>
                  </div>
                )}
              </div>


              <div className="border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', overflow: 'hidden' }}>
                <div className="cursor-pointer p-3 flex items-center justify-between hover:bg-gray-50 transition-colors" onClick={() => toggleSection('responses')} style={{ borderBottom: expandedSections.has('responses') ? '1px solid #F3F4F6' : 'none' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 text-gray-950 dark:text-gray-50" style={font}>
                    <MessageSquare className="w-4 h-4 text-gray-700" />
                    Respostas por Competência ({responses.length})
                  </h3>
                  {expandedSections.has('responses') ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                </div>
                {expandedSections.has('responses') && (() => {
                  const f11Analyses = f11Report?.response_analyses || []
                  const f11Map: Record<string, any> = {}
                  f11Analyses.forEach((a: any) => { if (a.competency) f11Map[a.competency] = a })

                  return (
                  <div className="divide-y divide-gray-100">
                    {responses.map((resp, idx) => {
                      const f11 = f11Map[resp.competency] || {}
                      const starData = f11.star || { S: false, T: false, A: false, R: false }
                      const gapStatus = (f11.gap_status || 'ok') as keyof typeof gapConfig
                      const gap = gapConfig[gapStatus] || gapConfig.ok
                      const GapIcon = gap.icon
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
                        <div key={idx}>
                          <button
                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left"
                            onClick={() => toggleSection(`resp-${idx}`)}
                          >
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-sm font-medium text-gray-800" style={font}>{resp.competency}</span>
                              <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{getFrameworkLabel(resp.question?.framework || f11.framework || '')}</span>
                              {isCritical && (
                                <span className="flex items-center gap-0.5 text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded-full">
                                  <ShieldAlert className="w-2.5 h-2.5" /> Crítica
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-bold ${getScoreColor3Tier(finalScore)}`} style={font}>
                                {finalScore.toFixed(1)}/5.0
                              </span>
                              {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                            </div>
                          </button>

                          {isOpen && (
                            <div className="px-4 pb-4 space-y-4 bg-gray-50/50">
                              <div className="space-y-2">
                                <div className="bg-white border border-gray-100 rounded-lg p-3">
                                  <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1" style={font}>Pergunta</p>
                                  <p className="text-xs text-gray-700 leading-relaxed" style={font}>{resp.question?.text || f11.question_text}</p>
                                </div>
                                <div className="bg-white border border-gray-100 rounded-lg p-3">
                                  <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1" style={font}>Resposta do Candidato</p>
                                  <p className="text-xs text-gray-800 leading-relaxed" style={font}>{resp.response_text}</p>
                                </div>
                              </div>

                              <div className="bg-white border border-gray-100 rounded-lg p-3">
                                <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-2" style={font}>Qualidade da resposta (STAR)</p>
                                <div className="flex items-center gap-2 flex-wrap">
                                  {starComponents.map(({ key, label, desc }) => {
                                    const present = starData[key]
                                    return (
                                      <div
                                        key={key}
                                        title={desc}
                                        className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                                          present
                                            ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                                            : "bg-gray-100 border-gray-200 text-gray-400"
                                        }`}
                                      >
                                        {present
                                          ? <CheckCircle className="w-3 h-3" />
                                          : <span className="w-3 h-3 flex items-center justify-center text-gray-300 font-bold text-[10px]">–</span>
                                        }
                                        <span>{label}</span>
                                      </div>
                                    )
                                  })}
                                  {!starData.R && (
                                    <span className="text-[10px] text-amber-600 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full">
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
                                  <div key={s.label} className="bg-white border border-gray-100 rounded-lg p-2 text-center">
                                    <p className="text-[9px] text-gray-400 mb-1" style={font}>{s.label}</p>
                                    <p className="text-sm font-bold text-gray-900" style={font}>{s.value}</p>
                                  </div>
                                ))}
                              </div>

                              <div className={`flex items-center justify-between rounded-lg border px-3 py-2.5 ${gap.bg} ${gap.border}`}>
                                <div className="flex items-center gap-2">
                                  <GapIcon className={`w-3.5 h-3.5 ${gap.color}`} />
                                  <span className={`text-xs font-medium ${gap.color}`} style={font}>Esperado pela vaga</span>
                                </div>
                                <div className="flex items-center gap-4 text-xs">
                                  <div className="text-right">
                                    <p className="text-[9px] text-gray-400" style={font}>Bloom</p>
                                    <p className={`font-semibold ${gap.color}`} style={font}>{bloomLabel(bloomExpected)}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-[9px] text-gray-400" style={font}>Dreyfus</p>
                                    <p className={`font-semibold ${gap.color}`} style={font}>{dreyfusLabel(dreyfusExpected)}</p>
                                  </div>
                                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gap.bg} ${gap.color} border ${gap.border}`}>
                                    {gap.label}
                                  </span>
                                </div>
                              </div>

                              {resp.evidences && resp.evidences.length > 0 && (
                                <div>
                                  <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-2" style={font}>Evidências</p>
                                  <div className="flex flex-wrap gap-2">
                                    {resp.evidences.map((ev, i) => (
                                      <span key={i} className="flex items-center gap-1 text-[11px] bg-white border border-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                        <CheckCircle className="w-3 h-3 text-emerald-500" /> {ev}
                                      </span>
                                    ))}
                                  </div>
                                  <p className="text-xs text-gray-500 italic mt-2" style={font}>{resp.justification || f11.justification}</p>
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

              {/* Alertas — apenas para EM_AVALIACAO */}
              {(scores.overall_wsi >= 3.0 && scores.overall_wsi < 3.75) && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="w-4 h-4 text-amber-600" />
                    <h3 className="text-sm font-semibold text-amber-700" style={font}>Pontos de Atenção</h3>
                    <span className="ml-auto text-[10px] bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full font-medium border border-amber-200">Revisão humana recomendada</span>
                  </div>
                  <ul className="space-y-1.5">
                    {(f11Report?.attention_flags || report?.flags || ["Score WSI dentro da zona de revisão — decisão requer análise do recrutador responsável."]).map((a: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-amber-800" style={font}>
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" /> {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {report && (
                <>
                  <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                    <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950 dark:text-gray-50" style={font}>
                      <Brain className="w-4 h-4 text-wedo-cyan" />
                      Sumário Executivo
                    </h3>
                    <p className="text-[11px] text-gray-700 leading-relaxed" style={font}>{report.executive_summary}</p>
                  </div>

                  {report.technical_analysis && Object.keys(report.technical_analysis).length > 0 && (
                    <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                      <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                        <Target className="w-4 h-4 text-gray-700" />
                        Análise Técnica
                      </h3>
                      {report.technical_analysis.pontos_fortes && (
                        <div className="mb-2">
                          <p className="text-[10px] font-medium text-emerald-700 mb-1 flex items-center gap-1" style={font}><CheckCircle className="w-3.5 h-3.5" /> Pontos Fortes:</p>
                          {report.technical_analysis.pontos_fortes.map((p: string, i: number) => (
                            <div key={i} className="flex items-start gap-1.5 mb-1">
                              <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0 text-emerald-500" />
                              <p className="text-[11px] text-gray-700" style={font}>{p}</p>
                            </div>
                          ))}
                        </div>
                      )}
                      {report.technical_analysis.gaps && report.technical_analysis.gaps.length > 0 && (
                        <div className="mb-2">
                          <p className="text-[10px] font-medium text-gray-600 mb-1 flex items-center gap-1" style={font}><AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Gaps Identificados:</p>
                          <ul className="space-y-2">
                            {report.technical_analysis.gaps.map((g: any, i: number) => {
                              const gs = typeof g === 'string' ? { texto: g, severidade: 'baixa' } : g
                              const sc = sevConfig[(gs.severidade as keyof typeof sevConfig) || 'baixa']
                              return (
                                <li key={i} className={`flex items-start gap-2.5 text-xs text-gray-700 rounded-lg border px-3 py-2 ${sc.bg} ${sc.border}`} style={font}>
                                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sc.dot}`} />
                                  <span className="flex-1">{gs.texto || gs}</span>
                                  <span className={`text-[9px] font-bold tracking-wider shrink-0 ${sc.color}`}>{sc.label}</span>
                                </li>
                              )
                            })}
                          </ul>
                        </div>
                      )}
                      {report.technical_analysis.evidencias && (
                        <div>
                          <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Evidências:</p>
                          {report.technical_analysis.evidencias.map((e: string, i: number) => (
                            <div key={i} className="flex items-start gap-1.5 mb-1">
                              <Zap className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-400" />
                              <p className="text-[11px] text-gray-600" style={font}>{e}</p>
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
                        <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                          <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                            <User className="w-4 h-4 text-gray-700" />
                            Análise Comportamental
                          </h3>
                          <div className="space-y-2">
                            {entries.map(([key, val]: [string, any]) => (
                              <div key={key}>
                                <div className="flex items-center justify-between mb-0.5">
                                  <span className="text-[11px] text-gray-800 capitalize" style={font}>{key}</span>
                                  <span className="text-[11px] font-bold" style={{ ...font }}>{val.score?.toFixed(1)}/5.0</span>
                                </div>
                                <Progress value={((val.score || 0) / 5) * 100} className="h-1.5 mb-1" />
                                <p className="text-[10px] text-gray-500" style={font}>{val.descricao}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                    }
                    const seniority = sessionInfo?.seniority_label || "Sênior"
                    return (
                      <div className="p-3 border border-gray-100 space-y-4" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                        <div>
                          <h3 className="text-xs font-semibold flex items-center gap-2 text-gray-950" style={font}>
                            <User className="w-4 h-4 text-gray-700" />
                            Perfil de Personalidade
                          </h3>
                          <p className="text-[10px] text-gray-400 mt-0.5" style={font}>
                            Dimensões <span className="text-purple-600 font-medium">críticas</span> determinam fit de performance e cultura.
                          </p>
                        </div>
                        <div className="flex items-center gap-4 text-[10px] text-gray-400">
                          <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-800 rounded-sm inline-block" /> Candidato</span>
                          <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-200 rounded-sm inline-block border border-gray-300" /> Esperado</span>
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
                                  <span className="text-[11px] font-medium text-gray-800" style={font}>{traitName}</span>
                                  {val.is_critical && (
                                    <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full border text-purple-700 bg-purple-50 border-purple-200">Crítica para esta vaga</span>
                                  )}
                                  {status === "gap"   && <span className="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-200">⚠️ Diferença</span>}
                                  {status === "acima" && <span className="text-[9px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-full border border-blue-200">↑ Acima</span>}
                                  {status === "ok"    && <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200">✓ Alinhado</span>}
                                  {hint && (
                                    <button className="ml-auto" onClick={() => setBigFiveHint(showHint ? null : key)}>
                                      <Info className="w-3 h-3 text-gray-300 hover:text-gray-500 transition-colors" />
                                    </button>
                                  )}
                                </div>
                                {showHint && hint && (
                                  <p className="text-[11px] text-gray-500 bg-gray-50 border border-gray-100 rounded-md px-2.5 py-1.5" style={font}>{hint}</p>
                                )}
                                <div className="relative h-3">
                                  <div className="absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full bg-gray-200 border border-gray-300" style={{ width: `${vagaEsperado}%` }} />
                                  <div className={`absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full ${status === "gap" ? "bg-amber-400" : status === "acima" ? "bg-blue-400" : "bg-gray-800"}`} style={{ width: `${candidato}%` }} />
                                </div>
                                <div className="flex items-center justify-between text-[10px] text-gray-400" style={font}>
                                  <span>Candidato: <span className="font-semibold text-gray-600">{candidato}%</span></span>
                                  <span>Vaga espera: <span className="font-semibold text-gray-600">{vagaEsperado}%</span></span>
                                </div>
                                <DreyfusRow dreyfusEsperado={dreyfusEsperado} dreyfusDemonstrado={dreyfusDemonstrado} senioridade={seniority} />
                              </div>
                            )
                          })}
                        </div>
                        <p className="text-[10px] text-gray-400 pt-1 border-t border-gray-100" style={font}>
                          Clique em <Info className="w-2.5 h-2.5 inline" /> para entender o que cada dimensão mede.
                        </p>
                      </div>
                    )
                  })()}

                  {report.recommendation && Object.keys(report.recommendation).length > 0 && (
                    <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                      <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                        <Award className="w-4 h-4 text-gray-700" />
                        Recomendação
                      </h3>
                      <div className="p-2.5 rounded-lg mb-2" style={{ backgroundColor: decisionDisplay.bg }}>
                        <p className="text-xs font-semibold" style={{ ...font, color: decisionDisplay.color }}>{report.recommendation.decisao}</p>
                        <p className="text-[11px] mt-1 text-gray-700" style={font}>{report.recommendation.justificativa}</p>
                      </div>
                      {report.recommendation.proximos_passos && (
                        <div>
                          <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Próximos Passos:</p>
                          {report.recommendation.proximos_passos.map((step: string, i: number) => (
                            <div key={i} className="flex items-center gap-1.5 mb-1">
                              <span className="w-4 h-4 rounded-full bg-gray-200 flex items-center justify-center text-[9px] font-bold text-gray-600">{i + 1}</span>
                              <p className="text-[11px] text-gray-700" style={font}>{step}</p>
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
                <div className="p-3 border border-gray-100 space-y-3" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <div>
                    <h3 className="text-xs font-semibold flex items-center gap-2 text-gray-950" style={font}>
                      <Mic2 className="w-4 h-4 text-gray-500" /> Perguntas sugeridas para a entrevista
                    </h3>
                    <p className="text-[10px] text-gray-400 mt-0.5" style={font}>
                      Geradas com base nos gaps identificados — use na entrevista presencial
                    </p>
                  </div>
                  {f11Report.cbi_questions.map((q: any, i: number) => {
                    const sev = sevConfig[(q.severity as keyof typeof sevConfig) ?? 'baixa']
                    return (
                      <div key={i} className={`border rounded-lg p-4 space-y-2 ${sev.bg} ${sev.border}`}>
                        <p className="text-xs text-gray-800 leading-relaxed" style={font}>"{q.question || q.texto}"</p>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-gray-400" style={font}>Foco:</span>
                          <span className="text-[10px] text-gray-600 font-medium bg-white border border-gray-200 px-2 py-0.5 rounded-full" style={font}>{q.focus || q.foco || "Competência comportamental"}</span>
                          <span className={`text-[9px] font-bold ${sev.color}`} style={font}>Gap {sev.label}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {isPendingDecision && !!details && (
                <div className="p-3 border border-gray-100 space-y-3" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 text-gray-950" style={font}>
                    <BookOpen className="w-4 h-4 text-blue-500" /> Feedback para o Candidato
                  </h3>
                  <p className="text-xs text-gray-500 italic" style={font}>Aguardando decisão do recrutador para liberar feedback ao candidato.</p>
                  <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
                    <p className="text-[10px] text-gray-400 font-medium mb-0.5" style={font}>Prévia do feedback (rascunho)</p>
                    <p className="text-xs text-gray-600" style={font}>Agradecemos sua participação na triagem. Suas respostas foram analisadas e entraremos em contato em breve com o próximo passo do processo.</p>
                  </div>
                </div>
              )}

              {canTriggerFeedback && (
                <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                    <MessageSquare className="w-4 h-4 text-wedo-cyan" />
                    Envio de Feedback Automático
                  </h3>
                  <p className="text-[11px] text-gray-600 mb-3" style={font}>
                    O candidato obteve classificação "{scores.classification}" e pode receber feedback construtivo automaticamente.
                  </p>
                  {feedbackSuccess && (
                    <div className="flex items-center gap-2 p-2 mb-3 rounded-lg" style={{ backgroundColor: 'rgba(34, 197, 94, 0.08)', border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                      <CheckCircle className="w-4 h-4" style={{ color: '#166534' }} />
                      <span className="text-[11px] font-medium" style={{ ...font, color: '#166534' }}>Feedback enviado com sucesso</span>
                    </div>
                  )}
                  {feedbackError && (
                    <div className="flex items-center gap-2 p-2 mb-3 rounded-lg" style={{ backgroundColor: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                      <AlertCircle className="w-4 h-4" style={{ color: '#991B1B' }} />
                      <span className="text-[11px] font-medium" style={{ ...font, color: '#991B1B' }}>{feedbackError}</span>
                    </div>
                  )}
                  <button
                    onClick={handleSendFeedback}
                    disabled={sendingFeedback || feedbackAlreadySent}
                    className="flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      ...font,
                      backgroundColor: feedbackAlreadySent ? '#E5E7EB' : '#1F2937',
                      color: feedbackAlreadySent ? '#6B7280' : '#FFFFFF',
                    }}
                  >
                    {sendingFeedback ? (
                      <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Enviando...</>
                    ) : feedbackAlreadySent ? (
                      <><CheckCircle className="w-3.5 h-3.5" /> Feedback já Enviado</>
                    ) : (
                      <><MessageSquare className="w-3.5 h-3.5" /> Enviar Feedback ao Candidato</>
                    )}
                  </button>
                </div>
              )}

              {(feedback || (f11Report?.response_analyses && f11Report.response_analyses.length > 0)) && (
                <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold flex items-center gap-2 text-gray-950" style={font}>
                      <BookOpen className="w-4 h-4 text-blue-500" />
                      Feedback para o Candidato
                    </h3>
                    <button
                      onClick={() => {
                        const f11Feedback = f11Report?.response_analyses?.map((a: any) => a.feedback).filter(Boolean) || []
                        const text = [
                          ...(feedback ? [
                            feedback.main_message,
                            ...(feedback.technical_strengths || []),
                            ...(feedback.behavioral_strengths || []),
                            ...(feedback.development_opportunities || []),
                            feedback.personalized_tip || '',
                            feedback.next_steps || '',
                          ] : []),
                          ...(f11Feedback.length > 0 ? (feedback ? ['', '--- Avaliação detalhada ---'] : []).concat(f11Feedback) : []),
                        ].filter(Boolean).join('\n')
                        navigator.clipboard.writeText(text)
                        setCopiedFeedback(true)
                        setTimeout(() => setCopiedFeedback(false), 2000)
                      }}
                      className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-gray-500 hover:text-gray-700 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                      style={font}
                    >
                      {copiedFeedback ? <CheckCircle className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      {copiedFeedback ? "Copiado!" : "Copiar feedback"}
                    </button>
                  </div>
                  {feedback?.main_message && (
                    <p className="text-[11px] text-gray-700 leading-relaxed mb-3" style={font}>{feedback.main_message}</p>
                  )}

                  {!feedback && f11Report?.response_analyses && (
                    <div className="mb-3 space-y-1">
                      {f11Report.response_analyses.slice(0, 3).map((a: any, i: number) => (
                        a.feedback && (
                          <p key={i} className="text-[11px] text-gray-700 leading-relaxed" style={font}>{a.feedback}</p>
                        )
                      ))}
                    </div>
                  )}

                  {feedback?.technical_strengths && feedback.technical_strengths.length > 0 && (
                    <div className="mb-2">
                      <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Pontos Fortes Técnicos:</p>
                      {feedback.technical_strengths.map((s: string, i: number) => (
                        <div key={i} className="flex items-start gap-1.5 mb-0.5">
                          <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: '#166534' }} />
                          <p className="text-[11px] text-gray-700" style={font}>{s}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {feedback?.behavioral_strengths && feedback.behavioral_strengths.length > 0 && (
                    <div className="mb-2">
                      <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Pontos Fortes Comportamentais:</p>
                      {feedback.behavioral_strengths.map((s: string, i: number) => (
                        <div key={i} className="flex items-start gap-1.5 mb-0.5">
                          <Star className="w-3 h-3 mt-0.5 flex-shrink-0 text-gray-400" />
                          <p className="text-[11px] text-gray-700" style={font}>{s}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {feedback?.development_opportunities && feedback.development_opportunities.length > 0 && (
                    <div className="mb-2">
                      <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Oportunidades de Desenvolvimento:</p>
                      {feedback.development_opportunities.map((d: string, i: number) => (
                        <div key={i} className="flex items-start gap-1.5 mb-0.5">
                          <BookOpen className="w-3 h-3 mt-0.5 flex-shrink-0 text-blue-500" />
                          <p className="text-[11px] text-gray-700" style={font}>{d}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {feedback?.personalized_tip && (
                    <div className="p-2 rounded-lg mt-2" style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', border: '1px solid rgba(96, 190, 209, 0.2)' }}>
                      <p className="text-[10px] font-medium mb-0.5 text-wedo-cyan" style={{ ...font }}>Dica Personalizada</p>
                      <p className="text-[11px] text-gray-700" style={font}>{feedback.personalized_tip}</p>
                    </div>
                  )}

                  {feedback?.next_steps && (
                    <div className="mt-2 p-2 rounded-lg bg-gray-100">
                      <p className="text-[10px] font-medium text-gray-500 mb-0.5" style={font}>Próximos Passos:</p>
                      <p className="text-[11px] text-gray-700" style={font}>{feedback.next_steps}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {activeTab === 'comparativo' && (
            <div className="p-4 space-y-4">
              {/* Pool averages */}
              {vacancyRanking && vacancyRanking.total_screened > 0 ? (
                <>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Média Geral', value: vacancyRanking.averages.overall, icon: BarChart3 },
                      { label: 'Média Técnica', value: vacancyRanking.averages.technical, icon: Target },
                      { label: 'Média Comportamental', value: vacancyRanking.averages.behavioral, icon: Brain },
                    ].map(({ label, value, icon: Icon }) => (
                      <div key={label} className="border border-gray-200 rounded-md p-3 dark:border-gray-700">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Icon className="w-3.5 h-3.5 text-gray-400" />
                          <span className="text-[10px] text-gray-500 uppercase tracking-wide" style={font}>{label}</span>
                        </div>
                        <p className="text-lg font-semibold text-gray-900 dark:text-gray-100" style={font}>
                          {value.toFixed(1)}<span className="text-xs text-gray-400">/10</span>
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Ranking table */}
                  <div className="border border-gray-200 rounded-md overflow-hidden dark:border-gray-700">
                    <div className="bg-gray-50 dark:bg-gray-800 px-3 py-2 flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <Trophy className="w-3.5 h-3.5 text-gray-500" />
                        <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-300" style={font}>
                          Ranking — {vacancyRanking.total_screened} candidato{vacancyRanking.total_screened !== 1 ? 's' : ''} avaliado{vacancyRanking.total_screened !== 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>
                    <div className="divide-y divide-gray-100 dark:divide-gray-700">
                      {vacancyRanking.ranking.map((entry) => {
                        const isCurrent = entry.candidate_id === candidate?.id
                        return (
                          <div
                            key={entry.result_id}
                            className={`flex items-center gap-3 px-3 py-2.5 ${isCurrent ? 'bg-gray-900 dark:bg-gray-700' : 'hover:bg-gray-50 dark:hover:bg-gray-800'}`}
                          >
                            {/* Rank badge */}
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${
                              entry.rank === 1 ? 'bg-yellow-100 text-yellow-700' :
                              entry.rank === 2 ? 'bg-gray-100 text-gray-600' :
                              entry.rank === 3 ? 'bg-orange-100 text-orange-700' :
                              isCurrent ? 'bg-white text-gray-900' : 'bg-gray-100 text-gray-500'
                            }`} style={font}>
                              {entry.rank}
                            </div>
                            {/* Name */}
                            <div className="flex-1 min-w-0">
                              <p className={`text-[11px] font-medium truncate ${isCurrent ? 'text-white' : 'text-gray-800 dark:text-gray-200'}`} style={font}>
                                {isCurrent ? `${entry.candidate_name} (você)` : entry.candidate_name}
                              </p>
                              {entry.candidate_title && (
                                <p className={`text-[10px] truncate ${isCurrent ? 'text-gray-300' : 'text-gray-400'}`} style={font}>{entry.candidate_title}</p>
                              )}
                            </div>
                            {/* Scores */}
                            <div className="flex items-center gap-3 flex-shrink-0">
                              <div className="text-right">
                                <p className={`text-[10px] ${isCurrent ? 'text-gray-400' : 'text-gray-400'}`} style={font}>Tec</p>
                                <p className={`text-[11px] font-semibold ${isCurrent ? 'text-white' : 'text-gray-700 dark:text-gray-300'}`} style={font}>{entry.technical_wsi.toFixed(1)}</p>
                              </div>
                              <div className="text-right">
                                <p className={`text-[10px] ${isCurrent ? 'text-gray-400' : 'text-gray-400'}`} style={font}>Comp</p>
                                <p className={`text-[11px] font-semibold ${isCurrent ? 'text-white' : 'text-gray-700 dark:text-gray-300'}`} style={font}>{entry.behavioral_wsi.toFixed(1)}</p>
                              </div>
                              <div className="text-right min-w-[36px]">
                                <p className={`text-[10px] ${isCurrent ? 'text-gray-400' : 'text-gray-400'}`} style={font}>WSI</p>
                                <p className={`text-[12px] font-bold ${isCurrent ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`} style={font}>{entry.overall_wsi.toFixed(1)}</p>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 gap-4">
                  <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-gray-400" />
                  </div>
                  <div className="text-center max-w-xs">
                    <p className="text-sm font-semibold text-gray-600" style={font}>Ranking e Comparativo</p>
                    <p className="text-xs text-gray-400 mt-1" style={font}>
                      O comparativo entre candidatos estará disponível quando houver 2 ou mais candidatos avaliados nesta vaga.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>

        <div className="flex-shrink-0 px-4 py-3 flex items-center justify-between border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-500" style={font}>Decisão do Recrutador</span>
          </div>
          <div className="flex items-center gap-2">
            {confirmReject ? (
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] text-red-600 font-medium" style={font}>Confirmar reprovação?</span>
                <button
                  onClick={async () => {
                    setRejecting(true)
                    await onReject?.(candidate)
                    setRejecting(false)
                    setConfirmReject(false)
                  }}
                  disabled={rejecting}
                  className="flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-medium rounded-full transition-colors disabled:opacity-50"
                  style={{ ...font, backgroundColor: '#EF4444', color: '#FFFFFF' }}
                >
                  {rejecting ? <Loader2 className="w-3 h-3 animate-spin" /> : <ThumbsDown className="w-3 h-3" />}
                  Sim, reprovar
                </button>
                <button
                  onClick={() => setConfirmReject(false)}
                  className="px-2.5 py-1.5 text-[11px] font-medium rounded-full transition-colors hover:bg-gray-100 border border-gray-200" style={{ ...font, backgroundColor: '#FFFFFF' }}
                >
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmReject(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors hover:bg-red-50 border border-gray-200" style={{ ...font, backgroundColor: '#FFFFFF', color: '#EF4444' }}
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
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md transition-colors hover:bg-gray-800 disabled:opacity-50 bg-gray-800" style={{ ...font, color: '#FFFFFF' }}
            >
              {approving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ThumbsUp className="w-3.5 h-3.5" />}
              Aprovar para Entrevista
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
