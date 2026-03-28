"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Play, Pause, Plus, Settings, Save, Eye, Edit, Trash2,
  Zap, GitBranch, Clock, Filter, MessageSquare, Mail,
  Smartphone, User, Calendar, CheckCircle, AlertTriangle,
  ArrowRight, ArrowDown, MoreHorizontal, Search, Download,
  Upload, RefreshCw, Target, Workflow, Brain, Code,
  Database, Cpu, Network, Share2, FileText, BarChart3
} from "lucide-react"

interface WorkflowNode {
  id: string
  type: 'trigger' | 'condition' | 'action' | 'delay'
  title: string
  description: string
  config: any
  position: { x: number; y: number }
  inputs: string[]
  outputs: string[]
}

interface WorkflowEdge {
  id: string
  source: string
  target: string
  condition?: string
}

interface Workflow {
  id: string
  name: string
  description: string
  trigger: string
  status: 'active' | 'inactive' | 'draft'
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  executions: number
  successRate: number
  lastExecution?: string
  createdAt: string
  category: string
}

interface AutomationTemplate {
  id: string
  name: string
  description: string
  category: string
  workflow: Workflow
  usageCount: number
  rating: number
}

// Mock data
const workflows: Workflow[] = [
  {
    id: '1',
    name: 'Onboarding Automático',
    description: 'Processo completo de integração de novos colaboradores',
    trigger: 'candidate_approved',
    status: 'active',
    executions: 45,
    successRate: 94,
    lastExecution: '2024-01-20T14:30:00Z',
    createdAt: '2024-01-01T00:00:00Z',
    category: 'Onboarding',
    nodes: [
      {
        id: 'trigger_1',
        type: 'trigger',
        title: 'Candidato Aprovado',
        description: 'Dispara quando um candidato é aprovado',
        config: { event: 'candidate_approved' },
        position: { x: 100, y: 100 },
        inputs: [],
        outputs: ['condition_1']
      },
      {
        id: 'condition_1',
        type: 'condition',
        title: 'Verificar Departamento',
        description: 'Verifica se é departamento de TI',
        config: { field: 'department', operator: 'equals', value: 'TI' },
        position: { x: 300, y: 100 },
        inputs: ['trigger_1'],
        outputs: ['action_1', 'action_2']
      },
      {
        id: 'action_1',
        type: 'action',
        title: 'Enviar Welcome Kit TI',
        description: 'Envia kit específico para colaboradores de TI',
        config: { template: 'welcome_kit_ti', channel: 'email' },
        position: { x: 500, y: 50 },
        inputs: ['condition_1'],
        outputs: []
      },
      {
        id: 'action_2',
        type: 'action',
        title: 'Enviar Welcome Kit Geral',
        description: 'Envia kit padrão para outros departamentos',
        config: { template: 'welcome_kit_general', channel: 'email' },
        position: { x: 500, y: 150 },
        inputs: ['condition_1'],
        outputs: []
      }
    ],
    edges: [
      { id: 'e1', source: 'trigger_1', target: 'condition_1' },
      { id: 'e2', source: 'condition_1', target: 'action_1', condition: 'true' },
      { id: 'e3', source: 'condition_1', target: 'action_2', condition: 'false' }
    ]
  },
  {
    id: '2',
    name: 'Lembretes de Entrevista',
    description: 'Envia lembretes automáticos antes das entrevistas',
    trigger: 'interview_scheduled',
    status: 'active',
    executions: 128,
    successRate: 98,
    lastExecution: '2024-01-20T10:00:00Z',
    createdAt: '2024-01-05T00:00:00Z',
    category: 'Entrevistas',
    nodes: [],
    edges: []
  },
  {
    id: '3',
    name: 'Follow-up Candidatos',
    description: 'Acompanhamento automático após processo seletivo',
    trigger: 'process_completed',
    status: 'draft',
    executions: 0,
    successRate: 0,
    createdAt: '2024-01-15T00:00:00Z',
    category: 'Follow-up',
    nodes: [],
    edges: []
  }
]

const automationTemplates: AutomationTemplate[] = [
  {
    id: 'template_1',
    name: 'Processo de Aprovação',
    description: 'Workflow completo desde a aprovação até o primeiro dia',
    category: 'Onboarding',
    usageCount: 23,
    rating: 4.8,
    workflow: workflows[0]
  },
  {
    id: 'template_2',
    name: 'Coleta de Feedback',
    description: 'Automatiza coleta de feedback pós-entrevista',
    category: 'Feedback',
    usageCount: 15,
    rating: 4.6,
    workflow: workflows[1]
  },
  {
    id: 'template_3',
    name: 'Agendamento Inteligente',
    description: 'Automatiza agendamento baseado em disponibilidade',
    category: 'Entrevistas',
    usageCount: 31,
    rating: 4.9,
    workflow: workflows[1]
  }
]

