"use client"

// Camada 1 (hooks): Estado e ações centralizadas do TasksPage
// Padrão: { state, actions } — compatível com futura migração Pinia/Vue

import { useState, useMemo, useCallback } from "react"
import React from "react"
import { MessageSquare, Calendar, Search } from "lucide-react"

// --- Interfaces ---

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

// --- Dados Mock (preparados para API) ---

export const MOCK_PENDING_TASKS: PendingTask[] = [
  {
    id: 'pt-1',
    title: 'Feedback de Entrevista Técnica',
    description: 'Avaliar candidato João Silva após entrevista de React',
    type: 'feedback',
    priority: 'high',
    dueDate: new Date(2025, 10, 29, 14, 0),
    relatedJob: 'UX Designer Sênior',
    candidateName: 'João Silva',
    createdAt: new Date(2025, 10, 28, 10, 0)
  },
  {
    id: 'pt-2',
    title: 'Agendar Entrevista Final',
    description: 'Coordenar horário com gestor para candidato aprovado',
    type: 'entrevista',
    priority: 'medium',
    dueDate: new Date(2025, 10, 30, 11, 0),
    relatedJob: 'Desenvolvedor React Sênior',
    candidateName: 'Maria Santos',
    createdAt: new Date(2025, 10, 27, 16, 0)
  },
  {
    id: 'pt-3',
    title: 'Sourcing de Candidatos',
    description: 'Buscar 10 perfis de Data Scientists no LinkedIn',
    type: 'sourcing',
    priority: 'medium',
    dueDate: new Date(2025, 11, 1, 18, 0),
    relatedJob: 'Data Scientist',
    createdAt: new Date(2025, 10, 26, 9, 0)
  },
  {
    id: 'pt-4',
    title: 'Feedback de Fit Cultural',
    description: 'Validar alinhamento de valores do candidato',
    type: 'feedback',
    priority: 'low',
    dueDate: new Date(2025, 11, 2, 10, 0),
    relatedJob: 'Gerente de Vendas',
    candidateName: 'Carlos Oliveira',
    createdAt: new Date(2025, 10, 25, 14, 0)
  },
  {
    id: 'pt-5',
    title: 'Confirmar Entrevista',
    description: 'Reconfirmar disponibilidade do candidato',
    type: 'entrevista',
    priority: 'high',
    dueDate: new Date(2025, 10, 29, 9, 0),
    relatedJob: 'UX Designer Pleno',
    candidateName: 'Ana Costa',
    createdAt: new Date(2025, 10, 28, 8, 0)
  }
]

export const MOCK_ACTIVE_ALERTS: ActiveAlert[] = [
  {
    id: 'alert-1',
    title: 'Candidatos sem contato há 5+ dias',
    description: '3 candidatos aguardando retorno na vaga de UX Designer',
    severity: 'high',
    jobId: 'WDT-2025-001',
    jobTitle: 'UX Designer Sênior',
    createdAt: new Date(2025, 10, 28, 8, 0),
    action: 'Enviar follow-up automático'
  },
  {
    id: 'alert-2',
    title: 'Prazo de preenchimento próximo',
    description: 'Vaga de React Sênior deve ser preenchida em 7 dias',
    severity: 'medium',
    jobId: 'WDT-2025-002',
    jobTitle: 'Desenvolvedor React Sênior',
    createdAt: new Date(2025, 10, 27, 14, 0),
    action: 'Acelerar processo'
  },
  {
    id: 'alert-3',
    title: 'Taxa de conversão baixa',
    description: 'Apenas 15% dos candidatos passam da triagem',
    severity: 'medium',
    jobId: 'WDT-2025-004',
    jobTitle: 'Data Scientist',
    createdAt: new Date(2025, 10, 26, 10, 0),
    action: 'Revisar requisitos'
  },
  {
    id: 'alert-4',
    title: 'Feedback pendente do gestor',
    description: 'Roberto Silva não respondeu avaliação há 3 dias',
    severity: 'low',
    jobId: 'WDT-2025-001',
    jobTitle: 'UX Designer Sênior',
    createdAt: new Date(2025, 10, 25, 16, 0),
    action: 'Cobrar gestor'
  }
]

