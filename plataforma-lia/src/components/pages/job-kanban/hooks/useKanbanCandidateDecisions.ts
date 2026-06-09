"use client"

import { type KanbanCandidate, type DynamicStage } from "@/components/kanban"
import { type KanbanJob } from "@/components/pages/job-kanban/types"
import { toast } from "sonner"

interface RubricCriterion {
  name: string
  score: number
  weight: number
  details: string
}

interface RubricEvaluationData {
  overall_score: number
  recommendation: 'approve' | 'review' | 'reject'
  summary: string
  criteria: RubricCriterion[]
}

export interface KanbanCandidateDecisionsContext {
  toast: typeof import("sonner").toast
  job: KanbanJob | null
  dynamicStages: DynamicStage[]
  setCandidatesData: (updater: (prev: Record<string, KanbanCandidate[]>) => Record<string, KanbanCandidate[]>) => void
  setShowDecisionFlowModal: (open: boolean) => void
  setDecisionFlowCandidate: (candidate: KanbanCandidate | null) => void
  decisionFlowCandidate: KanbanCandidate | null
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  setTransitionInitialPrompt: (prompt: string | undefined) => void
  onCloseTriagem: () => void
  setRubricCandidate: (candidate: KanbanCandidate) => void
  setShowRubricModal: (open: boolean) => void
  setRubricEvaluationData: (data: RubricEvaluationData) => void
  setDecisionFlowType: (type: string) => void
}