const nodeTypes = [
  {
    type: 'trigger',
    title: 'Triggers',
    icon: Zap,
    color: 'bg-green-50 border-green-200 text-green-700',
    items: [
      { id: 'candidate_approved', name: 'Candidato Aprovado', description: 'Quando um candidato é aprovado' },
      { id: 'interview_scheduled', name: 'Entrevista Agendada', description: 'Quando uma entrevista é marcada' },
      { id: 'document_uploaded', name: 'Documento Enviado', description: 'Quando candidato envia documento' },
      { id: 'feedback_received', name: 'Feedback Recebido', description: 'Quando gestor envia feedback' }
    ]
  },
  {
    type: 'condition',
    title: 'Condições',
    icon: GitBranch,
    color: 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400',
    items: [
      { id: 'department_check', name: 'Verificar Departamento', description: 'Condição baseada no departamento' },
      { id: 'score_check', name: 'Verificar Score', description: 'Condição baseada no score LIA' },
      { id: 'time_check', name: 'Verificar Horário', description: 'Condição baseada no horário' },
      { id: 'custom_field', name: 'Campo Personalizado', description: 'Condição em campo customizado' }
    ]
  },
  {
    type: 'action',
    title: 'Ações',
    icon: Target,
    color: 'bg-purple-50 border-purple-200 text-purple-700',
    items: [
      { id: 'send_email', name: 'Enviar Email', description: 'Envia email personalizado' },
      { id: 'send_whatsapp', name: 'Enviar WhatsApp', description: 'Envia mensagem WhatsApp' },
      { id: 'send_sms', name: 'Enviar SMS', description: 'Envia SMS' },
      { id: 'update_status', name: 'Atualizar Status', description: 'Atualiza status do candidato' },
      { id: 'create_task', name: 'Criar Tarefa', description: 'Cria tarefa para equipe' },
      { id: 'schedule_meeting', name: 'Agendar Reunião', description: 'Agenda reunião automaticamente' }
    ]
  },
  {
    type: 'delay',
    title: 'Espera',
    icon: Clock,
    color: 'bg-orange-50 border-orange-200 text-orange-700',
    items: [
      { id: 'delay_minutes', name: 'Aguardar Minutos', description: 'Espera X minutos' },
      { id: 'delay_hours', name: 'Aguardar Horas', description: 'Espera X horas' },
      { id: 'delay_days', name: 'Aguardar Dias', description: 'Espera X dias' },
      { id: 'delay_until', name: 'Aguardar Até', description: 'Espera até data específica' }
    ]
  }
]

