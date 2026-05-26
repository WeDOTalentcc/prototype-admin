"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"
import { useJWTAuth } from "@/contexts/auth-context"
import { toast } from "@/lib/toast"

const API_BASE = '/api/backend-proxy'

interface BackendTask {
  id: string
  title: string
  description: string
  task_type: string | null
  priority: string | null
  status: string | null
  due_date: string | null
  created_at: string | null
  related_job_id: string | null
  related_candidate_id: string | null
  assigned_to_user_id: string | null
  created_by_agent: string | null
  is_automated: boolean
  context: {
    candidate_name?: string
    [key: string]: unknown
  } | null
}

interface BackendSummary {
  pending: number
  in_progress: number
  completed: number
  overdue: number
  critical: number
  total_active: number
}

interface BackendAlert {
  id: string
  title: string
  message: string
  description: string
  severity: string | null
  job_id: string | null
  created_at: string | null
  suggested_actions: string[] | null
  context: {
    job_title?: string
    [key: string]: unknown
  } | null
}

interface BackendJob {
  id: string
  code: string
  title: string
  department: string
  area: string
  status: string
  total_candidates: number
  candidates_count: number
  hiring_manager: string
  manager_name: string
  manager_email: string
  created_at: string
  days_open: number
  deadline: string | null
  budget: number
  budget_used: number
  published_linkedin: boolean
  published_website: boolean
  published_indeed: boolean
  is_published: boolean
  pipeline_stages: Record<string, number>
  stages: Record<string, number>
  lia_pendencies: string[]
}

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
  relatedJobId?: string
  relatedCandidateId?: string
  rawTaskType?: string
  candidateName?: string
  createdAt: Date
}

export interface ActiveAlert {
  id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
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

function mapTaskType(taskType: string | null): PendingTask['type'] {
  switch (taskType) {
    case 'feedback_pending':
    case 'evaluation':
    case 'feedback':
      return 'feedback'
    case 'interview_schedule':
    case 'interview':
    case 'interview_prep':
      return 'entrevista'
    case 'sourcing':
    case 'candidate_outreach':
    case 'screening':
      return 'sourcing'
    default:
      return 'feedback'
  }
}

function mapPriority(priority: string | null): PendingTask['priority'] {
  switch (priority) {
    case 'critical':
    case 'high':
      return 'high'
    case 'medium':
      return 'medium'
    case 'low':
      return 'low'
    default:
      return 'medium'
  }
}

function mapAlertSeverity(severity: string | null): ActiveAlert['severity'] {
  switch (severity) {
    case 'critical':
      return 'critical'
    case 'high':
      return 'high'
    case 'medium':
      return 'medium'
    case 'low':
      return 'low'
    case 'info':
      return 'info'
    default:
      return 'medium'
  }
}

function calculateUrgencyLevel(job: Partial<BackendJob>): JobWithAlert['urgencyLevel'] {
  const daysOpen = job.days_open || 0
  const deadline = job.deadline ? new Date(job.deadline) : null
  const daysUntilDeadline = deadline ? Math.ceil((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : null

  if (daysOpen > 45 || (daysUntilDeadline !== null && daysUntilDeadline < 7)) return 'critical'
  if (daysOpen > 30 || (daysUntilDeadline !== null && daysUntilDeadline < 14)) return 'urgent'
  return 'normal'
}

function mapJobToJobWithAlert(job: Partial<BackendJob>): JobWithAlert {
  const stages = job.pipeline_stages || job.stages || {}
  const totalCandidates = job.total_candidates || job.candidates_count || Object.values(stages).reduce((sum: number, val: unknown) => sum + (Number(val) || 0), 0)
  const daysOpen = job.days_open || (job.created_at ? Math.ceil((Date.now() - new Date(job.created_at).getTime()) / (1000 * 60 * 60 * 24)) : 0)
  const urgencyLevel = calculateUrgencyLevel({ ...job, days_open: daysOpen })

  let alertType: 'urgent' | 'warning' | 'info' | 'success' = 'info'
  let alertMessage = 'Vaga em andamento'
  let alertAction = 'Ver detalhes'

  if (urgencyLevel === 'critical') {
    alertType = 'urgent'
    alertMessage = `Vaga aberta há ${daysOpen} dias - ação necessária`
    alertAction = 'Acelerar processo'
  } else if (urgencyLevel === 'urgent') {
    alertType = 'warning'
    alertMessage = `${totalCandidates} candidatos no funil`
    alertAction = 'Revisar pipeline'
  } else {
    alertType = 'success'
    alertMessage = `Pipeline com ${totalCandidates} candidatos`
    alertAction = 'Ver candidatos'
  }

  return {
    id: job.id || '',
    jobId: job.code || job.id || '',
    title: job.title || '',
    department: job.department || job.area || 'Geral',
    stage: job.status || 'Ativa',
    totalCandidates,
    manager: job.hiring_manager || job.manager_name || 'Não definido',
    managerEmail: job.manager_email || '',
    openDate: job.created_at || new Date().toISOString(),
    daysOpen,
    urgencyLevel,
    budget: job.budget || undefined,
    budgetUsed: job.budget_used || undefined,
    publishedLinkedIn: job.published_linkedin || false,
    publishedWebsite: job.published_website || job.is_published || false,
    publishedIndeed: job.published_indeed || false,
    stages: {
      new: stages.new || stages.novo || 0,
      uncontacted: stages.uncontacted || stages.triagem || 0,
      contacted: stages.contacted || stages.contato || 0,
      replied: stages.replied || stages.resposta || 0,
      phoneScreen: stages.phone_screen || stages.telefone || 0,
      onsite: stages.onsite || stages.entrevista || 0,
      makeOffer: stages.make_offer || stages.oferta || 0,
      hired: stages.hired || stages.contratado || 0,
    },
    alert: {
      type: alertType,
      message: alertMessage,
      action: alertAction,
    },
    liaPendencies: job.lia_pendencies || [],
  }
}

const RETRYABLE_STATUSES = new Set([401, 502, 503, 504, 429])

async function fetchEndpointWithRetry(url: string, retries = 2, baseDelayMs = 2000): Promise<Response> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      console.debug(`[useTasksCore] fetch attempt ${attempt}/${retries}: ${url}`)
      const res = await fetch(url, { signal: AbortSignal.timeout(12000) })
      console.debug(`[useTasksCore] fetch result: ${url} → ${res.status}`)
      if (res.ok || attempt === retries || !RETRYABLE_STATUSES.has(res.status)) {
        return res
      }
      console.debug(`[useTasksCore] retryable status ${res.status}, will retry`)
    } catch (err) {
      console.warn(`[useTasksCore] fetch error attempt ${attempt}: ${url}`, (err as Error)?.message)
      if (attempt === retries) throw err
    }
    const delay = Math.min(baseDelayMs * Math.pow(1.5, attempt), 15000)
    await new Promise(r => setTimeout(r, delay))
  }
  throw new Error("unreachable")
}

