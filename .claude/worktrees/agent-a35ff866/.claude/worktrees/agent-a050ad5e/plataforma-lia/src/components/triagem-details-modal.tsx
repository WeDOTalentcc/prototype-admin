"use client"

import { useState, useEffect } from "react"
import { formatScorePercent } from '@/lib/design-tokens'
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  X, Brain, MessageSquare, Target, TrendingUp, Award, AlertCircle,
  CheckCircle, Clock, FileText, BarChart3, User,
  ChevronDown, ChevronUp, ThumbsUp,
  ThumbsDown, Mic, Phone,
  Code, BookOpen, Zap, Trophy, ArrowUp, ArrowDown, Minus,
  Download, Share2, Loader2, Star
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

const getClassificationColor = (classification: string) => {
  switch (classification) {
    case 'excelente': return { bg: 'rgba(34, 197, 94, 0.12)', text: '#166534' }
    case 'alto': return { bg: 'rgba(16, 185, 129, 0.12)', text: '#065F46' }
    case 'medio': return { bg: 'rgba(234, 179, 8, 0.12)', text: '#854D0E' }
    case 'regular': return { bg: 'rgba(249, 115, 22, 0.12)', text: '#9A3412' }
    case 'baixo': return { bg: 'rgba(239, 68, 68, 0.12)', text: '#991B1B' }
    default: return { bg: 'rgba(96, 190, 209, 0.12)', text: '#374151' }
  }
}

const getDecisionDisplay = (decision?: string) => {
  switch (decision) {
    case 'aprovado': return { label: 'Aprovado', icon: ThumbsUp, color: '#166534', bg: 'rgba(34, 197, 94, 0.12)' }
    case 'aguardando': return { label: 'Em Avaliação', icon: Clock, color: '#854D0E', bg: 'rgba(234, 179, 8, 0.12)' }
    case 'nao_aprovado': return { label: 'Não Aprovado', icon: ThumbsDown, color: '#991B1B', bg: 'rgba(239, 68, 68, 0.12)' }
    default: return { label: 'Pendente', icon: Clock, bg: '#F3F4F6' }
  }
}

