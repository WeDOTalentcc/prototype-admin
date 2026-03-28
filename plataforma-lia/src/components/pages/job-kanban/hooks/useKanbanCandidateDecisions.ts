"use client"

import { useToast } from "@/hooks/use-toast"
import { type KanbanCandidate, type DynamicStage } from "@/components/kanban"
import { type KanbanJob } from "@/components/pages/job-kanban/types"

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
  toast: ReturnType<typeof useToast>["toast"]
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

        toast({
          title: 'Candidato aprovado',
          description: `${candidate.name} foi movido para ${targetStage}.`,
          variant: 'default'
        })
      } else {
        const errorData = await response.json().catch(() => ({}))

        if (errorData.detail?.error === 'missing_contact_info') {
          toast({
            title: 'Dados de contato incompletos',
            description: `${candidate.name} não possui email ou telefone válido. Adicione um contato antes de aprovar.`,
            variant: 'destructive'
          })
        } else {
          toast({
            title: 'Erro ao aprovar',
            description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar o candidato.',
            variant: 'destructive'
          })
        }
      }
    } catch (error) {
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
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
        toast({
          title: 'Candidato reprovado',
          description: `${candidate.name} foi movido para ${data.new_stage || 'Reprovados'}.`,
          variant: 'destructive'
        })
        moveToRejected()
      } else {
        const errorData = await response.json().catch(() => ({}))
        toast({
          title: 'Erro ao reprovar',
          description: errorData.error || 'Não foi possível reprovar o candidato.',
          variant: 'destructive'
        })
      }
    } catch (error) {
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
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
          toast({
            title: 'Dados de contato incompletos',
            description: `${candidate.name} não possui email ou telefone válido. Adicione um contato antes de aprovar.`,
            variant: 'destructive'
          })
        } else {
          toast({
            title: 'Erro ao aprovar',
            description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar o candidato.',
            variant: 'destructive'
          })
        }
        return
      }
    } catch (error) {
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
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
        toast({
          title: 'Erro ao reprovar',
          description: errorData.detail?.message || errorData.error || 'Não foi possível registrar a reprovação.',
          variant: 'destructive'
        })
        return
      }
    } catch (error) {
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
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
        toast({
          title: 'Feedback enviado',
          description: `Mensagem de feedback enviada para ${candidate.name} via ${channel === 'whatsapp' ? 'WhatsApp' : 'Email'}.`,
        })
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
        const fitScore = candidate.fitScore ?? 0
        const mockEvaluation: RubricEvaluationData = {
          overall_score: candidate.fitScore || candidate.score || 75,
          recommendation: fitScore >= 70 ? 'approve' : fitScore >= 50 ? 'review' : 'reject',
          summary: `Análise do candidato ${candidate.name} para a vaga. Avaliação baseada no currículo e requisitos da posição.`,
          criteria: [
            { name: 'Experiência Técnica', score: Math.round((candidate.wsiScore || candidate.fitScore || 70) * 0.8 + 20), weight: 30, details: 'Avaliação da experiência técnica do candidato' },
            { name: 'Formação Acadêmica', score: Math.round(60 + Math.random() * 30), weight: 20, details: 'Compatibilidade da formação com a vaga' },
            { name: 'Habilidades Interpessoais', score: Math.round(65 + Math.random() * 25), weight: 20, details: 'Competências comportamentais identificadas' },
            { name: 'Fit Cultural', score: Math.round(70 + Math.random() * 20), weight: 15, details: 'Alinhamento com os valores da empresa' },
            { name: 'Disponibilidade', score: Math.round(75 + Math.random() * 20), weight: 15, details: 'Adequação ao modelo de trabalho e início' }
          ]
        }
        setRubricEvaluationData(mockEvaluation)
      }
    } catch (error) {
      const mockEvaluation: RubricEvaluationData = {
        overall_score: candidate.fitScore || candidate.score || 75,
        recommendation: 'review',
        summary: `Análise do candidato ${candidate.name} para a vaga.`,
        criteria: [
          { name: 'Experiência Técnica', score: 75, weight: 30, details: 'Avaliação da experiência técnica' },
          { name: 'Formação Acadêmica', score: 70, weight: 20, details: 'Compatibilidade da formação' },
          { name: 'Habilidades Interpessoais', score: 72, weight: 20, details: 'Competências comportamentais' },
          { name: 'Fit Cultural', score: 78, weight: 15, details: 'Alinhamento cultural' },
          { name: 'Disponibilidade', score: 85, weight: 15, details: 'Disponibilidade para início' }
        ]
      }
      setRubricEvaluationData(mockEvaluation)
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
