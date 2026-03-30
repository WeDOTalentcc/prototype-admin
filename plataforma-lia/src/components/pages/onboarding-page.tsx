"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Plus, Users, Calendar, CheckCircle, Clock, AlertTriangle,
  Send, FileText, Mail, Phone, MapPin, Building, User,
  Play, Pause, Edit, Eye, MoreHorizontal, Target, TrendingUp,
  Briefcase, GraduationCap, Award, Heart, MessageSquare,
  Settings, Filter, Search, Download, Share2, Zap,
  UserPlus, CalendarDays, ClipboardList, BookOpen, Video,
  BarChart3
} from "lucide-react"

interface OnboardingCandidate {
  id: string
  name: string
  email: string
  phone: string
  avatar?: string
  position: string
  department: string
  manager: string
  startDate: string
  status: 'pending' | 'in_progress' | 'completed' | 'delayed'
  progress: number
  currentStep: string
  completedTasks: number
  totalTasks: number
  lastActivity: string
  hireDate: string
}

interface OnboardingTemplate {
  id: string
  name: string
  description: string
  department: string
  duration: number // dias
  tasks: OnboardingTask[]
  isActive: boolean
}

interface OnboardingTask {
  id: string
  title: string
  description: string
  type: 'document' | 'meeting' | 'training' | 'system_access' | 'equipment' | 'custom'
  assignedTo: 'candidate' | 'hr' | 'manager' | 'it' | 'admin'
  dueDate: number // dias após início
  priority: 'low' | 'medium' | 'high' | 'critical'
  estimatedTime: number // minutos
  dependencies?: string[]
  isCompleted: boolean
  completedDate?: string
  automationTrigger?: 'immediate' | 'previous_task' | 'specific_date'
}

// Mock data
const onboardingCandidates: OnboardingCandidate[] = [
  {
    id: '1',
    name: 'Carlos Santos',
    email: 'carlos.santos@empresa.com',
    phone: '+55 11 99999-1234',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    position: 'Frontend Developer Sênior',
    department: 'Tecnologia',
    manager: 'Ana Silva',
    startDate: '2024-02-01',
    status: 'in_progress',
    progress: 65,
    currentStep: 'Configuração de Sistemas',
    completedTasks: 13,
    totalTasks: 20,
    lastActivity: 'Há 2 horas',
    hireDate: '2024-01-15'
  },
  {
    id: '2',
    name: 'Maria Oliveira',
    email: 'maria.oliveira@empresa.com',
    phone: '+55 11 88888-5678',
    avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b95c?w=150&h=150&fit=crop&crop=face',
    position: 'UX Designer',
    department: 'Design',
    manager: 'João Costa',
    startDate: '2024-02-05',
    status: 'pending',
    progress: 0,
    currentStep: 'Aguardando Início',
    completedTasks: 0,
    totalTasks: 18,
    lastActivity: 'Pendente',
    hireDate: '2024-01-20'
  },
  {
    id: '3',
    name: 'Lucas Mendes',
    email: 'lucas.mendes@empresa.com',
    phone: '+55 21 77777-9012',
    position: 'Product Manager',
    department: 'Produto',
    manager: 'Rafael Lima',
    startDate: '2024-01-20',
    status: 'completed',
    progress: 100,
    currentStep: 'Onboarding Concluído',
    completedTasks: 22,
    totalTasks: 22,
    lastActivity: 'Há 3 dias',
    hireDate: '2024-01-05'
  },
  {
    id: '4',
    name: 'Ana Pereira',
    email: 'ana.pereira@empresa.com',
    phone: '+55 11 66666-3456',
    position: 'Data Scientist',
    department: 'Dados',
    manager: 'Pedro Santos',
    startDate: '2024-02-10',
    status: 'delayed',
    progress: 35,
    currentStep: 'Documentação Pendente',
    completedTasks: 7,
    totalTasks: 20,
    lastActivity: 'Há 5 dias',
    hireDate: '2024-01-25'
  }
]

