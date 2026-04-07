"use client"

import { useState } from "react"
import {
  MessageSquare, UserCheck, CheckCircle, Users,
  MessageCircle, AtSign, Calendar, BarChart3
} from "lucide-react"
import type {
  Integration, NotificationTemplate, WebhookEvent, NewIntegrationForm, AvailableEvent
} from "./integrations-page.types"

const INITIAL_INTEGRATIONS: Integration[] = [

  {
    id: 'teams-rh',
    name: 'Equipe RH',
    type: 'teams',
    status: 'active',
    icon: MessageSquare,
    color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary',
    webhookUrl: 'https://outlook.office.com/webhook/xxxxx/IncomingWebhook/yyyyy',
    channels: ['RH Geral', 'Aprovações'],
    events: ['aprovacao_lote', 'candidato_final', 'relatorio_semanal'],
    lastActivity: '2025-03-15T09:15:00Z',
    messagesCount: 156,
    errorCount: 0,
    createdAt: '2025-02-01T14:00:00Z',
    createdBy: 'Carlos Mendes'
  },

]

const INITIAL_TEMPLATES: NotificationTemplate[] = [
  {
    id: 'novo-candidato',
    name: 'Novo Candidato',
    event: 'novo_candidato',
    title: '🎯 Novo candidato aplicou!',
    message: 'O candidato **{candidate_name}** se candidatou para a vaga **{job_title}**.\n\n📊 Score LIA: **{lia_score}%**\n📍 Localização: {location}\n⭐ Match: {match_score}%\n\n[Ver perfil completo]({candidate_url})',
    mentions: ['@channel'],
    active: true,
    integrations: ['teams-rh']
  },
  {
    id: 'aprovacao-candidato',
    name: 'Aprovação de Candidato',
    event: 'aprovacao',
    title: '✅ Candidato aprovado!',
    message: 'O candidato **{candidate_name}** foi aprovado para **{job_title}**!\n\n👤 Aprovado por: {approver_name}\n📅 Data: {approval_date}\n💬 Comentário: "{approval_comment}"\n\n🎉 Próximo passo: {next_step}',
    mentions: ['@here'],
    active: true,
    integrations: ['teams-rh']
  },
  {
    id: 'nova-nota',
    name: 'Nova Nota/Comentário',
    event: 'nova_nota',
    title: '💬 Nova nota adicionada',
    message: '**{author_name}** adicionou uma nota sobre **{candidate_name}**:\n\n"{note_content}"\n\n🏷️ Tags: {tags}\n📂 Categoria: {category}\n\n[Ver nota completa]({note_url})',
    mentions: [],
    active: true,
    integrations: ['teams-rh']
  },
  {
    id: 'mencao',
    name: 'Menção em Nota',
    event: 'mencao',
    title: '👋 Você foi mencionado!',
    message: '**{author_name}** mencionou você em uma nota sobre **{candidate_name}**:\n\n"{note_content}"\n\n[Responder]({note_url})',
    mentions: ['{mentioned_user}'],
    active: true,
    integrations: ['teams-rh']
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
]

const INITIAL_EVENTS: WebhookEvent[] = [
  {
    id: '1',
    integration: 'teams-rh',
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
    integration: 'teams-rh',
    event: 'entrevista_tecnica',
    status: 'failed',
    timestamp: '2025-03-15T12:00:00Z',
    payload: { candidate_name: 'Pedro Santos' },
    error: 'Webhook URL inválida'
  }
]

export const AVAILABLE_EVENTS: AvailableEvent[] = [
  { id: 'novo_candidato', label: 'Novo Candidato', icon: UserCheck, description: 'Quando um novo candidato se inscreve' },
  { id: 'aprovacao', label: 'Aprovação Individual', icon: CheckCircle, description: 'Quando um candidato é aprovado' },
  { id: 'aprovacao_lote', label: 'Aprovação em Lote', icon: Users, description: 'Quando múltiplos candidatos são processados' },
  { id: 'nova_nota', label: 'Nova Nota', icon: MessageCircle, description: 'Quando uma nota é adicionada' },
  { id: 'mencao', label: 'Menção', icon: AtSign, description: 'Quando alguém é mencionado em uma nota' },
  { id: 'entrevista_agendada', label: 'Entrevista Agendada', icon: Calendar, description: 'Quando uma entrevista é marcada' },
  { id: 'relatorio_semanal', label: 'Relatório Semanal', icon: BarChart3, description: 'Relatório automático semanal' }
]

export function useIntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>(INITIAL_INTEGRATIONS)
  const [templates, setTemplates] = useState<NotificationTemplate[]>(INITIAL_TEMPLATES)
  const [webhookEvents, setWebhookEvents] = useState<WebhookEvent[]>(INITIAL_EVENTS)
  const [showNewIntegration, setShowNewIntegration] = useState(false)
  const [showTemplateEditor, setShowTemplateEditor] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<NotificationTemplate | null>(null)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)
  const [showWebhookLogs, setShowWebhookLogs] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [testingIntegration, setTestingIntegration] = useState<string | null>(null)
  const [newIntegration, setNewIntegration] = useState<NewIntegrationForm>({
    name: '',
    type: 'teams',
    webhookUrl: '',
    channels: [''],
    events: []
  })

  const testIntegration = (integrationId: string) => {
    setTestingIntegration(integrationId)
    setTimeout(() => {
      setTestingIntegration(null)
      const testEvent: WebhookEvent = {
        id: Date.now().toString(),
        integration: integrationId,
        event: 'test',
        status: 'success',
        timestamp: new Date().toISOString(),
        payload: { test: true, message: 'Teste de conexão' },
        response: { ok: true, message: 'Teste enviado com sucesso!' }
      }
      setWebhookEvents(prev => [testEvent, ...prev])
    }, 2000)
  }

  const toggleIntegrationStatus = (integrationId: string) => {
    setIntegrations(prev => prev.map(integration =>
      integration.id === integrationId
        ? { ...integration, status: integration.status === 'active' ? 'inactive' : 'active' }
        : integration
    ))
  }

  const deleteIntegration = (integrationId: string) => {
    setIntegrations(prev => prev.filter(integration => integration.id !== integrationId))
  }

  const saveTemplate = (template: NotificationTemplate) => {
    if (template.id) {
      setTemplates(prev => prev.map(t => t.id === template.id ? template : t))
    } else {
      setTemplates(prev => [...prev, { ...template, id: Date.now().toString() }])
    }
    setShowTemplateEditor(false)
    setSelectedTemplate(null)
  }

  const createIntegration = () => {
    const integration: Integration = {
      id: Date.now().toString(),
      name: newIntegration.name,
      type: newIntegration.type,
      status: 'active',
      icon: MessageSquare,
      color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary',
      webhookUrl: newIntegration.webhookUrl,
      channels: newIntegration.channels,
      events: newIntegration.events,
      lastActivity: new Date().toISOString(),
      messagesCount: 0,
      errorCount: 0,
      createdAt: new Date().toISOString(),
      createdBy: 'Ana Silva'
    }
    setIntegrations(prev => [...prev, integration])
    setShowNewIntegration(false)
    setNewIntegration({ name: '', type: 'teams', webhookUrl: '', channels: [''], events: [] })
  }

  const filteredEvents = webhookEvents.filter(event => {
    if (filterStatus === 'all') return true
    return event.status === filterStatus
  })

  return {
    integrations,
    templates,
    webhookEvents,
    filteredEvents,
    showNewIntegration,
    setShowNewIntegration,
    showTemplateEditor,
    setShowTemplateEditor,
    selectedTemplate,
    setSelectedTemplate,
    selectedIntegration,
    setSelectedIntegration,
    showWebhookLogs,
    setShowWebhookLogs,
    filterStatus,
    setFilterStatus,
    testingIntegration,
    newIntegration,
    setNewIntegration,
    testIntegration,
    toggleIntegrationStatus,
    deleteIntegration,
    saveTemplate,
    createIntegration,
  }
}
