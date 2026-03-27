"use client"

import React, { useState, useMemo } from "react"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"

import {
  CheckCircle2, Clock, AlertCircle, Calendar, ChevronLeft, ChevronRight,
  Plus, UserPlus, Upload, Search, Share2, Send, FileText, Users, Briefcase,
  TrendingUp, Filter, MoreVertical, Eye, Edit, MessageSquare, Mail,
  Phone, Video, MapPin, DollarSign, Target, Zap, Brain,
  CheckCircle, XCircle, AlertTriangle, Info, ChevronUp, ChevronDown, User,
  Linkedin, Globe, ExternalLink, Copy, Trash2, ArrowUpDown, SlidersHorizontal, X,
  Bell, Play, Download, Paperclip, History, Activity
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ActivityFeed } from "@/components/activity-feed"
import { DailyBriefingCard } from "@/components/daily-briefing-card"

// Interfaces
interface Task {
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

interface JobRequest {
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

interface JobWithAlert {
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

interface PendingTask {
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

interface ActiveAlert {
  id: string
  title: string
  description: string
  severity: 'high' | 'medium' | 'low'
  jobId: string
  jobTitle: string
  createdAt: Date
  action: string
}

interface TasksPageProps {
  onNavigate?: (page: string) => void
}

export function TasksPage({ onNavigate }: TasksPageProps = {}) {
  const [currentPage, setCurrentPage] = useState("Tarefas")

  // Estados para busca e filtros de vagas
  const [jobSearchTerm, setJobSearchTerm] = useState("")
  const [showJobFilters, setShowJobFilters] = useState(false)
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])
  const [selectedUrgencies, setSelectedUrgencies] = useState<string[]>([])
  const [selectedPublications, setSelectedPublications] = useState<string[]>([])
  const [jobSortBy, setJobSortBy] = useState<'daysOpen' | 'candidates' | 'urgency'>('urgency')

  // Estados para requisições de vagas
  const [requestSearchTerm, setRequestSearchTerm] = useState("")
  const [showRequestFilters, setShowRequestFilters] = useState(false)
  const [selectedRequestStatus, setSelectedRequestStatus] = useState<string[]>([])
  const [selectedRequestDepartments, setSelectedRequestDepartments] = useState<string[]>([])
  const [requestSortBy, setRequestSortBy] = useState<'date' | 'priority' | 'status'>('priority')

  // Estados para modal de detalhes da atividade
  const [selectedActivity, setSelectedActivity] = useState<any | null>(null)
  const [showActivityModal, setShowActivityModal] = useState(false)

  // Estados para o novo card de tarefas pendentes
  const [pendingTaskFilter, setPendingTaskFilter] = useState<'all' | 'feedback' | 'entrevista' | 'sourcing'>('all')

  // Mock data - Tarefas Pendentes (preparado para API /api/v1/tasks)
  const pendingTasks: PendingTask[] = [
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

  // Mock data - Alertas Ativos (preparado para API /api/v1/alerts)
  const activeAlerts: ActiveAlert[] = [
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

  // Filtrar tarefas pendentes por tipo
  const filteredPendingTasks = useMemo(() => {
    if (pendingTaskFilter === 'all') return pendingTasks
    return pendingTasks.filter(task => task.type === pendingTaskFilter)
  }, [pendingTaskFilter])

  // Função para confirmar tarefa
  const handleConfirmTask = (task: PendingTask) => {
    const prompt = `Confirmar tarefa: ${task.title} - ${task.description}${task.candidateName ? ` para candidato ${task.candidateName}` : ''}`
    if (typeof window !== 'undefined') {
      localStorage.setItem('liaPrompt', prompt)
    }
    if (onNavigate) {
      onNavigate('Chat com LIA')
    }
  }

  // Função para rejeitar tarefa
  const handleRejectTask = (task: PendingTask) => {
    const prompt = `Rejeitar/Cancelar tarefa: ${task.title} - ${task.description}${task.candidateName ? ` para candidato ${task.candidateName}` : ''}`
    if (typeof window !== 'undefined') {
      localStorage.setItem('liaPrompt', prompt)
    }
    if (onNavigate) {
      onNavigate('Chat com LIA')
    }
  }

  // Função para ação de alerta
  const handleAlertAction = (alert: ActiveAlert) => {
    const prompt = `${alert.action} para a vaga ${alert.jobTitle} (${alert.jobId}): ${alert.description}`
    if (typeof window !== 'undefined') {
      localStorage.setItem('liaPrompt', prompt)
    }
    if (onNavigate) {
      onNavigate('Chat com LIA')
    }
  }

  // Helper para obter cor de prioridade de tarefa
  const getTaskPriorityStyle = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high':
        return { backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }
      case 'medium':
        return { backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }
      case 'low':
        return { backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }
    }
  }

  // Helper para obter cor de severidade de alerta
  const getAlertSeverityStyle = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high':
        return { backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }
      case 'medium':
        return { backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }
      case 'low':
        return { backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }
    }
  }

