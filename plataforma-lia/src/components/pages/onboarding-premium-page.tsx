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
  BarChart3, Crown, Workflow, Bell, Upload, X,
  Linkedin, Twitter, Instagram, ArrowRight,
  ExternalLink, Copy, Archive, RefreshCw, Timer
} from "lucide-react"

// Candidatos aprovados aguardando onboarding
interface ApprovedCandidate {
  id: string
  name: string
  email: string
  phone: string
  avatar?: string
  position: string
  department: string
  manager: string
  hireDate: string
  startDate: string
  salary: number
  stage: 'welcome' | 'documentation' | 'equipment' | 'systems' | 'medical' | 'integration' | 'completed'
  progress: number
  tasks: OnboardingTask[]
  communications: Communication[]
  documents: Document[]
  medicalExams: MedicalExam[]
  firstDaySchedule?: FirstDaySchedule
}

interface OnboardingTask {
  id: string
  title: string
  description: string
  type: 'communication' | 'document' | 'meeting' | 'system' | 'equipment' | 'medical' | 'custom'
  assignedTo: string
  dueDate: string
  isCompleted: boolean
  completedDate?: string
  automationTrigger?: string
  template?: string
}

interface Communication {
  id: string
  type: 'email' | 'whatsapp' | 'sms' | 'call'
  templateId: string
  sentDate: string
  status: 'sent' | 'delivered' | 'read' | 'replied'
  content: string
}

interface Document {
  id: string
  name: string
  type: string
  isRequired: boolean
  status: 'pending' | 'uploaded' | 'approved' | 'rejected'
  uploadDate?: string
  url?: string
}

interface MedicalExam {
  id: string
  type: string
  provider: string
  scheduledDate?: string
  status: 'pending' | 'scheduled' | 'completed' | 'approved'
  results?: string
}

interface FirstDaySchedule {
  date: string
  activities: {
    time: string
    activity: string
    location: string
    responsible: string
  }[]
}

// Mock data
const approvedCandidates: ApprovedCandidate[] = [
  {
    id: '1',
    name: 'Carlos Santos',
    email: 'carlos.santos@empresa.com',
    phone: '+55 11 99999-1234',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
    position: 'Frontend Developer Sênior',
    department: 'Tecnologia',
    manager: 'Ana Silva',
    hireDate: '2024-01-15',
    startDate: '2024-02-01',
    salary: 13500,
    stage: 'documentation',
    progress: 35,
    tasks: [],
    communications: [],
    documents: [
      { id: '1', name: 'RG', type: 'identification', isRequired: true, status: 'uploaded' },
      { id: '2', name: 'CPF', type: 'identification', isRequired: true, status: 'approved' },
      { id: '3', name: 'Comprovante de Residência', type: 'address', isRequired: true, status: 'pending' }
    ],
    medicalExams: [
      { id: '1', type: 'Admissional', provider: 'Clínica Ocupacional SP', status: 'pending' }
    ]
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
    hireDate: '2024-01-20',
    startDate: '2024-02-05',
    salary: 9500,
    stage: 'welcome',
    progress: 15,
    tasks: [],
    communications: [],
    documents: [],
    medicalExams: []
  },
  {
    id: '3',
    name: 'Ana Pereira',
    email: 'ana.pereira@empresa.com',
    phone: '+55 11 66666-3456',
    position: 'Data Scientist',
    department: 'Dados',
    manager: 'Pedro Santos',
    hireDate: '2024-01-25',
    startDate: '2024-02-10',
    salary: 16000,
    stage: 'systems',
    progress: 70,
    tasks: [],
    communications: [],
    documents: [],
    medicalExams: [
      { id: '1', type: 'Admissional', provider: 'Clínica Ocupacional SP', status: 'completed' }
    ]
  }
]