export function WorkflowAutomationPage() {
  const [selectedView, setSelectedView] = useState<'overview' | 'builder' | 'templates' | 'analytics'>('overview')
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null)
  const [showBuilder, setShowBuilder] = useState(false)

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Workflows Ativos</p>
                <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">{workflows.filter(w => w.status === 'active').length}</p>
                <p className="text-xs text-green-600">+2 esta semana</p>
              </div>
              <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                <Workflow className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Execuções Hoje</p>
                <p className="text-2xl font-bold text-green-900">847</p>
                <p className="text-xs text-green-600">+12% vs ontem</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-md flex items-center justify-center">
                <Play className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Taxa de Sucesso</p>
                <p className="text-2xl font-bold text-purple-900">94.2%</p>
                <p className="text-xs text-purple-600">+0.8% vs semana</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-md flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tempo Médio</p>
                <p className="text-2xl font-bold text-orange-900">2.3s</p>
                <p className="text-xs text-orange-600">-0.2s vs semana</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-md flex items-center justify-center">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Workflows List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs">Workflows</CardTitle>
            <Button
              onClick={() => setShowBuilder(true)}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              Novo Workflow
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows.map(workflow => (
              <div key={workflow.id} className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-md flex items-center justify-center ${
                      workflow.status === 'active' ? 'bg-green-100' :
                      workflow.status === 'inactive' ? 'bg-gray-100' : 'bg-yellow-100'
                    }`}>
                      <Workflow className={`w-6 h-6 ${
                        workflow.status === 'active' ? 'text-green-600' :
                        workflow.status === 'inactive' ? 'text-gray-600' : 'text-yellow-600'
                      }`} />
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-950 dark:text-gray-50">{workflow.name}</h4>
                      <p className="text-sm text-gray-600">{workflow.description}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">{workflow.category}</Badge>
                        <Badge variant={
                          workflow.status === 'active' ? 'default' :
                          workflow.status === 'inactive' ? 'secondary' : 'outline'
                        } className="text-xs">
                          {workflow.status === 'active' ? 'Ativo' :
                           workflow.status === 'inactive' ? 'Inativo' : 'Rascunho'}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <p className="font-medium text-gray-950 dark:text-gray-50">{workflow.executions}</p>
                      <p className="text-gray-600">Execuções</p>
                    </div>

                    <div className="text-center">
                      <p className="font-medium text-green-600">{workflow.successRate}%</p>
                      <p className="text-gray-600">Sucesso</p>
                    </div>

                    {workflow.lastExecution && (
                      <div className="text-center">
                        <p className="font-medium text-gray-950 dark:text-gray-50">
                          {new Date(workflow.lastExecution).toLocaleDateString('pt-BR')}
                        </p>
                        <p className="text-gray-600">Última exec.</p>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedWorkflow(workflow)}
                        className="gap-2"
                      >
                        <Eye className="w-4 h-4" />
                        Ver
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedWorkflow(workflow)
                          setShowBuilder(true)
                        }}
                        className="gap-2"
                      >
                        <Edit className="w-4 h-4" />
                        Editar
                      </Button>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderTemplates = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50">Templates de Automação</h3>
          <p className="text-sm text-gray-600">Use templates prontos para criar workflows rapidamente</p>
        </div>
        <Button className="gap-2">
          <Upload className="w-4 h-4" />
          Importar Template
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {automationTemplates.map(template => (
          <Card key={template.id} className="hover:transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <p className="text-sm text-gray-600">{template.category}</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map(star => (
                      <div
                        key={star}
                        className={`w-3 h-3 ${star <= template.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                      >
                        ⭐
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-600">{template.usageCount} usos</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-800 dark:text-gray-200">{template.description}</p>

                <div className="flex flex-wrap gap-1">
                  <Badge variant="outline" className="text-xs">
                    {template.workflow.nodes.filter(n => n.type === 'trigger').length} Triggers
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {template.workflow.nodes.filter(n => n.type === 'action').length} Ações
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {template.workflow.nodes.filter(n => n.type === 'condition').length} Condições
                  </Badge>
                </div>

                <div className="flex gap-2">
                  <Button size="sm" variant="outline" className="flex-1 gap-2">
                    <Eye className="w-4 h-4" />
                    Visualizar
                  </Button>
                  <Button size="sm" className="flex-1 gap-2">
                    <Download className="w-4 h-4" />
                    Usar Template
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  const renderBuilder = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50">Workflow Builder</h3>
          <p className="text-sm text-gray-600">Arraste e solte componentes para criar seu workflow</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Save className="w-4 h-4" />
            Salvar
          </Button>
          <Button className="gap-2">
            <Play className="w-4 h-4" />
            Testar
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-96">
        {/* Palette */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-950 dark:text-gray-50">Componentes</h4>
          {nodeTypes.map(nodeType => (
            <Card key={nodeType.type}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <nodeType.icon className="w-4 h-4" />
                  {nodeType.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {nodeType.items.map(item => (
                  <div
                    key={item.id}
                    className={`p-2 border rounded cursor-pointer hover:bg-gray-50 ${nodeType.color}`}
                    draggable
                  >
                    <p className="text-xs font-medium">{item.name}</p>
                    <p className="text-xs text-gray-600">{item.description}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Canvas */}
        <div className="lg:col-span-3">
          <div className="w-full h-full border-2 border-dashed border-gray-300 rounded-md bg-gray-50 flex items-center justify-center">
            <div className="text-center">
              <Workflow className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600">Arraste componentes aqui para começar</p>
            </div>
          </div>
        </div>
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
                <Workflow className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                Automação Avançada de Workflows
              </h1>
              <p className="text-gray-600">
                Crie fluxos automatizados inteligentes para otimizar processos
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <BarChart3 className="w-4 h-4" />
                Analytics
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
              { id: 'builder', label: 'Builder', icon: Code },
              { id: 'templates', label: 'Templates', icon: FileText },
              { id: 'analytics', label: 'Analytics', icon: Brain }
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
        {selectedView === 'overview' && renderOverview()}
        {selectedView === 'builder' && renderBuilder()}
        {selectedView === 'templates' && renderTemplates()}
        {selectedView === 'analytics' && (
          <div className="text-center py-12">
            <Brain className="w-12 h-12 text-wedo-cyan mx-auto mb-4" />
            <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50 mb-2">Analytics de Automação</h3>
            <p className="text-gray-600">Métricas detalhadas de performance em desenvolvimento</p>
          </div>
        )}

        {/* Workflow Builder Modal */}
        {showBuilder && (
          <WorkflowBuilderModal
            workflow={selectedWorkflow}
            onClose={() => {
              setShowBuilder(false)
              setSelectedWorkflow(null)
            }}
          />
        )}
      </div>
    </div>
  )
}

// Workflow Builder Modal
interface WorkflowBuilderModalProps {
  workflow?: Workflow | null
  onClose: () => void
}

function WorkflowBuilderModal({ workflow, onClose }: WorkflowBuilderModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-md w-full max-w-6xl h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50">
            {workflow ? `Editar: ${workflow.name}` : 'Novo Workflow'}
          </h2>
          <Button variant="ghost" onClick={onClose}>×</Button>
        </div>

        <div className="flex-1 p-6">
          <div className="text-center py-12">
            <Code className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xs font-medium text-gray-950 dark:text-gray-50 mb-2">Workflow Builder Avançado</h3>
            <p className="text-gray-600">Interface visual de drag-and-drop em desenvolvimento</p>
          </div>
        </div>
      </div>
    </div>
  )
}
