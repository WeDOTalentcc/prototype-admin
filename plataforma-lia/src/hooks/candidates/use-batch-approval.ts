"use client"

import { useState } from "react"
import { integrationsService } from "@/services/integrations-service"

export interface BatchApprovalCandidate {
  id: string
  name: string
  email: string
  phone: string
  avatar?: string
  position: string
  experience: string
  location: string
  liaScore: number
  skillsMatch: number
  currentStage: string
  appliedDate: string
  notes: string
  priority: 'alta' | 'média' | 'baixa'
  source: string
  status: 'pending' | 'approved' | 'rejected' | 'moved'
  newStage?: string
  individualComment?: string
  tags: string[]
  skills: string[]
  jobTitle: string
  department: string
}

export interface BatchApprovalAction {
  type: 'approve' | 'reject' | 'move' | 'note'
  targetStage?: string
  comment?: string
  notifyTeam?: boolean
  scheduleInterview?: boolean
  sendEmail?: boolean
  addToTalentPool?: boolean
}

export interface BatchApprovalModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: BatchApprovalCandidate[]
  onApprovalComplete: (results: Record<string, unknown>) => void
}

export type StepType = 'selection' | 'action' | 'review' | 'processing' | 'complete'

export interface BatchResults {
  total: number
  approved: number
  rejected: number
  moved: number
}

