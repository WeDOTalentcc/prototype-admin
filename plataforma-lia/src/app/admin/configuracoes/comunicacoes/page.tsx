"use client"

import React, { useState, useEffect, useCallback } from "react"
import { toast } from "sonner"
import { CheckCircle, AlertCircle } from "lucide-react"

import {
  SystemTemplate,
  ApiTemplate,
  WebhookConfig,
  ApiWebhook,
  WebhookLog,
  WebhookEvent,
  GlobalPolicy,
  ApiPolicy,
  PolicyType,
  PolicyScope,
  TechnicalAlert,
  AutomationRule,
  ApiAutomation,
  CommunicationLogEntry,
  ApiCommunication,
  MatrixEntry,
  MatrixModule,
  ApiMatrixEntry,
  TemplateChannelFilter,
  HistoryChannelFilter,
  HistoryStatusFilter,
  HistoryPeriodFilter
} from './components/types'

import {
  tabs,
  moduleLabels,
  defaultAutomations
} from './components/constants'

import {
  mapApiTemplateToLocal,
  mapApiWebhookToLocal,
  mapApiPolicyToLocal,
  mapApiAutomationToLocal,
  mapApiCommunicationToLocal,
  mapApiMatrixEntryToLocal
} from './components/mappers'

import { TemplatesSection } from './components/TemplatesSection'
import { WebhooksSection } from './components/WebhooksSection'
import { PoliciesSection } from './components/PoliciesSection'
import { AlertsSection } from './components/AlertsSection'
import { AutomationsSection } from './components/AutomationsSection'
import { MatrixSection } from './components/MatrixSection'
import { BriefingsSection } from './components/BriefingsSection'
import { HistorySection } from './components/HistorySection'

