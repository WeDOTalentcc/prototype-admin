"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Settings, Slack, MessageSquare, Bell, Users, Check, X, Plus,
  ExternalLink, Copy, Eye, Edit, Trash2, AlertCircle, CheckCircle,
  Zap, Hash, AtSign, Calendar, FileText, UserCheck, MessageCircle,
  Webhook, Key, Globe, Shield, RefreshCw, Download, Upload,
  PlayCircle, PauseCircle, Activity, BarChart3, Clock, Filter
} from "lucide-react"

interface Integration {
  id: string
  name: string
  type: 'slack' | 'teams' | 'discord' | 'email'
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

interface WebhookEvent {
  id: string
  integration: string
  event: string
  status: 'success' | 'failed' | 'pending'
  timestamp: string
  payload: Record<string, unknown>
  response?: Record<string, unknown>
  error?: string
}

export function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([
    {
      id: 'slack-recruiting',
      name: 'Canal #recrutamento',
      type: 'slack',
      status: 'active',
      icon: Slack,
      color: 'bg-wedo-purple/15 text-wedo-purple',
      webhookUrl: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
      channels: ['#recrutamento', '#aprovacoes', '#geral'],
      events: ['novo_candidato', 'aprovacao', 'nova_nota', 'mencao'],
      lastActivity: '2025-03-15T14:30:00Z',
      messagesCount: 247,
      errorCount: 2,
      createdAt: '2025-01-15T10:00:00Z',
      createdBy: 'Ana Silva'
    },
    {
      id: 'teams-rh',
      name: 'Equipe RH',
      type: 'teams',
      status: 'active',
      icon: MessageSquare,
      color: 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary',
      webhookUrl: 'https://outlook.office.com/webhook/xxxxx/IncomingWebhook/yyyyy',
      channels: ['RH Geral', 'Aprovações'],
      events: ['aprovacao_lote', 'candidato_final', 'relatorio_semanal'],
      lastActivity: '2025-03-15T09:15:00Z',
      messagesCount: 156,
      errorCount: 0,
      createdAt: '2025-02-01T14:00:00Z',
      createdBy: 'Carlos Mendes'
    },
    {
      id: 'slack-tech',
      name: 'Canal #tech-hiring',
      type: 'slack',
      status: 'error',
      icon: Slack,
      color: 'bg-status-error/15 text-status-error',
      webhookUrl: 'https://hooks.slack.com/services/invalid',
      channels: ['#tech-hiring'],
      events: ['entrevista_tecnica', 'aprovacao_tech'],
      lastActivity: '2025-03-14T16:45:00Z',
      messagesCount: 89,
      errorCount: 12,
      createdAt: '2025-02-15T11:30:00Z',
      createdBy: 'Marina Costa'
    }
  ])

  const [templates, setTemplates] = useState<NotificationTemplate[]>([
    {
      id: 'novo-candidato',
      name: 'Novo Candidato',
      event: 'novo_candidato',
      title: '🎯 Novo candidato aplicou!',
      message: 'O candidato **{candidate_name}** se candidatou para a vaga **{job_title}**.\n\n📊 Score LIA: **{lia_score}%**\n📍 Localização: {location}\n⭐ Match: {match_score}%\n\n[Ver perfil completo]({candidate_url})',
      mentions: ['@channel'],
      active: true,
      integrations: ['slack-recruiting', 'teams-rh']
    },
    {
      id: 'aprovacao-candidato',
      name: 'Aprovação de Candidato',
      event: 'aprovacao',
      title: '✅ Candidato aprovado!',
      message: 'O candidato **{candidate_name}** foi aprovado para **{job_title}**!\n\n👤 Aprovado por: {approver_name}\n📅 Data: {approval_date}\n💬 Comentário: "{approval_comment}"\n\n🎉 Próximo passo: {next_step}',
      mentions: ['@here'],
      active: true,
      integrations: ['slack-recruiting', 'teams-rh']
    },
    {
      id: 'nova-nota',
      name: 'Nova Nota/Comentário',
      event: 'nova_nota',
      title: '💬 Nova nota adicionada',
      message: '**{author_name}** adicionou uma nota sobre **{candidate_name}**:\n\n"{note_content}"\n\n🏷️ Tags: {tags}\n📂 Categoria: {category}\n\n[Ver nota completa]({note_url})',
      mentions: [],
      active: true,
      integrations: ['slack-recruiting']
    },
    {
      id: 'mencao',
      name: 'Menção em Nota',
      event: 'mencao',
      title: '👋 Você foi mencionado!',
      message: '**{author_name}** mencionou você em uma nota sobre **{candidate_name}**:\n\n"{note_content}"\n\n[Responder]({note_url})',
      mentions: ['{mentioned_user}'],
      active: true,
      integrations: ['slack-recruiting', 'teams-rh']
    },
    {
      id: 'aprovacao-lote',
      name: 'Aprovação em Lote',
      event: 'aprovacao_lote',
      title: '📦 Aprovação em lote realizada',
      message: '**{approver_name}** realizou uma aprovação em lote:\n\n✅ **{approved_count}** candidatos aprovados\n❌ **{rejected_count}** candidatos rejeitados\n📝 **{moved_count}** candidatos movidos\n\n💬 Comentário geral: "{batch_comment}"\n\n[Ver detalhes]({batch_url})',
      mentions: ['@channel'],
      active: true,
      integrations: ['teams-rh']
    }
  ])

