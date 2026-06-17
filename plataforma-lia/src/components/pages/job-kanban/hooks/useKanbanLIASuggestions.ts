"use client"

import { useEffect, useRef, useMemo } from "react"

interface DynamicStage {
  id: string
  displayName: string
  [key: string]: unknown
}

interface LIAMessage {
  id: string
  type: string
  content: string
  timestamp: number
}

interface KanbanCandidate extends Record<string, unknown> {
  id: string
  name?: string
  stage?: string
  movedAt?: string
  addedAt?: string
  daysInStage?: number
  score?: number
  wsiScore?: number
  lia_score?: number
  liaScore?: number
}

interface UseKanbanLIASuggestionsParams {
  dynamicStages: DynamicStage[]
  candidatesData: Record<string, KanbanCandidate[]>
  allTableCandidates: KanbanCandidate[]
  currentJob: Record<string, unknown> | null | undefined
  liaMessages: LIAMessage[]
  companyId: string
  setLiaMessages: (fn: (prev: LIAMessage[]) => LIAMessage[]) => void
}

export function useKanbanLIASuggestions({
  dynamicStages,
  candidatesData,
  allTableCandidates,
  currentJob,
  liaMessages,
  companyId,
  setLiaMessages,
}: UseKanbanLIASuggestionsParams) {
  const computedSuggestions = useMemo(() => {
    const suggestions: Array<{
      type: string; severity: string; candidate_id: string;
      candidate_name: string; message: string; suggested_action: string; stage: string
    }> = []
    const now = Date.now()
    dynamicStages.forEach(stage => {
      const stageCandidates = candidatesData[stage.id] || []
      stageCandidates.forEach((candidate) => {
        const addedDate = candidate.movedAt || candidate.addedAt
        const daysInStage = addedDate ? Math.floor((now - new Date(addedDate as string).getTime()) / (1000 * 60 * 60 * 24)) : 0
        if (daysInStage > 7) {
          suggestions.push({ type: 'stale_candidate', severity: 'warning', candidate_id: candidate.id, candidate_name: candidate.name || 'Candidato', message: `${candidate.name || 'Candidato'} está parado em "${stage.displayName}" há ${daysInStage} dias`, suggested_action: 'Considere avançar ou dar retorno', stage: stage.id })
        }
        const score = (candidate.lia_score || candidate.liaScore || 0) as number
        if (score >= 80) {
          suggestions.push({ type: 'high_score', severity: 'success', candidate_id: candidate.id, candidate_name: candidate.name || 'Candidato', message: `${candidate.name || 'Candidato'} tem score WSI alto (${Math.round(score)})`, suggested_action: 'Considere priorizar este candidato', stage: stage.id })
        }
        if (score > 0 && score < 40) {
          suggestions.push({ type: 'low_score', severity: 'danger', candidate_id: candidate.id, candidate_name: candidate.name || 'Candidato', message: `${candidate.name || 'Candidato'} tem score WSI baixo (${Math.round(score)})`, suggested_action: 'Avaliar permanência no processo', stage: stage.id })
        }
      })
    })
    return suggestions
  }, [dynamicStages, candidatesData])

  const hasShownProactiveSuggestion = useRef(false)
  const lastBriefingJobId = useRef<string | null>(null)

  useEffect(() => {
    if (currentJob?.id && currentJob.id !== lastBriefingJobId.current) {
      hasShownProactiveSuggestion.current = false
      lastBriefingJobId.current = currentJob.id as string
    }
  }, [currentJob?.id])

  useEffect(() => {
    if (liaMessages.length > 0 || hasShownProactiveSuggestion.current || !currentJob?.id) return
    hasShownProactiveSuggestion.current = true

    const buildBriefing = async () => {
      const total = allTableCandidates.length
      const stageMap: Record<string, number> = {}
      allTableCandidates.forEach(c => { const s = (c.stage || 'sourcing') as string; stageMap[s] = (stageMap[s] || 0) + 1 })
      const stageLabels: Record<string, string> = {
        sourcing: 'Sourcing', screening: 'Screening', interview_hr: 'Entrevista RH',
        interview_technical: 'Entrevista Técnica', interview_manager: 'Entrevista Gestor',
        offer: 'Proposta', hired: 'Contratado'
      }
      const pipelineLines = Object.entries(stageMap).map(([k, v]) => `${stageLabels[k] || k}: ${v}`).join(' | ')
      const staleCount = computedSuggestions.filter(s => s.type === 'stale_candidate').length
      const highScoreCount = computedSuggestions.filter(s => s.type === 'high_score').length
      const lowScoreCount = computedSuggestions.filter(s => s.type === 'low_score').length
      const atRiskCandidates = allTableCandidates.filter(c => ((c.daysInStage || 0) as number) > 14)
      const dropoutRiskCandidates = allTableCandidates.filter(c => ((c.daysInStage || 0) as number) > 10 && ((c.score || c.wsiScore || 0) as number) >= 70)

      const alertParts: string[] = []
      if (staleCount > 0) alertParts.push(`${staleCount} candidato${staleCount > 1 ? 's' : ''} parado${staleCount > 1 ? 's' : ''} ha mais de 7 dias`)
      if (atRiskCandidates.length > 0) alertParts.push(`${atRiskCandidates.length} candidato${atRiskCandidates.length > 1 ? 's' : ''} em risco (parado${atRiskCandidates.length > 1 ? 's' : ''} ha mais de 14 dias)`)
      if (dropoutRiskCandidates.length > 0) alertParts.push(`${dropoutRiskCandidates.length} candidato${dropoutRiskCandidates.length > 1 ? 's' : ''} com risco de desistencia (score alto + longo tempo de espera)`)
      if (highScoreCount > 0) alertParts.push(`${highScoreCount} candidato${highScoreCount > 1 ? 's' : ''} com score alto para priorizar`)
      if (lowScoreCount > 0) alertParts.push(`${lowScoreCount} candidato${lowScoreCount > 1 ? 's' : ''} com score baixo para revisar`)

      let mlSection = ''
      try {
        const jobPayload = { title: currentJob.title, department: currentJob.department, seniority: currentJob.seniority, location: currentJob.location, work_model: currentJob.workModel, employment_type: currentJob.employmentType }
        const [ttfRes, salRes] = await Promise.allSettled([
          fetch('/api/backend-proxy/ml/predict/time-to-fill', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ company_id: companyId, job_data: jobPayload }) }).then(r => r.ok ? r.json() : null),
          fetch('/api/backend-proxy/ml/predict/salary', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ company_id: companyId, job_data: jobPayload }) }).then(r => r.ok ? r.json() : null),
        ])
        const ttf = ttfRes.status === 'fulfilled' ? ttfRes.value : null
        const sal = salRes.status === 'fulfilled' ? salRes.value : null
        const mlParts: string[] = []
        if (ttf?.predicted_days) mlParts.push(`Tempo estimado: **${ttf.predicted_days} dias** (${ttf.range_min}-${ttf.range_max}d)`)
        if (sal?.suggested_min && sal?.suggested_max) {
          const fmt = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
          mlParts.push(`Faixa salarial sugerida: **${fmt(sal.suggested_min)} - ${fmt(sal.suggested_max)}** (percentil ${sal.market_percentile || '—'}%)`)
        }
        if (mlParts.length > 0) mlSection = `\n\n**Previsoes IA:**\n• ${mlParts.join('\n• ')}`
      } catch {}

      const sections: string[] = []
      sections.push(`**Pipeline:** ${total} candidato${total !== 1 ? 's' : ''} — ${pipelineLines}`)
      if (alertParts.length > 0) sections.push(`**Alertas:**\n• ${alertParts.join('\n• ')}`)
      if (mlSection) sections.push(mlSection.trim())
      if (dropoutRiskCandidates.length > 0) {
        const names = dropoutRiskCandidates.slice(0, 3).map(c => c.name).join(', ')
        sections.push(`**Acao sugerida:** Priorize contato com ${names}${dropoutRiskCandidates.length > 3 ? ` e mais ${dropoutRiskCandidates.length - 3}` : ''} para evitar perda de talentos qualificados.`)
      }
      sections.push('Posso ajudar com analises, comparacoes, previsoes de risco ou acoes. O que precisa?')
      const message = `Ola! Preparei o briefing desta vaga:\n\n${sections.join('\n\n')}`

      setLiaMessages(prev => {
        if (prev.length > 0) return prev
        return [{ id: `proactive-${Date.now()}`, type: 'response', content: message, timestamp: Date.now() }]
      })
    }

    buildBriefing()
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: allTableCandidates.length avoids full array dep; currentJob.* fields omitted intentionally
  }, [currentJob?.id, allTableCandidates.length, computedSuggestions, liaMessages.length, companyId, setLiaMessages])

  return { computedSuggestions, hasShownProactiveSuggestion, lastBriefingJobId }
}