export default function AdminComunicacoesPage() {
  const [activeTab, setActiveTab] = useState('templates')
  const [loading, setLoading] = useState(false)
  const [templatesLoading, setTemplatesLoading] = useState(true)
  const [savingTemplate, setSavingTemplate] = useState(false)
  const [publishingTemplate, setPublishingTemplate] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [systemTemplates, setSystemTemplates] = useState<SystemTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<SystemTemplate | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<SystemTemplate | null>(null)
  const [templateChannelFilter, setTemplateChannelFilter] = useState<TemplateChannelFilter>('email')
  const [showHtmlView, setShowHtmlView] = useState(false)

  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([])
  const [webhooksLoading, setWebhooksLoading] = useState(true)
  const [editingWebhook, setEditingWebhook] = useState<WebhookConfig | null>(null)
  const [savingWebhook, setSavingWebhook] = useState(false)
  const [testingWebhook, setTestingWebhook] = useState<string | null>(null)
  const [showWebhookSecret, setShowWebhookSecret] = useState<string | null>(null)
  const [selectedWebhookForLogs, setSelectedWebhookForLogs] = useState<WebhookConfig | null>(null)
  const [webhookLogs, setWebhookLogs] = useState<WebhookLog[]>([])
  const [webhookLogsLoading, setWebhookLogsLoading] = useState(false)
  const [availableEvents, setAvailableEvents] = useState<WebhookEvent[]>([])
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [webhookHeaderKey, setWebhookHeaderKey] = useState('')
  const [webhookHeaderValue, setWebhookHeaderValue] = useState('')

  const [policies, setPolicies] = useState<GlobalPolicy[]>([])
  const [policiesLoading, setPoliciesLoading] = useState(true)
  const [policyTypes, setPolicyTypes] = useState<PolicyType[]>([])
  const [policyScopes, setPolicyScopes] = useState<PolicyScope[]>([])
  const [editingPolicy, setEditingPolicy] = useState<GlobalPolicy | null>(null)
  const [savingPolicy, setSavingPolicy] = useState(false)
  const [showCreatePolicyModal, setShowCreatePolicyModal] = useState(false)
  const [newPolicy, setNewPolicy] = useState<{
    name: string
    description: string
    policy_type: string
    value: Record<string, unknown>
    scope: string
  }>({
    name: '',
    description: '',
    policy_type: 'rate_limit',
    value: { limit: 100, period: 'day' },
    scope: 'company'
  })

  const [technicalAlerts, setTechnicalAlerts] = useState<TechnicalAlert[]>([])
  const [technicalAlertsLoading, setTechnicalAlertsLoading] = useState(true)
  const [savingTechnicalAlerts, setSavingTechnicalAlerts] = useState(false)
  const [technicalAlertsHasChanges, setTechnicalAlertsHasChanges] = useState(false)

  const [automations, setAutomations] = useState<AutomationRule[]>([])
  const [automationsLoading, setAutomationsLoading] = useState(true)
  const [togglingAutomation, setTogglingAutomation] = useState<string | null>(null)
  const [selectedAutomation, setSelectedAutomation] = useState<AutomationRule | null>(null)

  const [communicationLogs, setCommunicationLogs] = useState<CommunicationLogEntry[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyTotal, setHistoryTotal] = useState(0)
  const [historyPeriodFilter, setHistoryPeriodFilter] = useState<HistoryPeriodFilter>('7days')
  const [historyChannelFilter, setHistoryChannelFilter] = useState<HistoryChannelFilter>('all')
  const [historyStatusFilter, setHistoryStatusFilter] = useState<HistoryStatusFilter>('all')
  const [historyTypeFilter, setHistoryTypeFilter] = useState<string>('all')
  const [historySearch, setHistorySearch] = useState('')
  const [historyPage, setHistoryPage] = useState(1)
  const historyPerPage = 10

  const [matrixModules, setMatrixModules] = useState<MatrixModule[]>([])
  const [matrixLoading, setMatrixLoading] = useState(false)
  const [selectedMatrixModule, setSelectedMatrixModule] = useState<string | null>(null)
  const [updatingMatrixEntry, setUpdatingMatrixEntry] = useState<string | null>(null)
  const [seedingMatrix, setSeedingMatrix] = useState(false)

  const showSuccess = (message: string) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  const showError = (message: string) => {
    setError(message)
    setTimeout(() => setError(null), 5000)
  }

  const fetchTemplates = useCallback(async () => {
    setTemplatesLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/backend-proxy/email-templates?channel=${templateChannelFilter}`)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || 'Erro ao carregar templates')
      }
      const data = await response.json()
      const templates = (data.items || []).map(mapApiTemplateToLocal)
      setSystemTemplates(templates)
    } catch (err) {
      console.error('Error fetching templates:', err)
      showError(err instanceof Error ? err.message : 'Erro ao carregar templates')
    } finally {
      setTemplatesLoading(false)
    }
  }, [templateChannelFilter])

  const seedDefaultAutomations = useCallback(async () => {
    const seedAutomations = [
      { name: 'Lembrete Triagem 24h', description: 'Envia lembrete por email quando candidato não completa triagem em 24h', trigger_type: 'no_response_48h', action_type: 'send_email', action_config: { template_id: 'tpl-screening-reminder' }, conditions: [{ field: 'screening_status', operator: 'equals', value: 'pending' }], is_active: true, priority: 'normal' },
      { name: 'Lembrete Entrevista 24h', description: 'Envia lembrete por email/WhatsApp 24h antes da entrevista', trigger_type: 'interview_scheduled', action_type: 'send_email', action_config: { template_id: 'tpl-interview-reminder-24h' }, conditions: [{ field: 'time_before', operator: 'equals', value: '24h' }], is_active: true, priority: 'normal' },
      { name: 'Confirmação de Candidatura', description: 'Envia confirmação automática quando CV é recebido', trigger_type: 'candidate_applied', action_type: 'send_email', action_config: { template_id: 'tpl-application-confirmation' }, conditions: [], is_active: true, priority: 'normal' },
      { name: 'Solicitação de Feedback', description: 'Solicita feedback do entrevistador 48h após entrevista', trigger_type: 'feedback_received', action_type: 'send_email', action_config: { template_id: 'tpl-feedback-request' }, conditions: [{ field: 'feedback_status', operator: 'equals', value: 'pending' }], is_active: true, priority: 'normal' }
    ]
    for (const automation of seedAutomations) {
      try {
        await fetch('/api/backend-proxy/automations?company_id=admin_company', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(automation) })
      } catch (err) { console.error('Error seeding automation:', err) }
    }
  }, [])

  const fetchAutomations = useCallback(async () => {
    setAutomationsLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/automations?company_id=admin_company')
      if (!response.ok) throw new Error('Erro ao carregar automações')
      const data = await response.json()
      setAutomations((data.data?.automations || []).map(mapApiAutomationToLocal))
    } catch (err) {
      console.error('Error fetching automations:', err)
      setAutomations([])
    } finally {
      setAutomationsLoading(false)
    }
  }, [])

  const handleSeedDefaultAutomations = useCallback(async () => {
    setAutomationsLoading(true)
    try {
      await seedDefaultAutomations()
      const response = await fetch('/api/backend-proxy/automations?company_id=admin_company')
      if (response.ok) {
        const data = await response.json()
        setAutomations((data.data?.automations || []).map(mapApiAutomationToLocal))
      }
      showSuccess('Automações padrão criadas com sucesso!')
    } catch (err) {
      showError('Erro ao criar automações padrão')
    } finally {
      setAutomationsLoading(false)
    }
  }, [seedDefaultAutomations])

  const fetchCommunicationHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('company_id', 'admin_company')
      params.set('limit', String(historyPerPage))
      params.set('offset', String((historyPage - 1) * historyPerPage))
      if (historyChannelFilter !== 'all') params.set('channel', historyChannelFilter)
      if (historyStatusFilter !== 'all') params.set('status', historyStatusFilter)
      if (historyTypeFilter !== 'all') params.set('communication_type', historyTypeFilter)
      
      const response = await fetch(`/api/backend-proxy/communications?${params.toString()}`)
      if (!response.ok) throw new Error('Erro ao carregar histórico')
      
      const data = await response.json()
      const responseData = data.data || data
      setCommunicationLogs((responseData.communications || []).map(mapApiCommunicationToLocal))
      setHistoryTotal(responseData.total || 0)
    } catch (err) {
      console.error('Error fetching communication history:', err)
      setCommunicationLogs([])
      setHistoryTotal(0)
    } finally {
      setHistoryLoading(false)
    }
  }, [historyPage, historyChannelFilter, historyStatusFilter, historyTypeFilter])

  const fetchWebhooks = useCallback(async () => {
    setWebhooksLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/webhooks')
      if (!response.ok) throw new Error('Erro ao carregar webhooks')
      const data = await response.json()
      setWebhooks((data.webhooks || data.data?.webhooks || []).map(mapApiWebhookToLocal))
    } catch (err) {
      console.error('Error fetching webhooks:', err)
      setWebhooks([])
    } finally {
      setWebhooksLoading(false)
    }
  }, [])

  const fetchAvailableEvents = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/webhooks/events')
      if (response.ok) {
        const data = await response.json()
        setAvailableEvents(data.events || [])
      }
    } catch (err) { console.error('Error fetching available events:', err) }
  }, [])

  const fetchWebhookLogs = useCallback(async (webhookId: string) => {
    setWebhookLogsLoading(true)
    try {
      const response = await fetch(`/api/backend-proxy/webhooks/${webhookId}/logs?limit=50`)
      if (response.ok) {
        const data = await response.json()
        setWebhookLogs(data.logs || data.data?.logs || [])
      }
    } catch (err) {
      console.error('Error fetching webhook logs:', err)
      setWebhookLogs([])
    } finally {
      setWebhookLogsLoading(false)
    }
  }, [])

  const fetchPolicies = useCallback(async () => {
    setPoliciesLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/policies')
      if (!response.ok) throw new Error('Erro ao carregar políticas')
      const data = await response.json()
      setPolicies((data.data?.policies || []).map(mapApiPolicyToLocal))
    } catch (err) {
      console.error('Error fetching policies:', err)
      setPolicies([])
    } finally {
      setPoliciesLoading(false)
    }
  }, [])

  const fetchPolicyTypes = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/policies/types')
      if (response.ok) {
        const data = await response.json()
        setPolicyTypes(data.types || [])
        setPolicyScopes(data.scopes || [])
      }
    } catch (err) { console.error('Error fetching policy types:', err) }
  }, [])

  const fetchTechnicalAlerts = useCallback(async () => {
    setTechnicalAlertsLoading(true)
    try {
      const response = await fetch('/api/backend-proxy/alerts/config', { headers: { 'X-Company-ID': 'admin_company' } })
      if (response.ok) {
        const data = await response.json()
        setTechnicalAlerts(data.technicalAlerts || [])
        setTechnicalAlertsHasChanges(false)
      }
    } catch (err) {
      console.error('Error fetching technical alerts:', err)
    } finally {
      setTechnicalAlertsLoading(false)
    }
  }, [])

  const saveTechnicalAlerts = async () => {
    setSavingTechnicalAlerts(true)
    try {
      const response = await fetch('/api/backend-proxy/alerts/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-Company-ID': 'admin_company' },
        body: JSON.stringify({ alerts: technicalAlerts.map(a => ({ id: a.id, name: a.name, description: a.description, severity: a.severity, enabled: a.enabled, channels: a.channels, threshold: a.threshold, thresholdUnit: a.thresholdUnit })), briefing_frequency: 'daily' })
      })
      if (response.ok) {
        setTechnicalAlertsHasChanges(false)
        toast.success('Alertas técnicos salvos com sucesso!')
      }
    } catch (err) {
      toast.error('Erro ao salvar alertas técnicos')
    } finally {
      setSavingTechnicalAlerts(false)
    }
  }

  const handleToggleAlert = (id: string) => {
    setTechnicalAlerts(prev => prev.map(a => a.id === id ? { ...a, enabled: !a.enabled } : a))
    setTechnicalAlertsHasChanges(true)
  }

  const handleToggleAlertChannel = (alertId: string, channel: 'email' | 'slack' | 'webhook') => {
    setTechnicalAlerts(prev => prev.map(a => {
      if (a.id !== alertId) return a
      const channels = a.channels.includes(channel) ? a.channels.filter(c => c !== channel) : [...a.channels, channel]
      return { ...a, channels }
    }))
    setTechnicalAlertsHasChanges(true)
  }

  const handleUpdateAlertThreshold = (alertId: string, threshold: number) => {
    setTechnicalAlerts(prev => prev.map(a => a.id === alertId ? { ...a, threshold } : a))
    setTechnicalAlertsHasChanges(true)
  }

  const fetchMatrixEntries = useCallback(async () => {
    setMatrixLoading(true)
    try {
      const params = new URLSearchParams()
      if (selectedMatrixModule) params.set('module', selectedMatrixModule)
      const response = await fetch(`/api/backend-proxy/communication-matrix?${params.toString()}`)
      if (!response.ok) throw new Error('Erro ao carregar matriz')
      const data = await response.json()
      if (data.success && data.data?.modules) {
        const modules: MatrixModule[] = data.data.modules.map((mod: any) => ({
          module: mod.module,
          label: mod.label || moduleLabels[mod.module]?.label || mod.module,
          description: mod.description || '',
          icon: mod.icon || 'folder',
          entries: (mod.entries || []).map(mapApiMatrixEntryToLocal),
          totalEntries: mod.total_entries || mod.entries?.length || 0,
          activeEntries: mod.active_entries || 0
        }))
        setMatrixModules(modules)
      }
    } catch (err) {
      console.error('Error fetching matrix entries:', err)
    } finally {
      setMatrixLoading(false)
    }
  }, [selectedMatrixModule])

  const handleUpdateMatrixEntry = async (entryId: string, updates: Partial<{ channels: string[], is_automatic: boolean, template_id: string | null, requires_approval: boolean, is_active: boolean }>) => {
    setUpdatingMatrixEntry(entryId)
    try {
      const response = await fetch(`/api/backend-proxy/communication-matrix/${entryId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(updates) })
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.data) {
          const updatedEntry = mapApiMatrixEntryToLocal(data.data)
          setMatrixModules(prev => prev.map(mod => ({
            ...mod,
            entries: mod.entries.map(e => e.id === updatedEntry.id ? updatedEntry : e),
            activeEntries: mod.entries.filter(e => e.id === updatedEntry.id ? updatedEntry.isActive : e.isActive).length
          })))
          toast.success('Configuração atualizada!')
        }
      }
    } catch (err) {
      console.error('Error updating matrix entry:', err)
    } finally {
      setUpdatingMatrixEntry(null)
    }
  }

  const handleToggleMatrixChannel = async (entry: MatrixEntry, channel: string) => {
    const newChannels = entry.channels.includes(channel) ? entry.channels.filter(c => c !== channel) : [...entry.channels, channel]
    await handleUpdateMatrixEntry(entry.id, { channels: newChannels })
  }

  const handleToggleMatrixActive = async (entry: MatrixEntry) => {
    await handleUpdateMatrixEntry(entry.id, { is_active: !entry.isActive })
  }

  const handleSeedMatrix = async () => {
    setSeedingMatrix(true)
    try {
      const response = await fetch('/api/backend-proxy/communication-matrix/seed', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ confirm: true }) })
      if (response.ok) {
        toast.success('Matriz populada com dados padrão!')
        fetchMatrixEntries()
      }
    } catch (err) {
      toast.error('Erro ao popular matriz')
    } finally {
      setSeedingMatrix(false)
    }
  }

  useEffect(() => {
    fetchTemplates()
    fetchAutomations()
    fetchWebhooks()
    fetchAvailableEvents()
    fetchPolicies()
    fetchPolicyTypes()
    fetchTechnicalAlerts()
  }, [fetchTemplates, fetchAutomations, fetchWebhooks, fetchAvailableEvents, fetchPolicies, fetchPolicyTypes, fetchTechnicalAlerts])

  useEffect(() => {
    if (activeTab === 'history') fetchCommunicationHistory()
    if (activeTab === 'matrix') fetchMatrixEntries()
    if (activeTab === 'alerts') fetchTechnicalAlerts()
  }, [activeTab, fetchCommunicationHistory, fetchMatrixEntries, fetchTechnicalAlerts])

  const handleCreateTemplate = async () => {
    const newTemplate: SystemTemplate = {
      id: '', name: 'Novo Template de Sistema', category: 'system', subject: '', body: '', variables: [], isActive: false, channel: templateChannelFilter as 'email' | 'whatsapp', lastUpdated: new Date().toISOString().split('T')[0], usedByCompanies: 0
    }
    setEditingTemplate(newTemplate)
    setSelectedTemplate(null)
  }

  const handleSaveTemplate = async () => {
    if (!editingTemplate) return
    setSavingTemplate(true)
    try {
      const isNew = !editingTemplate.id
      const payload = { name: editingTemplate.name, subject: editingTemplate.subject || null, body_html: editingTemplate.body, body_text: editingTemplate.body.replace(/<[^>]*>/g, ''), category: editingTemplate.category, channel: editingTemplate.channel, variables: editingTemplate.variables, is_active: editingTemplate.isActive }
      const response = isNew
        ? await fetch('/api/backend-proxy/email-templates', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        : await fetch(`/api/backend-proxy/email-templates/${editingTemplate.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (!response.ok) throw new Error('Erro ao salvar template')
      const savedTemplate = await response.json()
      const mappedTemplate = mapApiTemplateToLocal(savedTemplate)
      if (isNew) setSystemTemplates(prev => [mappedTemplate, ...prev])
      else setSystemTemplates(prev => prev.map(t => t.id === mappedTemplate.id ? mappedTemplate : t))
      setEditingTemplate(null)
      setSelectedTemplate(mappedTemplate)
      showSuccess(isNew ? 'Template criado com sucesso!' : 'Template atualizado com sucesso!')
    } catch (err) {
      showError('Erro ao salvar template')
    } finally {
      setSavingTemplate(false)
    }
  }

  const handleDeleteTemplate = async (id: string) => {
    if (!confirm('Tem certeza que deseja remover este template?')) return
    try {
      const response = await fetch(`/api/backend-proxy/email-templates/${id}`, { method: 'DELETE' })
      if (response.ok) {
        setSystemTemplates(prev => prev.filter(t => t.id !== id))
        if (selectedTemplate?.id === id) setSelectedTemplate(null)
        showSuccess('Template removido com sucesso!')
      }
    } catch (err) {
      showError('Erro ao remover template')
    }
  }

  const handleToggleTemplateActive = async (id: string) => {
    const template = systemTemplates.find(t => t.id === id)
    if (!template) return
    try {
      const response = await fetch(`/api/backend-proxy/email-templates/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: !template.isActive }) })
      if (response.ok) setSystemTemplates(prev => prev.map(t => t.id === id ? { ...t, isActive: !t.isActive } : t))
    } catch (err) {
      showError('Erro ao atualizar template')
    }
  }

  const handlePublishTemplate = async (id: string) => {
    setPublishingTemplate(id)
    try {
      const response = await fetch(`/api/backend-proxy/email-templates/${id}/publish`, { method: 'POST' })
      if (response.ok) {
        const result = await response.json()
        showSuccess(`Template publicado para ${result.companies_count} empresas!`)
      }
    } catch (err) {
      showError('Erro ao publicar template')
    } finally {
      setPublishingTemplate(null)
    }
  }

  const handleSaveWebhook = async () => {
    if (!editingWebhook) return
    setSavingWebhook(true)
    const isNew = !editingWebhook.id || editingWebhook.id.startsWith('new-')
    try {
      const payload = { name: editingWebhook.name, description: editingWebhook.description || null, url: editingWebhook.url, events: editingWebhook.events, headers: editingWebhook.headers || null, retry_count: editingWebhook.retryCount, timeout_seconds: editingWebhook.timeoutSeconds, is_active: editingWebhook.isActive }
      const response = isNew
        ? await fetch('/api/backend-proxy/webhooks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        : await fetch(`/api/backend-proxy/webhooks/${editingWebhook.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (response.ok) {
        const savedWebhook = await response.json()
        const webhookData = savedWebhook.webhook || savedWebhook.data?.webhook || savedWebhook
        const mappedWebhook = mapApiWebhookToLocal(webhookData)
        if (isNew) setWebhooks(prev => [mappedWebhook, ...prev])
        else setWebhooks(prev => prev.map(w => w.id === mappedWebhook.id ? mappedWebhook : w))
        setEditingWebhook(null)
        toast.success(isNew ? 'Webhook criado!' : 'Webhook atualizado!')
      }
    } catch (err) {
      toast.error('Erro ao salvar webhook')
    } finally {
      setSavingWebhook(false)
    }
  }

  const handleDeleteWebhook = async (id: string) => {
    if (!confirm('Excluir webhook?')) return
    try {
      const response = await fetch(`/api/backend-proxy/webhooks/${id}`, { method: 'DELETE' })
      if (response.ok) {
        setWebhooks(prev => prev.filter(w => w.id !== id))
        toast.success('Webhook excluído!')
      }
    } catch (err) {
      toast.error('Erro ao excluir webhook')
    }
  }

  const handleToggleWebhookActive = async (id: string) => {
    const webhook = webhooks.find(w => w.id === id)
    if (!webhook) return
    const newIsActive = !webhook.isActive
    setWebhooks(prev => prev.map(w => w.id === id ? { ...w, isActive: newIsActive } : w))
    try {
      await fetch(`/api/backend-proxy/webhooks/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: newIsActive }) })
      toast.success(newIsActive ? 'Webhook ativado!' : 'Webhook desativado!')
    } catch (err) {
      setWebhooks(prev => prev.map(w => w.id === id ? { ...w, isActive: !newIsActive } : w))
    }
  }

  const handleTestWebhook = async (webhookId: string) => {
    setTestingWebhook(webhookId)
    try {
      const response = await fetch(`/api/backend-proxy/webhooks/${webhookId}/test`, { method: 'POST' })
      const data = await response.json()
      if (data.success) toast.success('Webhook testado!')
      else toast.error('Falha no teste')
    } catch (err) {
      toast.error('Erro ao testar webhook')
    } finally {
      setTestingWebhook(null)
    }
  }

  const handleViewWebhookLogs = async (webhook: WebhookConfig) => {
    setSelectedWebhookForLogs(webhook)
    setShowLogsModal(true)
    await fetchWebhookLogs(webhook.id)
  }

  const handleCreateWebhook = () => {
    setEditingWebhook({ id: `new-${Date.now()}`, name: '', url: '', description: '', events: [], isActive: true, secret: '', headers: {}, retryCount: 3, timeoutSeconds: 30, successRate: 100 })
    setWebhookHeaderKey('')
    setWebhookHeaderValue('')
  }

  const handleAddWebhookHeader = () => {
    if (!editingWebhook || !webhookHeaderKey.trim()) return
    setEditingWebhook({ ...editingWebhook, headers: { ...editingWebhook.headers, [webhookHeaderKey.trim()]: webhookHeaderValue } })
    setWebhookHeaderKey('')
    setWebhookHeaderValue('')
  }

  const handleRemoveWebhookHeader = (key: string) => {
    if (!editingWebhook?.headers) return
    const newHeaders = { ...editingWebhook.headers }
    delete newHeaders[key]
    setEditingWebhook({ ...editingWebhook, headers: newHeaders })
  }

  const handleToggleWebhookEvent = (eventName: string) => {
    if (!editingWebhook) return
    const events = editingWebhook.events.includes(eventName) ? editingWebhook.events.filter(e => e !== eventName) : [...editingWebhook.events, eventName]
    setEditingWebhook({ ...editingWebhook, events })
  }

  const handleCreatePolicy = async () => {
    if (!newPolicy.name.trim()) return
    setSavingPolicy(true)
    try {
      const response = await fetch('/api/backend-proxy/policies', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: newPolicy.name, description: newPolicy.description || null, policy_type: newPolicy.policy_type, value: newPolicy.value, scope: newPolicy.scope, is_active: true }) })
      if (response.ok) {
        const data = await response.json()
        setPolicies(prev => [mapApiPolicyToLocal(data.data), ...prev])
        setShowCreatePolicyModal(false)
        setNewPolicy({ name: '', description: '', policy_type: 'rate_limit', value: { limit: 100, period: 'day' }, scope: 'company' })
        toast.success('Política criada!')
      }
    } catch (err) {
      toast.error('Erro ao criar política')
    } finally {
      setSavingPolicy(false)
    }
  }

  const handleUpdatePolicy = async (policy: GlobalPolicy, updates: GlobalPolicy) => {
    setSavingPolicy(true)
    try {
      const payload: Record<string, unknown> = {}
      if (updates.name !== undefined) payload.name = updates.name
      if (updates.description !== undefined) payload.description = updates.description
      if (updates.isActive !== undefined) payload.is_active = updates.isActive
      if (updates.value !== undefined) payload.value = updates.value
      if (updates.type !== undefined) payload.policy_type = updates.type
      if (updates.scope !== undefined) payload.scope = updates.scope
      const response = await fetch(`/api/backend-proxy/policies/${policy.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (response.ok) {
        const data = await response.json()
        setPolicies(prev => prev.map(p => p.id === data.data.id ? mapApiPolicyToLocal(data.data) : p))
        setEditingPolicy(null)
        toast.success('Política atualizada!')
      }
    } catch (err) {
      toast.error('Erro ao atualizar política')
    } finally {
      setSavingPolicy(false)
    }
  }

  const handleDeletePolicy = async (policyId: string) => {
    if (!confirm('Excluir política?')) return
    try {
      const response = await fetch(`/api/backend-proxy/policies/${policyId}`, { method: 'DELETE' })
      if (response.ok) {
        setPolicies(prev => prev.filter(p => p.id !== policyId))
        toast.success('Política excluída!')
      }
    } catch (err) {
      toast.error('Erro ao excluir política')
    }
  }

  const handleTogglePolicyActiveApi = async (policy: GlobalPolicy) => {
    const newIsActive = !policy.isActive
    setPolicies(prev => prev.map(p => p.id === policy.id ? { ...p, isActive: newIsActive } : p))
    try {
      await fetch(`/api/backend-proxy/policies/${policy.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: newIsActive }) })
      toast.success(newIsActive ? 'Política ativada!' : 'Política desativada!')
    } catch (err) {
      setPolicies(prev => prev.map(p => p.id === policy.id ? { ...p, isActive: !newIsActive } : p))
    }
  }

  const handleToggleAutomationActive = async (id: string) => {
    const automation = automations.find(a => a.id === id)
    if (!automation) return
    setTogglingAutomation(id)
    const newIsActive = !automation.isActive
    setAutomations(prev => prev.map(a => a.id === id ? { ...a, isActive: newIsActive } : a))
    try {
      const response = await fetch(`/api/backend-proxy/automations/${id}?company_id=admin_company`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: newIsActive, name: automation.name }) })
      if (response.ok) showSuccess(newIsActive ? 'Automação ativada!' : 'Automação desativada!')
      else throw new Error()
    } catch (err) {
      setAutomations(prev => prev.map(a => a.id === id ? { ...a, isActive: !newIsActive } : a))
      showError('Erro ao atualizar automação')
    } finally {
      setTogglingAutomation(null)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
          Comunicações
        </h1>
        <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
          Gerenciamento global de templates, webhooks e políticas de comunicação
        </p>
      </div>

      {successMessage && (
        <div className="mb-4 px-3 py-2 rounded-md flex items-center gap-2" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', borderColor: 'rgba(96, 190, 209, 0.3)', color: 'var(--wedo-cyan-dark)', border: '1px solid' }}>
          <CheckCircle className="w-4 h-4 text-gray-700" />
          <span className="text-sm">{successMessage}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <div className="flex gap-2 mb-6 border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
        {tabs.map(tab => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative ${isActive ? 'text-gray-700 dark:text-gray-300' : ''}`}
              style={!isActive ? { color: 'var(--eleven-text-secondary)' } : {}}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {isActive && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-50" />}
            </button>
          )
        })}
      </div>

      {activeTab === 'templates' && (
        <TemplatesSection
          systemTemplates={systemTemplates}
          templateChannelFilter={templateChannelFilter}
          setTemplateChannelFilter={setTemplateChannelFilter}
          selectedTemplate={selectedTemplate}
          setSelectedTemplate={setSelectedTemplate}
          editingTemplate={editingTemplate}
          setEditingTemplate={setEditingTemplate}
          templatesLoading={templatesLoading}
          savingTemplate={savingTemplate}
          publishingTemplate={publishingTemplate}
          showHtmlView={showHtmlView}
          setShowHtmlView={setShowHtmlView}
          fetchTemplates={fetchTemplates}
          handleCreateTemplate={handleCreateTemplate}
          handleSaveTemplate={handleSaveTemplate}
          handleDeleteTemplate={handleDeleteTemplate}
          handleToggleTemplateActive={handleToggleTemplateActive}
          handlePublishTemplate={handlePublishTemplate}
        />
      )}

      {activeTab === 'matrix' && (
        <MatrixSection
          matrixModules={matrixModules}
          matrixLoading={matrixLoading}
          selectedMatrixModule={selectedMatrixModule}
          setSelectedMatrixModule={setSelectedMatrixModule}
          updatingMatrixEntry={updatingMatrixEntry}
          seedingMatrix={seedingMatrix}
          fetchMatrixEntries={fetchMatrixEntries}
          handleSeedMatrix={handleSeedMatrix}
          handleToggleMatrixActive={handleToggleMatrixActive}
          handleToggleMatrixChannel={handleToggleMatrixChannel}
        />
      )}

      {activeTab === 'briefings' && <BriefingsSection />}

      {activeTab === 'webhooks' && (
        <WebhooksSection
          webhooks={webhooks}
          webhooksLoading={webhooksLoading}
          savingWebhook={savingWebhook}
          testingWebhook={testingWebhook}
          editingWebhook={editingWebhook}
          setEditingWebhook={setEditingWebhook}
          showWebhookSecret={showWebhookSecret}
          setShowWebhookSecret={setShowWebhookSecret}
          showLogsModal={showLogsModal}
          setShowLogsModal={setShowLogsModal}
          selectedWebhookForLogs={selectedWebhookForLogs}
          setSelectedWebhookForLogs={setSelectedWebhookForLogs}
          webhookLogs={webhookLogs}
          setWebhookLogs={setWebhookLogs}
          webhookLogsLoading={webhookLogsLoading}
          availableEvents={availableEvents}
          webhookHeaderKey={webhookHeaderKey}
          setWebhookHeaderKey={setWebhookHeaderKey}
          webhookHeaderValue={webhookHeaderValue}
          setWebhookHeaderValue={setWebhookHeaderValue}
          fetchWebhooks={fetchWebhooks}
          handleCreateWebhook={handleCreateWebhook}
          handleSaveWebhook={handleSaveWebhook}
          handleDeleteWebhook={handleDeleteWebhook}
          handleToggleWebhookActive={handleToggleWebhookActive}
          handleTestWebhook={handleTestWebhook}
          handleViewWebhookLogs={handleViewWebhookLogs}
          handleToggleWebhookEvent={handleToggleWebhookEvent}
          handleAddWebhookHeader={handleAddWebhookHeader}
          handleRemoveWebhookHeader={handleRemoveWebhookHeader}
        />
      )}

      {activeTab === 'policies' && (
        <PoliciesSection
          policies={policies}
          policiesLoading={policiesLoading}
          savingPolicy={savingPolicy}
          editingPolicy={editingPolicy}
          setEditingPolicy={setEditingPolicy}
          showCreatePolicyModal={showCreatePolicyModal}
          setShowCreatePolicyModal={setShowCreatePolicyModal}
          newPolicy={newPolicy}
          setNewPolicy={setNewPolicy}
          policyTypes={policyTypes}
          policyScopes={policyScopes}
          fetchPolicies={fetchPolicies}
          handleCreatePolicy={handleCreatePolicy}
          handleUpdatePolicy={handleUpdatePolicy}
          handleDeletePolicy={handleDeletePolicy}
          handleTogglePolicyActiveApi={handleTogglePolicyActiveApi}
        />
      )}

      {activeTab === 'alerts' && (
        <AlertsSection
          technicalAlerts={technicalAlerts}
          technicalAlertsLoading={technicalAlertsLoading}
          savingTechnicalAlerts={savingTechnicalAlerts}
          technicalAlertsHasChanges={technicalAlertsHasChanges}
          fetchTechnicalAlerts={fetchTechnicalAlerts}
          saveTechnicalAlerts={saveTechnicalAlerts}
          handleToggleAlert={handleToggleAlert}
          handleToggleAlertChannel={handleToggleAlertChannel}
          handleUpdateAlertThreshold={handleUpdateAlertThreshold}
        />
      )}

      {activeTab === 'automations' && (
        <AutomationsSection
          automations={automations}
          automationsLoading={automationsLoading}
          selectedAutomation={selectedAutomation}
          setSelectedAutomation={setSelectedAutomation}
          togglingAutomation={togglingAutomation}
          fetchAutomations={fetchAutomations}
          handleToggleAutomationActive={handleToggleAutomationActive}
          handleSeedDefaultAutomations={handleSeedDefaultAutomations}
        />
      )}

      {activeTab === 'history' && (
        <HistorySection
          communicationLogs={communicationLogs}
          historyLoading={historyLoading}
          historySearch={historySearch}
          setHistorySearch={setHistorySearch}
          historyChannel={historyChannelFilter}
          setHistoryChannel={setHistoryChannelFilter}
          historyStatus={historyStatusFilter}
          setHistoryStatus={setHistoryStatusFilter}
          historyPeriod={historyPeriodFilter}
          setHistoryPeriod={setHistoryPeriodFilter}
          historyPage={historyPage}
          setHistoryPage={setHistoryPage}
          historyTotal={historyTotal}
          historyPerPage={historyPerPage}
          fetchCommunicationHistory={fetchCommunicationHistory}
        />
      )}
    </div>
  )
}
