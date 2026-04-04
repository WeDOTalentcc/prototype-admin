"use client"

import { useState, useMemo, useCallback } from "react"
import {
  MOCK_PENDING_TASKS, MOCK_ACTIVE_ALERTS, MOCK_TASKS,
  MOCK_JOBS_WITH_ALERTS, MOCK_JOB_REQUESTS
} from "./tasks-mock-data"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

export interface Task {
  id: string
  title: string
  description: string
  type: 'minha' | 'ia' | 'entrevista' | 'email' | 'oferta'
  status: 'pending' | 'completed' | 'cancelled'
  dueDate: Date
  priority: 'high' | 'medium' | 'low'
  relatedTo?: string
  color?: string
}

export interface PendingTask {
  id: string
  title: string
  description: string
  type: 'feedback' | 'entrevista' | 'sourcing'
  priority: 'high' | 'medium' | 'low'
  dueDate: Date
  relatedJob?: string
  candidateName?: string
  createdAt: Date
}

export interface ActiveAlert {
  id: string
  title: string
  description: string
  severity: 'high' | 'medium' | 'low'
  jobId: string
  jobTitle: string
  createdAt: Date
  action: string
}

export interface JobWithAlert {
  id: string
  jobId: string
  title: string
  department: string
  stage: string
  totalCandidates: number
  manager: string
  managerEmail: string
  openDate: string
  daysOpen: number
  urgencyLevel: 'critical' | 'urgent' | 'normal'
  budget?: number
  budgetUsed?: number
  publishedLinkedIn: boolean
  publishedWebsite: boolean
  publishedIndeed?: boolean
  stages: {
    new: number
    uncontacted: number
    contacted: number
    replied: number
    phoneScreen: number
    onsite: number
    makeOffer: number
    hired: number
  }
  alert: {
    type: 'urgent' | 'warning' | 'info' | 'success'
    message: string
    action: string
  }
  liaPendencies: string[]
}

export interface JobRequest {
  id: string
  requestId: string
  title: string
  department: string
  requester: string
  requesterEmail: string
  requestDate: string
  status: 'draft' | 'pending_approval' | 'approved' | 'rejected' | 'in_review' | 'requires_changes' | 'published'
  priority: 'critical' | 'high' | 'medium' | 'low'
  headcount: number
  estimatedSalary: string
  workModel: 'remote' | 'hybrid' | 'onsite'
  justification: string
  approvers: {
    name: string
    role: string
    status: 'pending' | 'approved' | 'rejected'
    date?: string
    comments?: string
  }[]
  attachments?: string[]
  daysWaiting: number
}