export const MOCK_TASKS: Task[] = [
  { id: '1', title: 'Entrevista Técnica - João Silva', description: 'Frontend Developer • React + TypeScript', type: 'entrevista', status: 'pending', dueDate: new Date(2025, 9, 11, 9, 0), priority: 'high', relatedTo: 'UX Designer Sênior', color: 'border-l-gray-700 dark:border-l-gray-300' },
  { id: '2', title: 'Enviar Lembrete', description: 'Entrevista João Silva - 09:00', type: 'ia', status: 'pending', dueDate: new Date(2025, 9, 11, 8, 45), priority: 'medium', relatedTo: 'Lembrete automático', color: 'border-l-gray-700 dark:border-l-gray-300' },
  { id: '3', title: 'Revisar CVs - Backend Dev', description: '15 candidatos pendentes', type: 'minha', status: 'pending', dueDate: new Date(2025, 9, 11, 10, 30), priority: 'medium', relatedTo: 'Triagem inicial', color: 'border-l-gray-500' },
  { id: '4', title: 'Revisar Perfis', description: '15 candidatos pendentes • Sugestão LIA', type: 'ia', status: 'pending', dueDate: new Date(2025, 9, 11, 11, 0), priority: 'medium', relatedTo: 'Triagem rápida', color: 'border-l-gray-700 dark:border-l-gray-300' },
  { id: '5', title: 'Autorizar Feedback - Ana Costa', description: 'UX Designer • Processo finalizado', type: 'minha', status: 'pending', dueDate: new Date(2025, 9, 11, 14, 0), priority: 'high', relatedTo: 'Aprovação necessária', color: 'border-l-gray-700 dark:border-l-gray-300' },
  { id: '6', title: 'Publicar Vaga - UX Designer', description: 'Área de Produto • Revisão final', type: 'minha', status: 'pending', dueDate: new Date(2025, 9, 11, 15, 30), priority: 'medium', relatedTo: 'Publicação em 3 canais', color: 'border-l-gray-700 dark:border-l-gray-300' },
  { id: '7', title: 'Aprovar Oferta', description: 'Lucas Mendes - Backend • Sugestão LIA', type: 'ia', status: 'pending', dueDate: new Date(2025, 9, 11, 16, 0), priority: 'high', relatedTo: 'Oferta R$ 12.000', color: 'border-l-gray-700 dark:border-l-gray-300' },
  { id: '8', title: 'Enviar Oferta - Lucas Mendes', description: 'Backend Developer • Aprovado', type: 'oferta', status: 'pending', dueDate: new Date(2025, 9, 11, 16, 30), priority: 'high', relatedTo: 'R$ 12.000', color: 'border-l-gray-700 dark:border-l-gray-300' }
]

export const MOCK_JOBS_WITH_ALERTS: JobWithAlert[] = [
  {
    id: '1', jobId: 'WDT-2025-001', title: 'UX Designer Sênior', department: 'Design', stage: 'Entrevistas',
    totalCandidates: 45, manager: 'Roberto Silva', managerEmail: 'roberto.silva@sodexo.com',
    openDate: '2025-03-01', daysOpen: 28, urgencyLevel: 'urgent', budget: 25000, budgetUsed: 18500,
    publishedLinkedIn: true, publishedWebsite: true, publishedIndeed: true,
    stages: { new: 12, uncontacted: 8, contacted: 15, replied: 10, phoneScreen: 7, onsite: 4, makeOffer: 2, hired: 0 },
    alert: { type: 'urgent', message: '3 candidatos aguardando feedback há 5+ dias', action: 'Enviar feedbacks' },
    liaPendencies: ['Aprovar feedback de Ana Costa', 'Agendar entrevista com João Silva', 'Responder candidato Pedro Alves']
  },
  {
    id: '2', jobId: 'WDT-2025-002', title: 'Desenvolvedor React Sênior', department: 'Tecnologia', stage: 'Finalização',
    totalCandidates: 68, manager: 'Carlos Santos', managerEmail: 'carlos.santos@sodexo.com',
    openDate: '2025-02-15', daysOpen: 42, urgencyLevel: 'critical', budget: 35000, budgetUsed: 32000,
    publishedLinkedIn: true, publishedWebsite: false, publishedIndeed: true,
    stages: { new: 5, uncontacted: 2, contacted: 8, replied: 12, phoneScreen: 10, onsite: 6, makeOffer: 3, hired: 2 },
    alert: { type: 'success', message: '2 ofertas aceitas - preparar onboarding', action: 'Iniciar onboarding' },
    liaPendencies: ['Preparar onboarding de Carlos M.', 'Negociar data de início']
  },
  {
    id: '3', jobId: 'WDT-2025-004', title: 'Data Scientist', department: 'Tecnologia', stage: 'Triagem',
    totalCandidates: 52, manager: 'Roberto Silva', managerEmail: 'roberto.silva@sodexo.com',
    openDate: '2025-02-20', daysOpen: 15, urgencyLevel: 'normal', budget: 60000, budgetUsed: 45000,
    publishedLinkedIn: true, publishedWebsite: true, publishedIndeed: false,
    stages: { new: 23, uncontacted: 15, contacted: 8, replied: 4, phoneScreen: 2, onsite: 0, makeOffer: 0, hired: 0 },
    alert: { type: 'warning', message: 'Taxa de resposta baixa (26%) - revisar abordagem', action: 'Otimizar outreach' },
    liaPendencies: ['Finalizar triagem automática', 'Preparar teste prático']
  }
]