  const [webhookEvents, setWebhookEvents] = useState<WebhookEvent[]>([
    {
      id: '1',
      integration: 'slack-recruiting',
      event: 'novo_candidato',
      status: 'success',
      timestamp: '2025-03-15T14:30:00Z',
      payload: { candidate_name: 'Ana Costa', job_title: 'UX Designer Sênior' },
      response: { ok: true, ts: '1647267000.000100' }
    },
    {
      id: '2',
      integration: 'teams-rh',
      event: 'aprovacao',
      status: 'success',
      timestamp: '2025-03-15T13:15:00Z',
      payload: { candidate_name: 'João Silva', approver: 'Marina Costa' }
    },
    {
      id: '3',
      integration: 'slack-tech',
      event: 'entrevista_tecnica',
      status: 'failed',
      timestamp: '2025-03-15T12:00:00Z',
      payload: { candidate_name: 'Pedro Santos' },
      error: 'Webhook URL inválida'
    }
  ])

  const [showNewIntegration, setShowNewIntegration] = useState(false)
  const [showTemplateEditor, setShowTemplateEditor] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<NotificationTemplate | null>(null)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [showWebhookLogs, setShowWebhookLogs] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [testingIntegration, setTestingIntegration] = useState<string | null>(null)

  const [newIntegration, setNewIntegration] = useState({
    name: '',
    type: 'slack' as 'slack' | 'teams',
    webhookUrl: '',
    channels: [''],
    events: [] as string[]
  })

