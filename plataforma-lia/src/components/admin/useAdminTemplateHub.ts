"use client"

import { useState, useMemo, useEffect, useRef } from "react"
import {
  EmailTemplate,
  AIResultModal,
  ChannelFilter,
  TriggerTypeFilter,
  TEMPLATE_GROUPS,
  stripHtmlTags,
} from "./AdminTemplateHub.types"

export function useAdminTemplateHub() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
  const bodyTextareaRef = useRef<HTMLTextAreaElement>(null)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [aiPrompt, setAiPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [aiResultModal, setAiResultModal] = useState<AIResultModal | null>(null)

  const [channelFilter, setChannelFilter] = useState<ChannelFilter>('all')
  const [triggerTypeFilter, setTriggerTypeFilter] = useState<TriggerTypeFilter>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['alertas', 'relatorios', 'workflow'])

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

  const handleChannelFilterChange = (channel: ChannelFilter) => {
    setChannelFilter(channel)
    setSelectedTemplate(null)
    setEditingTemplate(null)
  }

  const getTemplateGroup = (template: EmailTemplate): string => {
    const situation = template.situation?.toLowerCase() || ''
    const channel = template.channel?.toLowerCase() || ''

    if (channel === 'parecer') return 'parecer'
    if (channel === 'briefing' || channel === 'report') return 'relatorios'

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

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)

        const templatesResponse = await fetch(`/api/backend-proxy/email-templates?visibility=admin`)

        if (templatesResponse.ok) {
          const result = await templatesResponse.json()
          const templatesArray = result.items || (Array.isArray(result) ? result : [])
          setTemplates(templatesArray.map((t: Record<string, unknown>) => ({
            id: t.id,
            name: t.name,
            category: t.category || 'system',
            subject: t.subject || '',
            body: t.body || t.body_text || (t.body_html ? stripHtmlTags(t.body_html as string) : ''),
            variables: t.variables || [],
            isActive: t.is_active ?? true,
            lastUpdated: t.updated_at || t.last_updated || new Date().toISOString().split('T')[0],
            channel: t.channel || 'email',
            situation: t.situation || '',
            trigger_type: t.trigger_type || 'automatic',
            used_in: t.used_in || [],
            priority: t.priority || 'medium'
          })))
        } else {
          setTemplates([])
        }
      } catch {
        setError('Erro ao carregar dados. Por favor, tente novamente.')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

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
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
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
        setTimeout(() => setError(null), 5000)
      }
    } catch {
      setError('Erro ao conectar com o serviço de IA')
      setTimeout(() => setError(null), 5000)
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
    setTimeout(() => setSuccessMessage(null), 5000)
    setAiResultModal(null)
  }

  const handleCancelAIAdjustment = () => {
    setAiResultModal(null)
  }

  return {
    templates,
    selectedTemplate,
    setSelectedTemplate,
    editingTemplate,
    setEditingTemplate,
    bodyTextareaRef,
    loading,
    saving,
    error,
    successMessage,
    aiPrompt,
    setAiPrompt,
    isGenerating,
    aiResultModal,
    channelFilter,
    triggerTypeFilter,
    setTriggerTypeFilter,
    searchQuery,
    setSearchQuery,
    expandedGroups,
    setExpandedGroups,
    filteredTemplates,
    groupedTemplates,
    insertVariableAtCursor,
    handleChannelFilterChange,
    handleSaveTemplate,
    handleAdjustWithAI,
    handleConfirmAIAdjustment,
    handleCancelAIAdjustment,
  }
}