const onboardingTemplates: OnboardingTemplate[] = [
  {
    id: 'tech-template',
    name: 'Onboarding Tecnologia',
    description: 'Template para desenvolvedores e profissionais de TI',
    department: 'Tecnologia',
    duration: 14,
    isActive: true,
    tasks: [
      {
        id: 'welcome',
        title: 'Email de Boas-Vindas',
        description: 'Envio automático de email de boas-vindas com informações iniciais',
        type: 'document',
        assignedTo: 'hr',
        dueDate: 0,
        priority: 'high',
        estimatedTime: 5,
        isCompleted: true,
        automationTrigger: 'immediate'
      },
      {
        id: 'docs',
        title: 'Documentação Admissional',
        description: 'Envio e coleta de documentos necessários para admissão',
        type: 'document',
        assignedTo: 'candidate',
        dueDate: 2,
        priority: 'critical',
        estimatedTime: 60,
        isCompleted: false,
        automationTrigger: 'previous_task'
      },
      {
        id: 'equipment',
        title: 'Entrega de Equipamentos',
        description: 'Notebook, monitor, mouse, teclado e acessórios',
        type: 'equipment',
        assignedTo: 'it',
        dueDate: 1,
        priority: 'high',
        estimatedTime: 30,
        isCompleted: false,
        dependencies: ['docs']
      },
      {
        id: 'system_access',
        title: 'Criação de Acessos',
        description: 'Emails, sistemas internos, repositórios, ferramentas de desenvolvimento',
        type: 'system_access',
        assignedTo: 'it',
        dueDate: 1,
        priority: 'critical',
        estimatedTime: 45,
        isCompleted: false
      },
      {
        id: 'welcome_meeting',
        title: 'Reunião de Boas-Vindas',
        description: 'Apresentação da empresa, cultura e time',
        type: 'meeting',
        assignedTo: 'manager',
        dueDate: 1,
        priority: 'high',
        estimatedTime: 90,
        isCompleted: false
      }
    ]
  }
]