export function useTasksCore(onNavigate?: (page: string) => void) {
  // Estados de filtros — vagas
  const [jobSearchTerm, setJobSearchTerm] = useState("")
  const [showJobFilters, setShowJobFilters] = useState(false)
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])
  const [selectedUrgencies, setSelectedUrgencies] = useState<string[]>([])
  const [selectedPublications, setSelectedPublications] = useState<string[]>([])
  const [jobSortBy, setJobSortBy] = useState<'daysOpen' | 'candidates' | 'urgency'>('urgency')

  // Estados de filtros — requisições
  const [requestSearchTerm, setRequestSearchTerm] = useState("")
  const [showRequestFilters, setShowRequestFilters] = useState(false)
  const [selectedRequestStatus, setSelectedRequestStatus] = useState<string[]>([])
  const [selectedRequestDepartments, setSelectedRequestDepartments] = useState<string[]>([])
  const [requestSortBy, setRequestSortBy] = useState<'date' | 'priority' | 'status'>('priority')

  // Estados de UI
  const [selectedActivity, setSelectedActivity] = useState<any | null>(null)
  const [showActivityModal, setShowActivityModal] = useState(false)
  const [pendingTaskFilter, setPendingTaskFilter] = useState<'all' | 'feedback' | 'entrevista' | 'sourcing'>('all')

  // Dados estáticos (prontos para substituição por API)
  const pendingTasks = MOCK_PENDING_TASKS
  const activeAlerts = MOCK_ACTIVE_ALERTS
  const tasks = MOCK_TASKS
  const jobsWithAlerts = MOCK_JOBS_WITH_ALERTS
  const jobRequests = MOCK_JOB_REQUESTS

  const metrics = { total: 8, completed: 3, pending: 4, iaTasks: 1 }

  // Derived state — tarefas filtradas
  const filteredPendingTasks = useMemo(() => {
    if (pendingTaskFilter === 'all') return pendingTasks
    return pendingTasks.filter(task => task.type === pendingTaskFilter)
  }, [pendingTaskFilter])

  // Derived state — vagas filtradas
  const filteredAndSortedJobs = useMemo(() => {
    const filtered = jobsWithAlerts.filter(job => {
      const searchLower = jobSearchTerm.toLowerCase()
      const matchesSearch = jobSearchTerm === "" ||
        job.title.toLowerCase().includes(searchLower) ||
        job.jobId.toLowerCase().includes(searchLower) ||
        job.manager.toLowerCase().includes(searchLower) ||
        job.department.toLowerCase().includes(searchLower)
      const matchesDepartment = selectedDepartments.length === 0 || selectedDepartments.includes(job.department)
      const matchesUrgency = selectedUrgencies.length === 0 || selectedUrgencies.includes(job.urgencyLevel)
      let matchesPublication = true
      if (selectedPublications.length > 0) {
        matchesPublication = selectedPublications.some(pub => {
          if (pub === 'linkedin') return job.publishedLinkedIn
          if (pub === 'site') return job.publishedWebsite
          if (pub === 'indeed') return job.publishedIndeed
          return false
        })
      }
      return matchesSearch && matchesDepartment && matchesUrgency && matchesPublication
    })
    filtered.sort((a, b) => {
      if (jobSortBy === 'daysOpen') return b.daysOpen - a.daysOpen
      if (jobSortBy === 'candidates') return b.totalCandidates - a.totalCandidates
      const urgencyOrder = { critical: 3, urgent: 2, normal: 1 }
      return urgencyOrder[b.urgencyLevel] - urgencyOrder[a.urgencyLevel]
    })
    return filtered
  }, [jobsWithAlerts, jobSearchTerm, selectedDepartments, selectedUrgencies, selectedPublications, jobSortBy])

  // Derived state — requisições filtradas
  const filteredAndSortedRequests = useMemo(() => {
    const filtered = jobRequests.filter(request => {
      const searchLower = requestSearchTerm.toLowerCase()
      const matchesSearch = requestSearchTerm === "" ||
        request.title.toLowerCase().includes(searchLower) ||
        request.requestId.toLowerCase().includes(searchLower) ||
        request.requester.toLowerCase().includes(searchLower) ||
        request.department.toLowerCase().includes(searchLower)
      const matchesStatus = selectedRequestStatus.length === 0 || selectedRequestStatus.includes(request.status)
      const matchesDepartment = selectedRequestDepartments.length === 0 || selectedRequestDepartments.includes(request.department)
      return matchesSearch && matchesStatus && matchesDepartment
    })
    filtered.sort((a, b) => {
      if (requestSortBy === 'date') return new Date(b.requestDate).getTime() - new Date(a.requestDate).getTime()
      if (requestSortBy === 'priority') {
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
        return priorityOrder[b.priority] - priorityOrder[a.priority]
      }
      const statusOrder: Record<string, number> = { requires_changes: 7, pending_approval: 6, in_review: 5, approved: 4, published: 3, draft: 2, rejected: 1 }
      return (statusOrder[b.status] || 0) - (statusOrder[a.status] || 0)
    })
    return filtered
  }, [jobRequests, requestSearchTerm, selectedRequestStatus, selectedRequestDepartments, requestSortBy])

  // Helpers de UI
  const activeJobFiltersCount = selectedDepartments.length + selectedUrgencies.length + selectedPublications.length
  const activeRequestFiltersCount = selectedRequestStatus.length + selectedRequestDepartments.length
  const uniqueDepartments = Array.from(new Set(jobsWithAlerts.map(job => job.department)))
  const uniqueRequestDepartments = Array.from(new Set(jobRequests.map(req => req.department)))

  // Actions — navegação LIA
  const navigateToLIA = useCallback((prompt: string) => {
    useUIPreferencesStore.getState().setLiaPrompt(prompt)
    if (onNavigate) onNavigate('Chat com LIA')
  }, [onNavigate])

  const handleConfirmTask = useCallback((task: PendingTask) => {
    const prompt = `Confirmar tarefa: ${task.title} - ${task.description}${task.candidateName ? ` para candidato ${task.candidateName}` : ''}`
    navigateToLIA(prompt)
  }, [navigateToLIA])

  const handleRejectTask = useCallback((task: PendingTask) => {
    const prompt = `Rejeitar/Cancelar tarefa: ${task.title} - ${task.description}${task.candidateName ? ` para candidato ${task.candidateName}` : ''}`
    navigateToLIA(prompt)
  }, [navigateToLIA])

  const handleAlertAction = useCallback((alert: ActiveAlert) => {
    navigateToLIA(`${alert.action} para a vaga ${alert.jobTitle} (${alert.jobId}): ${alert.description}`)
  }, [navigateToLIA])

  const handleLIAAction = useCallback((action: string, job: JobWithAlert) => {
    const prompts: Record<string, string> = {
      kanban: `Mostrar o kanban completo da vaga ${job.title} (${job.jobId}) com todos os ${job.totalCandidates} candidatos`,
      report: `Gerar relatório detalhado da vaga ${job.title} (${job.jobId}) incluindo métricas de conversão, tempo médio de resposta e análise de performance`,
      share: `Compartilhar a vaga ${job.title} (${job.jobId}) no LinkedIn, Site e Indeed com descrição otimizada`,
      edit: `Editar os requisitos e descrição da vaga ${job.title} (${job.jobId}) mantendo o alinhamento com as expectativas do gestor ${job.manager}`,
      duplicate: `Duplicar a vaga ${job.title} (${job.jobId}) criando uma nova posição similar para ${job.department}`,
      cancel: `Cancelar a vaga ${job.title} (${job.jobId}) e notificar todos os ${job.totalCandidates} candidatos e o gestor ${job.manager}`
    }
    navigateToLIA(prompts[action] || `Ajudar com a vaga ${job.title} (${job.jobId})`)
  }, [navigateToLIA])

  const handleRequestAction = useCallback((action: string, request: JobRequest) => {
    const prompts: Record<string, string> = {
      approve: `Aprovar a requisição ${request.requestId} - ${request.title} do departamento ${request.department} solicitada por ${request.requester}`,
      reject: `Rejeitar a requisição ${request.requestId} - ${request.title} e notificar ${request.requester} com justificativa`,
      request_changes: `Solicitar alterações na requisição ${request.requestId} - ${request.title} para ${request.requester}`,
      send_approval: `Enviar a requisição ${request.requestId} - ${request.title} para aprovação dos gestores`,
      edit: `Editar a requisição ${request.requestId} - ${request.title} incluindo justificativa, budget e requisitos`,
      publish: `Publicar a vaga ${request.title} (${request.requestId}) nas plataformas LinkedIn, Site e Indeed`,
      view_details: `Mostrar todos os detalhes da requisição ${request.requestId} - ${request.title} incluindo aprovadores e histórico`
    }
    navigateToLIA(prompts[action] || `Ajudar com a requisição ${request.requestId} - ${request.title}`)
  }, [navigateToLIA])

  const handleActivityClick = useCallback((task: Task) => {
    const activityDetails = {
      ...task,
      candidateName: task.title.includes('João Silva') ? 'João Silva' :
                     task.title.includes('Ana Costa') ? 'Ana Costa' :
                     task.title.includes('Lucas Mendes') ? 'Lucas Mendes' : 'Candidato',
      candidateEmail: 'candidato@email.com',
      candidatePhone: '+55 11 98765-4321',
      jobTitle: task.relatedTo,
      createdAt: new Date(2025, 9, 8, 14, 30),
      createdBy: 'Ana Silva',
      history: [
        { id: '1', type: 'created', user: 'Ana Silva', date: new Date(2025, 9, 8, 14, 30), description: 'Atividade criada', icon: 'plus' },
        { id: '2', type: 'comment', user: 'Roberto Silva', date: new Date(2025, 9, 9, 10, 15), description: 'Candidato aprovado na triagem inicial.', icon: 'message' },
        { id: '3', type: 'status_change', user: 'LIA', date: new Date(2025, 9, 10, 8, 0), description: 'Status alterado de "Triagem" para "Entrevista Agendada"', icon: 'check' },
        { id: '4', type: 'reminder', user: 'Sistema', date: new Date(2025, 9, 10, 8, 45), description: 'Lembrete automático enviado - Entrevista em 15 minutos', icon: 'bell' }
      ],
      attachments: [
        { id: '1', name: 'CV_JoaoSilva.pdf', size: '245 KB', uploadedBy: 'João Silva', date: new Date(2025, 9, 5) },
        { id: '2', name: 'Portfolio.pdf', size: '1.2 MB', uploadedBy: 'João Silva', date: new Date(2025, 9, 5) }
      ],
      comments: [
        { id: '1', user: 'Ana Silva', avatar: '/avatars/ana.jpg', date: new Date(2025, 9, 9, 16, 30), text: 'Candidato muito promissor.' },
        { id: '2', user: 'Roberto Silva', avatar: '/avatars/roberto.jpg', date: new Date(2025, 9, 10, 8, 15), text: 'Confirmar equipamento necessário para entrevista técnica.' }
      ],
      nextSteps: ['Realizar entrevista técnica', 'Avaliar fit cultural', 'Enviar feedback em até 24h']
    }
    setSelectedActivity(activityDetails)
    setShowActivityModal(true)
  }, [])

  const clearJobFilters = useCallback(() => {
    setJobSearchTerm("")
    setSelectedDepartments([])
    setSelectedUrgencies([])
    setSelectedPublications([])
  }, [])

  const clearRequestFilters = useCallback(() => {
    setRequestSearchTerm("")
    setSelectedRequestStatus([])
    setSelectedRequestDepartments([])
  }, [])

  return {
    state: {
      // Filtros vagas
      jobSearchTerm, showJobFilters, selectedDepartments, selectedUrgencies, selectedPublications, jobSortBy,
      // Filtros requisições
      requestSearchTerm, showRequestFilters, selectedRequestStatus, selectedRequestDepartments, requestSortBy,
      // UI
      selectedActivity, showActivityModal, pendingTaskFilter,
      // Dados
      pendingTasks, activeAlerts, tasks, jobsWithAlerts, jobRequests, metrics,
      // Derived
      filteredPendingTasks, filteredAndSortedJobs, filteredAndSortedRequests,
      activeJobFiltersCount, activeRequestFiltersCount, uniqueDepartments, uniqueRequestDepartments
    },
    actions: {
      // Setters vagas
      setJobSearchTerm, setShowJobFilters, setSelectedDepartments, setSelectedUrgencies,
      setSelectedPublications, setJobSortBy, clearJobFilters,
      // Setters requisições
      setRequestSearchTerm, setShowRequestFilters, setSelectedRequestStatus,
      setSelectedRequestDepartments, setRequestSortBy, clearRequestFilters,
      // Setters UI
      setSelectedActivity, setShowActivityModal, setPendingTaskFilter,
      // Actions LIA
      handleConfirmTask, handleRejectTask, handleAlertAction,
      handleLIAAction, handleRequestAction, handleActivityClick
    }
  }
}
