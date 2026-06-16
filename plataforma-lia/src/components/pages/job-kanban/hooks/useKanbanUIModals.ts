"use client"

import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"
import { type BulkActionType } from "@/components/ui/bulk-actions-bar"
import { toast } from "sonner"
import { useJobUIStore } from "@/stores/job-ui-store"
import { useLiaChatContext } from "@/contexts/lia-float-context"

export function useKanbanUIModals({ job }: {
  job?: Record<string, unknown>
}) {
  // Preview
  const [previewCandidate, setPreviewCandidate] = useState<Record<string, unknown> | null>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [showCandidatePage, setShowCandidatePage] = useState(false)
  const [isPreviewMaximized, setIsPreviewMaximized] = useState(false)

  // Triagem
  const [triagemCandidate, setTriagemCandidate] = useState<Record<string, unknown> | null>(null)
  const [showReport, setShowReport] = useState(false)
  const [isTriagemOpen, setIsTriagemOpen] = useState(false)
  const [showTestPreview, setShowTestPreview] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null)
  const [showTestLibrary, setShowTestLibrary] = useState(false)
  const [showTestHistory, setShowTestHistory] = useState(false)
  const [selectedTestForHistory, setSelectedTestForHistory] = useState<string | null>(null)
  const [showConceptualPrompt, setShowConceptualPrompt] = useState(false)
  const [isEditModeTriagem, setIsEditModeTriagem] = useState(false)
  const [showConceptualPromptTriagem, setShowConceptualPromptTriagem] = useState(false)
  const [showApresentacaoPrompt, setShowApresentacaoPrompt] = useState(false)
  const [showFechamentoPrompt, setShowFechamentoPrompt] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showTriagemSuggestions, setShowTriagemSuggestions] = useState(false)
  const [selectedTriagemQuestion, setSelectedTriagemQuestion] = useState<string | null>(null)
  const [expandedCronograma, setExpandedCronograma] = useState(false)
  const [expandedTesteTecnico, setExpandedTesteTecnico] = useState(false)
  const [expandedTesteIngles, setExpandedTesteIngles] = useState(false)
  const [expandedRoteiro, setExpandedRoteiro] = useState(false)

  // Perguntas e pesos (triagem)
  const [perguntasEliminatorias, setPerguntasEliminatorias] = useState([
    '1️⃣ Você está aberto(a) a novas oportunidades no momento? (opções: Sim / Não)',
    '2️⃣ Você tem disponibilidade para o modelo de trabalho [modelo da vaga]? (opções: Sim / Não)'
  ])
  const [perguntasInformativas, setPerguntasInformativas] = useState([
    '3️⃣ Qual sua disponibilidade para início, caso avance no processo? (opções: Imediata / Até 30 dias / Acima de 30 dias)',
    '4️⃣ Qual sua expectativa salarial para contratação CLT? (resposta aberta)'
  ])
  const [habilidadesTecnicas, setHabilidadesTecnicas] = useState([
    'Design System', 'Prototipagem Figma', 'User Research',
    'Testes de Usabilidade', 'Metodologias Ágeis', 'Métricas de UX'
  ])
  const [perguntasTecnicasAvaliacao, setPerguntasTecnicasAvaliacao] = useState([
    '1️⃣ De 1 a 5, como você avalia seu domínio em **[Skill 1]**? (1 = iniciante / 5 = especialista)',
    '2️⃣ Conte brevemente sobre um projeto em que aplicou **[Skill 2]**.',
    '3️⃣ Como você costuma validar seus resultados ao trabalhar com **[Skill 3]**?',
    '4️⃣ Qual foi o principal desafio técnico que enfrentou em **[Skill 4]** e como resolveu?',
    '5️⃣ Quando você redesenha uma interface, quais **métricas** usa para avaliar se ela teve sucesso?'
  ])
  const defaultSkillWeights = [
    { skill: 'Design System', weight: 25, avgScore: 4.3, classification: 'Alto', validationType: 'Contexto real + microteste' },
    { skill: 'Prototipagem (Figma)', weight: 25, avgScore: 4.8, classification: 'Excelente', validationType: 'Microcase prático' },
    { skill: 'User Research', weight: 20, avgScore: 3.9, classification: 'Médio', validationType: 'Situação contextual' },
    { skill: 'Testes de Usabilidade', weight: 15, avgScore: 4.1, classification: 'Alto', validationType: 'Autodeclarado + microteste' },
    { skill: 'Métricas de UX', weight: 15, avgScore: 4.0, classification: 'Alto', validationType: 'Pergunta teórica' }
  ]
  const [skillWeights, setSkillWeights] = useState(defaultSkillWeights)
  const [originalSkillWeights] = useState(defaultSkillWeights)
  const [isSkillWeightsModified, setIsSkillWeightsModified] = useState(false)
  const [perguntasSituacionais, setPerguntasSituacionais] = useState([
    '1️⃣ Como você lida com **feedbacks críticos** sobre seu trabalho?',
    '2️⃣ Conte sobre uma situação em que precisou **defender uma decisão técnica ou de design**.',
    '3️⃣ Quando há **demandas conflitantes** entre diferentes áreas, como você prioriza?'
  ])

  // LIA / Chat (apenas estado ainda em uso pelos handlers — o chat unificado
  // flutuante cuida da janela de conversa)
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(false)
  const [liaSuggestionsData, setLiaSuggestionsData] = useState<Array<{
    type: string; severity: string; candidate_id: string; candidate_name: string;
    message: string; suggested_action: string; stage: string
  }>>([])
  const [showLiaSuggestionsPanel, setShowLiaSuggestionsPanel] = useState(true)
  const [transitionInitialPrompt, setTransitionInitialPrompt] = useState<string | undefined>(undefined)
  const [transitionAllowStageSelection, setTransitionAllowStageSelection] = useState(false)
  const [transitionInterviewAlert, setTransitionInterviewAlert] = useState<{ name: string; date: string } | null>(null)
  const [liaPromptValue, setLiaPromptValue] = useState("")
  const { chatMessages: unifiedMessages, setChatMessages: setUnifiedMessages } = useLiaChatContext()
  const liaMessages = useMemo(() => unifiedMessages.map(m => ({
    id: m.id,
    type: (m.sender === 'user' ? 'user' : 'response') as 'user' | 'response',
    content: m.content,
    timestamp: Date.now(),
    metadata: m.metadata,
  })), [unifiedMessages])
  type KanbanMsg = { id: string; type: 'user' | 'response'; content: string; timestamp: number; metadata?: Record<string, unknown> }
  const setLiaMessages = useCallback((val: KanbanMsg[] | ((prev: KanbanMsg[]) => KanbanMsg[])) => {
    const toUnified = (arr: KanbanMsg[]) => arr.map(m => ({
      id: m.id,
      sender: (m.type === 'user' ? 'user' : 'lia') as 'user' | 'lia',
      content: m.content,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      metadata: m.metadata,
    }))
    if (typeof val === 'function') {
      setUnifiedMessages(prevUnified => {
        const prevKanban: KanbanMsg[] = prevUnified.map(m => ({
          id: m.id,
          type: (m.sender === 'user' ? 'user' : 'response') as 'user' | 'response',
          content: m.content,
          timestamp: Date.now(),
          metadata: m.metadata,
        }))
        return toUnified(val(prevKanban))
      })
    } else if (val.length === 0) {
      setUnifiedMessages([])
    } else {
      setUnifiedMessages(toUnified(val))
    }
  }, [setUnifiedMessages])
  const [isLiaLoading, setIsLiaLoading] = useState(false)
  const [liaConversationId, setLiaConversationId] = useState<string | undefined>(undefined)
  const chatScrollRef = useRef<HTMLDivElement>(null)
  const [liaSearchQuery, setLiaSearchQuery] = useState("")

  // Email modal
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailCandidate, setEmailCandidate] = useState<Record<string, unknown> | null>(null)

  // Share Gestor
  const [showShareGestorModal, setShowShareGestorModal] = useState(false)

  // Unified Communication Modal
  const [unifiedModalOpen, setUnifiedModalOpen] = useState(false)
  const [unifiedModalType, setUnifiedModalType] = useState<CommunicationType>('email')
  const [unifiedModalCandidate, setUnifiedModalCandidate] = useState<Record<string, unknown> | null>(null)
  const [unifiedModalSituation, setUnifiedModalSituation] = useState<string | undefined>(undefined)

  // WSI Text Screening Modal
  const [showWSIModal, setShowWSIModal] = useState(false)
  const [wsiCandidate, setWsiCandidate] = useState<Record<string, unknown> | null>(null)

  // WSI Triagem Invite Modal
  const [showWSIInviteModal, setShowWSIInviteModal] = useState(false)
  const [wsiInviteCandidate, setWsiInviteCandidate] = useState<Record<string, unknown> | null>(null)

  // Add to Vacancy Modal
  const [showAddToVacancyModal, setShowAddToVacancyModal] = useState(false)
  const [candidateForVacancy, setCandidateForVacancy] = useState<Record<string, unknown> | null>(null)

  // Rubric Evaluation Modal
  const [showRubricModal, setShowRubricModal] = useState(false)
  const [rubricCandidate, setRubricCandidate] = useState<Record<string, unknown> | null>(null)
  const [rubricEvaluationData, setRubricEvaluationData] = useState<Record<string, unknown> | null>(null)

  // Score modals (table)
  const [selectedCandidateForModal, setSelectedCandidateForModal] = useState<Record<string, unknown> | null>(null)
  const [activeModal, setActiveModal] = useState<'scoreGeral' | 'triagem' | 'testeTecnico' | 'testeIngles' | null>(null)
  const [showBigFiveModal, setShowBigFiveModal] = useState(false)

  // Score modals (Kanban cards)
  const [showGeneralScoreModal, setShowGeneralScoreModal] = useState(false)
  const [showTechnicalTestModal, setShowTechnicalTestModal] = useState(false)
  const [showEnglishTestModal, setShowEnglishTestModal] = useState(false)
  const [scoreModalCandidate, setScoreModalCandidate] = useState<Record<string, unknown> | null>(null)

  // Compare modal
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [compareCandidates, setCompareCandidates] = useState<{ id: string; name: string }[]>([])
  const [selectedForCompare, setSelectedForCompare] = useState<Set<string>>(new Set())

  // Decision flow modal
  const [showDecisionFlowModal, setShowDecisionFlowModal] = useState(false)
  const [decisionFlowCandidate, setDecisionFlowCandidate] = useState<Record<string, unknown> | null>(null)
  const [decisionFlowType, setDecisionFlowType] = useState<
    'approve_to_triage' | 'approve_to_interview' | 'reject_pre_triage' |
    'reject_post_triage' | 'request_urgency' | 'reschedule_interview' | 'confirm_hire'
  >('approve_to_triage')

  // Sub-status / pending move modal
  const [pendingMove, setPendingMove] = useState<{
    candidate: Record<string, unknown>; fromColumn: string; toColumn: string
  } | null>(null)
  const [statusModalOpen, setStatusModalOpen] = useState(false)
  const [selectedSubStatus, setSelectedSubStatus] = useState<string>('')

  // Job Status / Close Vacancy modals
  const [showJobStatusModal, setShowJobStatusModal] = useState(false)
  const [jobStatusModalMode, setJobStatusModalMode] = useState<'pause' | 'activate'>('pause')
  const [showCloseVacancyModal, setShowCloseVacancyModal] = useState(false)

  // Bulk action modal
  const [showAddToListModal, setShowAddToListModal] = useState(false)
  const [isAddingToList, setIsAddingToList] = useState(false)
  const [showBulkActionModal, setShowBulkActionModal] = useState(false)
  const [bulkActionType, setBulkActionType] = useState<BulkActionType>('move_stage')

  // Data request modal
  const [showDataRequestModal, setShowDataRequestModal] = useState(false)
  const [dataRequestModalCandidate, setDataRequestModalCandidate] = useState<Record<string, unknown> | null>(null)

  // Viewed candidates
  const [viewedCandidateIds, setViewedCandidateIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch('/api/backend-proxy/candidates/viewed')
        if (response.ok) {
          const data = await response.json()
          const viewedIds = new Set<string>(data.viewed_candidate_ids || data.viewedCandidateIds || [])
          setViewedCandidateIds(viewedIds)
        }
      } catch {}
    }
    load()
  }, [])

  const consumePendingCommunicationAction = useJobUIStore(s => s.consumePendingCommunicationAction)

  useEffect(() => {
    if (!job?.id) return
    const action = consumePendingCommunicationAction(String(job.id))
    if (!action) return
    setTimeout(() => {
      const candidateCount = action.candidateIds?.length || 0
      const channelType = action.channel === 'whatsapp' ? 'whatsapp' : 'email'
      setUnifiedModalCandidate(null)
      setUnifiedModalType(channelType as CommunicationType)
      setUnifiedModalOpen(true)
      if (candidateCount > 0) {
        toast.success('Modal de comunicação aberto', { description: `${candidateCount} candidato(s) prontos para notificação via ${channelType === 'whatsapp' ? 'WhatsApp' : 'E-mail'}.` })
      }
    }, 500)
  }, [job?.id, consumePendingCommunicationAction])

  return {
    state: {
      previewCandidate, isPreviewOpen, showCandidatePage, isPreviewMaximized,
      triagemCandidate, showReport, isTriagemOpen, showTestPreview, editingQuestion,
      showTestLibrary, showTestHistory, selectedTestForHistory,
      showConceptualPrompt, isEditModeTriagem, showConceptualPromptTriagem,
      showApresentacaoPrompt, showFechamentoPrompt, isEditMode,
      showTriagemSuggestions, selectedTriagemQuestion,
      expandedCronograma, expandedTesteTecnico, expandedTesteIngles, expandedRoteiro,
      perguntasEliminatorias, perguntasInformativas, habilidadesTecnicas,
      perguntasTecnicasAvaliacao, skillWeights, originalSkillWeights, isSkillWeightsModified, perguntasSituacionais,
      showLiaSuggestions, liaSuggestionsData, showLiaSuggestionsPanel,
      transitionInitialPrompt, transitionAllowStageSelection, transitionInterviewAlert,
      liaPromptValue, liaMessages, isLiaLoading, liaConversationId,
      chatScrollRef, liaSearchQuery,
      showEmailModal, emailCandidate, showShareGestorModal,
      unifiedModalOpen, unifiedModalType, unifiedModalCandidate, unifiedModalSituation,
      showWSIModal, wsiCandidate, showWSIInviteModal, wsiInviteCandidate,
      showAddToVacancyModal, candidateForVacancy,
      showRubricModal, rubricCandidate, rubricEvaluationData,
      selectedCandidateForModal, activeModal, showBigFiveModal,
      showGeneralScoreModal, showTechnicalTestModal, showEnglishTestModal, scoreModalCandidate,
      showCompareModal, compareCandidates, selectedForCompare,
      showDecisionFlowModal, decisionFlowCandidate, decisionFlowType,
      pendingMove, statusModalOpen, selectedSubStatus,
      showJobStatusModal, jobStatusModalMode, showCloseVacancyModal,
      showAddToListModal, isAddingToList, showBulkActionModal, bulkActionType,
      showDataRequestModal, dataRequestModalCandidate, viewedCandidateIds,
    },
    actions: {
      setPreviewCandidate, setIsPreviewOpen, setShowCandidatePage, setIsPreviewMaximized,
      setTriagemCandidate, setShowReport, setIsTriagemOpen, setShowTestPreview, setEditingQuestion,
      setShowTestLibrary, setShowTestHistory, setSelectedTestForHistory,
      setShowConceptualPrompt, setIsEditModeTriagem, setShowConceptualPromptTriagem,
      setShowApresentacaoPrompt, setShowFechamentoPrompt, setIsEditMode,
      setShowTriagemSuggestions, setSelectedTriagemQuestion,
      setExpandedCronograma, setExpandedTesteTecnico, setExpandedTesteIngles, setExpandedRoteiro,
      setPerguntasEliminatorias, setPerguntasInformativas, setHabilidadesTecnicas,
      setPerguntasTecnicasAvaliacao, setSkillWeights, setIsSkillWeightsModified, setPerguntasSituacionais,
      setShowLiaSuggestions, setLiaSuggestionsData, setShowLiaSuggestionsPanel,
      setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert,
      setLiaPromptValue, setLiaMessages, setIsLiaLoading, setLiaConversationId,
      setLiaSearchQuery,
      setShowEmailModal, setEmailCandidate, setShowShareGestorModal,
      setUnifiedModalOpen, setUnifiedModalType, setUnifiedModalCandidate, setUnifiedModalSituation,
      setShowWSIModal, setWsiCandidate, setShowWSIInviteModal, setWsiInviteCandidate,
      setShowAddToVacancyModal, setCandidateForVacancy,
      setShowRubricModal, setRubricCandidate, setRubricEvaluationData,
      setSelectedCandidateForModal, setActiveModal, setShowBigFiveModal,
      setShowGeneralScoreModal, setShowTechnicalTestModal, setShowEnglishTestModal, setScoreModalCandidate,
      setShowCompareModal, setCompareCandidates, setSelectedForCompare,
      setShowDecisionFlowModal, setDecisionFlowCandidate, setDecisionFlowType,
      setPendingMove, setStatusModalOpen, setSelectedSubStatus,
      setShowJobStatusModal, setJobStatusModalMode, setShowCloseVacancyModal,
      setShowAddToListModal, setIsAddingToList, setShowBulkActionModal, setBulkActionType,
      setShowDataRequestModal, setDataRequestModalCandidate, setViewedCandidateIds,
    },
  }
}

export type KanbanUIModalsState = ReturnType<typeof useKanbanUIModals>