export function OnboardingPage() {
  const [selectedView, setSelectedView] = useState<'overview' | 'candidates' | 'templates' | 'analytics'>('overview')
  const [selectedCandidate, setSelectedCandidate] = useState<OnboardingCandidate | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const filteredCandidates = onboardingCandidates.filter(candidate => {
    const matchesSearch = candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         candidate.position.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || candidate.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-status-warning/15 text-status-warning border-status-warning/30',
      in_progress: 'bg-gray-100 dark:bg-lia-bg-secondary text-gray-700 dark:text-lia-text-secondary border-lia-border-default dark:border-lia-border-default',
      completed: 'bg-status-success/15 text-status-success border-status-success/30',
      delayed: 'bg-status-error/15 text-status-error border-status-error/30'
    }
    return colors[status as keyof typeof colors] || colors.pending
  }

  const getStatusLabel = (status: string) => {
    const labels = {
      pending: 'Pendente',
      in_progress: 'Em Andamento',
      completed: 'Concluído',
      delayed: 'Atrasado'
    }
    return labels[status as keyof typeof labels] || status
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total de Novos Colaboradores</p>
                <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">{onboardingCandidates.length}</p>
                <p className="text-xs text-gray-800 dark:text-lia-text-primary">este mês</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 dark:bg-lia-bg-secondary rounded-md flex items-center justify-center">
                <UserPlus className="w-6 h-6 text-gray-600 dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Em Andamento</p>
                <p className="text-2xl font-bold text-gray-700 dark:text-lia-text-secondary">
                  {onboardingCandidates.filter(c => c.status === 'in_progress').length}
                </p>
                <p className="text-xs text-gray-800 dark:text-lia-text-primary">processos ativos</p>
              </div>
              <div className="w-12 h-12 bg-status-warning/15 rounded-md flex items-center justify-center">
                <Clock className="w-6 h-6 text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Concluídos</p>
                <p className="text-2xl font-bold text-status-success">
                  {onboardingCandidates.filter(c => c.status === 'completed').length}
                </p>
                <p className="text-xs text-gray-800 dark:text-lia-text-primary">com sucesso</p>
              </div>
              <div className="w-12 h-12 bg-status-success/15 rounded-md flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Taxa de Sucesso</p>
                <p className="text-2xl font-bold text-wedo-purple">92%</p>
                <p className="text-xs text-gray-800 dark:text-lia-text-primary">últimos 3 meses</p>
              </div>
              <div className="w-12 h-12 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Onboarding Processes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xs">Processos Ativos de Onboarding</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {onboardingCandidates.filter(c => c.status === 'in_progress' || c.status === 'delayed').map(candidate => (
              <div key={candidate.id} className="p-4 border border-lia-border-subtle rounded-md hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={candidate.avatar} alt={candidate.name} />
                      <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                    </Avatar>

                    <div>
                      <h4 className="font-medium text-gray-950 dark:text-gray-50">{candidate.name}</h4>
                      <p className="text-sm text-gray-600">{candidate.position} • {candidate.department}</p>
                      <p className="text-sm text-gray-800 dark:text-lia-text-primary">Início: {new Date(candidate.startDate).toLocaleDateString('pt-BR')}</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <Badge className={getStatusColor(candidate.status)}>
                      {getStatusLabel(candidate.status)}
                    </Badge>
                    <p className="text-sm text-gray-800 dark:text-lia-text-primary mt-1">{candidate.currentStep}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full"
                          style={{width: `${candidate.progress}%`}}
                        />
                      </div>
                      <span className="text-sm font-medium">{candidate.progress}%</span>
                    </div>
                    <p className="text-xs text-gray-800 dark:text-lia-text-primary mt-1">
                      {candidate.completedTasks}/{candidate.totalTasks} tarefas
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Tasks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xs">Próximas Tarefas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { task: 'Configurar email corporativo', candidate: 'Carlos Santos', dueDate: 'Hoje', priority: 'high' },
              { task: 'Reunião de apresentação', candidate: 'Maria Oliveira', dueDate: 'Amanhã', priority: 'medium' },
              { task: 'Treinamento de segurança', candidate: 'Carlos Santos', dueDate: '2 dias', priority: 'medium' },
              { task: 'Entrega de equipamentos', candidate: 'Ana Pereira', dueDate: '3 dias', priority: 'high' }
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    item.priority === 'high' ? 'bg-status-error' :
                    item.priority === 'medium' ? 'bg-status-warning' : 'bg-status-success'
                  }`} />
                  <div>
                    <p className="font-medium text-gray-950 dark:text-gray-50">{item.task}</p>
                    <p className="text-sm text-gray-600">{item.candidate}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-950 dark:text-gray-50">{item.dueDate}</p>
                  <Badge variant="outline" className="text-xs">
                    {item.priority === 'high' ? 'Alta' : item.priority === 'medium' ? 'Média' : 'Baixa'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderCandidates = () => (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar colaboradores..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-lia-border-default rounded-md bg-lia-bg-primary text-gray-950 dark:text-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 w-80"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-lia-border-default rounded-md bg-lia-bg-primary text-gray-950 dark:text-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
          >
            <option value="all">Todos os Status</option>
            <option value="pending">Pendente</option>
            <option value="in_progress">Em Andamento</option>
            <option value="completed">Concluído</option>
            <option value="delayed">Atrasado</option>
          </select>
        </div>

        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Onboarding
        </Button>
      </div>

      {/* Candidates Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredCandidates.map(candidate => (
          <Card key={candidate.id} className="hover:transition-shadow cursor-pointer">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Avatar className="w-12 h-12">
                    <AvatarImage src={candidate.avatar} alt={candidate.name} />
                    <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                  </Avatar>
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">{candidate.name}</h4>
                    <p className="text-sm text-gray-600">{candidate.position}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-800 dark:text-lia-text-primary">Status:</span>
                  <Badge className={getStatusColor(candidate.status)}>
                    {getStatusLabel(candidate.status)}
                  </Badge>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-800 dark:text-lia-text-primary">Departamento:</span>
                  <span className="font-medium">{candidate.department}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-800 dark:text-lia-text-primary">Gestor:</span>
                  <span className="font-medium">{candidate.manager}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-800 dark:text-lia-text-primary">Início:</span>
                  <span className="font-medium">{new Date(candidate.startDate).toLocaleDateString('pt-BR')}</span>
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-800 dark:text-lia-text-primary">Progresso:</span>
                    <span className="font-medium">{candidate.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        candidate.status === 'completed' ? 'bg-status-success' :
                        candidate.status === 'delayed' ? 'bg-status-error' : 'bg-gray-700 dark:bg-gray-300'
                      }`}
                      style={{width: `${candidate.progress}%`}}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-800 dark:text-lia-text-primary">Tarefas:</span>
                  <span className="font-medium">{candidate.completedTasks}/{candidate.totalTasks}</span>
                </div>

                <div className="text-sm text-gray-800 dark:text-lia-text-primary">
                  Última atividade: {candidate.lastActivity}
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1 gap-2"
                  onClick={() => setSelectedCandidate(candidate)}
                >
                  <Eye className="w-4 h-4" />
                  Ver Detalhes
                </Button>
                <Button size="sm" variant="outline" className="gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Contato
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  const renderTemplates = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50">Templates de Onboarding</h3>
          <p className="text-sm text-gray-600">Configure fluxos automatizados por departamento</p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Template
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {onboardingTemplates.map(template => (
          <Card key={template.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xs">{template.name}</CardTitle>
                  <p className="text-sm text-gray-800 dark:text-lia-text-primary mt-1">{template.description}</p>
                </div>
                <Badge variant={template.isActive ? "default" : "secondary"}>
                  {template.isActive ? 'Ativo' : 'Inativo'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Departamento</p>
                    <p className="text-sm text-gray-950 dark:text-gray-50">{template.department}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Duração</p>
                    <p className="text-sm text-gray-950 dark:text-gray-50">{template.duration} dias</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Tarefas ({template.tasks.length})</p>
                  <div className="space-y-2">
                    {template.tasks.slice(0, 3).map(task => (
                      <div key={task.id} className="flex items-center gap-2 text-sm">
                        <CheckCircle className={`w-4 h-4 ${task.isCompleted ? 'text-status-success' : 'text-gray-600'}`} />
                        <span className="text-gray-950 dark:text-gray-50">{task.title}</span>
                        <Badge variant="outline" className="text-xs">
                          {task.type === 'document' ? 'Doc' :
                           task.type === 'meeting' ? 'Reunião' :
                           task.type === 'training' ? 'Treinamento' :
                           task.type === 'system_access' ? 'Sistema' :
                           task.type === 'equipment' ? 'Equipamento' : 'Outro'}
                        </Badge>
                      </div>
                    ))}
                    {template.tasks.length > 3 && (
                      <p className="text-xs text-gray-800 dark:text-lia-text-primary">+{template.tasks.length - 3} tarefas adicionais</p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1 gap-2">
                    <Edit className="w-4 h-4" />
                    Editar
                  </Button>
                  <Button size="sm" variant="outline" className="gap-2">
                    <Eye className="w-4 h-4" />
                    Visualizar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-sm font-semibold font-sans text-gray-950 dark:text-gray-50 mb-1">
                Onboarding Automatizado
              </h1>
              <p className="text-gray-600">
                Gerencie e automatize o processo de integração de novos colaboradores
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <Download className="w-4 h-4" />
                Exportar
              </Button>
              <Button variant="outline" className="gap-2">
                <Settings className="w-4 h-4" />
                Configurações
              </Button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
            {[
              { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
              { id: 'candidates', label: 'Colaboradores', icon: Users },
              { id: 'templates', label: 'Templates', icon: ClipboardList },
              { id: 'analytics', label: 'Analytics', icon: TrendingUp }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedView === tab.id
                    ? 'bg-lia-bg-primary text-gray-950 dark:text-gray-50'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {selectedView === 'overview' && renderOverview()}
        {selectedView === 'candidates' && renderCandidates()}
        {selectedView === 'templates' && renderTemplates()}
        {selectedView === 'analytics' && (
          <div className="text-center py-12">
            <TrendingUp className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50 mb-2">Analytics em Desenvolvimento</h3>
            <p className="text-gray-600">Métricas avançadas de onboarding em breve</p>
          </div>
        )}

        {/* Candidate Detail Modal */}
        {selectedCandidate && (
          <CandidateDetailModal
            candidate={selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
          />
        )}
      </div>
    </div>
  )
}

// Modal de detalhes do candidato
interface CandidateDetailModalProps {
  candidate: OnboardingCandidate
  onClose: () => void
}

function CandidateDetailModal({ candidate, onClose }: CandidateDetailModalProps) {
  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-status-warning/15 text-status-warning border-status-warning/30',
      in_progress: 'bg-gray-100 dark:bg-lia-bg-secondary text-gray-700 dark:text-lia-text-secondary border-lia-border-default dark:border-lia-border-default',
      completed: 'bg-status-success/15 text-status-success border-status-success/30',
      delayed: 'bg-status-error/15 text-status-error border-status-error/30'
    }
    return colors[status as keyof typeof colors] || colors.pending
  }

  const getStatusLabel = (status: string) => {
    const labels = {
      pending: 'Pendente',
      in_progress: 'Em Andamento',
      completed: 'Concluído',
      delayed: 'Atrasado'
    }
    return labels[status as keyof typeof labels] || status
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-md w-full max-w-4xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarImage src={candidate.avatar} alt={candidate.name} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50">{candidate.name}</h2>
              <p className="text-gray-600">{candidate.position} • {candidate.department}</p>
              <Badge className={`mt-1 ${getStatusColor(candidate.status)}`}>
                {getStatusLabel(candidate.status)}
              </Badge>
            </div>
          </div>
          <Button variant="ghost" onClick={onClose}>
            ×
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Info */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Informações Pessoais</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">{candidate.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">{candidate.phone}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">Gestor: {candidate.manager}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-600" />
                    <span className="text-sm">Início: {new Date(candidate.startDate).toLocaleDateString('pt-BR')}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Progresso</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Progresso Geral</span>
                      <span className="text-sm font-medium">{candidate.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-gray-700 dark:bg-gray-300 h-3 rounded-full"
                        style={{width: `${candidate.progress}%`}}
                      />
                    </div>
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{candidate.completedTasks} de {candidate.totalTasks} tarefas</span>
                      <span>{candidate.lastActivity}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tasks */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Tarefas de Onboarding</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {onboardingTemplates[0].tasks.map((task, index) => (
                      <div key={task.id} className="flex items-start gap-3 p-3 border border-lia-border-subtle rounded-md">
                        <CheckCircle className={`w-5 h-5 mt-0.5 ${task.isCompleted ? 'text-status-success' : 'text-gray-600'}`} />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-medium text-gray-950 dark:text-gray-50">{task.title}</h4>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                {task.assignedTo === 'candidate' ? 'Colaborador' :
                                 task.assignedTo === 'hr' ? 'RH' :
                                 task.assignedTo === 'manager' ? 'Gestor' :
                                 task.assignedTo === 'it' ? 'TI' : 'Admin'}
                              </Badge>
                              <Badge variant={task.priority === 'critical' ? 'destructive' : 'outline'} className="text-xs">
                                {task.priority === 'critical' ? 'Crítica' :
                                 task.priority === 'high' ? 'Alta' :
                                 task.priority === 'medium' ? 'Média' : 'Baixa'}
                              </Badge>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-lia-text-primary">
                            <span>Prazo: Dia {task.dueDate}</span>
                            <span>Tempo estimado: {task.estimatedTime}min</span>
                            {task.completedDate && (
                              <span className="text-status-success">
                                Concluído em {new Date(task.completedDate).toLocaleDateString('pt-BR')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
