"use client"

  import { useState } from "react"
  import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
  import { Button } from "@/components/ui/button"
  import { Badge } from "@/components/ui/badge"
  import { hasModuleAccess } from "@/utils/license-manager"
  import { ModuleUpsell } from "@/components/module-access/module-upsell"
  import {
    Link2, Database, MessageSquare, Plus, RefreshCw,
    BarChart3, Server, GitBranch, FileText, Bell, Send,
    CheckCircle, Edit, Settings, Check, X, Activity,
    CheckCircle2, XCircle, Minus, AlertCircle, Info
  } from "lucide-react"

  interface ATSSystem {
    id: string
    name: string
    type: 'sap' | 'workday' | 'bamboohr' | 'greenhouse' | 'custom'
    status: 'connected' | 'connecting' | 'error' | 'disabled'
    description: string
    logo?: string
    lastSync?: string
    totalRecords: number
    syncedRecords: number
    errorCount: number
    features: string[]
    webhookUrl?: string
    apiEndpoint?: string
    version?: string
  }

  interface CommunicationIntegration {
    id: string
    name: string
    type: 'teams'
    status: 'active' | 'inactive' | 'error'
    icon: React.ElementType
    color: string
    webhookUrl: string
    channels: string[]
    events: string[]
    lastActivity: string
    messagesCount: number
    errorCount: number
    createdAt: string
    createdBy: string
  }

  interface NotificationTemplate {
    id: string
    name: string
    event: string
    title: string
    message: string
    mentions: string[]
    active: boolean
    integrations: string[]
  }

  interface SyncLog {
    id: string
    timestamp: string
    system: string
    type: 'sync' | 'webhook' | 'manual'
    status: 'success' | 'warning' | 'error'
    records: number
    duration: number
    message: string
    details?: string
  }

  export interface SettingsIntegrationsTabProps {
    onSettingsChange: (changed: boolean) => void
  }

  // Componente de Integrações (ATS + Comunicação)
