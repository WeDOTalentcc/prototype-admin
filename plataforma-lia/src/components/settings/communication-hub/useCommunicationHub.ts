import { useState, useMemo, useRef, useEffect } from "react"
import type { AlertConfig, EmailTemplate, AiResultModal } from './CommunicationHub.types'
import { DEFAULT_ALERTS, TEMPLATE_GROUPS } from './CommunicationHub.constants'

export function useCommunicationHub(activeSubsection?: string) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'templates')
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiResultModal, setAiResultModal] = useState<AiResultModal | null>(null)
  const bodyTextareaRef = useRef<HTMLTextAreaElement>(null)

  const [isGenerating, setIsGenerating] = useState(false)
  const [signature, setSignature] = useState(`{{recrutador_nome}} | {{cargo}}
{{empresa_nome}}
📧 {{email}} | 📱 {{telefone}}
🌐 {{website}}`)
  const [sendingHours, setSendingHours] = useState({ start: 8, end: 20 })
  const [respectHolidays, setRespectHolidays] = useState(true)
  const [respectWeekends, setRespectWeekends] = useState(true)
  const [maxMessagesPerDay, setMaxMessagesPerDay] = useState(3)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savingSettings, setSavingSettings] = useState(false)
  const [savingAlerts, setSavingAlerts] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  const [alerts, setAlerts] = useState<AlertConfig[]>(DEFAULT_ALERTS)
  const [briefingFrequency, setBriefingFrequency] = useState<'twice_daily' | 'daily' | 'weekly' | 'monthly'>('daily')
  const [channelFilter, setChannelFilter] = useState<'all' | 'email' | 'whatsapp'>('all')
  const [triggerTypeFilter, setTriggerTypeFilter] = useState<'all' | 'automatic' | 'manual' | 'both'>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['primeiro_contato', 'triagem', 'entrevista'])
  const [companyId, setCompanyId] = useState<string>('')

  const [isEditingSignature, setIsEditingSignature] = useState(false)
  const [isEditingSchedule, setIsEditingSchedule] = useState(false)
  const [isEditingAlerts, setIsEditingAlerts] = useState(false)

  const [weeklyDigestEnabled, setWeeklyDigestEnabled] = useState(true)
  const [savingWeeklyDigest, setSavingWeeklyDigest] = useState(false)

  const handleToggleWeeklyDigest = async () => {
    setSavingWeeklyDigest(true)
    const newValue = !weeklyDigestEnabled
    try {
      const res = await fetch("/api/backend-proxy/digest/weekly/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "default_user", enabled: newValue }),
      })
      if (res.ok) {
        setWeeklyDigestEnabled(newValue)
        setSuccessMessage(newValue ? "Resumo semanal ativado" : "Resumo semanal desativado")
        setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null) }, 3000)
      }
    } catch {
      setError("Erro ao atualizar preferência do resumo semanal")
      setTimeout(() => { if (isMountedRef.current) setError(null) }, 3000)
    } finally {
      setSavingWeeklyDigest(false)
    }
  }

  const handleChannelFilterChange = (channel: 'all' | 'email' | 'whatsapp') => {
    setChannelFilter(channel)
    setSelectedTemplate(null)
    setEditingTemplate(null)
  }

  const getTemplateGroup = (template: EmailTemplate): string => {
    const situation = template.situation?.toLowerCase() || ''
    for (const [groupKey, group] of Object.entries(TEMPLATE_GROUPS)) {
      if (group.situations.some(s => situation.includes(s) || s.includes(situation))) {
        return groupKey
      }
    }
    return 'outros'
  }

  const filteredTemplates = useMemo(() => {
    return templates.filter(template => {
      const matchesChannel = channelFilter === 'all' || template.channel === channelFilter
      const matchesTrigger = triggerTypeFilter === 'all' || template.trigger_type === triggerTypeFilter
      const matchesSearch = searchQuery === '' ||
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.subject?.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesChannel && matchesTrigger && matchesSearch
    })
  }, [templates, channelFilter, triggerTypeFilter, searchQuery])

  const groupedTemplates = useMemo(() => {
    const groups: Record<string, EmailTemplate[]> = {}
    Object.keys(TEMPLATE_GROUPS).forEach(key => {
      groups[key] = []
    })
    filteredTemplates.forEach(template => {
      const groupKey = getTemplateGroup(template)
      if (!groups[groupKey]) {
        groups[groupKey] = []
      }
      groups[groupKey].push(template)
    })
    return groups
  }, [filteredTemplates])

  const insertVariableAtCursor = (variable: string) => {
    if (!editingTemplate || !bodyTextareaRef.current) return

    const textarea = bodyTextareaRef.current
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = editingTemplate.body

    const newText = text.substring(0, start) + variable + text.substring(end)
    setEditingTemplate(prev => prev ? { ...prev, body: newText } : null)

    setTimeout(() => {
      textarea.focus()
      const newCursorPos = start + variable.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
    }, 0)
  }

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      let fetchedCompanyId = ''
      try {
        const profileRes = await fetch('/api/backend-proxy/company/profile')
        if (profileRes.ok) {
          const profileData = await profileRes.json()
          if (profileData && profileData.id) {
            fetchedCompanyId = profileData.id
            setCompanyId(fetchedCompanyId)
          }
        }
      } catch (_e) {
        // silently ignore profile fetch errors
      }

      const headers: HeadersInit = fetchedCompanyId
        ? { 'X-Company-ID': fetchedCompanyId }
        : {}

      const [templatesResponse, settingsResponse, alertsResponse] = await Promise.all([
        fetch(`/api/backend-proxy/email-templates?visibility=recruiter`),
        fetch('/api/backend-proxy/company/communication-settings', { headers }),
        fetch('/api/backend-proxy/alerts/config', { headers })
      ])

      if (templatesResponse.ok) {
        const result = await templatesResponse.json()
        const templatesArray = result.items || (Array.isArray(result) ? result : [])
        setTemplates(templatesArray.map((t: Record<string, unknown>) => ({
          id: t.id,
          name: t.name,
          category: t.category || 'followup',
          subject: t.subject || '',
          body: t.body || t.body_text || (t.body_html ? (t.body_html as string).replace(/<[^>]*>/g, '') : ''),
          variables: t.variables || [],
          isActive: t.is_active ?? true,
          lastUpdated: t.updated_at || t.last_updated || new Date().toISOString().split('T')[0],
          channel: t.channel || 'email',
          situation: t.situation || '',
          trigger_type: t.trigger_type || 'manual',
          used_in: t.used_in || [],
          priority: t.priority || 'medium'
        })))
      } else {
        setTemplates([])
      }

      if (settingsResponse.ok) {
        const settings = await settingsResponse.json()
        if (settings && !settings.error) {
          if (settings.signature) setSignature(settings.signature)
          if (settings.sending_hours_start !== undefined) {
            setSendingHours(prev => ({ ...prev, start: settings.sending_hours_start }))
          }
          if (settings.sending_hours_end !== undefined) {
            setSendingHours(prev => ({ ...prev, end: settings.sending_hours_end }))
          }
          if (settings.respect_holidays !== undefined) setRespectHolidays(settings.respect_holidays)
          if (settings.respect_weekends !== undefined) setRespectWeekends(settings.respect_weekends)
          if (settings.max_messages_per_day !== undefined) setMaxMessagesPerDay(settings.max_messages_per_day)
        }
      }

      if (alertsResponse.ok) {
        const alertsResult = await alertsResponse.json()
        if (alertsResult && Array.isArray(alertsResult.alerts)) {
          setAlerts(alertsResult.alerts.map((a: Record<string, unknown>) => ({
            id: a.id,
            name: a.name,
            description: a.description,
            enabled: a.enabled ?? true,
            channel: a.channel || 'email'
          })))
        }
        if (alertsResult?.briefing_frequency) {
          setBriefingFrequency(alertsResult.briefing_frequency)
        }
      }

      try {
        const digestPrefRes = await fetch('/api/backend-proxy/digest/weekly/preferences?user_id=default_user')
        if (digestPrefRes.ok) {
          const prefData = await digestPrefRes.json()
          if (prefData && prefData.weekly_report_enabled !== undefined) {
            setWeeklyDigestEnabled(prefData.weekly_report_enabled)
          }
        }
      } catch {
        // silently ignore — defaults to true
      }
    } catch (_err) {
      setError('Erro ao carregar dados. Por favor, tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  const saveCommunicationSettings = async () => {
    try {
      setSavingSettings(true)
      setError(null)

      const headers: HeadersInit = { 'Content-Type': 'application/json' }
      if (companyId) {
        headers['X-Company-ID'] = companyId
      }

      const response = await fetch('/api/backend-proxy/company/communication-settings', {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          signature,
          sending_hours_start: sendingHours.start,
          sending_hours_end: sendingHours.end,
          respect_holidays: respectHolidays,
          respect_weekends: respectWeekends,
          max_messages_per_day: maxMessagesPerDay,
          lgpd_compliant: true
        })
      })

      if (!response.ok) {
        throw new Error('Falha ao salvar configurações')
      }

      setSuccessMessage('Configurações salvas com sucesso!')
      { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar configurações')
      { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 5000); }
    } finally {
      setSavingSettings(false)
    }
  }

  const saveTemplateToAPI = async (template: EmailTemplate) => {
    try {
      setSaving(true)
      const response = await fetch(`/api/backend-proxy/email-templates/${template.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: template.name,
          category: template.category,
          subject: template.subject,
          body: template.body,
          variables: template.variables,
          is_active: template.isActive
        })
      })

      if (!response.ok) {
        throw new Error('Falha ao salvar template')
      }

      setSuccessMessage('Template salvo com sucesso!')
      { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleAlert = (id: string) => {
    setAlerts(prev => prev.map(a =>
      a.id === id ? { ...a, enabled: !a.enabled } : a
    ))
  }

  const handleChangeChannel = (id: string, channel: 'email' | 'teams' | 'both') => {
    setAlerts(prev => prev.map(a =>
      a.id === id ? { ...a, channel } : a
    ))
  }

  const saveAlertsConfig = async () => {
    try {
      setSavingAlerts(true)
      const headers: HeadersInit = { 'Content-Type': 'application/json' }
      if (companyId) {
        headers['X-Company-ID'] = companyId
      }
      const response = await fetch('/api/backend-proxy/alerts/config', {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          alerts: alerts.map(a => ({
            id: a.id,
            name: a.name,
            description: a.description,
            enabled: a.enabled,
            channel: a.channel
          })),
          briefing_frequency: briefingFrequency
        })
      })

      if (!response.ok) {
        throw new Error('Falha ao salvar configuração de alertas')
      }

      setSuccessMessage('Configuração de alertas salva com sucesso!')
      { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
      { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 5000); }
    } finally {
      setSavingAlerts(false)
    }
  }

  const handleAdjustWithAI = async () => {
    if (!editingTemplate || !aiPrompt.trim()) return

    setIsGenerating(true)
    try {
      const response = await fetch('/api/backend-proxy/email-templates/adjust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: editingTemplate.id,
          prompt: aiPrompt,
          current_subject: editingTemplate.subject || '',
          current_body: editingTemplate.body,
          channel: editingTemplate.channel || 'email'
        })
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setAiResultModal({
            show: true,
            newSubject: result.data.subject || editingTemplate.subject,
            newBody: result.data.body,
            changesMade: result.data.changes_made || ['Ajustes aplicados']
          })
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        setError(errorData.details?.detail || 'Erro ao ajustar template com a LIA')
        { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 5000); }
      }
    } catch (_err) {
      setError('Erro ao conectar com o serviço de IA')
      { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 5000); }
    } finally {
      setIsGenerating(false)
      setAiPrompt('')
    }
  }

  const handleConfirmAIAdjustment = () => {
    if (!aiResultModal || !editingTemplate) return
    setEditingTemplate(prev => prev ? {
      ...prev,
      subject: aiResultModal.newSubject,
      body: aiResultModal.newBody
    } : null)
    setSuccessMessage('Ajustes da LIA aplicados. Clique em "Salvar" para confirmar as alterações.')
    { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 5000); }
    setAiResultModal(null)
  }

  const handleCancelAIAdjustment = () => {
    setAiResultModal(null)
  }

  const handleSaveTemplate = async () => {
    if (!editingTemplate) return

    const updatedTemplate = { ...editingTemplate, lastUpdated: new Date().toISOString().split('T')[0] }
    setTemplates(prev => prev.map(t =>
      t.id === editingTemplate.id ? updatedTemplate : t
    ))
    setEditingTemplate(null)
    await saveTemplateToAPI(updatedTemplate)
  }

  return {
    // State
    activeTab,
    setActiveTab,
    templates,
    selectedTemplate,
    setSelectedTemplate,
    editingTemplate,
    setEditingTemplate,
    aiPrompt,
    setAiPrompt,
    aiResultModal,
    bodyTextareaRef,
    isGenerating,
    signature,
    setSignature,
    sendingHours,
    setSendingHours,
    respectHolidays,
    setRespectHolidays,
    respectWeekends,
    setRespectWeekends,
    maxMessagesPerDay,
    setMaxMessagesPerDay,
    loading,
    saving,
    savingSettings,
    savingAlerts,
    error,
    successMessage,
    alerts,
    briefingFrequency,
    setBriefingFrequency,
    channelFilter,
    triggerTypeFilter,
    setTriggerTypeFilter,
    searchQuery,
    setSearchQuery,
    expandedGroups,
    setExpandedGroups,
    isEditingSignature,
    setIsEditingSignature,
    isEditingSchedule,
    setIsEditingSchedule,
    isEditingAlerts,
    setIsEditingAlerts,
    weeklyDigestEnabled,
    savingWeeklyDigest,
    handleToggleWeeklyDigest,
    // Derived
    filteredTemplates,
    groupedTemplates,
    // Handlers
    handleChannelFilterChange,
    insertVariableAtCursor,
    fetchData,
    saveCommunicationSettings,
    handleToggleAlert,
    handleChangeChannel,
    saveAlertsConfig,
    handleAdjustWithAI,
    handleConfirmAIAdjustment,
    handleCancelAIAdjustment,
    handleSaveTemplate,
  }
}