  const availableEvents = [
    { id: 'novo_candidato', label: 'Novo Candidato', icon: UserCheck, description: 'Quando um novo candidato se inscreve' },
    { id: 'aprovacao', label: 'Aprovação Individual', icon: CheckCircle, description: 'Quando um candidato é aprovado' },
    { id: 'aprovacao_lote', label: 'Aprovação em Lote', icon: Users, description: 'Quando múltiplos candidatos são processados' },
    { id: 'nova_nota', label: 'Nova Nota', icon: MessageCircle, description: 'Quando uma nota é adicionada' },
    { id: 'mencao', label: 'Menção', icon: AtSign, description: 'Quando alguém é mencionado em uma nota' },
    { id: 'entrevista_agendada', label: 'Entrevista Agendada', icon: Calendar, description: 'Quando uma entrevista é marcada' },
    { id: 'relatorio_semanal', label: 'Relatório Semanal', icon: BarChart3, description: 'Relatório automático semanal' }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-status-success" />
      case 'inactive': return <PauseCircle className="w-4 h-4 text-lia-text-secondary" />
      case 'error': return <AlertCircle className="w-4 h-4 text-status-error" />
      default: return <Clock className="w-4 h-4 text-status-warning" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-status-success/15 text-status-success border-status-success/30'
      case 'inactive': return 'bg-gray-100 text-lia-text-primary border-lia-border-subtle'
      case 'error': return 'bg-status-error/15 text-status-error border-status-error/30'
      default: return 'bg-status-warning/15 text-status-warning border-status-warning/30'
    }
  }

  const testIntegration = async (integrationId: string) => {
    setTestingIntegration(integrationId)

    // Simular teste de webhook
    setTimeout(() => {
      setTestingIntegration(null)
      // Adicionar evento de teste
      const testEvent: WebhookEvent = {
        id: Date.now().toString(),
        integration: integrationId,
        event: 'test',
        status: 'success',
        timestamp: new Date().toISOString(),
        payload: { test: true, message: 'Teste de conexão' },
        response: { ok: true, message: 'Teste enviado com sucesso!' }
      }
      setWebhookEvents([testEvent, ...webhookEvents])
    }, 2000)
  }

  const toggleIntegrationStatus = (integrationId: string) => {
    setIntegrations(integrations.map(integration =>
      integration.id === integrationId
        ? {
            ...integration,
            status: integration.status === 'active' ? 'inactive' : 'active'
          }
        : integration
    ))
  }

  const deleteIntegration = (integrationId: string) => {
    setIntegrations(integrations.filter(integration => integration.id !== integrationId))
  }

  const saveTemplate = (template: NotificationTemplate) => {
    if (template.id) {
      setTemplates(templates.map(t => t.id === template.id ? template : t))
    } else {
      setTemplates([...templates, { ...template, id: Date.now().toString() }])
    }
    setShowTemplateEditor(false)
    setSelectedTemplate(null)
  }

  const filteredEvents = webhookEvents.filter(event => {
    if (filterStatus === 'all') return true
    return event.status === filterStatus
  })

  return (
    <div className="min-h-screen bg-white dark:bg-lia-bg-primary p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary mb-2 flex items-center gap-3 font-sans">
                <Settings className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Integrações Externas
              </h1>
              <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
                Configure notificações automáticas para Slack, Teams e outras ferramentas
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowWebhookLogs(!showWebhookLogs)}
                className="gap-2"
              >
                <Activity className="w-4 h-4" />
                Logs de Webhook
              </Button>
              <Button
                onClick={() => setShowNewIntegration(true)}
                className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
              >
                <Plus className="w-4 h-4" />
                Nova Integração
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                    Integrações Ativas
                  </p>
                  <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                    {integrations.filter(i => i.status === 'active').length}
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-status-success" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                    Mensagens Enviadas
                  </p>
                  <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                    {integrations.reduce((acc, i) => acc + i.messagesCount, 0)}
                  </p>
                </div>
                <MessageCircle className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                    Templates Ativos
                  </p>
                  <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                    {templates.filter(t => t.active).length}
                  </p>
                </div>
                <FileText className="w-8 h-8 text-wedo-purple" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                    Taxa de Sucesso
                  </p>
                  <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                    {Math.round(((webhookEvents.filter(e => e.status === 'success').length / webhookEvents.length) * 100) || 0)}%
                  </p>
                </div>
                <BarChart3 className="w-8 h-8 text-wedo-orange" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Integrações Configuradas */}
          <div className="col-span-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Webhook className="w-5 h-5" />
                  Integrações Configuradas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {integrations.map((integration) => (
                    <div key={integration.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className={`w-12 h-12 rounded-md flex items-center justify-center ${integration.color}`}>
                            <integration.icon className="w-6 h-6" />
                          </div>

                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">
                                {integration.name}
                              </h3>
                              <Badge className={`${getStatusColor(integration.status)} text-xs`}>
                                {getStatusIcon(integration.status)}
                                <span className="ml-1 capitalize">{integration.status}</span>
                              </Badge>
                            </div>

                            <div className="space-y-2">
                              <div className="flex items-center gap-4 text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                                <div className="flex items-center gap-1">
                                  <Hash className="w-4 h-4" />
                                  <span>{integration.channels.join(', ')}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Bell className="w-4 h-4" />
                                  <span>{integration.events.length} eventos</span>
                                </div>
                              </div>

                              <div className="flex items-center gap-4 text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                                <div>
                                  <span className="font-medium text-status-success">{integration.messagesCount}</span> mensagens enviadas
                                </div>
                                <div>
                                  <span className="font-medium text-status-error">{integration.errorCount}</span> erros
                                </div>
                                <div>
                                  Última atividade: {new Date(integration.lastActivity).toLocaleDateString('pt-BR')}
                                </div>
                              </div>

                              <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                                Criado por {integration.createdBy} em {new Date(integration.createdAt).toLocaleDateString('pt-BR')}
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => testIntegration(integration.id)}
                            disabled={testingIntegration === integration.id}
                            className="gap-2"
                          >
                            {testingIntegration === integration.id ? (
                              <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                            ) : (
                              <PlayCircle className="w-4 h-4" />
                            )}
                            Testar
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedIntegration(integration)}
                            className="gap-2"
                          >
                            <Edit className="w-4 h-4" />
                            Editar
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleIntegrationStatus(integration.id)}
                            className="gap-2"
                          >
                            {integration.status === 'active' ? (
                              <PauseCircle className="w-4 h-4" />
                            ) : (
                              <PlayCircle className="w-4 h-4" />
                            )}
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteIntegration(integration.id)}
                            className="gap-2 text-status-error hover:text-status-error"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Templates de Notificação */}
            <Card className="mt-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <MessageCircle className="w-5 h-5" />
                    Templates de Notificação
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedTemplate(null)
                      setShowTemplateEditor(true)
                    }}
                    className="gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Novo Template
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {templates.map((template) => (
                    <div key={template.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">
                              {template.name}
                            </h4>
                            <Badge variant={template.active ? "default" : "secondary"} className="text-xs">
                              {template.active ? 'Ativo' : 'Inativo'}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {template.event}
                            </Badge>
                          </div>

                          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary mb-2">
                            {template.title}
                          </p>

                          <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                            Usado em: {template.integrations.join(', ')}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedTemplate(template)
                              setShowTemplateEditor(true)
                            }}
                            className="gap-2"
                          >
                            <Edit className="w-4 h-4" />
                            Editar
                          </Button>

                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-2"
                          >
                            <Eye className="w-4 h-4" />
                            Preview
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Webhook Logs */}
          <div className="col-span-4">
            {showWebhookLogs && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Activity className="w-4 h-4" />
                      Logs de Webhook
                    </CardTitle>
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="text-xs border rounded-md px-2 py-1"
                    >
                      <option value="all">Todos</option>
                      <option value="success">Sucesso</option>
                      <option value="failed">Falha</option>
                      <option value="pending">Pendente</option>
                    </select>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {filteredEvents.map((event) => (
                      <div key={event.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {event.status === 'success' && <CheckCircle className="w-4 h-4 text-status-success" />}
                            {event.status === 'failed' && <AlertCircle className="w-4 h-4 text-status-error" />}
                            {event.status === 'pending' && <Clock className="w-4 h-4 text-status-warning" />}
                            <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                              {event.event}
                            </span>
                          </div>
                          <span className="text-xs text-lia-text-secondary">
                            {new Date(event.timestamp).toLocaleTimeString('pt-BR')}
                          </span>
                        </div>

                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mb-1">
                          {event.integration}
                        </p>

                        {event.error && (
                          <p className="text-xs text-status-error bg-status-error/10 dark:bg-status-error/20 p-2 rounded-md">
                            {event.error}
                          </p>
                        )}

                        {event.response && (
                          <p className="text-xs text-status-success bg-status-success/10 dark:bg-status-success/20 p-2 rounded-md">
                            ✓ Enviado com sucesso
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Eventos Disponíveis */}
            <Card className={showWebhookLogs ? "mt-6" : ""}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Bell className="w-4 h-4" />
                  Eventos Disponíveis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {availableEvents.map((event) => (
                    <div key={event.id} className="flex items-start gap-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800">
                      <event.icon className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5" />
                      <div>
                        <h5 className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                          {event.label}
                        </h5>
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          {event.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Modals placeholder */}
        {showNewIntegration && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-lia-bg-secondary rounded-md max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary mb-4">
                  Nova Integração
                </h3>
                {/* Form for new integration */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                      Plataforma
                    </label>
                    <select
                      value={newIntegration.type}
                      onChange={(e) => setNewIntegration({...newIntegration, type: e.target.value as 'slack' | 'teams'})}
                      className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary"
                    >
                      <option value="slack">Slack</option>
                      <option value="teams">Microsoft Teams</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                      Nome da Integração
                    </label>
                    <input
                      type="text"
                      value={newIntegration.name}
                      onChange={(e) => setNewIntegration({...newIntegration, name: e.target.value})}
                      placeholder="Ex: Canal #recrutamento"
                      className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                      Webhook URL
                    </label>
                    <input
                      type="url"
                      value={newIntegration.webhookUrl}
                      onChange={(e) => setNewIntegration({...newIntegration, webhookUrl: e.target.value})}
                      placeholder="https://hooks.slack.com/services/..."
                      className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                      Eventos para Notificar
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {availableEvents.map((event) => (
                        <label key={event.id} className="flex items-center gap-2 p-2 border border-lia-border-subtle dark:border-lia-border-subtle rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                          <input
                            type="checkbox"
                            checked={newIntegration.events.includes(event.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setNewIntegration({
                                  ...newIntegration,
                                  events: [...newIntegration.events, event.id]
                                })
                              } else {
                                setNewIntegration({
                                  ...newIntegration,
                                  events: newIntegration.events.filter(ev => ev !== event.id)
                                })
                              }
                            }}
                            className="rounded-md border-lia-border-default"
                          />
                          <event.icon className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                          <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">{event.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button
                    onClick={() => {
                      // Save new integration
                      const integration: Integration = {
                        id: Date.now().toString(),
                        name: newIntegration.name,
                        type: newIntegration.type,
                        status: 'active',
                        icon: newIntegration.type === 'slack' ? Slack : MessageSquare,
                        color: newIntegration.type === 'slack' ? 'bg-wedo-purple/15 text-wedo-purple' : 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary',
                        webhookUrl: newIntegration.webhookUrl,
                        channels: newIntegration.channels,
                        events: newIntegration.events,
                        lastActivity: new Date().toISOString(),
                        messagesCount: 0,
                        errorCount: 0,
                        createdAt: new Date().toISOString(),
                        createdBy: 'Ana Silva'
                      }
                      setIntegrations([...integrations, integration])
                      setShowNewIntegration(false)
                      setNewIntegration({
                        name: '',
                        type: 'slack',
                        webhookUrl: '',
                        channels: [''],
                        events: []
                      })
                    }}
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
                  >
                    Criar Integração
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowNewIntegration(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