export const MOCK_JOB_REQUESTS: JobRequest[] = [
  {
    id: '1', requestId: 'REQ-2025-045', title: 'Desenvolvedor Full Stack Sênior', department: 'Tecnologia',
    requester: 'Carlos Mendes', requesterEmail: 'carlos.mendes@sodexo.com', requestDate: '2025-10-05',
    status: 'pending_approval', priority: 'critical', headcount: 2, estimatedSalary: 'R$ 12.000 - R$ 15.000',
    workModel: 'hybrid', justification: 'Expansão do time de produto para atender demanda de novos projetos estratégicos.',
    approvers: [
      { name: 'Roberto Silva', role: 'Diretor de Tecnologia', status: 'approved', date: '2025-10-06', comments: 'Aprovado. Projeto crítico.' },
      { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' },
      { name: 'Pedro Souza', role: 'CFO', status: 'pending' }
    ], daysWaiting: 6
  },
  {
    id: '2', requestId: 'REQ-2025-046', title: 'UX Designer Pleno', department: 'Design',
    requester: 'Juliana Oliveira', requesterEmail: 'juliana.oliveira@sodexo.com', requestDate: '2025-10-08',
    status: 'in_review', priority: 'high', headcount: 1, estimatedSalary: 'R$ 8.000 - R$ 10.000',
    workModel: 'remote', justification: 'Necessidade de reforço no time para redesign da plataforma mobile.',
    approvers: [
      { name: 'Roberto Silva', role: 'Head de Design', status: 'approved', date: '2025-10-09', comments: 'Aprovado com ressalvas sobre budget' },
      { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' }
    ], daysWaiting: 3
  },
  {
    id: '3', requestId: 'REQ-2025-047', title: 'Analista de Marketing Digital', department: 'Marketing',
    requester: 'Marina Santos', requesterEmail: 'marina.santos@sodexo.com', requestDate: '2025-10-09',
    status: 'requires_changes', priority: 'medium', headcount: 1, estimatedSalary: 'R$ 6.000 - R$ 8.000',
    workModel: 'hybrid', justification: 'Reforço para campanhas de lançamento de novos produtos.',
    approvers: [
      { name: 'Paula Lima', role: 'Diretora de Marketing', status: 'rejected', date: '2025-10-10', comments: 'Solicito revisão do budget e escopo' }
    ], daysWaiting: 2
  },
  {
    id: '4', requestId: 'REQ-2025-048', title: 'Gerente de Vendas - Região Sul', department: 'Vendas',
    requester: 'Fernando Costa', requesterEmail: 'fernando.costa@sodexo.com', requestDate: '2025-10-01',
    status: 'approved', priority: 'high', headcount: 1, estimatedSalary: 'R$ 15.000 - R$ 18.000',
    workModel: 'hybrid', justification: 'Expansão da operação comercial na região Sul.',
    approvers: [
      { name: 'Ricardo Alves', role: 'VP de Vendas', status: 'approved', date: '2025-10-02', comments: 'Aprovado. Iniciar processo imediatamente.' },
      { name: 'Pedro Souza', role: 'CFO', status: 'approved', date: '2025-10-03', comments: 'Budget aprovado' }
    ], daysWaiting: 10
  },
  {
    id: '5', requestId: 'REQ-2025-049', title: 'Assistente Administrativo', department: 'Operações',
    requester: 'Carla Mendes', requesterEmail: 'carla.mendes@sodexo.com', requestDate: '2025-10-10',
    status: 'draft', priority: 'low', headcount: 1, estimatedSalary: 'R$ 3.500 - R$ 4.500',
    workModel: 'onsite', justification: 'Reposição de colaborador que será promovido internamente.',
    approvers: [{ name: 'Ana Costa', role: 'VP de Operações', status: 'pending' }],
    daysWaiting: 1
  }
]

// --- Hook Principal (Camada 1) ---

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
    if (typeof window !== 'undefined') {
      localStorage.setItem('liaPrompt', prompt)
    }
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