const wsiToPercent = (score: number) => Math.round((score / 5) * 100)

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

  const canTriggerFeedback = details && (
    details.scores.classification === 'regular' || details.scores.classification === 'medio'
  )
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
                  <p style="font-size:13px;"><strong>Classificação:</strong> ${details.scores.classification.charAt(0).toUpperCase() + details.scores.classification.slice(1)}
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
                  <p className="text-base font-bold text-gray-950 dark:text-gray-50" style={font}>{scores.overall_wsi.toFixed(1)}/5.0</p>
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
                    {scores.classification.charAt(0).toUpperCase() + scores.classification.slice(1)}
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
                <div className="flex items-center gap-3 mt-3">
                  <Badge variant="outline" className="text-[10px]">
                    {sessionInfo.screening_type === 'voice' ? '🎤 Triagem por Voz' : '💬 Triagem por Texto'}
                  </Badge>
                  {scores.percentile && (
                    <span className="text-[10px] text-gray-500 flex items-center gap-1" style={font}>
                      <TrendingUp className="w-3 h-3" />
                      Top {100 - scores.percentile}%
                    </span>
                  )}
                  {sessionInfo.started_at && (
                    <span className="text-[10px] text-gray-500" style={font}>
                      {new Date(sessionInfo.started_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>
              </div>


              <div className="border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px', overflow: 'hidden' }}>
                <div className="cursor-pointer p-3 flex items-center justify-between hover:bg-gray-50 transition-colors" onClick={() => toggleSection('responses')} style={{ borderBottom: expandedSections.has('responses') ? '1px solid #F3F4F6' : 'none' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 text-gray-950 dark:text-gray-50" style={font}>
                    <MessageSquare className="w-4 h-4 text-gray-700" />
                    Respostas por Competência ({responses.length})
                  </h3>
                  {expandedSections.has('responses') ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                </div>
                {expandedSections.has('responses') && (
                  <div className="p-3 space-y-3 max-h-96 overflow-y-auto bg-gray-50">
                    {responses.map((resp, idx) => (
                      <div key={idx} className="p-3 rounded-lg border border-gray-100" style={{ backgroundColor: '#FFFFFF' }}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-semibold text-gray-950" style={font}>{resp.competency}</span>
                            <Badge variant="outline" className="text-[9px] px-1.5">{getFrameworkLabel(resp.question.framework)}</Badge>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-[11px] font-bold" style={{ ...font, color: resp.scores.final_score >= 4 ? '#166534' : resp.scores.final_score >= 3 ? '#854D0E' : '#991B1B' }}>
                              {resp.scores.final_score.toFixed(1)}/5.0
                            </span>
                          </div>
                        </div>

                        <div className="mb-2 p-2 rounded bg-gray-100">
                          <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Pergunta:</p>
                          <p className="text-[11px] text-gray-700" style={font}>{resp.question.text}</p>
                        </div>

                        <div className="mb-2">
                          <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Resposta do Candidato:</p>
                          <p className="text-[11px] text-gray-800 leading-relaxed" style={font}>{resp.response_text}</p>
                        </div>

                        <div className="grid grid-cols-4 gap-2 mb-2">
                          {resp.scores.autodeclaration != null && (
                            <div className="text-center p-1.5 rounded border border-gray-100">
                              <p className="text-[9px] text-gray-500" style={font}>Autodeclaração</p>
                              <p className="text-[11px] font-bold text-gray-950" style={font}>{resp.scores.autodeclaration.toFixed(1)}</p>
                            </div>
                          )}
                          {resp.scores.context != null && (
                            <div className="text-center p-1.5 rounded border border-gray-100">
                              <p className="text-[9px] text-gray-500" style={font}>Contexto</p>
                              <p className="text-[11px] font-bold text-gray-950" style={font}>{resp.scores.context.toFixed(1)}</p>
                            </div>
                          )}
                          {resp.scores.bloom_level != null && (
                            <div className="text-center p-1.5 rounded border border-gray-100">
                              <p className="text-[9px] text-gray-500" style={font}>Bloom</p>
                              <p className="text-[11px] font-bold text-gray-950" style={font}>Nível {resp.scores.bloom_level}</p>
                            </div>
                          )}
                          {resp.scores.dreyfus_level != null && (
                            <div className="text-center p-1.5 rounded border border-gray-100">
                              <p className="text-[9px] text-gray-500" style={font}>Dreyfus</p>
                              <p className="text-[11px] font-bold text-gray-950" style={font}>Nível {resp.scores.dreyfus_level}</p>
                            </div>
                          )}
                        </div>

                        {resp.evidences && resp.evidences.length > 0 && (
                          <div className="mb-1.5">
                            <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Evidências:</p>
                            <div className="flex flex-wrap gap-1">
                              {resp.evidences.map((ev, i) => (
                                <span key={i} className="inline-flex items-center px-1.5 py-0.5 text-[9px] rounded-full" style={{ ...font }}>
                                  <CheckCircle className="w-2.5 h-2.5 mr-0.5" /> {ev}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        <p className="text-[10px] text-gray-500 italic" style={font}>{resp.justification}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'parecer' && (
            <div className="space-y-3">
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
                          <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Pontos Fortes:</p>
                          {report.technical_analysis.pontos_fortes.map((p: string, i: number) => (
                            <div key={i} className="flex items-start gap-1.5 mb-1">
                              <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: '#166534' }} />
                              <p className="text-[11px] text-gray-700" style={font}>{p}</p>
                            </div>
                          ))}
                        </div>
                      )}
                      {report.technical_analysis.gaps && report.technical_analysis.gaps.length > 0 && (
                        <div className="mb-2">
                          <p className="text-[10px] font-medium text-gray-500 mb-1" style={font}>Gaps Identificados:</p>
                          {report.technical_analysis.gaps.map((g: string, i: number) => (
                            <div key={i} className="flex items-start gap-1.5 mb-1">
                              <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0 text-amber-500" />
                              <p className="text-[11px] text-gray-700" style={font}>{g}</p>
                            </div>
                          ))}
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

                  {report.behavioral_analysis && Object.keys(report.behavioral_analysis).length > 0 && (
                    <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                      <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                        <User className="w-4 h-4 text-gray-700" />
                        Análise Comportamental
                      </h3>
                      <div className="space-y-2">
                        {Object.entries(report.behavioral_analysis).map(([key, val]: [string, any]) => (
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
                  )}

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

              {feedback && (
                <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                    <MessageSquare className="w-4 h-4 text-wedo-cyan" />
                    Feedback para o Candidato
                  </h3>
                  <p className="text-[11px] text-gray-700 leading-relaxed mb-3" style={font}>{feedback.main_message}</p>

                  {feedback.technical_strengths && feedback.technical_strengths.length > 0 && (
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

                  {feedback.behavioral_strengths && feedback.behavioral_strengths.length > 0 && (
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

                  {feedback.development_opportunities && feedback.development_opportunities.length > 0 && (
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

                  {feedback.personalized_tip && (
                    <div className="p-2 rounded-lg mt-2" style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', border: '1px solid rgba(96, 190, 209, 0.2)' }}>
                      <p className="text-[10px] font-medium mb-0.5 text-wedo-cyan" style={{ ...font }}>Dica Personalizada</p>
                      <p className="text-[11px] text-gray-700" style={font}>{feedback.personalized_tip}</p>
                    </div>
                  )}

                  {feedback.next_steps && (
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
            <div className="space-y-3">
              {ranking?.ranked && (
                <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                    <Trophy className="w-4 h-4 text-gray-700" />
                    Posição no Ranking
                  </h3>
                  <div className="text-center py-3">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-full mb-2" style={{ backgroundColor: 'rgba(96, 190, 209, 0.12)' }}>
                      <Trophy className="w-7 h-7 text-gray-700" />
                    </div>
                    <p className="text-2xl font-bold text-gray-950" style={font}>#{ranking.rank}</p>
                    <p className="text-[11px] mt-1 text-gray-500" style={font}>de {ranking.total} candidatos triados</p>
                    {scores.percentile && (
                      <div className="mt-2 flex items-center justify-center gap-2">
                        <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded-full" style={{ backgroundColor: classColors.bg, color: classColors.text, ...font }}>
                          Top {100 - scores.percentile}%
                        </span>
                        {vacancyRanking && scores.overall_wsi > vacancyRanking.averages.overall && (
                          <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded-full text-gray-800" style={{ ...font }}>
                            Acima da Média
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {vacancyRanking && (
                    <div className="mt-3 space-y-1.5">
                      <div className="flex items-center justify-between p-2 rounded-md border border-gray-100">
                        <span className="text-[10px] text-gray-500" style={font}>Melhor que</span>
                        <span className="text-[10px] font-bold" style={{ ...font }}>{scores.percentile}% dos candidatos</span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-md border border-gray-100">
                        <span className="text-[10px] text-gray-500" style={font}>Score vs Média</span>
                        <span className="text-[10px] font-bold" style={{ ...font, color: scores.overall_wsi > vacancyRanking.averages.overall ? '#166534' : '#991B1B' }}>
                          {scores.overall_wsi > vacancyRanking.averages.overall ? '+' : ''}{(scores.overall_wsi - vacancyRanking.averages.overall).toFixed(2)} pontos
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-md border border-gray-100">
                        <span className="text-[10px] text-gray-500" style={font}>Classificação</span>
                        <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded-full" style={{ backgroundColor: classColors.bg, color: classColors.text, ...font }}>
                          {scores.classification.charAt(0).toUpperCase() + scores.classification.slice(1)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {vacancyRanking && (
                <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                    <BarChart3 className="w-4 h-4 text-gray-700" />
                    Comparação com Outros Candidatos
                  </h3>
                  <div className="space-y-3">
                    {[
                      { label: 'Score Geral', candidate: scores.overall_wsi, avg: vacancyRanking.averages.overall },
                      { label: 'Comp. Técnicas', candidate: scores.technical_wsi, avg: vacancyRanking.averages.technical },
                      { label: 'Comp. Comportamentais', candidate: scores.behavioral_wsi, avg: vacancyRanking.averages.behavioral },
                    ].map(metric => (
                      <div key={metric.label}>
                        <p className="text-[11px] font-medium mb-1 text-gray-950" style={font}>{metric.label}</p>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] w-16 text-gray-500" style={font}>Candidato</span>
                            <div className="flex-1 h-5 rounded-full relative overflow-hidden bg-gray-100">
                              <div className="h-5 rounded-full flex items-center justify-end pr-1.5 bg-gray-900" style={{ width: `${wsiToPercent(metric.candidate)}%` }}>
                                <span className="text-[10px] text-white font-bold" style={font}>{metric.candidate.toFixed(1)}</span>
                              </div>
                            </div>
                            {metric.candidate > metric.avg ? <ArrowUp className="w-3 h-3" style={{ color: '#166534' }} /> :
                             metric.candidate < metric.avg ? <ArrowDown className="w-3 h-3 text-gray-400" /> :
                             <Minus className="w-3 h-3 text-gray-400" />}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] w-16 text-gray-500" style={font}>Média</span>
                            <div className="flex-1 h-3 rounded-full relative overflow-hidden bg-gray-100">
                              <div className="h-3 rounded-full flex items-center justify-end pr-1.5 bg-gray-400" style={{ width: `${wsiToPercent(metric.avg)}%` }}>
                                <span className="text-[10px] text-white" style={font}>{metric.avg.toFixed(1)}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {vacancyRanking && vacancyRanking.ranking.length > 0 && (
                <div className="p-3 border border-gray-100" style={{ backgroundColor: '#FFFFFF', borderRadius: '8px' }}>
                  <h3 className="text-xs font-semibold flex items-center gap-2 mb-2 text-gray-950" style={font}>
                    <Award className="w-4 h-4 text-gray-700" />
                    Ranking Completo ({vacancyRanking.total_screened} candidatos)
                  </h3>
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {vacancyRanking.ranking.map((r) => {
                      const isCurrentCandidate = r.candidate_id === candidate.id
                      const rColors = getClassificationColor(r.classification)
                      return (
                        <div
                          key={r.result_id}
                          className="flex items-center justify-between p-2 rounded-md transition-colors"
                          style={{
                            backgroundColor: isCurrentCandidate ? 'rgba(96, 190, 209, 0.08)' : '#F9FAFB',
                            border: isCurrentCandidate ? '1px solid rgba(96, 190, 209, 0.3)' : '1px solid #F3F4F6'
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold" style={{ backgroundColor: isCurrentCandidate ? '#1F2937' : '#F3F4F6', color: isCurrentCandidate ? '#FFFFFF' : '#6B7280' }}>
                              {r.rank}
                            </span>
                            <div>
                              <p className={`text-[11px] ${isCurrentCandidate ? 'font-bold' : 'font-medium'} text-gray-900`} style={font}>
                                {r.candidate_name} {isCurrentCandidate && '(atual)'}
                              </p>
                              <p className="text-[9px] text-gray-500" style={font}>{r.candidate_title}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] font-bold text-gray-900" style={font}>{r.overall_wsi.toFixed(1)}</span>
                            <span className="inline-flex px-1.5 py-0.5 text-[9px] font-medium rounded-full" style={{ backgroundColor: rColors.bg, color: rColors.text, ...font }}>
                              {r.classification}
                            </span>
                          </div>
                        </div>
                      )
                    })}
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