  // Helper para obter label de prioridade
  const getPriorityLabel = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high': return 'Alta'
      case 'medium': return 'Média'
      case 'low': return 'Baixa'
    }
  }

  // Helper para obter label de severidade
  const getSeverityLabel = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': return 'Alto'
      case 'medium': return 'Médio'
      case 'low': return 'Baixo'
    }
  }

  // Helper para obter ícone do tipo de tarefa
  const getTaskTypeIcon = (type: 'feedback' | 'entrevista' | 'sourcing') => {
    switch (type) {
      case 'feedback': return <MessageSquare className="w-3.5 h-3.5" />
      case 'entrevista': return <Calendar className="w-3.5 h-3.5" />
      case 'sourcing': return <Search className="w-3.5 h-3.5" />
    }
  }

  // Função para navegar ao Chat com LIA com prompt pré-construído
  const handleLIAAction = (action: string, job: JobWithAlert) => {
    let prompt = ''
    switch (action) {
      case 'kanban':
        prompt = `Mostrar o kanban completo da vaga ${job.title} (${job.jobId}) com todos os ${job.totalCandidates} candidatos`
        break
      case 'report':
        prompt = `Gerar relatório detalhado da vaga ${job.title} (${job.jobId}) incluindo métricas de conversão, tempo médio de resposta e análise de performance`
        break
      case 'share':
        prompt = `Compartilhar a vaga ${job.title} (${job.jobId}) no LinkedIn, Site e Indeed com descrição otimizada`
        break
      case 'edit':
        prompt = `Editar os requisitos e descrição da vaga ${job.title} (${job.jobId}) mantendo o alinhamento com as expectativas do gestor ${job.manager}`
        break
      case 'duplicate':
        prompt = `Duplicar a vaga ${job.title} (${job.jobId}) criando uma nova posição similar para ${job.department}`
        break
      case 'cancel':
        prompt = `Cancelar a vaga ${job.title} (${job.jobId}) e notificar todos os ${job.totalCandidates} candidatos e o gestor ${job.manager}`
        break
      default:
        prompt = `Ajudar com a vaga ${job.title} (${job.jobId})`
    }

    // Armazenar o prompt no localStorage para ser recuperado pelo chat
    if (typeof window !== 'undefined') {
      localStorage.setItem('liaPrompt', prompt)
    }

    // Navegar para o Chat com LIA
    if (onNavigate) {
      onNavigate('Chat com LIA')
    } else {
      console.log('Navegando para Chat LIA com prompt:', prompt)
    }
  }

  // Mock data - métricas
  const metrics = {
    total: 8,
    completed: 3,
    pending: 4,
    iaTasks: 1
  }

  // Mock data - tarefas expandido com mais detalhes
  const tasks: Task[] = [
    {
      id: '1',
      title: 'Entrevista Técnica - João Silva',
      description: 'Frontend Developer • React + TypeScript',
      type: 'entrevista',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 9, 0),
      priority: 'high',
      relatedTo: 'UX Designer Sênior',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    },
    {
      id: '2',
      title: 'Enviar Lembrete',
      description: 'Entrevista João Silva - 09:00',
      type: 'ia',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 8, 45),
      priority: 'medium',
      relatedTo: 'Lembrete automático',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    },
    {
      id: '3',
      title: 'Revisar CVs - Backend Dev',
      description: '15 candidatos pendentes',
      type: 'minha',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 10, 30),
      priority: 'medium',
      relatedTo: 'Triagem inicial',
      color: 'border-l-gray-500'
    },
    {
      id: '4',
      title: 'Revisar Perfis',
      description: '15 candidatos pendentes • Sugestão LIA',
      type: 'ia',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 11, 0),
      priority: 'medium',
      relatedTo: 'Triagem rápida',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    },
    {
      id: '5',
      title: 'Autorizar Feedback - Ana Costa',
      description: 'UX Designer • Processo finalizado',
      type: 'minha',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 14, 0),
      priority: 'high',
      relatedTo: 'Aprovação necessária',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    },
    {
      id: '6',
      title: 'Publicar Vaga - UX Designer',
      description: 'Área de Produto • Revisão final',
      type: 'minha',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 15, 30),
      priority: 'medium',
      relatedTo: 'Publicação em 3 canais',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    },
    {
      id: '7',
      title: 'Aprovar Oferta',
      description: 'Lucas Mendes - Backend • Sugestão LIA',
      type: 'ia',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 16, 0),
      priority: 'high',
      relatedTo: 'Oferta R$ 12.000',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    },
    {
      id: '8',
      title: 'Enviar Oferta - Lucas Mendes',
      description: 'Backend Developer • Aprovado',
      type: 'oferta',
      status: 'pending',
      dueDate: new Date(2025, 9, 11, 16, 30),
      priority: 'high',
      relatedTo: 'R$ 12.000',
      color: 'border-l-gray-700 dark:border-l-gray-300'
    }
  ]

  // Mock data - vagas ativas com alertas (ATUALIZADO com budget e publicações)
  const jobsWithAlerts: JobWithAlert[] = [
    {
      id: '1',
      jobId: 'WDT-2025-001',
      title: 'UX Designer Sênior',
      department: 'Design',
      stage: 'Entrevistas',
      totalCandidates: 45,
      manager: 'Roberto Silva',
      managerEmail: 'roberto.silva@sodexo.com',
      openDate: '2025-03-01',
      daysOpen: 28,
      urgencyLevel: 'urgent',
      budget: 25000,
      budgetUsed: 18500,
      publishedLinkedIn: true,
      publishedWebsite: true,
      publishedIndeed: true,
      stages: {
        new: 12,
        uncontacted: 8,
        contacted: 15,
        replied: 10,
        phoneScreen: 7,
        onsite: 4,
        makeOffer: 2,
        hired: 0
      },
      alert: {
        type: 'urgent',
        message: '3 candidatos aguardando feedback há 5+ dias',
        action: 'Enviar feedbacks'
      },
      liaPendencies: [
        'Aprovar feedback de Ana Costa',
        'Agendar entrevista com João Silva',
        'Responder candidato Pedro Alves'
      ]
    },
    {
      id: '2',
      jobId: 'WDT-2025-002',
      title: 'Desenvolvedor React Sênior',
      department: 'Tecnologia',
      stage: 'Finalização',
      totalCandidates: 68,
      manager: 'Carlos Santos',
      managerEmail: 'carlos.santos@sodexo.com',
      openDate: '2025-02-15',
      daysOpen: 42,
      urgencyLevel: 'critical',
      budget: 35000,
      budgetUsed: 32000,
      publishedLinkedIn: true,
      publishedWebsite: false,
      publishedIndeed: true,
      stages: {
        new: 5,
        uncontacted: 2,
        contacted: 8,
        replied: 12,
        phoneScreen: 10,
        onsite: 6,
        makeOffer: 3,
        hired: 2
      },
      alert: {
        type: 'success',
        message: '2 ofertas aceitas - preparar onboarding',
        action: 'Iniciar onboarding'
      },
      liaPendencies: [
        'Preparar onboarding de Carlos M.',
        'Negociar data de início'
      ]
    },
    {
      id: '3',
      jobId: 'WDT-2025-004',
      title: 'Data Scientist',
      department: 'Tecnologia',
      stage: 'Triagem',
      totalCandidates: 52,
      manager: 'Roberto Silva',
      managerEmail: 'roberto.silva@sodexo.com',
      openDate: '2025-02-20',
      daysOpen: 15,
      urgencyLevel: 'normal',
      budget: 60000,
      budgetUsed: 45000,
      publishedLinkedIn: true,
      publishedWebsite: true,
      publishedIndeed: false,
      stages: {
        new: 23,
        uncontacted: 15,
        contacted: 8,
        replied: 4,
        phoneScreen: 2,
        onsite: 0,
        makeOffer: 0,
        hired: 0
      },
      alert: {
        type: 'warning',
        message: 'Taxa de resposta baixa (26%) - revisar abordagem',
        action: 'Otimizar outreach'
      },
      liaPendencies: [
        'Finalizar triagem automática',
        'Preparar teste prático'
      ]
    }
  ]

  // Mock data - requisições de vagas
  const jobRequests: JobRequest[] = [
    {
      id: '1',
      requestId: 'REQ-2025-045',
      title: 'Desenvolvedor Full Stack Sênior',
      department: 'Tecnologia',
      requester: 'Carlos Mendes',
      requesterEmail: 'carlos.mendes@sodexo.com',
      requestDate: '2025-10-05',
      status: 'pending_approval',
      priority: 'critical',
      headcount: 2,
      estimatedSalary: 'R$ 12.000 - R$ 15.000',
      workModel: 'hybrid',
      justification: 'Expansão do time de produto para atender demanda de novos projetos estratégicos. Necessário expertise em React, Node.js e Cloud.',
      approvers: [
        { name: 'Roberto Silva', role: 'Diretor de Tecnologia', status: 'approved', date: '2025-10-06', comments: 'Aprovado. Projeto crítico.' },
        { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' },
        { name: 'Pedro Souza', role: 'CFO', status: 'pending' }
      ],
      daysWaiting: 6
    },
    {
      id: '2',
      requestId: 'REQ-2025-046',
      title: 'UX Designer Pleno',
      department: 'Design',
      requester: 'Juliana Oliveira',
      requesterEmail: 'juliana.oliveira@sodexo.com',
      requestDate: '2025-10-08',
      status: 'in_review',
      priority: 'high',
      headcount: 1,
      estimatedSalary: 'R$ 8.000 - R$ 10.000',
      workModel: 'remote',
      justification: 'Necessidade de reforço no time para redesign da plataforma mobile.',
      approvers: [
        { name: 'Roberto Silva', role: 'Head de Design', status: 'approved', date: '2025-10-09', comments: 'Aprovado com ressalvas sobre budget' },
        { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' }
      ],
      daysWaiting: 3
    },
    {
      id: '3',
      requestId: 'REQ-2025-047',
      title: 'Analista de Marketing Digital',
      department: 'Marketing',
      requester: 'Marina Santos',
      requesterEmail: 'marina.santos@sodexo.com',
      requestDate: '2025-10-09',
      status: 'requires_changes',
      priority: 'medium',
      headcount: 1,
      estimatedSalary: 'R$ 6.000 - R$ 8.000',
      workModel: 'hybrid',
      justification: 'Reforço para campanhas de lançamento de novos produtos.',
      approvers: [
        { name: 'Paula Lima', role: 'Diretora de Marketing', status: 'rejected', date: '2025-10-10', comments: 'Solicito revisão do budget e escopo das atividades' }
      ],
      daysWaiting: 2
    },
    {
      id: '4',
      requestId: 'REQ-2025-048',
      title: 'Gerente de Vendas - Região Sul',
      department: 'Vendas',
      requester: 'Fernando Costa',
      requesterEmail: 'fernando.costa@sodexo.com',
      requestDate: '2025-10-01',
      status: 'approved',
      priority: 'high',
      headcount: 1,
      estimatedSalary: 'R$ 15.000 - R$ 18.000',
      workModel: 'hybrid',
      justification: 'Expansão da operação comercial na região Sul. Posição crítica para atingir metas de Q4.',
      approvers: [
        { name: 'Ricardo Alves', role: 'VP de Vendas', status: 'approved', date: '2025-10-02', comments: 'Aprovado. Iniciar processo imediatamente.' },
        { name: 'Pedro Souza', role: 'CFO', status: 'approved', date: '2025-10-03', comments: 'Budget aprovado' }
      ],
      daysWaiting: 10
    },
    {
      id: '5',
      requestId: 'REQ-2025-049',
      title: 'Assistente Administrativo',
      department: 'Operações',
      requester: 'Carla Mendes',
      requesterEmail: 'carla.mendes@sodexo.com',
      requestDate: '2025-10-10',
      status: 'draft',
      priority: 'low',
      headcount: 1,
      estimatedSalary: 'R$ 3.500 - R$ 4.500',
      workModel: 'onsite',
      justification: 'Reposição de colaborador que será promovido internamente.',
      approvers: [
        { name: 'Ana Costa', role: 'VP de Operações', status: 'pending' }
      ],
      daysWaiting: 1
    }
  ]

  // Função para filtrar e ordenar vagas
  const filteredAndSortedJobs = useMemo(() => {
    const filtered = jobsWithAlerts.filter(job => {
      // Busca por texto
      const searchLower = jobSearchTerm.toLowerCase()
      const matchesSearch = jobSearchTerm === "" ||
        job.title.toLowerCase().includes(searchLower) ||
        job.jobId.toLowerCase().includes(searchLower) ||
        job.manager.toLowerCase().includes(searchLower) ||
        job.department.toLowerCase().includes(searchLower)

      // Filtro por departamento
      const matchesDepartment = selectedDepartments.length === 0 ||
        selectedDepartments.includes(job.department)

      // Filtro por urgência
      const matchesUrgency = selectedUrgencies.length === 0 ||
        selectedUrgencies.includes(job.urgencyLevel)

      // Filtro por publicação
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

    // Ordenação
    filtered.sort((a, b) => {
      if (jobSortBy === 'daysOpen') {
        return b.daysOpen - a.daysOpen
      } else if (jobSortBy === 'candidates') {
        return b.totalCandidates - a.totalCandidates
      } else if (jobSortBy === 'urgency') {
        const urgencyOrder = { critical: 3, urgent: 2, normal: 1 }
        return urgencyOrder[b.urgencyLevel] - urgencyOrder[a.urgencyLevel]
      }
      return 0
    })

    return filtered
  }, [jobsWithAlerts, jobSearchTerm, selectedDepartments, selectedUrgencies, selectedPublications, jobSortBy])

  // Função para limpar todos os filtros de vagas
  const clearJobFilters = () => {
    setJobSearchTerm("")
    setSelectedDepartments([])
    setSelectedUrgencies([])
    setSelectedPublications([])
  }

  // Contar filtros ativos
  const activeJobFiltersCount = selectedDepartments.length + selectedUrgencies.length + selectedPublications.length

  // Obter departamentos únicos
  const uniqueDepartments = Array.from(new Set(jobsWithAlerts.map(job => job.department)))

  // Função para filtrar e ordenar requisições de vagas
  const filteredAndSortedRequests = useMemo(() => {
    const filtered = jobRequests.filter(request => {
      // Busca por texto
      const searchLower = requestSearchTerm.toLowerCase()
      const matchesSearch = requestSearchTerm === "" ||
        request.title.toLowerCase().includes(searchLower) ||
        request.requestId.toLowerCase().includes(searchLower) ||
        request.requester.toLowerCase().includes(searchLower) ||
        request.department.toLowerCase().includes(searchLower)

      // Filtro por status
      const matchesStatus = selectedRequestStatus.length === 0 ||
        selectedRequestStatus.includes(request.status)

      // Filtro por departamento
      const matchesDepartment = selectedRequestDepartments.length === 0 ||
        selectedRequestDepartments.includes(request.department)

      return matchesSearch && matchesStatus && matchesDepartment
    })

    // Ordenação
    filtered.sort((a, b) => {
      if (requestSortBy === 'date') {
        return new Date(b.requestDate).getTime() - new Date(a.requestDate).getTime()
      } else if (requestSortBy === 'priority') {
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
        return priorityOrder[b.priority] - priorityOrder[a.priority]
      } else if (requestSortBy === 'status') {
        const statusOrder: Record<string, number> = {
          requires_changes: 7,
          pending_approval: 6,
          in_review: 5,
          approved: 4,
          published: 3,
          draft: 2,
          rejected: 1
        }
        return (statusOrder[b.status] || 0) - (statusOrder[a.status] || 0)
      }
      return 0
    })

    return filtered
  }, [jobRequests, requestSearchTerm, selectedRequestStatus, selectedRequestDepartments, requestSortBy])

  // Função para limpar filtros de requisições
  const clearRequestFilters = () => {
    setRequestSearchTerm("")
    setSelectedRequestStatus([])
    setSelectedRequestDepartments([])
  }

  // Contar filtros ativos de requisições
  const activeRequestFiltersCount = selectedRequestStatus.length + selectedRequestDepartments.length

  // Obter departamentos únicos das requisições
  const uniqueRequestDepartments = Array.from(new Set(jobRequests.map(req => req.department)))

  // Funções auxiliares
  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'urgent': return <AlertTriangle className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
      case 'warning': return <AlertCircle className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
      case 'success': return <CheckCircle className="w-4 h-4" style={{ color: 'var(--eleven-text-primary)' }} />
      default: return <Info className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
    }
  }

  const getAlertColor = (type: string) => {
    // Paleta sépia/pastel ElevenLabs
    switch (type) {
      case 'urgent': return 'border-0' // Aplicado via inline style
      case 'warning': return 'border-0' // Aplicado via inline style
      case 'success': return 'border-0' // Aplicado via inline style
      default: return 'border-0' // Aplicado via inline style
    }
  }
  
  const getAlertStyle = (type: string) => {
    switch (type) {
      case 'urgent': return { backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }
      case 'warning': return { backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }
      case 'success': return { backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }
      default: return { backgroundColor: 'var(--eleven-sepia-cream)', color: 'var(--eleven-text-secondary)' }
    }
  }

  const getUrgencyColor = (urgency: string) => {
    // Cores sépia/pastel
    return '' // Aplicado via inline style
  }

  const getUrgencyBadge = (urgency: string, daysOpen: number) => {
    if (urgency === 'critical') {
      return <Badge className="border-0 text-xs font-medium" style={{ backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }}>🔴 Crítico</Badge>
    }
    if (urgency === 'urgent') {
      return <Badge className="border-0 text-xs font-semibold" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>⚠ Urgente</Badge>
    }
    if (daysOpen > 30) {
      return <Badge className="border-0 text-xs font-medium" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>⏰ Atenção</Badge>
    }
    return <Badge className="border-0 text-xs" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>✓ Normal</Badge>
  }

  // Nova função para calcular taxa de conversão
  const getConversionRate = (from: number, to: number) => {
    if (from === 0) return 0
    return Math.round((to / from) * 100)
  }

  // Nova função para determinar cor da taxa de conversão (sépia)
  const getConversionColor = (rate: number) => {
    if (rate >= 70) return 'font-semibold' // Verde menta via inline
    if (rate >= 50) return 'font-medium' // Dourado via inline
    return 'font-semibold' // Salmão via inline
  }
  
  const getConversionStyle = (rate: number) => {
    if (rate >= 70) return { color: 'var(--eleven-text-primary)' }
    if (rate >= 50) return { color: 'var(--eleven-text-primary)' }
    return { color: 'var(--eleven-text-primary)' }
  }

  // Funções helper para requisições de vagas (paleta sépia)
  const getRequestStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return { label: 'Rascunho', color: 'border-0', style: { backgroundColor: 'var(--eleven-sepia-cream)', color: 'var(--eleven-text-secondary)' }, icon: '📝' }
      case 'pending_approval':
        return { label: 'Aguardando Aprovação', color: 'border-0 font-medium', style: { backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }, icon: '⏳' }
      case 'in_review':
        return { label: 'Em Revisão', color: 'border-0 font-medium', style: { backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }, icon: '👁️' }
      case 'requires_changes':
        return { label: 'Requer Alterações', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }, icon: '✏️' }
      case 'approved':
        return { label: 'Aprovado', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }, icon: '✅' }
      case 'rejected':
        return { label: 'Rejeitado', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }, icon: '❌' }
      case 'published':
        return { label: 'Publicado', color: 'border-0 font-medium', style: { backgroundColor: 'var(--gray-950)', color: 'var(--gray-50)' }, icon: '🚀' }
      default:
        return { label: status, color: 'border-0', style: { backgroundColor: 'var(--eleven-sepia-cream)', color: 'var(--eleven-text-secondary)' }, icon: '•' }
    }
  }

  const getRequestPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'critical':
        return { label: 'Crítico', color: 'border-0 font-medium', style: { backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }, icon: '🔴' }
      case 'high':
        return { label: 'Alta', color: 'border-0 font-semibold', style: { backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }, icon: '🟠' }
      case 'medium':
        return { label: 'Média', color: 'border-0 font-medium', style: { backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }, icon: '🟡' }
      case 'low':
        return { label: 'Baixa', color: 'border-0', style: { backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }, icon: '🟢' }
      default:
        return { label: priority, color: 'border-0', style: { backgroundColor: 'var(--eleven-sepia-cream)', color: 'var(--eleven-text-secondary)' }, icon: '•' }
    }
  }

  const getWorkModelLabel = (model: string) => {
    switch (model) {
      case 'remote': return { label: 'Remoto', icon: '🏠' }
      case 'hybrid': return { label: 'Híbrido', icon: '🔄' }
      case 'onsite': return { label: 'Presencial', icon: '🏢' }
      default: return { label: model, icon: '•' }
    }
  }

  // Helper function para obter background pastel dos cards de atividades (tons claros ElevenLabs)
  const getTaskCardBackground = (taskType: Task['type']) => {
    return 'var(--gray-100)'
  }

  // Helper function para obter cor do ícone baseado no tipo (tons mais escuros para contraste)
  const getTaskIconBackground = (taskType: Task['type']) => {
    switch (taskType) {
      case 'entrevista':
        return 'var(--status-success)'
      case 'ia':
      case 'email':
      case 'oferta':
        return 'var(--gray-400)'
      default:
        return 'var(--gray-400)'
    }
  }

  // Função para abrir modal de detalhes da atividade
  const handleActivityClick = (task: Task) => {
    // Dados mockados de histórico completo da atividade
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
        {
          id: '1',
          type: 'created',
          user: 'Ana Silva',
          date: new Date(2025, 9, 8, 14, 30),
          description: 'Atividade criada',
          icon: 'plus'
        },
        {
          id: '2',
          type: 'comment',
          user: 'Roberto Silva',
          date: new Date(2025, 9, 9, 10, 15),
          description: 'Candidato aprovado na triagem inicial. Possui excelente experiência em React.',
          icon: 'message'
        },
        {
          id: '3',
          type: 'status_change',
          user: 'LIA',
          date: new Date(2025, 9, 10, 8, 0),
          description: 'Status alterado de "Triagem" para "Entrevista Agendada"',
          icon: 'check'
        },
        {
          id: '4',
          type: 'reminder',
          user: 'Sistema',
          date: new Date(2025, 9, 10, 8, 45),
          description: 'Lembrete automático enviado - Entrevista em 15 minutos',
          icon: 'bell'
        }
      ],
      attachments: [
        { id: '1', name: 'CV_JoaoSilva.pdf', size: '245 KB', uploadedBy: 'João Silva', date: new Date(2025, 9, 5) },
        { id: '2', name: 'Portfolio.pdf', size: '1.2 MB', uploadedBy: 'João Silva', date: new Date(2025, 9, 5) }
      ],
      comments: [
        {
          id: '1',
          user: 'Ana Silva',
          avatar: '/avatars/ana.jpg',
          date: new Date(2025, 9, 9, 16, 30),
          text: 'Candidato muito promissor. Experiência sólida em frontend e boas soft skills.'
        },
        {
          id: '2',
          user: 'Roberto Silva',
          avatar: '/avatars/roberto.jpg',
          date: new Date(2025, 9, 10, 8, 15),
          text: 'Confirmar com o candidato se precisa de algum equipamento específico para a entrevista técnica.'
        }
      ],
      nextSteps: [
        'Realizar entrevista técnica',
        'Avaliar fit cultural',
        'Enviar feedback em até 24h'
      ]
    }

    setSelectedActivity(activityDetails)
    setShowActivityModal(true)
  }

  // Função para lidar com ações nas requisições
  const handleRequestAction = (action: string, request: JobRequest) => {
    let prompt = ''
    switch (action) {
      case 'approve':
        prompt = `Aprovar a requisição ${request.requestId} - ${request.title} do departamento ${request.department} solicitada por ${request.requester}`
        break
      case 'reject':
        prompt = `Rejeitar a requisição ${request.requestId} - ${request.title} e notificar ${request.requester} com justificativa`
        break
      case 'request_changes':
        prompt = `Solicitar alterações na requisição ${request.requestId} - ${request.title} para ${request.requester}`
        break
      case 'send_approval':
        prompt = `Enviar a requisição ${request.requestId} - ${request.title} para aprovação dos gestores`
        break
      case 'edit':
        prompt = `Editar a requisição ${request.requestId} - ${request.title} incluindo justificativa, budget e requisitos`
        break
      case 'publish':
        prompt = `Publicar a vaga ${request.title} (${request.requestId}) nas plataformas LinkedIn, Site e Indeed`
        break
      case 'view_details':
        prompt = `Mostrar todos os detalhes da requisição ${request.requestId} - ${request.title} incluindo aprovadores e histórico`
        break
      default:
        prompt = `Ajudar com a requisição ${request.requestId} - ${request.title}`
    }

    // Armazenar o prompt no localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('liaPrompt', prompt)
    }

    // Navegar para o Chat com LIA
    if (onNavigate) {
      onNavigate('Chat com LIA')
    }
  }

  return (
    <>
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden">
      <div className="p-2 max-w-full overflow-x-auto">

        {/* Header - Saudação no topo (alinhado com outras páginas) */}
        <div className="flex items-center justify-between mb-1.5">
          <div>
            <h1 className="text-base font-['Open_Sans',sans-serif] font-semibold wedo-text-black mb-0.5 flex items-center gap-2">
              <Target className="w-4 h-4 text-gray-950 dark:text-gray-50" />
              Painel de Controle
            </h1>
            <p className={`${textStyles.bodySmall} wedo-text-gray`}>
              Você tem 30 novos candidatos e 4 vagas abertas.
            </p>
          </div>
          <Button 
            className="gap-1.5 h-7 px-2.5 font-open-sans text-xs"
            onClick={() => {
              if (onNavigate) {
                onNavigate('Chat com LIA')
                setTimeout(() => {
                  window.dispatchEvent(new CustomEvent('lia-new-task'))
                }, 100)
              }
            }}
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Tarefa
          </Button>
        </div>

        {/* Daily Briefing Card - Resumo do dia gerado por LIA */}
        <div className="mb-2">
          <DailyBriefingCard 
            onNavigate={onNavigate}
            onActionClick={(action, context) => {
              if (action === 'open_pipeline_chat') {
                if (onNavigate) {
                  onNavigate('Chat com LIA')
                  setTimeout(() => {
                    window.dispatchEvent(new CustomEvent('lia-open-pipeline', { 
                      detail: context 
                    }))
                  }, 100)
                }
              }
            }}
          />
        </div>

        <div className="space-y-2">

            {/* Cards de Status de Tarefas - LINHA HORIZONTAL ULTRA COMPACTA */}
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-800 p-2 rounded-md">
              <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                <Briefcase className="w-3 h-3 text-gray-950 dark:text-gray-50" />
                <span className="text-sm font-inter font-medium text-gray-950 dark:text-gray-50">{metrics.total}</span>
                <span className={`${textStyles.description} dark:text-gray-500`}>Total</span>
              </div>
              <div className="w-px h-6 bg-gray-300 dark:bg-gray-700"></div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                <CheckCircle2 className="w-3 h-3 text-gray-950 dark:text-gray-50 font-semibold" />
                <span className="text-sm font-inter font-medium text-gray-950 dark:text-gray-50">{metrics.completed}</span>
                <span className={`${textStyles.description} dark:text-gray-500`}>Concluídas</span>
              </div>
              <div className="w-px h-6 bg-gray-300 dark:bg-gray-700"></div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                <Clock className="w-3 h-3 text-gray-950 dark:text-gray-50" />
                <span className="text-sm font-inter font-medium text-gray-950 dark:text-gray-50">{metrics.pending}</span>
                <span className={`${textStyles.description} dark:text-gray-500`}>Pendentes</span>
              </div>
              <div className="w-px h-6 bg-gray-300 dark:bg-gray-700"></div>
              <div className="flex items-center gap-1.5 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                <Brain className="w-3 h-3 text-wedo-cyan" />
                <span className="text-sm font-inter font-medium text-gray-950 dark:text-gray-50">{metrics.iaTasks}</span>
                <span className={`${textStyles.description} dark:text-gray-500`}>IA</span>
              </div>
            </div>

            {/* Grid 2 colunas: Minhas Tarefas + Alertas Ativos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
              
              {/* Card: Minhas Tarefas */}
              <Card className="border-gray-200 dark:border-gray-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-gray-950 dark:text-gray-50" />
                      <CardTitle className={`${textStyles.label} font-semibold wedo-text-black`}>Minhas Tarefas</CardTitle>
                      <Badge variant="outline" className="text-xs font-inter">
                        {filteredPendingTasks.length}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 pb-2">
                  <Tabs defaultValue="tarefas" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 h-8 mb-3 bg-gray-100 dark:bg-gray-800 p-0.5">
                      <TabsTrigger value="tarefas" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-white data-[state=active]:text-gray-950 dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-gray-50">
                        Tarefas ({filteredPendingTasks.length})
                      </TabsTrigger>
                      <TabsTrigger value="historico" className="text-xs font-open-sans h-7 data-[state=active]:font-semibold data-[state=active]:bg-white data-[state=active]:text-gray-950 dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-gray-50">
                        Histórico
                      </TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="tarefas" className="mt-0">
                      {/* Filtros por tipo */}
                      <div className="flex items-center gap-1.5 mb-3 flex-wrap">
                        <button
                          onClick={() => setPendingTaskFilter('all')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors ${
                            pendingTaskFilter === 'all'
                              ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-950 font-medium'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700'
                          }`}
                        >
                          Todos ({pendingTasks.length})
                        </button>
                        <button
                          onClick={() => setPendingTaskFilter('feedback')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors flex items-center gap-1 ${
                            pendingTaskFilter === 'feedback'
                              ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-950 font-medium'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700'
                          }`}
                        >
                          <MessageSquare className="w-2.5 h-2.5" />
                          Feedback ({pendingTasks.filter(t => t.type === 'feedback').length})
                        </button>
                        <button
                          onClick={() => setPendingTaskFilter('entrevista')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors flex items-center gap-1 ${
                            pendingTaskFilter === 'entrevista'
                              ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-950 font-medium'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700'
                          }`}
                        >
                          <Calendar className="w-2.5 h-2.5" />
                          Entrevista ({pendingTasks.filter(t => t.type === 'entrevista').length})
                        </button>
                        <button
                          onClick={() => setPendingTaskFilter('sourcing')}
                          className={`px-2 py-1 text-xs font-open-sans rounded-full transition-colors flex items-center gap-1 ${
                            pendingTaskFilter === 'sourcing'
                              ? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-950 font-medium'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700'
                          }`}
                        >
                          <Search className="w-2.5 h-2.5" />
                          Sourcing ({pendingTasks.filter(t => t.type === 'sourcing').length})
                        </button>
                      </div>
                      
                      <div className="max-h-[320px] overflow-y-auto space-y-3">
                        {/* Sessão Manhã */}
                        {(() => {
                          const morningTasks = filteredPendingTasks.filter(t => t.dueDate.getHours() < 12)
                          if (morningTasks.length === 0) return null
                          return (
                            <div>
                              <div className="flex items-center gap-1.5 mb-1.5">
                                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--eleven-sepia-gold)' }}></div>
                                <h3 className="text-xs font-open-sans font-semibold text-gray-800 dark:text-gray-200">Sessão Manhã</h3>
                                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-400">{morningTasks.length} atividades</span>
                              </div>
                              <div className="space-y-1.5">
                                {morningTasks.map((task) => (
                                  <div
                                    key={task.id}
                                    className="border border-gray-200 dark:border-gray-700 rounded-md p-2.5 hover:transition-all bg-white dark:bg-gray-900"
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex items-start gap-2 flex-1">
                                        <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 bg-gray-100 dark:bg-gray-800">
                                          {getTaskTypeIcon(task.type)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                                            <span className="text-xs font-inter font-medium text-gray-950 dark:text-gray-50">
                                              {task.dueDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                            <h4 className="text-xs font-inter font-semibold text-gray-950 dark:text-gray-50">
                                              {task.title}
                                            </h4>
                                            <Badge 
                                              className="border-0 text-xs py-0 px-1.5 font-medium"
                                              style={getTaskPriorityStyle(task.priority)}
                                            >
                                              {getPriorityLabel(task.priority)}
                                            </Badge>
                                          </div>
                                          <p className="text-xs font-open-sans text-gray-800 dark:text-gray-500 mb-1 line-clamp-1">
                                            {task.description}
                                          </p>
                                          <div className="flex items-center gap-2 text-xs text-gray-800 dark:text-gray-500">
                                            {task.candidateName && (
                                              <span className="flex items-center gap-0.5">
                                                <User className="w-2.5 h-2.5" />
                                                {task.candidateName}
                                              </span>
                                            )}
                                            {task.relatedJob && (
                                              <span className="flex items-center gap-0.5">
                                                <Briefcase className="w-2.5 h-2.5" />
                                                {task.relatedJob}
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                      <div className="flex flex-col gap-1 flex-shrink-0">
                                        {task.type === 'feedback' && (
                                          <div className="flex items-center gap-1">
                                            <Button
                                              size="sm"
                                              onClick={() => handleConfirmTask(task)}
                                              className="h-5 px-2 text-xs gap-1 border-0"
                                              style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}
                                            >
                                              <MessageSquare className="w-2.5 h-2.5" />
                                              Avaliar
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="h-5 px-2 text-xs gap-1"
                                            >
                                              <FileText className="w-2.5 h-2.5" />
                                              Ver CV
                                            </Button>
                                          </div>
                                        )}
                                        {task.type === 'entrevista' && (
                                          <div className="flex items-center gap-1">
                                            <Button
                                              size="sm"
                                              onClick={() => handleConfirmTask(task)}
                                              className="h-5 px-2 text-xs gap-1 border-0"
                                              style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}
                                            >
                                              <Play className="w-2.5 h-2.5" />
                                              Iniciar
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="h-5 px-2 text-xs gap-1"
                                            >
                                              <FileText className="w-2.5 h-2.5" />
                                              Ver CV
                                            </Button>
                                          </div>
                                        )}
                                        {task.type === 'sourcing' && (
                                          <div className="flex items-center gap-1">
                                            <Button
                                              size="sm"
                                              onClick={() => handleConfirmTask(task)}
                                              className="h-5 px-2 text-xs gap-1 border-0"
                                              style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}
                                            >
                                              <Search className="w-2.5 h-2.5" />
                                              Buscar
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="h-5 px-2 text-xs gap-1"
                                            >
                                              <Users className="w-2.5 h-2.5" />
                                              Ver Perfis
                                            </Button>
                                          </div>
                                        )}
                                        <div className="flex items-center gap-1">
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => handleConfirmTask(task)}
                                            className="h-5 px-1.5 text-xs gap-0.5"
                                          >
                                            <CheckCircle className="w-2.5 h-2.5" />
                                            Confirmar
                                          </Button>
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => handleRejectTask(task)}
                                            className="h-5 px-1.5 text-xs gap-0.5 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
                                          >
                                            <XCircle className="w-2.5 h-2.5" />
                                            Rejeitar
                                          </Button>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        })()}
                        
                        {/* Sessão Tarde */}
                        {(() => {
                          const afternoonTasks = filteredPendingTasks.filter(t => t.dueDate.getHours() >= 12)
                          if (afternoonTasks.length === 0) return null
                          return (
                            <div>
                              <div className="flex items-center gap-1.5 mb-1.5">
                                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}></div>
                                <h3 className="text-xs font-open-sans font-semibold text-gray-800 dark:text-gray-200">Sessão Tarde</h3>
                                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-400">{afternoonTasks.length} atividades</span>
                              </div>
                              <div className="space-y-1.5">
                                {afternoonTasks.map((task) => (
                                  <div
                                    key={task.id}
                                    className="border border-gray-200 dark:border-gray-700 rounded-md p-2.5 hover:transition-all bg-white dark:bg-gray-900"
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex items-start gap-2 flex-1">
                                        <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 bg-gray-100 dark:bg-gray-800">
                                          {getTaskTypeIcon(task.type)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                                            <span className="text-xs font-inter font-medium text-gray-950 dark:text-gray-50">
                                              {task.dueDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                            <h4 className="text-xs font-inter font-semibold text-gray-950 dark:text-gray-50">
                                              {task.title}
                                            </h4>
                                            <Badge 
                                              className="border-0 text-xs py-0 px-1.5 font-medium"
                                              style={getTaskPriorityStyle(task.priority)}
                                            >
                                              {getPriorityLabel(task.priority)}
                                            </Badge>
                                          </div>
                                          <p className="text-xs font-open-sans text-gray-800 dark:text-gray-500 mb-1 line-clamp-1">
                                            {task.description}
                                          </p>
                                          <div className="flex items-center gap-2 text-xs text-gray-800 dark:text-gray-500">
                                            {task.candidateName && (
                                              <span className="flex items-center gap-0.5">
                                                <User className="w-2.5 h-2.5" />
                                                {task.candidateName}
                                              </span>
                                            )}
                                            {task.relatedJob && (
                                              <span className="flex items-center gap-0.5">
                                                <Briefcase className="w-2.5 h-2.5" />
                                                {task.relatedJob}
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                      <div className="flex flex-col gap-1 flex-shrink-0">
                                        {task.type === 'feedback' && (
                                          <div className="flex items-center gap-1">
                                            <Button
                                              size="sm"
                                              onClick={() => handleConfirmTask(task)}
                                              className="h-5 px-2 text-xs gap-1 border-0"
                                              style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}
                                            >
                                              <MessageSquare className="w-2.5 h-2.5" />
                                              Avaliar
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="h-5 px-2 text-xs gap-1"
                                            >
                                              <FileText className="w-2.5 h-2.5" />
                                              Ver CV
                                            </Button>
                                          </div>
                                        )}
                                        {task.type === 'entrevista' && (
                                          <div className="flex items-center gap-1">
                                            <Button
                                              size="sm"
                                              onClick={() => handleConfirmTask(task)}
                                              className="h-5 px-2 text-xs gap-1 border-0"
                                              style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}
                                            >
                                              <Play className="w-2.5 h-2.5" />
                                              Iniciar
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="h-5 px-2 text-xs gap-1"
                                            >
                                              <FileText className="w-2.5 h-2.5" />
                                              Ver CV
                                            </Button>
                                          </div>
                                        )}
                                        {task.type === 'sourcing' && (
                                          <div className="flex items-center gap-1">
                                            <Button
                                              size="sm"
                                              onClick={() => handleConfirmTask(task)}
                                              className="h-5 px-2 text-xs gap-1 border-0"
                                              style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}
                                            >
                                              <Search className="w-2.5 h-2.5" />
                                              Buscar
                                            </Button>
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              className="h-5 px-2 text-xs gap-1"
                                            >
                                              <Users className="w-2.5 h-2.5" />
                                              Ver Perfis
                                            </Button>
                                          </div>
                                        )}
                                        <div className="flex items-center gap-1">
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => handleConfirmTask(task)}
                                            className="h-5 px-1.5 text-xs gap-0.5"
                                          >
                                            <CheckCircle className="w-2.5 h-2.5" />
                                            Confirmar
                                          </Button>
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => handleRejectTask(task)}
                                            className="h-5 px-1.5 text-xs gap-0.5 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
                                          >
                                            <XCircle className="w-2.5 h-2.5" />
                                            Rejeitar
                                          </Button>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        })()}
                        
                        {filteredPendingTasks.length === 0 && (
                          <div className="text-center py-8">
                            <CheckCircle2 className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-3" />
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-50 mb-1">Nenhuma tarefa pendente</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">Todas as tarefas foram concluídas</p>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="historico" className="mt-0">
                      <ActivityFeed limit={15} className="max-h-[400px] overflow-y-auto" />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              {/* Card: Alertas Ativos */}
              <Card className="border-gray-200 dark:border-gray-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bell className="w-3.5 h-3.5 text-gray-950 dark:text-gray-50" />
                      <CardTitle className={`${textStyles.label} font-semibold wedo-text-black`}>Alertas Ativos</CardTitle>
                      <Badge variant="outline" className="text-xs font-inter">
                        {activeAlerts.length}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Badge 
                        className="border-0 text-xs font-medium"
                        style={{ backgroundColor: 'var(--eleven-sepia-salmon)', color: 'var(--eleven-text-primary)' }}
                      >
                        {activeAlerts.filter(a => a.severity === 'high').length} Alto
                      </Badge>
                      <Badge 
                        className="border-0 text-xs font-medium"
                        style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}
                      >
                        {activeAlerts.filter(a => a.severity === 'medium').length} Médio
                      </Badge>
                      <Badge 
                        className="border-0 text-xs font-medium"
                        style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}
                      >
                        {activeAlerts.filter(a => a.severity === 'low').length} Baixo
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 pb-2 max-h-[280px] overflow-y-auto">
                  <div className="space-y-2">
                    {activeAlerts.map((alert) => (
                      <div
                        key={alert.id}
                        className="border border-gray-200 dark:border-gray-700 rounded-md p-2.5 hover:transition-all"
                        style={{ backgroundColor: getAlertSeverityStyle(alert.severity).backgroundColor + '40' }}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-start gap-2 flex-1">
                            {/* Ícone de severidade */}
                            <div 
                              className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
                              style={getAlertSeverityStyle(alert.severity)}
                            >
                              {alert.severity === 'high' && <AlertTriangle className="w-3.5 h-3.5" />}
                              {alert.severity === 'medium' && <AlertCircle className="w-3.5 h-3.5" />}
                              {alert.severity === 'low' && <Info className="w-3.5 h-3.5" />}
                            </div>
                            
                            {/* Conteúdo */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
                                <h4 className="text-xs font-inter font-semibold text-gray-950 dark:text-gray-50">
                                  {alert.title}
                                </h4>
                                <Badge 
                                  className="border-0 text-xs py-0 px-1.5 font-medium"
                                  style={getAlertSeverityStyle(alert.severity)}
                                >
                                  {getSeverityLabel(alert.severity)}
                                </Badge>
                              </div>
                              <p className="text-xs font-open-sans text-gray-800 dark:text-gray-500 mb-1 line-clamp-1">
                                {alert.description}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-gray-800 dark:text-gray-500">
                                <span className="flex items-center gap-0.5">
                                  <Briefcase className="w-2.5 h-2.5" />
                                  {alert.jobTitle}
                                </span>
                                <span className="flex items-center gap-0.5">
                                  <Clock className="w-2.5 h-2.5" />
                                  {alert.createdAt.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          {/* Botão de ação com LIA */}
                          <Button
                            size="sm"
                            onClick={() => handleAlertAction(alert)}
                            className="h-6 px-2 text-xs gap-1 flex-shrink-0"
                          >
                            <Brain className="w-3 h-3 text-wedo-cyan" />
                            {alert.action}
                          </Button>
                        </div>
                      </div>
                    ))}
                    
                    {activeAlerts.length === 0 && (
                      <div className="text-center py-8">
                        <Bell className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-3" />
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-50 mb-1">Nenhum alerta ativo</p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">Sem alertas no momento</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tabela de Vagas Ativas - COM BUSCA E FILTROS */}
            <Card className="border-gray-200 dark:border-gray-800">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-open-sans font-semibold wedo-text-black">Minhas Vagas Ativas</CardTitle>
                  <div className="flex items-center gap-2">
                    {/* Contador de resultados */}
                    <Badge variant="outline" className="text-xs font-inter">
                      {filteredAndSortedJobs.length} vaga{filteredAndSortedJobs.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                </div>

                {/* Barra de Busca e Filtros */}
                <div className="mt-3 space-y-2">
                  <div className="flex items-center gap-2">
                    {/* Input de Busca */}
                    <div className="flex-1 relative">
                      <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                      <Input
                        placeholder="Buscar vagas por título, ID, gestor ou departamento..."
                        value={jobSearchTerm}
                        onChange={(e) => setJobSearchTerm(e.target.value)}
                        className="pl-8 h-8 text-xs"
                      />
                      {jobSearchTerm && (
                        <button
                          onClick={() => setJobSearchTerm("")}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
                          aria-label="Limpar busca"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      )}
                    </div>

                    {/* Botão de Filtros */}
                    <Button
                      variant={showJobFilters || activeJobFiltersCount > 0 ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowJobFilters(!showJobFilters)}
                      className="gap-1.5 h-8 px-3 text-xs"
                    >
                      <SlidersHorizontal className="w-3.5 h-3.5" />
                      Filtros
                      {activeJobFiltersCount > 0 && (
                        <Badge className="ml-1 bg-white text-gray-950 dark:bg-gray-800 dark:text-gray-50 text-xs h-4 px-1 font-semibold">
                          {activeJobFiltersCount}
                        </Badge>
                      )}
                    </Button>

                    {/* Dropdown de Ordenação */}
                    <div className="relative group">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 h-8 px-3 text-xs"
                      >
                        <ArrowUpDown className="w-3.5 h-3.5" />
                        Ordenar
                      </Button>

                      {/* Menu de Ordenação */}
                      <div className="absolute right-0 top-full mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                        <div className="py-1">
                          <button
                            onClick={() => setJobSortBy('urgency')}
                            className={`w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 dark:hover:bg-gray-700 ${
                              jobSortBy === 'urgency' ? 'bg-gray-200 text-gray-950 dark:bg-gray-700 dark:text-gray-50 font-semibold' : ''
                            }`}
                          >
                            Por Urgência
                          </button>
                          <button
                            onClick={() => setJobSortBy('daysOpen')}
                            className={`w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 dark:hover:bg-gray-700 ${
                              jobSortBy === 'daysOpen' ? 'bg-gray-200 text-gray-950 dark:bg-gray-700 dark:text-gray-50 font-semibold' : ''
                            }`}
                          >
                            Por Dias em Aberto
                          </button>
                          <button
                            onClick={() => setJobSortBy('candidates')}
                            className={`w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 dark:hover:bg-gray-700 ${
                              jobSortBy === 'candidates' ? 'bg-gray-200 text-gray-950 dark:bg-gray-700 dark:text-gray-50 font-semibold' : ''
                            }`}
                          >
                            Por Nº Candidatos
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Painel de Filtros Expandido */}
                  {showJobFilters && (
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-3 space-y-3 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-open-sans font-semibold text-gray-800 dark:text-gray-200">Filtros Avançados</span>
                        {activeJobFiltersCount > 0 && (
                          <button
                            onClick={clearJobFilters}
                            className="text-xs text-gray-800 hover:text-gray-950 dark:text-gray-200 dark:hover:text-gray-100 flex items-center gap-1 "
                          >
                            <X className="w-3 h-3" />
                            Limpar filtros
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        {/* Filtro por Departamento */}
                        <div>
                          <label className="text-xs font-open-sans font-medium text-gray-800 dark:text-gray-500 mb-1.5 block">
                            Departamento
                          </label>
                          <div className="space-y-1">
                            {uniqueDepartments.map(dept => (
                              <label key={dept} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedDepartments.includes(dept)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedDepartments([...selectedDepartments, dept])
                                    } else {
                                      setSelectedDepartments(selectedDepartments.filter(d => d !== dept))
                                    }
                                  }}
                                  className="w-4 h-4 rounded-sm border-gray-300 accent-gray-900 focus:ring-2 focus:ring-gray-900/20"
                                />
                                <span className="text-xs text-gray-800 dark:text-gray-200">{dept}</span>
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* Filtro por Urgência */}
                        <div>
                          <label className="text-xs font-open-sans font-medium text-gray-800 dark:text-gray-500 mb-1.5 block">
                            Urgência
                          </label>
                          <div className="space-y-1">
                            {['critical', 'urgent', 'normal'].map(urgency => (
                              <label key={urgency} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedUrgencies.includes(urgency)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedUrgencies([...selectedUrgencies, urgency])
                                    } else {
                                      setSelectedUrgencies(selectedUrgencies.filter(u => u !== urgency))
                                    }
                                  }}
                                  className="w-4 h-4 rounded-sm border-gray-300 accent-gray-900 focus:ring-2 focus:ring-gray-900/20"
                                />
                                <span className="text-xs text-gray-800 dark:text-gray-200 capitalize">
                                  {urgency === 'critical' ? 'Crítico' : urgency === 'urgent' ? 'Urgente' : 'Normal'}
                                </span>
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* Filtro por Publicação */}
                        <div>
                          <label className="text-xs font-open-sans font-medium text-gray-800 dark:text-gray-500 mb-1.5 block">
                            Publicado em
                          </label>
                          <div className="space-y-1">
                            {[
                              { id: 'linkedin', label: 'LinkedIn' },
                              { id: 'site', label: 'Site' },
                              { id: 'indeed', label: 'Indeed' }
                            ].map(pub => (
                              <label key={pub.id} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selectedPublications.includes(pub.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedPublications([...selectedPublications, pub.id])
                                    } else {
                                      setSelectedPublications(selectedPublications.filter(p => p !== pub.id))
                                    }
                                  }}
                                  className="w-4 h-4 rounded-sm border-gray-300 accent-gray-900 focus:ring-2 focus:ring-gray-900/20"
                                />
                                <span className="text-xs text-gray-800 dark:text-gray-200">{pub.label}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Filtros Ativos (Tags) */}
                  {activeJobFiltersCount > 0 && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-gray-800 dark:text-gray-500">Filtros ativos:</span>
                      {selectedDepartments.map(dept => (
                        <Badge
                          key={dept}
                          variant="secondary"
                          className="text-xs flex items-center gap-1 pr-1"
                        >
                          {dept}
                          <button
                            onClick={() => setSelectedDepartments(selectedDepartments.filter(d => d !== dept))}
                            className="hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full p-0.5" aria-label="Remover filtro"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                      {selectedUrgencies.map(urgency => (
                        <Badge
                          key={urgency}
                          variant="secondary"
                          className="text-xs flex items-center gap-1 pr-1"
                        >
                          {urgency === 'critical' ? 'Crítico' : urgency === 'urgent' ? 'Urgente' : 'Normal'}
                          <button
                            onClick={() => setSelectedUrgencies(selectedUrgencies.filter(u => u !== urgency))}
                            className="hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full p-0.5" aria-label="Remover filtro"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                      {selectedPublications.map(pub => (
                        <Badge
                          key={pub}
                          variant="secondary"
                          className="text-xs flex items-center gap-1 pr-1"
                        >
                          {pub === 'linkedin' ? 'LinkedIn' : pub === 'site' ? 'Site' : 'Indeed'}
                          <button
                            onClick={() => setSelectedPublications(selectedPublications.filter(p => p !== pub))}
                            className="hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full p-0.5" aria-label="Remover filtro"
                          >
                            <X className="w-2.5 h-2.5" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                {/* Mensagem de resultados vazios */}
                {filteredAndSortedJobs.length === 0 ? (
                  <div className="text-center py-8">
                    <Search className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
                    <p className="text-base font-medium text-gray-900 dark:text-gray-50 mb-1">Nenhuma vaga encontrada</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Tente ajustar os filtros ou buscar por outros termos
                    </p>
                    {activeJobFiltersCount > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={clearJobFilters}
                        className="mt-3 text-xs"
                      >
                        Limpar filtros
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredAndSortedJobs.map((job) => (
                      <div key={job.id} className="border border-gray-200 dark:border-gray-700 rounded-md p-3 hover:border-gray-400 hover:border-gray-400 dark:hover:border-gray-500 hover:scale-[1.01] transition-all duration-200 bg-white dark:bg-gray-900 cursor-pointer">
                        {/* Header da Vaga - Compacto com publicação inline */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 space-y-1">
                            {/* Linha 1: Título + Badges + Publicação */}
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="font-semibold text-sm text-gray-950 dark:text-gray-50">{job.title}</h3>
                              <Badge variant="outline" className="text-xs">{job.jobId}</Badge>
                              {getUrgencyBadge(job.urgencyLevel, job.daysOpen)}
                              {job.publishedLinkedIn && (
                                <Badge className="bg-gray-100 text-gray-950 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 text-xs flex items-center gap-1 font-medium">
                                  <Linkedin className="w-2.5 h-2.5" />
                                  LI
                                </Badge>
                              )}
                              {job.publishedWebsite && (
                                <Badge className="bg-gray-100 text-gray-950 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 text-xs flex items-center gap-1 font-medium">
                                  <Globe className="w-2.5 h-2.5" />
                                  Site
                                </Badge>
                              )}
                              {job.publishedIndeed && (
                                <Badge className="bg-gray-100 text-gray-950 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 text-xs flex items-center gap-1 font-medium">
                                  <Briefcase className="w-2.5 h-2.5" />
                                  Indeed
                                </Badge>
                              )}
                            </div>
                            {/* Linha 2: Informações inline compactas */}
                            <div className="flex items-center gap-3 text-xs text-gray-800 dark:text-gray-500 flex-wrap">
                              <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                <span className={`font-medium ${getUrgencyColor(job.urgencyLevel)}`}>{job.daysOpen}d</span>
                              </div>
                              <span className="text-gray-500 dark:text-gray-500">•</span>
                              <div className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                <span>{job.manager.split(' ')[0]}</span>
                              </div>
                              <span className="text-gray-500 dark:text-gray-500">•</span>
                              <div className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                <span>{job.department}</span>
                              </div>
                              <span className="text-gray-500 dark:text-gray-500">•</span>
                              <div className="flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                <span>{job.totalCandidates} candidatos</span>
                              </div>
                            </div>
                          </div>
                          {/* Menu Dropdown de Ações Rápidas - Integrado com LIA */}
                          <div className="relative group">
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0" aria-label="Ações da vaga">
                              <MoreVertical className="w-3.5 h-3.5" />
                            </Button>
                            {/* Dropdown Menu */}
                            <div className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                              <div className="py-1">
                                <button
                                  onClick={() => handleLIAAction('kanban', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-950 dark:hover:text-gray-100 transition-colors flex items-center gap-2"
                                >
                                  <Eye className="w-3 h-3" />
                                  Ver Kanban Completo
                                </button>
                                <button
                                  onClick={() => handleLIAAction('report', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-950 dark:hover:text-gray-100 transition-colors flex items-center gap-2"
                                >
                                  <FileText className="w-3 h-3" />
                                  Gerar Relatório
                                </button>
                                <button
                                  onClick={() => handleLIAAction('share', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-950 dark:hover:text-gray-100 transition-colors flex items-center gap-2"
                                >
                                  <Share2 className="w-3 h-3" />
                                  Compartilhar Vaga
                                </button>
                                <button
                                  onClick={() => handleLIAAction('edit', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-950 dark:hover:text-gray-100 transition-colors flex items-center gap-2"
                                >
                                  <Edit className="w-3 h-3" />
                                  Editar Requisitos
                                </button>
                                <button
                                  onClick={() => handleLIAAction('duplicate', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-950 dark:hover:text-gray-100 transition-colors flex items-center gap-2"
                                >
                                  <Copy className="w-3 h-3" />
                                  Duplicar Vaga
                                </button>
                                <div className="border-t border-gray-200 dark:border-gray-700 my-1"></div>
                                <button
                                  onClick={() => handleLIAAction('cancel', job)}
                                  className="w-full px-3 py-2 text-left text-xs hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 hover:text-red-700 dark:hover:text-red-400 transition-colors flex items-center gap-2"
                                >
                                  <Trash2 className="w-3 h-3" />
                                  Cancelar Vaga
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Funil Horizontal Unificado - Ultra Compacto */}
                        <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-1.5 mb-1.5">
                          <div className="flex items-center justify-between gap-1">
                            {/* Novos */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.new}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Novos</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.new, job.stages.uncontacted))}`}>
                                {getConversionRate(job.stages.new, job.stages.uncontacted)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Não Contactados */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.uncontacted}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Triag</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.uncontacted, job.stages.contacted))}`}>
                                {getConversionRate(job.stages.uncontacted, job.stages.contacted)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Contactados */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.contacted}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Cont</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.contacted, job.stages.replied))}`}>
                                {getConversionRate(job.stages.contacted, job.stages.replied)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Respondidos */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.replied}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Resp</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.replied, job.stages.phoneScreen))}`}>
                                {getConversionRate(job.stages.replied, job.stages.phoneScreen)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Telefone */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.phoneScreen}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Tel</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.phoneScreen, job.stages.onsite))}`}>
                                {getConversionRate(job.stages.phoneScreen, job.stages.onsite)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Entrevista */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.onsite}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Entrev</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.onsite, job.stages.makeOffer))}`}>
                                {getConversionRate(job.stages.onsite, job.stages.makeOffer)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Oferta */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.makeOffer}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Ofert</span>
                            </div>
                            <div className="flex flex-col items-center">
                              <span className={`text-xs font-medium ${getConversionColor(getConversionRate(job.stages.makeOffer, job.stages.hired))}`}>
                                {getConversionRate(job.stages.makeOffer, job.stages.hired)}%
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-400">→</span>
                            </div>

                            {/* Contratados */}
                            <div className="flex flex-col items-center">
                              <span className="text-xs font-medium text-gray-950 dark:text-gray-50">{job.stages.hired}</span>
                              <span className="text-xs text-gray-800 dark:text-gray-500 uppercase">Contr</span>
                            </div>
                          </div>
                        </div>

                        {/* Pendências e Alerta em Linha - Ultra Compacto */}
                        <div className="flex items-center gap-1.5">
                          {/* Pendências LIA */}
                          {job.liaPendencies.length > 0 && (
                            <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded px-1.5 py-1 flex-1">
                              <Brain className="w-2.5 h-2.5 text-wedo-cyan flex-shrink-0" />
                              <span className="text-xs text-gray-950 dark:text-gray-200 truncate font-medium">
                                {job.liaPendencies.length} pendência{job.liaPendencies.length > 1 ? 's' : ''}
                              </span>
                            </div>
                          )}

                          {/* Alerta LIA */}
                          <div 
                            className={`flex items-center gap-1 ${getAlertColor(job.alert.type)} rounded-md px-1.5 py-1 flex-1`}
                            style={getAlertStyle(job.alert.type)}
                          >
                            {getAlertIcon(job.alert.type)}
                            <span className="text-xs font-medium truncate flex-1">{job.alert.message}</span>
                            <Button
                              size="sm"
                              className="gap-0.5 h-4 text-xs px-1 hover:scale-105 transition-transform flex-shrink-0"
                              onClick={() => {
                                const actionPrompt = `${job.alert.action} para a vaga ${job.title} (${job.jobId})`
                                if (typeof window !== 'undefined') {
                                  localStorage.setItem('liaPrompt', actionPrompt)
                                }
                                if (onNavigate) {
                                  onNavigate('Chat com LIA')
                                }
                              }}
                            >
                              {job.alert.action}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

        </div>
      </div>
    </div>
    </>
  )
}
