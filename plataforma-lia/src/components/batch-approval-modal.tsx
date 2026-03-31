"use client"

import { useState } from "react"
import { integrationsService } from "@/services/integrations-service"
import { formatScorePercent } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  X, CheckCircle, XCircle, ArrowRight, Users, MessageSquare,
  ThumbsUp, ThumbsDown, AlertCircle, Clock, Send, FileText,
  Download, Share2, Bell, Zap, Brain, Star, Move, Copy,
  Filter, Search, SortAsc, SortDesc, Check, Minus, Plus,
  Calendar, Mail, Phone, MapPin, Building, Briefcase,
  Award, Globe, Eye, Edit, Trash2, MoreVertical, History,
  Target, TrendingUp, BarChart3, PieChart, Activity
} from "lucide-react"

interface BatchApprovalCandidate {
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

interface BatchApprovalAction {
  type: 'approve' | 'reject' | 'move' | 'note'
  targetStage?: string
  comment?: string
  notifyTeam?: boolean
  scheduleInterview?: boolean
  sendEmail?: boolean
  addToTalentPool?: boolean
}

interface BatchApprovalModalProps {
  isOpen: boolean
  onClose: () => void
  candidates: BatchApprovalCandidate[]
  onApprovalComplete: (results: Record<string, unknown>) => void
}

export function BatchApprovalModal({
  isOpen,
  onClose,
  candidates,
  onApprovalComplete
}: BatchApprovalModalProps) {
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
  const [currentStep, setCurrentStep] = useState<'selection' | 'action' | 'review' | 'processing' | 'complete'>('selection')
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
  const [results, setResults] = useState<{ total: number; approved: number; rejected: number; moved: number } | null>(null)

  // Available stages for moving candidates
  const availableStages = [
    { id: 'triagem', name: 'Triagem Inicial', color: 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary' },
    { id: 'entrevista_rh', name: 'Entrevista RH', color: 'bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-primary' },
    { id: 'teste_tecnico', name: 'Teste Técnico', color: 'bg-wedo-purple/15 text-wedo-purple' },
    { id: 'entrevista_tecnica', name: 'Entrevista Técnica', color: 'bg-wedo-orange/15 text-wedo-orange' },
    { id: 'entrevista_final', name: 'Entrevista Final', color: 'bg-status-warning/15 text-status-warning' },
    { id: 'aprovado', name: 'Aprovado', color: 'bg-status-success/15 text-status-success' },
    { id: 'rejeitado', name: 'Rejeitado', color: 'bg-status-error/15 text-status-error' }
  ]

  // Batch action templates
  const actionTemplates = [
    {
      id: 'approve_all',
      name: 'Aprovar Todos',
      type: 'approve' as const,
      description: 'Aprovar todos os candidatos selecionados',
      icon: CheckCircle,
      color: 'bg-status-success hover:bg-status-success/10',
      defaultComment: 'Candidatos aprovados em lote após análise detalhada.'
    },
    {
      id: 'reject_all',
      name: 'Rejeitar Todos',
      type: 'reject' as const,
      description: 'Rejeitar todos os candidatos selecionados',
      icon: XCircle,
      color: 'bg-status-error hover:bg-status-error',
      defaultComment: 'Candidatos não atendem aos critérios da vaga.'
    },
    {
      id: 'move_to_next',
      name: 'Avançar Etapa',
      type: 'move' as const,
      description: 'Mover candidatos para próxima etapa',
      icon: ArrowRight,
      color: 'bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200',
      defaultComment: 'Candidatos avançados para próxima etapa do processo.'
    },
    {
      id: 'add_notes',
      name: 'Adicionar Notas',
      type: 'note' as const,
      description: 'Adicionar comentários aos candidatos',
      icon: MessageSquare,
      color: 'bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200',
      defaultComment: 'Notas adicionadas durante revisão em lote.'
    }
  ]

  if (!isOpen) return null

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

  const updateCandidateAction = (candidateId: string, action: 'approve' | 'reject' | 'move', stage?: string, comment?: string) => {
    setCandidateStates(prev => ({
      ...prev,
      [candidateId]: {
        ...prev[candidateId],
        status: action === 'move' ? 'moved' : action === 'approve' ? 'approved' : 'rejected',
        newStage: stage,
        individualComment: comment
      }
    }))
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-status-success bg-status-success/15"
    if (score >= 70) return "text-lia-text-primary bg-gray-100 dark:bg-lia-bg-elevated"
    if (score >= 60) return "text-status-warning bg-status-warning/15"
    return "text-status-error bg-status-error/15"
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'alta': return 'bg-status-error/15 text-status-error'
      case 'média': return 'bg-wedo-orange/15 text-wedo-orange'
      case 'baixa': return 'bg-status-success/15 text-status-success'
      default: return 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="w-4 h-4 text-status-success" />
      case 'rejected': return <XCircle className="w-4 h-4 text-status-error" />
      case 'moved': return <ArrowRight className="w-4 h-4 text-lia-text-primary" />
      default: return <Clock className="w-4 h-4 lia-text-base" />
    }
  }

  // Filter and sort candidates
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
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  const selectedCount = selectedCandidates.size
  const approvedCount = Object.values(candidateStates).filter(c => c.status === 'approved').length
  const rejectedCount = Object.values(candidateStates).filter(c => c.status === 'rejected').length
  const movedCount = Object.values(candidateStates).filter(c => c.status === 'moved').length

  const processBatchApproval = async () => {
    setProcessing(true)
    setCurrentStep('processing')

    // Simulate processing time
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

    // Trigger integrations (Slack/Teams notifications)
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
      }
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50/70 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-lia-bg-secondary rounded-md w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 dark:bg-lia-bg-elevated rounded-md flex items-center justify-center">
              <Users className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-lia-text-primary">
                Aprovação em Lote
              </h2>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                Processe múltiplos candidatos simultaneamente
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Step indicator */}
            <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-lia-bg-elevated rounded-full">
              <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                Etapa {['selection', 'action', 'review', 'processing', 'complete'].indexOf(currentStep) + 1} de 5
              </span>
            </div>

            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated h-1">
          <div
            className="bg-gray-900 h-1 transition-colors motion-reduce:transition-none duration-500"
            style={{width: `${(['selection', 'action', 'review', 'processing', 'complete'].indexOf(currentStep) + 1) * 20}%`}}
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {currentStep === 'selection' && (
            <div className="p-6 h-full overflow-y-auto">
              {/* Filters and Search */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 lia-text-base w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Buscar candidatos..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
                    />
                  </div>

                  <select
                    value={filterCriteria.stage}
                    onChange={(e) => setFilterCriteria({...filterCriteria, stage: e.target.value})}
                    className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary text-sm"
                  >
                    <option value="all">Todas as etapas</option>
                    {availableStages.map(stage => (
                      <option key={stage.id} value={stage.id}>{stage.name}</option>
                    ))}
                  </select>

                  <select
                    value={filterCriteria.score}
                    onChange={(e) => setFilterCriteria({...filterCriteria, score: e.target.value})}
                    className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary text-sm"
                  >
                    <option value="all">Todos os scores</option>
                    <option value="high">Alto (85+)</option>
                    <option value="medium">Médio (70-84)</option>
                    <option value="low">Baixo (&lt;70)</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={selectAll}>
                    Selecionar Todos
                  </Button>
                  <Button variant="outline" size="sm" onClick={deselectAll}>
                    Limpar Seleção
                  </Button>
                  <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                    {selectedCount} de {filteredCandidates.length} selecionados
                  </span>
                </div>
              </div>

              {/* Candidates Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredCandidates.map((candidate) => (
                  <Card
                    key={candidate.id}
                    className={`cursor-pointer transition-colors motion-reduce:transition-none duration-200 ${
 selectedCandidates.has(candidate.id)
                        ? 'ring-2 ring-gray-900 dark:ring-gray-50 bg-gray-50 dark:bg-lia-bg-elevated'
                        : 'hover:border-lia-border-default'
                    }`}
                    onClick={() => toggleCandidateSelection(candidate.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <Avatar className="w-10 h-10">
                              <AvatarImage src={candidate.avatar} alt={candidate.name} />
                              <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-primary text-sm font-medium">
                                {candidate.name.split(' ').map(n => n[0]).join('')}
                              </AvatarFallback>
                            </Avatar>
                            {selectedCandidates.has(candidate.id) && (
                              <div className="absolute -top-1 -right-1 w-5 h-5 bg-gray-900 rounded-full flex items-center justify-center">
                                <Check className="w-3 h-3 text-white" />
                              </div>
                            )}
                          </div>
                          <div>
                            <h4 className="font-semibold text-lia-text-primary text-sm">
                              {candidate.name}
                            </h4>
                            <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                              {candidate.position}
                            </p>
                          </div>
                        </div>

                        <Badge className={`${getPriorityColor(candidate.priority)} text-xs`}>
                          {candidate.priority}
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">Score LIA:</span>
                          <Badge className={`${getScoreColor(candidate.liaScore)} text-xs font-bold`}>
                            {formatScorePercent(candidate.liaScore)}
                          </Badge>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">Etapa:</span>
                          <Badge variant="outline" className="text-xs">
                            {availableStages.find(s => s.id === candidate.currentStage)?.name || candidate.currentStage}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-1 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          <MapPin className="w-3 h-3" />
                          {candidate.location}
                        </div>

                        <div className="flex items-center gap-1 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          <Calendar className="w-3 h-3" />
                          {new Date(candidate.appliedDate).toLocaleDateString('pt-BR')}
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                        <div className="flex flex-wrap gap-1">
                          {candidate.skills.slice(0, 3).map((skill, index) => (
                            <Badge key={skill} variant="secondary" className="text-xs px-1 py-0">
                              {skill}
                            </Badge>
                          ))}
                          {candidate.skills.length > 3 && (
                            <Badge variant="outline" className="text-xs px-1 py-0">
                              +{candidate.skills.length - 3}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {filteredCandidates.length === 0 && (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 lia-text-base mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                    Nenhum candidato encontrado
                  </h3>
                  <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
                    Ajuste os filtros para encontrar candidatos
                  </p>
                </div>
              )}
            </div>
          )}

          {currentStep === 'action' && (
            <div className="p-6 h-full overflow-y-auto">
              <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-lia-text-primary mb-2">
                    Escolha a Ação para {selectedCount} Candidatos
                  </h3>
                  <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
                    Selecione a ação que deseja aplicar aos candidatos selecionados
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-8">
                  {actionTemplates.map((template) => (
                    <Card
                      key={template.id}
                      className={`cursor-pointer transition-colors motion-reduce:transition-none duration-200 ${
 batchAction.type === template.type
                          ? 'ring-2 ring-gray-900 dark:ring-gray-50 bg-gray-50 dark:bg-lia-bg-elevated'
                          : 'hover:border-lia-border-default'
                      }`}
                      onClick={() => setBatchAction({
                        ...batchAction,
                        type: template.type,
                        comment: template.defaultComment
                      })}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-md flex items-center justify-center ${template.color}`}>
                            <template.icon className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <h4 className="font-semibold text-lia-text-primary">
                              {template.name}
                            </h4>
                            <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                              {template.description}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Action Configuration */}
                <Card>
                  <CardHeader>
                    <CardTitle>Configurações da Ação</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {batchAction.type === 'move' && (
                      <div>
                        <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                          Mover para Etapa
                        </label>
                        <select
                          value={batchAction.targetStage || ''}
                          onChange={(e) => setBatchAction({...batchAction, targetStage: e.target.value})}
                          className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary"
                        >
                          <option value="">Selecione uma etapa</option>
                          {availableStages.map(stage => (
                            <option key={stage.id} value={stage.id}>{stage.name}</option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                        Comentário Geral
                      </label>
                      <textarea
                        value={batchAction.comment}
                        onChange={(e) => setBatchAction({...batchAction, comment: e.target.value})}
                        placeholder="Adicione um comentário sobre esta ação em lote..."
                        className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary h-24 resize-none"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                        <input
                          type="checkbox"
                          checked={batchAction.notifyTeam}
                          onChange={(e) => setBatchAction({...batchAction, notifyTeam: e.target.checked})}
                          className="rounded-md border-lia-border-default"
                        />
                        <Bell className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                        <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">Notificar equipe</span>
                      </label>

                      <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                        <input
                          type="checkbox"
                          checked={batchAction.sendEmail}
                          onChange={(e) => setBatchAction({...batchAction, sendEmail: e.target.checked})}
                          className="rounded-md border-lia-border-default"
                        />
                        <Mail className="w-4 h-4 text-status-success" />
                        <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">Enviar email aos candidatos</span>
                      </label>

                      <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                        <input
                          type="checkbox"
                          checked={batchAction.scheduleInterview}
                          onChange={(e) => setBatchAction({...batchAction, scheduleInterview: e.target.checked})}
                          className="rounded-md border-lia-border-default"
                        />
                        <Calendar className="w-4 h-4 text-wedo-purple" />
                        <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">Agendar entrevistas automaticamente</span>
                      </label>

                      <label className="flex items-center gap-2 p-3 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                        <input
                          type="checkbox"
                          checked={batchAction.addToTalentPool}
                          onChange={(e) => setBatchAction({...batchAction, addToTalentPool: e.target.checked})}
                          className="rounded-md border-lia-border-default"
                        />
                        <Star className="w-4 h-4 text-wedo-orange" />
                        <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">Adicionar ao banco de talentos</span>
                      </label>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {currentStep === 'review' && (
            <div className="p-6 h-full overflow-y-auto">
              <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-lia-text-primary mb-2">
                    Revisar Ação em Lote
                  </h3>
                  <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
                    Confirme os detalhes antes de processar
                  </p>
                </div>

                {/* Summary */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-lia-text-primary mb-1">{selectedCount}</div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Candidatos Selecionados</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-status-success mb-1">
                        {batchAction.type === 'approve' ? selectedCount : 0}
                      </div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Serão Aprovados</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-status-error mb-1">
                        {batchAction.type === 'reject' ? selectedCount : 0}
                      </div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Serão Rejeitados</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-4 text-center">
                      <div className="text-2xl font-bold text-wedo-purple mb-1">
                        {batchAction.type === 'move' ? selectedCount : 0}
                      </div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Serão Movidos</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Action Details */}
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle>Detalhes da Ação</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">Tipo de Ação:</label>
                        <p className="text-lia-text-primary capitalize">
                          {batchAction.type === 'approve' ? 'Aprovar' :
                           batchAction.type === 'reject' ? 'Rejeitar' :
                           batchAction.type === 'move' ? 'Mover para ' + (availableStages.find(s => s.id === batchAction.targetStage)?.name || '') :
                           'Adicionar Notas'}
                        </p>
                      </div>

                      {batchAction.comment && (
                        <div>
                          <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">Comentário:</label>
                          <p className="text-lia-text-primary">{batchAction.comment}</p>
                        </div>
                      )}

                      <div>
                        <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">Ações Adicionais:</label>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {batchAction.notifyTeam && (
                            <Badge className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-primary flex items-center gap-1">
                              <Bell className="w-3 h-3" />
                              Notificar equipe
                            </Badge>
                          )}
                          {batchAction.sendEmail && (
                            <Badge className="bg-status-success/15 text-status-success flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              Enviar emails
                            </Badge>
                          )}
                          {batchAction.scheduleInterview && (
                            <Badge className="bg-wedo-purple/15 text-wedo-purple flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              Agendar entrevistas
                            </Badge>
                          )}
                          {batchAction.addToTalentPool && (
                            <Badge className="bg-wedo-orange/15 text-wedo-orange flex items-center gap-1">
                              <Star className="w-3 h-3" />
                              Banco de talentos
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Selected Candidates List */}
                <Card>
                  <CardHeader>
                    <CardTitle>Candidatos Selecionados ({selectedCount})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {Array.from(selectedCandidates).map(candidateId => {
                        const candidate = candidates.find(c => c.id === candidateId)
                        if (!candidate) return null

                        return (
                          <div key={candidateId} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                            <div className="flex items-center gap-3">
                              <Avatar className="w-8 h-8">
                                <AvatarImage src={candidate.avatar} alt={candidate.name} />
                                <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-primary text-xs">
                                  {candidate.name.split(' ').map(n => n[0]).join('')}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <div className="font-medium text-lia-text-primary text-sm">
                                  {candidate.name}
                                </div>
                                <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                                  {candidate.position} • Score: {formatScorePercent(candidate.liaScore)}
                                </div>
                              </div>
                            </div>

                            <Badge className={`${getScoreColor(candidate.liaScore)} text-xs`}>
                              {formatScorePercent(candidate.liaScore)}
                            </Badge>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {currentStep === 'processing' && (
            <div className="p-6 h-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-gray-900 border-t-transparent rounded-full animate-spin motion-reduce:animate-none mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold text-lia-text-primary mb-2">
                  Processando Aprovação em Lote
                </h3>
                <p className="text-lia-text-secondary dark:text-lia-text-tertiary mb-4">
                  Aplicando ações para {selectedCount} candidatos...
                </p>
                <div className="space-y-2 text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                  <div className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-pulse motion-reduce:animate-none" />
                    Atualizando status dos candidatos
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <Bell className="w-4 h-4 animate-pulse motion-reduce:animate-none" />
                    Enviando notificações
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    <Mail className="w-4 h-4 animate-pulse motion-reduce:animate-none" />
                    Enviando emails automáticos
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentStep === 'complete' && results && (
            <div className="p-6 h-full overflow-y-auto">
              <div className="max-w-4xl mx-auto text-center">
                <div className="w-16 h-16 bg-status-success/15 dark:bg-status-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-status-success" />
                </div>

                <h3 className="text-xl font-semibold text-lia-text-primary mb-2">
                  Aprovação em Lote Concluída!
                </h3>

                <p className="text-lia-text-secondary dark:text-lia-text-tertiary mb-8">
                  {results.total} candidatos foram processados com sucesso
                </p>

                {/* Results Summary */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                  <Card>
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-lia-text-primary mb-2">{results.total}</div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Total Processados</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-status-success mb-2">{results.approved}</div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Aprovados</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-status-error mb-2">{results.rejected}</div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Rejeitados</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6 text-center">
                      <div className="text-3xl font-bold text-wedo-purple mb-2">{results.moved}</div>
                      <div className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Movidos</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Actions */}
                <div className="flex justify-center gap-4">
                  <Button
                    onClick={() => onApprovalComplete(results)}
                    className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
                  >
                    <Download className="w-4 h-4" />
                    Baixar Relatório
                  </Button>

                  <Button
                    variant="outline"
                    className="gap-2"
                  >
                    <Share2 className="w-4 h-4" />
                    Compartilhar Resultados
                  </Button>

                  <Button
                    variant="outline"
                    onClick={onClose}
                  >
                    Fechar
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-6">
          <div className="flex items-center justify-between">
            <div>
              {currentStep !== 'complete' && (
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                  {selectedCount} candidato{selectedCount !== 1 ? 's' : ''} selecionado{selectedCount !== 1 ? 's' : ''}
                </p>
              )}
            </div>

            <div className="flex gap-3">
              {currentStep === 'selection' && (
                <Button
                  onClick={() => setCurrentStep('action')}
                  disabled={selectedCount === 0}
                  className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
                >
                  Continuar
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              )}

              {currentStep === 'action' && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentStep('selection')}
                  >
                    Voltar
                  </Button>
                  <Button
                    onClick={() => setCurrentStep('review')}
                    disabled={!batchAction.type || (batchAction.type === 'move' && !batchAction.targetStage)}
                    className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
                  >
                    Revisar
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </>
              )}

              {currentStep === 'review' && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentStep('action')}
                  >
                    Voltar
                  </Button>
                  <Button
                    onClick={processBatchApproval}
                    disabled={processing}
                    className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200"
                  >
                    {processing ? 'Processando...' : 'Confirmar e Processar'}
                    <Zap className="w-4 h-4 ml-2" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