const kanbanStages = [
  { id: 'welcome', name: 'Boas-vindas', color: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300', description: 'Email de boas-vindas enviado' },
  { id: 'documentation', name: 'Documentação', color: 'bg-status-warning/15 text-status-warning', description: 'Coleta de documentos' },
  { id: 'equipment', name: 'Equipamentos', color: 'bg-wedo-orange/15 text-wedo-orange', description: 'Entrega de equipamentos' },
  { id: 'systems', name: 'Sistemas', color: 'bg-wedo-purple/15 text-wedo-purple', description: 'Criação de acessos' },
  { id: 'medical', name: 'Médico', color: 'bg-wedo-magenta/15 text-wedo-magenta', description: 'Exames ocupacionais' },
  { id: 'integration', name: 'Integração', color: 'bg-wedo-purple/15 text-wedo-purple', description: 'Primeiro dia' },
  { id: 'completed', name: 'Concluído', color: 'bg-status-success/15 text-status-success', description: 'Onboarding finalizado' }
]

const messageTemplates = [
  {
    id: 'welcome_email',
    name: 'Email de Boas-vindas',
    type: 'email',
    subject: 'Bem-vindo(a) à {{company_name}}! 🎉',
    content: `Olá {{candidate_name}},

É com grande prazer que damos as boas-vindas à {{company_name}}!

Estamos muito animados para tê-lo(a) em nossa equipe como {{position}} no departamento de {{department}}.

Sua jornada de onboarding começará em {{start_date}}. Nos próximos dias, você receberá informações importantes sobre:

• Documentação necessária
• Entrega de equipamentos
• Criação de acessos aos sistemas
• Exames médicos ocupacionais
• Agenda do primeiro dia

Seu gestor direto será {{manager_name}}, que entrará em contato em breve.

Estamos aqui para ajudar em qualquer dúvida!

Atenciosamente,
Equipe de RH`
  },
  {
    id: 'whatsapp_welcome',
    name: 'WhatsApp Boas-vindas',
    type: 'whatsapp',
    content: `🎉 Olá {{candidate_name}}!

Bem-vindo(a) à {{company_name}}!

Estamos muito felizes em tê-lo(a) em nossa equipe como {{position}}.

Em breve você receberá por email todas as informações sobre seu processo de onboarding.

Qualquer dúvida, estamos aqui! 😊

Equipe RH {{company_name}}`
  },
  {
    id: 'documentation_request',
    name: 'Solicitação de Documentos',
    type: 'email',
    subject: 'Documentos para Admissão - {{company_name}}',
    content: `Olá {{candidate_name}},

Para darmos continuidade ao seu processo de admissão, precisamos que você envie os seguintes documentos:

📄 DOCUMENTOS OBRIGATÓRIOS:
• RG (frente e verso)
• CPF
• Comprovante de residência (máximo 3 meses)
• Carteira de Trabalho (páginas principais)
• Título de Eleitor
• Certificado de Reservista (se aplicável)
• Diploma/Certificados de escolaridade

🏥 DOCUMENTOS MÉDICOS:
• Carteira de Vacinação atualizada
• Exames pré-admissionais (agendaremos)

📧 Envie os documentos digitalizados para: docs@{{company_name}}.com

⏰ Prazo: {{deadline}}

Em caso de dúvidas, entre em contato conosco.

Atenciosamente,
Equipe RH`
  }
]

export function OnboardingPremiumPage() {
  const [selectedView, setSelectedView] = useState<'kanban' | 'candidates' | 'templates' | 'analytics'>('kanban')
  const [selectedCandidate, setSelectedCandidate] = useState<ApprovedCandidate | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [stageFilter, setStageFilter] = useState('all')

  const handleDragStart = (e: React.DragEvent, candidate: ApprovedCandidate) => {
    e.dataTransfer.setData('candidateId', candidate.id)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, targetStage: string) => {
    e.preventDefault()
    const candidateId = e.dataTransfer.getData('candidateId')
    // Aqui implementaríamos a lógica de mover o candidato
  }

  const getStageColor = (stage: string) => {
    const stageData = kanbanStages.find(s => s.id === stage)
    return stageData?.color || 'bg-gray-100 text-gray-800 dark:text-gray-200'
  }

  const filteredCandidates = approvedCandidates.filter(candidate => {
    const matchesSearch = candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         candidate.position.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStage = stageFilter === 'all' || candidate.stage === stageFilter
    return matchesSearch && matchesStage
  })

  const renderKanbanView = () => (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Novos Colaboradores</p>
                <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">{approvedCandidates.length}</p>
                <p className="text-xs text-gray-800 dark:text-gray-200">em onboarding</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                <UserPlus className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Em Andamento</p>
                <p className="text-2xl font-bold text-status-warning">
                  {approvedCandidates.filter(c => c.stage !== 'completed').length}
                </p>
                <p className="text-xs text-gray-800 dark:text-gray-200">processos ativos</p>
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
                  {approvedCandidates.filter(c => c.stage === 'completed').length}
                </p>
                <p className="text-xs text-gray-800 dark:text-gray-200">este mês</p>
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
                <p className="text-sm font-medium text-gray-600">Tempo Médio</p>
                <p className="text-2xl font-bold text-wedo-purple">12d</p>
                <p className="text-xs text-gray-800 dark:text-gray-200">para conclusão</p>
              </div>
              <div className="w-12 h-12 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <Timer className="w-6 h-6 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

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
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md bg-white text-gray-950 dark:text-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 w-80"
            />
          </div>

          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-950 dark:text-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20"
          >
            <option value="all">Todas as Etapas</option>
            {kanbanStages.map(stage => (
              <option key={stage.id} value={stage.id}>{stage.name}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Exportar
          </Button>
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            Adicionar Colaborador
          </Button>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="overflow-x-auto">
        <div className="flex gap-6 min-w-max pb-6">
          {kanbanStages.map(stage => (
            <div
              key={stage.id}
              className="flex-shrink-0 w-80 bg-white rounded-md border border-gray-200"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, stage.id)}
            >
              {/* Column Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge className={stage.color}>
                      {stage.name}
                    </Badge>
                    <span className="text-sm font-medium text-gray-600">
                      {filteredCandidates.filter(c => c.stage === stage.id).length}
                    </span>
                  </div>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">{stage.description}</p>
              </div>

              {/* Cards */}
              <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                {filteredCandidates
                  .filter(candidate => candidate.stage === stage.id)
                  .map(candidate => (
                    <CandidateKanbanCard
                      key={candidate.id}
                      candidate={candidate}
                      onDragStart={handleDragStart}
                      onClick={() => setSelectedCandidate(candidate)}
                    />
                  ))}

                {/* Empty state */}
                {filteredCandidates.filter(c => c.stage === stage.id).length === 0 && (
                  <div className="text-center py-8 text-gray-800 dark:text-gray-200">
                    <Users className="w-8 h-8 mx-auto mb-2 opacity-50 text-gray-600" />
                    <p className="text-sm">Nenhum colaborador</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderTemplatesView = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50">Templates de Comunicação</h3>
          <p className="text-sm text-gray-600">Personalize mensagens automáticas para cada etapa</p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Novo Template
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {messageTemplates.map(template => (
          <Card key={template.id} className="hover:transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <Badge variant="outline" className="mt-1">
                    {template.type === 'email' ? '📧 Email' :
                     template.type === 'whatsapp' ? '📱 WhatsApp' :
                     template.type === 'sms' ? '💬 SMS' : '📞 Ligação'}
                  </Badge>
                </div>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {template.subject && (
                  <div>
                    <p className="text-sm font-medium text-gray-600">Assunto:</p>
                    <p className="text-sm text-gray-950 dark:text-gray-50">{template.subject}</p>
                  </div>
                )}

                <div>
                  <p className="text-sm font-medium text-gray-600">Conteúdo:</p>
                  <p className="text-sm text-gray-800 dark:text-gray-200 line-clamp-4">
                    {template.content}
                  </p>
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
                  <Button size="sm" variant="outline" className="gap-2">
                    <Copy className="w-4 h-4" />
                    Duplicar
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
              <h1 className="text-sm font-semibold font-sans text-gray-950 dark:text-gray-50 mb-1 flex items-center gap-1.5">
                <Crown className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                Onboarding Automatizado Premium
              </h1>
              <p className="text-gray-600">
                Sistema completo de integração de novos colaboradores aprovados
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <Settings className="w-4 h-4" />
                Configurações
              </Button>
              <Button variant="outline" className="gap-2">
                <BarChart3 className="w-4 h-4" />
                Relatórios
              </Button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
            {[
              { id: 'kanban', label: 'Kanban', icon: Workflow },
              { id: 'candidates', label: 'Colaboradores', icon: Users },
              { id: 'templates', label: 'Templates', icon: MessageSquare },
              { id: 'analytics', label: 'Analytics', icon: BarChart3 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedView === tab.id
                    ? 'bg-white text-gray-950 dark:text-gray-50'
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
        {selectedView === 'kanban' && renderKanbanView()}
        {selectedView === 'templates' && renderTemplatesView()}
        {selectedView === 'candidates' && (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50 mb-2">Lista de Colaboradores</h3>
            <p className="text-gray-600">Visão detalhada em desenvolvimento</p>
          </div>
        )}
        {selectedView === 'analytics' && (
          <div className="text-center py-12">
            <BarChart3 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50 mb-2">Analytics de Onboarding</h3>
            <p className="text-gray-600">Métricas detalhadas em desenvolvimento</p>
          </div>
        )}

        {/* Candidate Detail Modal */}
        {selectedCandidate && (
          <CandidateOnboardingModal
            candidate={selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
          />
        )}
      </div>
    </div>
  )
}

// Card do Kanban
interface CandidateKanbanCardProps {
  candidate: ApprovedCandidate
  onDragStart: (e: React.DragEvent, candidate: ApprovedCandidate) => void
  onClick: () => void
}

function CandidateKanbanCard({ candidate, onDragStart, onClick }: CandidateKanbanCardProps) {
  const daysUntilStart = Math.ceil((new Date(candidate.startDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))

  return (
    <Card
      className="cursor-move hover:transition-all duration-200 border-l-4 border-l-gray-400 dark:border-l-gray-500"
      draggable
      onDragStart={(e) => onDragStart(e, candidate)}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <Avatar className="w-10 h-10">
            <AvatarImage src={candidate.avatar} alt={candidate.name} />
            <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-sm text-gray-950 dark:text-gray-50 truncate">
              {candidate.name}
            </h4>
            <p className="text-xs text-gray-600">{candidate.position}</p>
            <p className="text-xs text-gray-800 dark:text-gray-200">{candidate.department}</p>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Progresso:</span>
            <span className="font-medium">{candidate.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full"
              style={{width: `${candidate.progress}%`}}
            />
          </div>
        </div>

        <div className="mt-3 space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Início:</span>
            <span className="font-medium">{new Date(candidate.startDate).toLocaleDateString('pt-BR')}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Gestor:</span>
            <span className="font-medium">{candidate.manager}</span>
          </div>
          {daysUntilStart > 0 && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-600">Faltam:</span>
              <Badge variant="outline" className="text-xs">
                {daysUntilStart} dias
              </Badge>
            </div>
          )}
        </div>

        {/* Indicators */}
        <div className="flex gap-1 mt-3">
          {candidate.documents.length > 0 && (
            <div className="w-2 h-2 bg-status-warning rounded-full" title="Documentos pendentes" />
          )}
          {candidate.medicalExams.length > 0 && (
            <div className="w-2 h-2 bg-wedo-magenta rounded-full" title="Exames médicos" />
          )}
          {candidate.communications.length > 0 && (
            <div className="w-2 h-2 bg-status-success rounded-full" title="Comunicações enviadas" />
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Modal de detalhes do candidato em onboarding
interface CandidateOnboardingModalProps {
  candidate: ApprovedCandidate
  onClose: () => void
}

function CandidateOnboardingModal({ candidate, onClose }: CandidateOnboardingModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'communications' | 'schedule'>('overview')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-md w-full max-w-5xl h-[90vh] flex flex-col">
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
              <div className="flex items-center gap-2 mt-1">
                <Badge className={kanbanStages.find(s => s.id === candidate.stage)?.color}>
                  {kanbanStages.find(s => s.id === candidate.stage)?.name}
                </Badge>
                <Badge variant="outline">
                  {candidate.progress}% concluído
                </Badge>
              </div>
            </div>
          </div>
          <Button variant="ghost" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Tabs */}
        <div className="flex border-b px-6">
          {[
            { id: 'overview', label: 'Visão Geral', icon: Eye },
            { id: 'documents', label: 'Documentos', icon: FileText },
            { id: 'communications', label: 'Comunicações', icon: MessageSquare },
            { id: 'schedule', label: 'Agenda', icon: Calendar }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "text-gray-600 dark:text-gray-400 border-b-2 border-gray-900 dark:border-gray-50"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Informações do Colaborador</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Email</p>
                        <p className="text-sm">{candidate.email}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Telefone</p>
                        <p className="text-sm">{candidate.phone}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Gestor</p>
                        <p className="text-sm">{candidate.manager}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Salário</p>
                        <p className="text-sm">R$ {candidate.salary.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Data de Contratação</p>
                        <p className="text-sm">{new Date(candidate.hireDate).toLocaleDateString('pt-BR')}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Início</p>
                        <p className="text-sm">{new Date(candidate.startDate).toLocaleDateString('pt-BR')}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Progresso do Onboarding</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
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

                      <div className="space-y-2">
                        {kanbanStages.map(stage => (
                          <div key={stage.id} className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">{stage.name}</span>
                            <CheckCircle
                              className={`w-4 h-4 ${
                                kanbanStages.findIndex(s => s.id === candidate.stage) >= kanbanStages.findIndex(s => s.id === stage.id)
                                  ? 'text-status-success'
                                  : 'text-gray-600'
                              }`}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Ações Rápidas</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Button className="w-full gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Enviar WhatsApp
                    </Button>
                    <Button variant="outline" className="w-full gap-2">
                      <Mail className="w-4 h-4" />
                      Enviar Email
                    </Button>
                    <Button variant="outline" className="w-full gap-2">
                      <Calendar className="w-4 h-4" />
                      Agendar Exame
                    </Button>
                    <Button variant="outline" className="w-full gap-2">
                      <Phone className="w-4 h-4" />
                      Ligar
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Próximas Tarefas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-3 p-2 bg-status-warning/10 rounded-md">
                        <Clock className="w-4 h-4 text-status-warning" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">Solicitar comprovante de residência</p>
                          <p className="text-xs text-gray-600">Vence hoje</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                        <Calendar className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">Agendar exame admissional</p>
                          <p className="text-xs text-gray-600">Vence em 2 dias</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-4">
              <h3 className="text-xs font-medium">Documentos</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {candidate.documents.map(doc => (
                  <Card key={doc.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{doc.name}</h4>
                        <Badge variant={
                          doc.status === 'approved' ? 'default' :
                          doc.status === 'uploaded' ? 'secondary' :
                          doc.status === 'rejected' ? 'destructive' : 'outline'
                        }>
                          {doc.status === 'approved' ? 'Aprovado' :
                           doc.status === 'uploaded' ? 'Enviado' :
                           doc.status === 'rejected' ? 'Rejeitado' : 'Pendente'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{doc.type}</p>
                      {doc.isRequired && (
                        <Badge variant="outline" className="text-xs">Obrigatório</Badge>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'communications' && (
            <div className="space-y-4">
              <h3 className="text-xs font-medium">Histórico de Comunicações</h3>
              <div className="text-center py-8 text-gray-800 dark:text-gray-200">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50 text-gray-600" />
                <p className="text-sm">Nenhuma comunicação enviada ainda</p>
              </div>
            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="space-y-4">
              <h3 className="text-xs font-medium">Agenda de Onboarding</h3>
              <div className="text-center py-8 text-gray-800 dark:text-gray-200">
                <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50 text-gray-600" />
                <p className="text-sm">Agenda será configurada automaticamente</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