export function SettingsIntegrationsTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [selectedIntegrationType, setSelectedIntegrationType] = useState<'ats' | 'communication'>('ats')
  const [selectedView, setSelectedView] = useState<'overview' | 'systems' | 'mapping' | 'logs'>('overview')
  const [selectedSystem, setSelectedSystem] = useState<ATSSystem | null>(null)
  const [showSystemModal, setShowSystemModal] = useState(false)

  // Mock data das integrações de comunicação
  const [communicationIntegrations, setCommunicationIntegrations] = useState<CommunicationIntegration[]>([

    {
      id: 'teams-rh',
      name: 'Equipe RH',
      type: 'teams',
      status: 'active',
      icon: MessageSquare,
      color: 'bg-lia-bg-secondary dark:bg-lia-bg-primary text-lia-text-primary',
      webhookUrl: 'https://outlook.office.com/webhook/xxxxx/IncomingWebhook/yyyyy',
      channels: ['RH Geral', 'Aprovações'],
      events: ['aprovacao_lote', 'candidato_final', 'relatorio_semanal'],
      lastActivity: '2025-03-15T09:15:00Z',
      messagesCount: 156,
      errorCount: 0,
      createdAt: '2025-02-01T14:00:00Z',
      createdBy: 'Carlos Mendes'
    }
  ])

  const [notificationTemplates, setNotificationTemplates] = useState<NotificationTemplate[]>([
    {
      id: 'novo-candidato',
      name: 'Novo Candidato',
      event: 'novo_candidato',
      title: '🎯 Novo candidato aplicou!',
      message: 'O candidato **{candidate_name}** se candidatou para a vaga **{job_title}**.\n\n📊 Score LIA: **{lia_score}%**\n📍 Localização: {location}\n⭐ Match: {match_score}%',
      mentions: ['@channel'],
      active: true,
      integrations: ['teams-rh']
    },
    {
      id: 'aprovacao-candidato',
      name: 'Aprovação de Candidato',
      event: 'aprovacao',
      title: '✅ Candidato aprovado!',
      message: 'O candidato **{candidate_name}** foi aprovado para a vaga **{job_title}**!\n\n👤 Aprovado por: {approver}\n📅 Data: {date}',
      mentions: ['@here'],
      active: true,
      integrations: ['teams-rh']
    }
  ])

  // Mock data dos sistemas ATS
  const atsystems: ATSSystem[] = [
    {
      id: 'sap_sf',
      name: 'SAP SuccessFactors',
      type: 'sap',
      status: 'connected',
      description: 'Sistema completo de gestão de recursos humanos',
      lastSync: '2024-01-20T14:30:00Z',
      totalRecords: 2847,
      syncedRecords: 2847,
      errorCount: 0,
      features: ['Candidatos', 'Vagas', 'Entrevistas', 'Ofertas', 'Onboarding'],
      webhookUrl: 'https://api.plataforma-lia.com/webhooks/sap',
      apiEndpoint: 'https://api.successfactors.com/v2',
      version: '2.0'
    },
    {
      id: 'workday',
      name: 'Workday HCM',
      type: 'workday',
      status: 'connecting',
      description: 'Plataforma de capital humano empresarial',
      totalRecords: 0,
      syncedRecords: 0,
      errorCount: 0,
      features: ['Funcionários', 'Requisições', 'Performance', 'Benefícios'],
      apiEndpoint: 'https://wd2-impl-services1.workday.com',
      version: '39.0'
    },
    {
      id: 'bamboohr',
      name: 'BambooHR',
      type: 'bamboohr',
      status: 'error',
      description: 'Sistema de RH para pequenas e médias empresas',
      lastSync: '2024-01-19T16:20:00Z',
      totalRecords: 156,
      syncedRecords: 134,
      errorCount: 22,
      features: ['Colaboradores', 'Relatórios', 'Time Off', 'Performance'],
      webhookUrl: 'https://api.plataforma-lia.com/webhooks/bamboo',
      apiEndpoint: 'https://api.bamboohr.com/api/gateway.php',
      version: '1.0'
    },
    {
      id: 'greenhouse',
      name: 'Greenhouse',
      type: 'greenhouse',
      status: 'disabled',
      description: 'ATS focado em recrutamento e seleção',
      totalRecords: 0,
      syncedRecords: 0,
      errorCount: 0,
      features: ['Candidatos', 'Vagas', 'Entrevistas', 'Scorecards'],
      apiEndpoint: 'https://harvest.greenhouse.io/v1',
      version: '1.0'
    }
  ]

  const syncLogs: SyncLog[] = [
    {
      id: '1',
      timestamp: '2024-01-20T14:30:00Z',
      system: 'SAP SuccessFactors',
      type: 'sync',
      status: 'success',
      records: 15,
      duration: 2340,
      message: 'Sincronização de candidatos concluída com sucesso',
      details: '15 novos candidatos importados, 3 atualizados'
    },
    {
      id: '2',
      timestamp: '2024-01-20T14:15:00Z',
      system: 'SAP SuccessFactors',
      type: 'webhook',
      status: 'success',
      records: 1,
      duration: 156,
      message: 'Nova vaga recebida via webhook',
      details: 'Vaga "Senior Developer" criada automaticamente'
    },
    {
      id: '3',
      timestamp: '2024-01-19T16:20:00Z',
      system: 'BambooHR',
      type: 'sync',
      status: 'error',
      records: 0,
      duration: 5000,
      message: 'Erro de autenticação na API',
      details: 'Token de acesso expirado - necessária renovação manual'
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4 text-status-success" />
      case 'connecting': return <RefreshCw className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
      case 'error': return <XCircle className="w-4 h-4 text-status-error" />
      case 'disabled': return <Minus className="w-4 h-4 text-lia-text-primary" />
      default: return <AlertCircle className="w-4 h-4 text-status-warning" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'bg-status-success/10 text-status-success border-status-success/30'
      case 'connecting': return 'bg-lia-bg-secondary dark:bg-lia-bg-primary text-lia-text-primary border-lia-btn-primary-bg dark:border-lia-border-subtle'
      case 'error': return 'bg-status-error/10 text-status-error border-status-error/30'
      case 'disabled': return 'bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle'
      default: return 'bg-status-warning/10 text-status-warning border-status-warning/30'
    }
  }

  const getSyncStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle2 className="w-4 h-4 text-status-success" />
      case 'warning': return <AlertCircle className="w-4 h-4 text-status-warning" />
      case 'error': return <XCircle className="w-4 h-4 text-status-error" />
      default: return <Info className="w-4 h-4 text-lia-text-secondary" />
    }
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Sistemas Conectados</p>
                <p className="text-2xl font-bold text-lia-text-primary">
                  {atsystems.filter(s => s.status === 'connected').length}
                </p>
                <p className="text-xs text-lia-text-primary">de {atsystems.length} configurados</p>
              </div>
              <div className="w-10 h-10 bg-status-success/15 rounded-md flex items-center justify-center">
                <Link2 className="w-5 h-5 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Registros Sincronizados</p>
                <p className="text-2xl font-bold text-wedo-cyan-dark">
                  {atsystems.reduce((acc, sys) => acc + sys.syncedRecords, 0).toLocaleString()}
                </p>
                <p className="text-xs text-status-success">+47 hoje</p>
              </div>
              <div className="w-10 h-10 bg-wedo-cyan/15 rounded-md flex items-center justify-center">
                <Database className="w-5 h-5 text-lia-text-secondary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Uptime Médio</p>
                <p className="text-2xl font-bold text-wedo-orange">99.7%</p>
                <p className="text-xs text-wedo-orange">últimos 30 dias</p>
              </div>
              <div className="w-10 h-10 bg-wedo-orange/15 rounded-md flex items-center justify-center">
                <Activity className="w-5 h-5 text-wedo-orange" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-lia-text-primary">Última Sincronização</p>
                <p className="text-lg font-bold text-lia-text-primary">Há 15min</p>
                <p className="text-xs text-lia-text-primary">SAP SuccessFactors</p>
              </div>
              <div className="w-10 h-10 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                <RefreshCw className="w-5 h-5 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sistemas Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Server className="w-4 h-4" />
            Status dos Sistemas ATS
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {atsystems.map(system => (
              <div key={system.id} className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-md">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-lia-bg-tertiary rounded-md flex items-center justify-center">
                    <Server className="w-5 h-5 text-lia-text-primary" />
                  </div>
                  <div>
                    <h4 className="font-medium text-lia-text-primary">{system.name}</h4>
                    <p className="text-sm text-lia-text-primary">{system.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(system.status)}
                      <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(system.status)}`}>
                        {system.status === 'connected' ? 'Conectado' :
                         system.status === 'connecting' ? 'Conectando' :
                         system.status === 'error' ? 'Erro' : 'Desabilitado'}
                      </span>
                      {system.lastSync && (
                        <span className="text-xs text-lia-text-primary">
                          Última sync: {new Date(system.lastSync).toLocaleString('pt-BR')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-sm">
                  {system.status === 'connected' && (
                    <>
                      <div className="text-center">
                        <p className="font-medium text-lia-text-primary">{system.syncedRecords}</p>
                        <p className="text-lia-text-primary">Registros</p>
                      </div>
                      <div className="text-center">
                        <p className="font-medium text-status-success">
                          {Math.round((system.syncedRecords / system.totalRecords) * 100)}%
                        </p>
                        <p className="text-lia-text-primary">Sincronizado</p>
                      </div>
                    </>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedSystem(system)
                      setShowSystemModal(true)
                      onSettingsChange(true)
                    }}
                  >
                    Configurar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Logs Recentes */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Logs Recentes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {syncLogs.slice(0, 3).map(log => (
              <div key={log.id} className="flex items-center justify-between p-3 bg-lia-bg-secondary rounded-md">
                <div className="flex items-center gap-3">
                  {getSyncStatusIcon(log.status)}
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary">{log.message}</p>
                    <p className="text-xs text-lia-text-primary">
                      {log.system} • {new Date(log.timestamp).toLocaleString('pt-BR')}
                    </p>
                  </div>
                </div>
                <div className="text-right text-xs text-lia-text-primary">
                  <p>{log.records} registros</p>
                  <p>{log.duration}ms</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-lia-text-primary flex items-center gap-2">
            <Link2 className="w-5 h-5 text-lia-text-secondary" />
            Integrações
          </h2>
          <p className="text-sm text-lia-text-primary">
            Conecte sistemas ATS, Teams e outras plataformas
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Sincronizar Tudo
          </Button>
          <Button size="sm" className="gap-2">
            <Plus className="w-4 h-4" />
            Nova Integração
          </Button>
        </div>
      </div>

      {/* Integration Type Tabs */}
      <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-md w-fit">
        <button
          onClick={() => setSelectedIntegrationType('ats')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
            selectedIntegrationType === 'ats'
              ? 'bg-lia-bg-primary text-lia-text-secondary'
              : 'text-lia-text-primary hover:text-lia-text-primary'
          }`}
        >
          <Database className="w-4 h-4" />
          Sistemas ATS
        </button>
        <button
          onClick={() => setSelectedIntegrationType('communication')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
            selectedIntegrationType === 'communication'
              ? 'bg-lia-bg-primary text-lia-text-secondary'
              : 'text-lia-text-primary hover:text-lia-text-primary'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          Comunicação
        </button>
      </div>

      {/* ATS Content */}
      {selectedIntegrationType === 'ats' && (
        <>
          {/* Check module access for ATS */}
          {!hasModuleAccess('ats_integrations') ? (
            <ModuleUpsell
              moduleId="ats_integrations"
              title="Integrações ATS Enterprise"
              description="Conecte e sincronize dados com sistemas HR externos como SAP SuccessFactors, Workday e BambooHR"
            />
          ) : (
            <>
              {/* ATS Navigation Tabs */}
              <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-md w-fit">
                {[
                  { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
                  { id: 'systems', label: 'Sistemas', icon: Server },
                  { id: 'mapping', label: 'Mapeamento', icon: GitBranch },
                  { id: 'logs', label: 'Logs', icon: FileText }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedView(tab.id as 'overview' | 'systems' | 'mapping' | 'logs')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
                      selectedView === tab.id
                        ? 'bg-lia-bg-primary text-lia-text-secondary'
                        : 'text-lia-text-primary hover:text-lia-text-primary'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* ATS Content based on selectedView */}
              {selectedView === 'overview' && renderOverview()}
              {selectedView === 'systems' && (
                <div className="text-center py-12">
                  <Server className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-lia-text-primary mb-2">Configuração de Sistemas</h3>
                  <p className="text-lia-text-primary">Conectar e configurar sistemas ATS externos</p>
                </div>
              )}
              {selectedView === 'mapping' && (
                <div className="text-center py-12">
                  <GitBranch className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-lia-text-primary mb-2">Mapeamento de Campos</h3>
                  <p className="text-lia-text-primary">Interface visual drag-and-drop para mapear campos entre sistemas</p>
                </div>
              )}
              {selectedView === 'logs' && (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-lia-text-primary mb-2">Logs Detalhados</h3>
                  <p className="text-lia-text-primary">Histórico completo de sincronizações e operações</p>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Communication Content */}
      {selectedIntegrationType === 'communication' && (
        <div className="space-y-6">
          {/* Communication Integrations Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-wedo-purple" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary">Integrações Ativas</p>
                    <p className="text-2xl font-bold text-lia-text-primary">
                      {communicationIntegrations.filter(i => i.status === 'active').length}
                    </p>
                    <p className="text-xs text-lia-text-primary">de {communicationIntegrations.length} total</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-wedo-cyan/15 rounded-md flex items-center justify-center">
                    <Send className="w-5 h-5 text-lia-text-secondary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary">Mensagens Enviadas</p>
                    <p className="text-2xl font-bold text-lia-text-primary">
                      {communicationIntegrations.reduce((acc, i) => acc + i.messagesCount, 0)}
                    </p>
                    <p className="text-xs text-lia-text-primary">últimos 30 dias</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-status-success/15 rounded-md flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary">Taxa de Sucesso</p>
                    <p className="text-2xl font-bold text-lia-text-primary">98.5%</p>
                    <p className="text-xs text-lia-text-primary">últimos 30 dias</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Active Integrations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Integrações Configuradas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {communicationIntegrations.map(integration => (
                  <div key={integration.id} className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-md">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-md flex items-center justify-center ${integration.color}`}>
                        <integration.icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-medium text-lia-text-primary">{integration.name}</h3>
                        <p className="text-sm text-lia-text-primary">{integration.channels.join(', ')}</p>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-xs text-lia-text-primary">
                            {integration.messagesCount} mensagens
                          </span>
                          <span className="text-xs text-lia-text-primary">
                            Criado por {integration.createdBy}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={`${
                        integration.status === 'active' ? 'bg-status-success/15 text-status-success' :
                        integration.status === 'error' ? 'bg-status-error/15 text-status-error' :
                        'bg-lia-bg-tertiary text-lia-text-primary'
                      }`}>
                        {integration.status === 'active' ? 'Ativo' :
                         integration.status === 'error' ? 'Erro' : 'Inativo'}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Notification Templates */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Templates de Notificação</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {notificationTemplates.map(template => (
                  <div key={template.id} className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-md">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-wedo-cyan/15 rounded-md flex items-center justify-center">
                        <Bell className="w-5 h-5 text-lia-text-secondary" />
                      </div>
                      <div>
                        <h3 className="font-medium text-lia-text-primary">{template.name}</h3>
                        <p className="text-sm text-lia-text-primary">{template.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-lia-text-primary">
                            {template.integrations.length} integrações
                          </span>
                          {template.mentions.length > 0 && (
                            <Badge variant="outline" className="text-xs">
                              {template.mentions.join(', ')}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={template.active ? 'bg-status-success/15 text-status-success' : 'bg-lia-bg-tertiary text-lia-text-primary'}>
                        {template.active ? 'Ativo' : 'Inativo'}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-md w-fit">
        {[
          { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
          { id: 'systems', label: 'Sistemas', icon: Server },
          { id: 'mapping', label: 'Mapeamento', icon: GitBranch },
          { id: 'logs', label: 'Logs', icon: FileText }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as 'overview' | 'systems' | 'mapping' | 'logs')}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none font-crimson ${
              selectedView === tab.id
                ? 'bg-lia-bg-primary text-lia-text-primary'
                : 'text-lia-text-primary hover:text-lia-text-primary'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {selectedView === 'overview' && renderOverview()}
      {selectedView === 'systems' && (
        <div className="text-center py-12">
          <Server className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
          <h3 className="text-lg font-medium text-lia-text-primary mb-2">Gerenciamento de Sistemas</h3>
          <p className="text-lia-text-primary">Interface de configuração detalhada dos sistemas ATS</p>
        </div>
      )}
      {selectedView === 'mapping' && (
        <div className="text-center py-12">
          <GitBranch className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
          <h3 className="text-lg font-medium text-lia-text-primary mb-2">Mapeamento de Campos</h3>
          <p className="text-lia-text-primary">Interface visual drag-and-drop para mapear campos entre sistemas</p>
        </div>
      )}
      {selectedView === 'logs' && (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
          <h3 className="text-lg font-medium text-lia-text-primary mb-2">Logs Detalhados</h3>
          <p className="text-lia-text-primary">Histórico completo de sincronizações e operações</p>
        </div>
      )}
    </div>
  )
}
  