export function useKanbanCandidateDecisions(ctx: KanbanCandidateDecisionsContext) {
  const {
    toast,
    job,
    dynamicStages,
    setCandidatesData,
    setShowDecisionFlowModal,
    setDecisionFlowCandidate,
    decisionFlowCandidate,
    openTransition,
    setTransitionInitialPrompt,
    onCloseTriagem,
    setRubricCandidate,
    setShowRubricModal,
    setRubricEvaluationData,
    setDecisionFlowType,
  } = ctx

  const handleApproveCandidate = async (candidate: KanbanCandidate) => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job?.id?.toString() || null,
          decision: 'approved'
        })
      })

      if (response.ok) {
        const data = await response.json()
        const targetStage = data.new_stage || 'Triagem'

        const stageMapping: Record<string, string> = {
          'Triagem': 'screening',
          'Entrevista': 'interview_hr',
          'Entrevista RH': 'interview_hr',
          'Long List': 'long_list',
          'Short List': 'short_list',
        }
        const targetStageId = stageMapping[targetStage] || 'screening'

        setCandidatesData(prev => {
          const currentStage = Object.keys(prev).find(stage =>
            prev[stage]?.some((c: KanbanCandidate) => c.id === candidate.id)
          )
          if (!currentStage) return prev

          const newData = { ...prev }
          newData[currentStage] = newData[currentStage].filter((c: KanbanCandidate) => c.id !== candidate.id)
          const updatedCandidate: KanbanCandidate = { ...candidate, stage: targetStageId, status: 'approved_screening' }
          newData[targetStageId] = [...(newData[targetStageId] || []), updatedCandidate]
          return newData
        })

        toast.success('Candidato aprovado', { description: `${candidate.name} foi movido para ${targetStage}.` })
      } else {
        const errorData = await response.json().catch(() => ({}))

        if (errorData.detail?.error === 'missing_contact_info') {
          toast.error('Dados de contato incompletos', { description: `${candidate.name} não possui email ou telefone válido. Adicione um contato antes de aprovar.` })
        } else {
          toast.error('Erro ao aprovar', { description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar o candidato.' })
        }
      }
    } catch (error) {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
    }
  }

  const handleRejectCandidate = async (candidate: KanbanCandidate) => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job?.id?.toString() || null,
          decision: 'rejected',
          reason: 'Reprovado via análise'
        })
      })

      const moveToRejected = () => {
        setCandidatesData(prev => {
          const currentStage = Object.keys(prev).find(stage =>
            prev[stage]?.some((c: KanbanCandidate) => c.id === candidate.id)
          )
          if (!currentStage) return prev

          const newData = { ...prev }
          newData[currentStage] = newData[currentStage].filter((c: KanbanCandidate) => c.id !== candidate.id)
          const updatedCandidate: KanbanCandidate = { ...candidate, stage: 'rejected', status: 'rejected_screening' }
          newData['rejected'] = [...(newData['rejected'] || []), updatedCandidate]
          return newData
        })
      }

      if (response.ok) {
        const data = await response.json()
        toast.error('Candidato reprovado', { description: `${candidate.name} foi movido para ${data.new_stage || 'Reprovados'}.` })
        moveToRejected()
      } else {
        const errorData = await response.json().catch(() => ({}))
        toast.error('Erro ao reprovar', { description: errorData.error || 'Não foi possível reprovar o candidato.' })
      }
    } catch (error) {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
    }
  }

  const handleApproveFromScreening = async (candidate: KanbanCandidate) => {
    const interviewStage = dynamicStages.find(s =>
      s.id.startsWith('interview') || s.id.includes('entrevista')
    )
    const targetStage = interviewStage?.id || 'interview_hr'
    const targetDisplayName = interviewStage?.displayName || 'Entrevista RH'

    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job?.id?.toString() || null,
          decision: 'approved'
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        if (errorData.detail?.error === 'missing_contact_info') {
          toast.error('Dados de contato incompletos', { description: `${candidate.name} não possui email ou telefone válido. Adicione um contato antes de aprovar.` })
        } else {
          toast.error('Erro ao aprovar', { description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar o candidato.' })
        }
        return
      }
    } catch (error) {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
      return
    }

    const scoreInfo = candidate.wsiScore || candidate.score
    const promptParts = [
      `${candidate.name} foi aprovado na triagem`,
      scoreInfo ? ` com score de ${scoreInfo}%` : '',
      ` e avança para "${targetDisplayName}".`,
      scoreInfo && Number(scoreInfo) >= 85 ? ` Excelente aproveitamento — um dos melhores candidatos desta triagem.` : '',
      ` Vou entrar em contato com o candidato pelo canal configurado (email/WhatsApp) e agendar a entrevista conforme sua agenda disponível.`,
      ` Se quiser sugerir um horário ou data específica, escreva aqui que vou priorizar. Caso contrário, é só confirmar que eu cuido de tudo.`,
    ]
    setTransitionInitialPrompt(promptParts.join(''))

    const kanbanCandidate: KanbanCandidate = {
      id: candidate.id,
      name: candidate.name,
      role: candidate.role,
      avatar: candidate.avatar,
      score: candidate.wsiScore || candidate.score,
      email: candidate.email,
      phone: candidate.phone,
    }

    openTransition([kanbanCandidate], 'screening', targetStage)
  }

  const handleRejectFromScreening = async (candidate: KanbanCandidate) => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: job?.id?.toString() || null,
          decision: 'rejected',
          reason: 'Reprovado via análise de triagem'
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        toast.error('Erro ao reprovar', { description: errorData.detail?.message || errorData.error || 'Não foi possível registrar a reprovação.' })
        return
      }
    } catch (error) {
      toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
      return
    }

    const scoreInfo = candidate.wsiScore || candidate.score
    const promptParts = [
      `O recrutador decidiu reprovar ${candidate.name} após a triagem`,
      scoreInfo ? ` (score: ${scoreInfo}%)` : '',
      `. Este candidato será movido para "Reprovados".`,
      ` Sugira um motivo de reprovação (ex: perfil desalinhado, experiência insuficiente, competências técnicas abaixo do esperado).`,
      ` Pergunte se o recrutador deseja enviar feedback construtivo ao candidato e por qual canal (email ou WhatsApp).`,
    ]
    setTransitionInitialPrompt(promptParts.join(''))

    const kanbanCandidate: KanbanCandidate = {
      id: candidate.id,
      name: candidate.name,
      role: candidate.role,
      avatar: candidate.avatar,
      score: candidate.wsiScore || candidate.score,
      email: candidate.email,
      phone: candidate.phone,
    }

    openTransition([kanbanCandidate], 'screening', 'rejected')
  }

  const handleDecisionFlowConfirm = async (action: string, feedbackMessage?: string, channel?: string) => {
    if (!decisionFlowCandidate) return

    const candidate = decisionFlowCandidate

    if (action === 'approve_to_triage' || action === 'approve_to_interview') {
      await handleApproveCandidate(candidate)
    } else if (action.startsWith('reject')) {
      await handleRejectCandidate(candidate)
      if (action === 'reject_with_feedback' && feedbackMessage) {
        toast.success('Feedback enviado', { description: `Mensagem de feedback enviada para ${candidate.name} via ${channel === 'whatsapp' ? 'WhatsApp' : 'Email'}.` })
      }
    } else if (action === 'confirm_hire') {
      try {
        const transitionResp = await fetch('/api/backend-proxy/transition/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vacancy_candidate_id: candidate.id,
            to_stage: 'hired',
            action: 'lia_auto',
            action_behavior: 'conclusion_hired',
            vacancy_id: job?.id?.toString() ?? null,
            channel: 'email',
          })
        })

        if (transitionResp.ok) {
          setCandidatesData(prev => {
            const currentStage = Object.keys(prev).find(stage =>
              prev[stage]?.some((c: KanbanCandidate) => c.id === candidate.id)
            )
            if (!currentStage) return prev

            const newData = { ...prev }
            newData[currentStage] = newData[currentStage].filter((c: KanbanCandidate) => c.id !== candidate.id)
            const updatedCandidate: KanbanCandidate = { ...candidate, stage: 'hired', status: 'hired' }
            newData['hired'] = [...(newData['hired'] || []), updatedCandidate]
            return newData
          })

          // fire-and-forget: welcome email ao contratado
          fetch('/api/backend-proxy/automation/handle-trigger/candidate-hired', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              candidate_id: candidate.id,
              vacancy_id: job?.id?.toString() ?? null,
              candidate_name: candidate.name,
              candidate_email: candidate.email ?? null,
            })
          }).catch(() => { /* fire-and-forget */ })

          toast.success('Candidato contratado!', { description: `${candidate.name} foi movido para Contratados.` })
        } else {
          const errorData = await transitionResp.json().catch(() => ({}))
          toast.error('Erro ao contratar', { description: errorData.detail?.message || errorData.error || 'Não foi possível registrar a contratação.' })
        }
      } catch {
        toast.error('Erro de conexão', { description: 'Não foi possível conectar ao servidor.' })
      }
    }

    setShowDecisionFlowModal(false)
    setDecisionFlowCandidate(null)
  }

  const handleTriagemApprove = async (candidate: KanbanCandidate) => {
    onCloseTriagem()
    await handleApproveFromScreening(candidate)
  }

  const handleTriagemReject = async (candidate: KanbanCandidate) => {
    onCloseTriagem()
    await handleRejectFromScreening(candidate)
  }

  const openDecisionFlowModal = (candidate: KanbanCandidate, action: 'approve' | 'reject') => {
    const stage = (candidate.stage || 'funil').toLowerCase()
    const isTriagemCompleted = stage === 'triagem' || stage === 'screening'

    setDecisionFlowCandidate(candidate)

    if (action === 'approve') {
      if (isTriagemCompleted) {
        setDecisionFlowType('approve_to_interview')
      } else {
        setDecisionFlowType('approve_to_triage')
      }
    } else {
      if (isTriagemCompleted) {
        setDecisionFlowType('reject_post_triage')
      } else {
        setDecisionFlowType('reject_pre_triage')
      }
    }

    setShowDecisionFlowModal(true)
  }

  const handleOpenAnalysis = async (candidate: KanbanCandidate) => {
    setRubricCandidate(candidate)
    setShowRubricModal(true)

    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/rubric-evaluation`)
      if (response.ok) {
        const data = await response.json()
        setRubricEvaluationData(data)
      } else {
        setRubricEvaluationData({
          overall_score: 0,
          recommendation: 'review',
          summary: 'Não foi possível carregar a avaliação deste candidato. A análise detalhada não está disponível no momento.',
          criteria: [],
          _unavailable: true,
        } as RubricEvaluationData)
      }
    } catch {
      setRubricEvaluationData({
        overall_score: 0,
        recommendation: 'review',
        summary: 'Erro ao carregar avaliação. Tente novamente mais tarde.',
        criteria: [],
        _unavailable: true,
      } as RubricEvaluationData)
    }
  }

  return {
    handleDecisionFlowConfirm,
    handleApproveCandidate,
    handleRejectCandidate,
    handleApproveFromScreening,
    handleRejectFromScreening,
    handleTriagemApprove,
    handleTriagemReject,
    handleOpenAnalysis,
    openDecisionFlowModal,
  }
}