export const availableStages = [
  { id: 'triagem', name: 'Triagem Inicial', color: 'bg-lia-bg-tertiary text-lia-text-primary' },
  { id: 'entrevista_rh', name: 'Entrevista RH', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary' },
  { id: 'teste_tecnico', name: 'Teste Técnico', color: 'bg-wedo-purple/15 text-wedo-purple-text' },
  { id: 'entrevista_tecnica', name: 'Entrevista Técnica', color: 'bg-wedo-orange/15 text-wedo-orange-text' },
  { id: 'entrevista_final', name: 'Entrevista Final', color: 'bg-status-warning/15 text-status-warning' },
  { id: 'aprovado', name: 'Aprovado', color: 'bg-status-success/15 text-status-success' },
  { id: 'rejeitado', name: 'Rejeitado', color: 'bg-status-error/15 text-status-error' }
]

export const actionTemplates = [
  {
    id: 'approve_all',
    name: 'Aprovar Todos',
    type: 'approve' as const,
    description: 'Aprovar todos os candidatos selecionados',
    icon: 'CheckCircle' as const,
    color: 'bg-status-success hover:bg-status-success/10',
    defaultComment: 'Candidatos aprovados em lote após análise detalhada.'
  },
  {
    id: 'reject_all',
    name: 'Rejeitar Todos',
    type: 'reject' as const,
    description: 'Rejeitar todos os candidatos selecionados',
    icon: 'XCircle' as const,
    color: 'bg-status-error hover:bg-status-error',
    defaultComment: 'Candidatos não atendem aos critérios da vaga.'
  },
  {
    id: 'move_to_next',
    name: 'Avançar Etapa',
    type: 'move' as const,
    description: 'Mover candidatos para próxima etapa',
    icon: 'ArrowRight' as const,
    color: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active',
    defaultComment: 'Candidatos avançados para próxima etapa do processo.'
  },
  {
    id: 'add_notes',
    name: 'Adicionar Notas',
    type: 'note' as const,
    description: 'Adicionar comentários aos candidatos',
    icon: 'MessageSquare' as const,
    color: 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active',
    defaultComment: 'Notas adicionadas durante revisão em lote.'
  }
]

export function getScoreColor(score: number) {
  if (score >= 85) return "text-status-success bg-status-success/15"
  if (score >= 70) return "text-lia-text-primary bg-lia-bg-tertiary dark:bg-lia-bg-elevated"
  if (score >= 60) return "text-status-warning bg-status-warning/15"
  return "text-status-error bg-status-error/15"
}

export function getPriorityColor(priority: string) {
  switch (priority) {
    case 'alta': return 'bg-status-error/15 text-status-error'
    case 'média': return 'bg-wedo-orange/15 text-wedo-orange-text'
    case 'baixa': return 'bg-status-success/15 text-status-success'
    default: return 'bg-lia-bg-tertiary text-lia-text-primary'
  }
}

export function useBatchApproval({ candidates, onApprovalComplete }: {
  candidates: BatchApprovalCandidate[]
  onApprovalComplete: (results: Record<string, unknown>) => void
}) {
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set(candidates.map(c => c.id)))
  const [batchAction, setBatchAction] = useState<BatchApprovalAction>({
    type: 'approve',
    comment: '',
    notifyTeam: true,
    scheduleInterview: false,
    sendEmail: true,
    addToTalentPool: false
  })
  const [candidateStates, setCandidateStates] = useState<Record<string, BatchApprovalCandidate>>(
    candidates.reduce((acc, candidate) => {
      acc[candidate.id] = { ...candidate, status: 'pending' }
      return acc
    }, {} as Record<string, BatchApprovalCandidate>)
  )
  const [generalComment, setGeneralComment] = useState('')
  const [currentStep, setCurrentStep] = useState<StepType>('selection')
  const [filterCriteria, setFilterCriteria] = useState({
    stage: 'all',
    score: 'all',
    priority: 'all',
    department: 'all'
  })
  const [sortBy, setSortBy] = useState<'name' | 'score' | 'date' | 'priority'>('score')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [searchTerm, setSearchTerm] = useState('')
  const [processing, setProcessing] = useState(false)
  const [results, setResults] = useState<BatchResults | null>(null)

  const filteredCandidates = candidates.filter(candidate => {
    if (searchTerm && !candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !candidate.position.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    if (filterCriteria.stage !== 'all' && candidate.currentStage !== filterCriteria.stage) return false
    if (filterCriteria.score !== 'all') {
      if (filterCriteria.score === 'high' && candidate.liaScore < 85) return false
      if (filterCriteria.score === 'medium' && (candidate.liaScore < 70 || candidate.liaScore >= 85)) return false
      if (filterCriteria.score === 'low' && candidate.liaScore >= 70) return false
    }
    if (filterCriteria.priority !== 'all' && candidate.priority !== filterCriteria.priority) return false
    if (filterCriteria.department !== 'all' && candidate.department !== filterCriteria.department) return false
    return true
  }).sort((a, b) => {
    let aValue: string | number | undefined, bValue: string | number | undefined
    switch (sortBy) {
      case 'name':
        aValue = a.name.toLowerCase()
        bValue = b.name.toLowerCase()
        break
      case 'score':
        aValue = a.liaScore
        bValue = b.liaScore
        break
      case 'date':
        aValue = new Date(a.appliedDate).getTime()
        bValue = new Date(b.appliedDate).getTime()
        break
      case 'priority':
        const priorityOrder = { 'alta': 3, 'média': 2, 'baixa': 1 }
        aValue = priorityOrder[a.priority]
        bValue = priorityOrder[b.priority]
        break
      default:
        return 0
    }
    if (aValue! < bValue!) return sortDirection === 'asc' ? -1 : 1
    if (aValue! > bValue!) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  const selectedCount = selectedCandidates.size
  const approvedCount = Object.values(candidateStates).filter(c => c.status === 'approved').length
  const rejectedCount = Object.values(candidateStates).filter(c => c.status === 'rejected').length
  const movedCount = Object.values(candidateStates).filter(c => c.status === 'moved').length

  const toggleCandidateSelection = (candidateId: string) => {
    const newSelected = new Set(selectedCandidates)
    if (newSelected.has(candidateId)) {
      newSelected.delete(candidateId)
    } else {
      newSelected.add(candidateId)
    }
    setSelectedCandidates(newSelected)
  }

  const selectAll = () => {
    setSelectedCandidates(new Set(filteredCandidates.map(c => c.id)))
  }

  const deselectAll = () => {
    setSelectedCandidates(new Set())
  }

  const processBatchApproval = async () => {
    setProcessing(true)
    setCurrentStep('processing')
    await new Promise(resolve => setTimeout(resolve, 3000))
    const processedResults = {
      total: selectedCount,
      approved: approvedCount,
      rejected: rejectedCount,
      moved: movedCount,
      generalComment,
      batchAction,
      candidates: Object.values(candidateStates).filter(c => selectedCandidates.has(c.id)),
      timestamp: new Date().toISOString(),
      processedBy: 'Ana Silva'
    }
    setResults(processedResults)
    setProcessing(false)
    setCurrentStep('complete')
    if (batchAction.notifyTeam) {
      try {
        await integrationsService.notifyBatchApproval({
          approver_name: 'Ana Silva',
          approved_count: approvedCount,
          rejected_count: rejectedCount,
          moved_count: movedCount,
          batch_comment: generalComment || batchAction.comment,
          batch_url: window.location.href,
          total_processed: selectedCount
        })
      } catch (error) {
        console.error("[use-batch-approval] Error:", error)
      }
    }
  }

  return {
    selectedCandidates,
    batchAction,
    setBatchAction,
    candidateStates,
    generalComment,
    setGeneralComment,
    currentStep,
    setCurrentStep,
    filterCriteria,
    setFilterCriteria,
    sortBy,
    setSortBy,
    sortDirection,
    setSortDirection,
    searchTerm,
    setSearchTerm,
    processing,
    results,
    filteredCandidates,
    selectedCount,
    approvedCount,
    rejectedCount,
    movedCount,
    toggleCandidateSelection,
    selectAll,
    deselectAll,
    processBatchApproval,
  }
}