export function useTasksCore(onNavigate?: (page: string) => void) {
  const { user } = useJWTAuth()
  const mountedRef = useRef(false)
  const [jobSearchTerm, setJobSearchTerm] = useState("")
  const [showJobFilters, setShowJobFilters] = useState(false)
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])
  const [selectedUrgencies, setSelectedUrgencies] = useState<string[]>([])
  const [selectedPublications, setSelectedPublications] = useState<string[]>([])
  const [jobSortBy, setJobSortBy] = useState<'daysOpen' | 'candidates' | 'urgency'>('urgency')

  const [requestSearchTerm, setRequestSearchTerm] = useState("")
  const [showRequestFilters, setShowRequestFilters] = useState(false)
  const [selectedRequestStatus, setSelectedRequestStatus] = useState<string[]>([])
  const [selectedRequestDepartments, setSelectedRequestDepartments] = useState<string[]>([])
  const [requestSortBy, setRequestSortBy] = useState<'date' | 'priority' | 'status'>('priority')

  const [selectedActivity, setSelectedActivity] = useState<PendingTask | null>(null)
  const [showActivityModal, setShowActivityModal] = useState(false)
  const [pendingTaskFilter, setPendingTaskFilter] = useState<'all' | 'feedback' | 'sourcing'>('all')

  const [pendingTasks, setPendingTasks] = useState<PendingTask[]>([])
  const [activeAlerts, setActiveAlerts] = useState<ActiveAlert[]>([])
  const [jobsWithAlerts, setJobsWithAlerts] = useState<JobWithAlert[]>([])
  const [metrics, setMetrics] = useState({ total: 0, completed: 0, pending: 0, iaTasks: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const currentUserId = user?.id || user?.email || 'default_user'

  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
    }
  }, [])

  useEffect(() => {
    fetchAllData()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUserId])

  const fetchAllData = async () => {
    if (!mountedRef.current) return
    setLoading(true)
    setError(null)

    console.log('[useTasksCore] fetchAllData starting, userId:', currentUserId)

    try {
      const [tasksRes, summaryRes, alertsRes, jobsRes] = await Promise.allSettled([
        fetchEndpointWithRetry(`${API_BASE}/tasks?limit=50&status=pending`),
        fetchEndpointWithRetry(`${API_BASE}/tasks/summary`),
        fetchEndpointWithRetry(`${API_BASE}/alerts?limit=20&status=active`),
        fetchEndpointWithRetry(`${API_BASE}/job-vacancies?limit=20`),
      ])
      console.log('[useTasksCore] responses:', {
        tasks: tasksRes.status === 'fulfilled' ? tasksRes.value.status : 'rejected',
        summary: summaryRes.status === 'fulfilled' ? summaryRes.value.status : 'rejected',
        alerts: alertsRes.status === 'fulfilled' ? alertsRes.value.status : 'rejected',
        jobs: jobsRes.status === 'fulfilled' ? jobsRes.value.status : 'rejected',
      })

      if (!mountedRef.current) return

      let parsedTasks: BackendTask[] = []
      if (tasksRes.status === 'fulfilled' && tasksRes.value.ok) {
        const tasksData = await tasksRes.value.json()
        parsedTasks = Array.isArray(tasksData) ? tasksData : (tasksData.tasks || [])
        const mapped: PendingTask[] = parsedTasks.map((t) => ({
          id: t.id,
          title: t.title || '',
          description: t.description || '',
          type: mapTaskType(t.task_type),
          priority: mapPriority(t.priority),
          dueDate: t.due_date ? new Date(t.due_date) : new Date(),
          relatedJob: t.context?.job_title as string | undefined || undefined,
          relatedJobId: t.related_job_id || undefined,
          relatedCandidateId: t.related_candidate_id || t.context?.candidate_id as string | undefined || undefined,
          rawTaskType: t.task_type || undefined,
          candidateName: t.context?.candidate_name || undefined,
          createdAt: t.created_at ? new Date(t.created_at) : new Date(),
        }))
        setPendingTasks(mapped)
      }

      if (summaryRes.status === 'fulfilled' && summaryRes.value.ok) {
        const summaryData: BackendSummary = await summaryRes.value.json()
        const iaCount = parsedTasks.filter(t => t.is_automated || t.created_by_agent != null).length
        setMetrics({
          total: (summaryData.total_active || 0) + (summaryData.completed || 0),
          completed: summaryData.completed || 0,
          pending: summaryData.pending || 0,
          iaTasks: iaCount,
        })
      }

      if (alertsRes.status === 'fulfilled' && alertsRes.value.ok) {
        const alertsData = await alertsRes.value.json()
        const alertsList: BackendAlert[] = Array.isArray(alertsData) ? alertsData : (alertsData.alerts || [])
        const mapped: ActiveAlert[] = alertsList.map((a) => ({
          id: a.id,
          title: a.title || '',
          description: a.message || a.description || '',
          severity: mapAlertSeverity(a.severity),
          jobId: a.job_id || '',
          jobTitle: a.context?.job_title || a.title || '',
          createdAt: a.created_at ? new Date(a.created_at) : new Date(),
          action: a.suggested_actions?.[0] || 'Verificar',
        }))
        setActiveAlerts(mapped)
      }

      if (jobsRes.status === 'fulfilled' && jobsRes.value.ok) {
        const jobsData = await jobsRes.value.json()
        const jobsList: Partial<BackendJob>[] = Array.isArray(jobsData)
          ? jobsData
          : (jobsData.items || jobsData.jobs || jobsData.vacancies || [])
        const mapped: JobWithAlert[] = jobsList.map(mapJobToJobWithAlert)
        setJobsWithAlerts(mapped)
      }

      if (!mountedRef.current) return

      const failedRequests = [tasksRes, summaryRes, alertsRes, jobsRes].filter(
        r => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.ok)
      )
      if (failedRequests.length === 4) {
        setError('Não foi possível conectar ao servidor. Verifique sua conexão.')
      } else if (failedRequests.length > 0) {
        setError('Alguns dados podem estar incompletos.')
      }
    } catch {
      if (!mountedRef.current) return
      setError('Erro ao carregar dados. Tente novamente.')
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }

  const tasks: Task[] = []
  const jobRequests = useMemo<JobRequest[]>(() => [], [])

  const filteredPendingTasks = useMemo(() => {
    if (pendingTaskFilter === 'all') return pendingTasks
    return pendingTasks.filter(task => task.type === pendingTaskFilter)
  }, [pendingTaskFilter, pendingTasks])

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

  const filteredAndSortedRequests = useMemo(() => {
    return jobRequests
  }, [jobRequests])

  const activeJobFiltersCount = selectedDepartments.length + selectedUrgencies.length + selectedPublications.length
  const activeRequestFiltersCount = selectedRequestStatus.length + selectedRequestDepartments.length
  const uniqueDepartments = Array.from(new Set(jobsWithAlerts.map(job => job.department)))
  const uniqueRequestDepartments: string[] = []

  const navigateToLIA = useCallback((prompt: string) => {
    useUIPreferencesStore.getState().setLiaPrompt(prompt)
    if (onNavigate) onNavigate('Chat com LIA')
  }, [onNavigate])

  const handleConfirmTask = useCallback(async (task: PendingTask) => {
    try {
      const res = await fetch(`${API_BASE}/task-lifecycle/${task.id}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmed_by: currentUserId }),
      })
      if (res.ok) {
        setPendingTasks(prev => prev.filter(t => t.id !== task.id))
        setMetrics(prev => ({
          ...prev,
          completed: prev.completed + 1,
          pending: Math.max(0, prev.pending - 1),
        }))
        toast.success('Tarefa confirmada', task.title)
      } else {
        toast.error('Erro ao confirmar tarefa', 'Tente novamente em instantes')
      }
    } catch {
      toast.error('Erro de conexão', 'Verifique sua conexão e tente novamente')
    }
  }, [currentUserId])

  const handleRejectTask = useCallback(async (task: PendingTask) => {
    try {
      const res = await fetch(`${API_BASE}/task-lifecycle/${task.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rejected_by: currentUserId }),
      })
      if (res.ok) {
        setPendingTasks(prev => prev.filter(t => t.id !== task.id))
        setMetrics(prev => ({
          ...prev,
          pending: Math.max(0, prev.pending - 1),
        }))
        toast.success('Tarefa rejeitada', task.title)
      } else {
        toast.error('Erro ao rejeitar tarefa', 'Tente novamente em instantes')
      }
    } catch {
      toast.error('Erro de conexão', 'Verifique sua conexão e tente novamente')
    }
  }, [currentUserId])

  const handleAlertAction = useCallback(async (alert: ActiveAlert) => {
    const encodedUserId = encodeURIComponent(currentUserId)
    const isCritical = alert.severity === 'critical' || alert.severity === 'high'
    const endpoint = isCritical
      ? `${API_BASE}/alerts/${alert.id}/resolve?user_id=${encodedUserId}`
      : `${API_BASE}/alerts/${alert.id}/acknowledge?user_id=${encodedUserId}`
    try {
      const res = await fetch(endpoint, { method: 'POST' })
      if (res.ok) {
        setActiveAlerts(prev => prev.filter(a => a.id !== alert.id))
        toast.success(isCritical ? 'Alerta resolvido' : 'Alerta reconhecido', alert.title)
      } else {
        toast.error('Erro ao processar alerta', 'Redirecionando para LIA...')
        navigateToLIA(`${alert.action} para a vaga ${alert.jobTitle} (${alert.jobId}): ${alert.description}`)
      }
    } catch {
      toast.error('Erro de conexão', 'Redirecionando para LIA...')
      navigateToLIA(`${alert.action} para a vaga ${alert.jobTitle} (${alert.jobId}): ${alert.description}`)
    }
  }, [navigateToLIA, currentUserId])

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
    navigateToLIA(`Ajudar com a requisição ${request.requestId} - ${request.title}`)
  }, [navigateToLIA])

  const handleActivityClick = useCallback((_task: Task) => {
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
      jobSearchTerm, showJobFilters, selectedDepartments, selectedUrgencies, selectedPublications, jobSortBy,
      requestSearchTerm, showRequestFilters, selectedRequestStatus, selectedRequestDepartments, requestSortBy,
      selectedActivity, showActivityModal, pendingTaskFilter,
      pendingTasks, activeAlerts, tasks, jobsWithAlerts, jobRequests, metrics,
      filteredPendingTasks, filteredAndSortedJobs, filteredAndSortedRequests,
      activeJobFiltersCount, activeRequestFiltersCount, uniqueDepartments, uniqueRequestDepartments,
      loading, error,
    },
    actions: {
      setJobSearchTerm, setShowJobFilters, setSelectedDepartments, setSelectedUrgencies,
      setSelectedPublications, setJobSortBy, clearJobFilters,
      setRequestSearchTerm, setShowRequestFilters, setSelectedRequestStatus,
      setSelectedRequestDepartments, setRequestSortBy, clearRequestFilters,
      setSelectedActivity, setShowActivityModal, setPendingTaskFilter,
      handleConfirmTask, handleRejectTask, handleAlertAction,
      handleLIAAction, handleRequestAction, handleActivityClick,
      refetch: fetchAllData,
    }
  }
}
