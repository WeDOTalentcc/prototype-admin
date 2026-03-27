"use client"

import React, { useState, useMemo, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { VariableSelector } from "@/components/ui/variable-selector"
import {
  Mail, Clock, Edit, Save, X, Eye, Brain, Send, FileText,
  Check, AlertCircle, MessageSquare, PenTool, RefreshCw, Copy,
  Bell, Shield, Calendar, Timer, Wand2, Zap, Loader2, CheckCircle,
  Search, Filter, Settings
} from "lucide-react"

const TEMPLATE_GROUPS: Record<string, { label: string; icon: string; situations: string[] }> = {
  'alertas': { label: 'Alertas', icon: '🔔', situations: ['critical_alert', 'sla_violated', 'no_show_alert', 'approval_pending', 'approval_expired', 'goal_at_risk', 'goal_missed', 'ats_sync_failed', 'credits_low', 'workforce_variance'] },
  'relatorios': { label: 'Relatórios', icon: '📊', situations: ['briefing', 'end_of_day_summary', 'weekly_summary', 'monthly_summary', 'monthly_report', 'team_report', 'job_executive_report', 'weekly_performance', 'daily_briefing'] },
  'workflow': { label: 'Workflow', icon: '⚙️', situations: ['approval_pending', 'approval_expired', 'screening_completed'] },
  'parecer': { label: 'Parecer LIA', icon: '🤖', situations: ['lia_opinion_compact', 'lia_opinion_detailed'] },
  'integrações': { label: 'Integrações', icon: '🔗', situations: ['ats_sync_failed', 'welcome_user'] },
  'outros': { label: 'Outros', icon: '📌', situations: [] }
}

const TRIGGER_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  'automatic': { label: 'Automático', color: 'bg-wedo-cyan/15 text-wedo-cyan-dark dark:text-wedo-cyan-dark' },
  'manual': { label: 'Manual', color: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' },
  'both': { label: 'Ambos', color: 'bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple' }
}

const PRIORITY_COLORS: Record<string, string> = {
  'high': 'bg-status-error',
  'medium': 'bg-status-warning',
  'low': 'bg-gray-400'
}

const CHANNEL_LABELS: Record<string, { label: string; color: string }> = {
  'email': { label: 'Email', color: 'bg-wedo-cyan/10 text-wedo-cyan-dark dark:text-wedo-cyan-dark' },
  'whatsapp': { label: 'WhatsApp', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  'bell': { label: 'Bell', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
  'teams': { label: 'Teams', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' },
 'briefing': { label: 'Briefing', color: 'bg-gray-50 text-gray-900 dark:bg-gray-800 dark:text-gray-300' },
  'parecer': { label: 'Parecer', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' },
  'report': { label: 'Report', color: 'bg-wedo-magenta/10 text-wedo-magenta dark:bg-wedo-magenta/20 dark:text-wedo-magenta' },
  'chat_lia': { label: 'Chat LIA', color: 'bg-wedo-cyan/10 text-wedo-cyan dark:bg-wedo-cyan/20 dark:text-wedo-cyan' }
}

interface EmailTemplate {
  id: string
  name: string
  category: string
  subject: string
  body: string
  variables: string[]
  isActive: boolean
  lastUpdated: string
  channel?: string
  situation?: string
  trigger_type?: 'automatic' | 'manual' | 'both'
  used_in?: string[]
  priority?: 'high' | 'medium' | 'low'
}

const stripHtmlTags = (html: string): string => {
  if (!html) return ''
  const isHtml = /<[a-z][\s\S]*>/i.test(html)
  if (!isHtml) return html
  
  let text = html
    .replace(/{{#if\s+\w+}}/gi, '')
    .replace(/{{\/if}}/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<p[^>]*>/gi, '')
    .replace(/<\/div>/gi, '\n')
    .replace(/<div[^>]*>/gi, '')
    .replace(/<\/li>/gi, '\n')
    .replace(/<li[^>]*>/gi, '• ')
    .replace(/<\/ul>/gi, '\n')
    .replace(/<ul[^>]*>/gi, '')
    .replace(/<\/ol>/gi, '\n')
    .replace(/<ol[^>]*>/gi, '')
    .replace(/<\/h[1-6]>/gi, '\n\n')
    .replace(/<h[1-6][^>]*>/gi, '')
    .replace(/<\/?(strong|b)[^>]*>/gi, '')
    .replace(/<\/?(em|i)[^>]*>/gi, '')
    .replace(/<a[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/gi, '$2')
    .replace(/<img[^>]*alt="([^"]*)"[^>]*\/?>/gi, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+/g, ' ')
    .trim()
  
  return text
}

export function AdminTemplateHub() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
  const bodyTextareaRef = useRef<HTMLTextAreaElement>(null)
  
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
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [aiPrompt, setAiPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [aiResultModal, setAiResultModal] = useState<{
    show: boolean
    newSubject: string
    newBody: string
    changesMade: string[]
  } | null>(null)
  
  const [channelFilter, setChannelFilter] = useState<'all' | 'email' | 'whatsapp' | 'teams' | 'bell' | 'briefing' | 'parecer' | 'report'>('all')
  const [triggerTypeFilter, setTriggerTypeFilter] = useState<'all' | 'automatic' | 'manual' | 'both'>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['alertas', 'relatorios', 'workflow'])
  
  const handleChannelFilterChange = (channel: typeof channelFilter) => {
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
          setTemplates(templatesArray.map((t: any) => ({
            id: t.id,
            name: t.name,
            category: t.category || 'system',
            subject: t.subject || '',
            body: t.body || t.body_text || (t.body_html ? stripHtmlTags(t.body_html) : ''),
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
      } catch (err) {
        console.error('Error fetching data:', err)
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
    } catch (err) {
      console.error('Error adjusting template with AI:', err)
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

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp': return <MessageSquare className="w-3.5 h-3.5" />
      case 'teams': return <MessageSquare className="w-3.5 h-3.5" />
      case 'bell': return <Bell className="w-3.5 h-3.5" />
      case 'briefing': return <FileText className="w-3.5 h-3.5" />
      case 'parecer': return <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
      case 'report': return <FileText className="w-3.5 h-3.5" />
      case 'chat_lia': return <MessageSquare className="w-3.5 h-3.5" />
      default: return <Mail className="w-3.5 h-3.5" />
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
          Templates de Sistema
        </h2>
        <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
          Gerencie templates automáticos, alertas e notificações internas
        </p>
      </div>

      {successMessage && (
        <div className="px-3 py-2 rounded-md flex items-center gap-2" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', borderColor: 'rgba(96, 190, 209, 0.3)', color: 'var(--wedo-cyan-dark)', border: '1px solid' }}>
          <CheckCircle className="w-4 h-4 text-gray-700" />
          <span>{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-3 py-2 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Buscar templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 text-sm h-9 rounded-md"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'Todos', icon: null },
              { key: 'email', label: 'Email', icon: Mail },
              { key: 'bell', label: 'Bell', icon: Bell },
              { key: 'teams', label: 'Teams', icon: MessageSquare },
              { key: 'briefing', label: 'Briefing', icon: FileText },
              { key: 'parecer', label: 'Parecer', icon: Brain },
              { key: 'report', label: 'Report', icon: FileText }
            ].map(({ key, label, icon: Icon }) => (
              <button 
                key={key}
                onClick={() => handleChannelFilterChange(key as typeof channelFilter)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  channelFilter === key 
                    ? 'text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
                style={channelFilter === key ? { backgroundColor: 'var(--gray-950)' } : {}}
              >
                {Icon && <Icon className="w-3.5 h-3.5" />}
                {label}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <select
              value={triggerTypeFilter}
              onChange={(e) => setTriggerTypeFilter(e.target.value as 'all' | 'automatic' | 'manual' | 'both')}
              className="px-2.5 py-1.5 rounded-md text-xs font-medium border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            >
              <option value="all">Todos Tipos</option>
              <option value="automatic">Automático</option>
              <option value="manual">Manual</option>
              <option value="both">Ambos</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-gray-500 flex items-center gap-2">
          <Filter className="w-3.5 h-3.5" />
          {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} encontrado{filteredTemplates.length !== 1 ? 's' : ''}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="rounded-md animate-pulse">
                <CardContent className="p-3">
                  <div className="flex items-start gap-2">
                    <div className="w-8 h-8 rounded-md" style={{ backgroundColor: 'rgba(96, 190, 209, 0.2)' }}></div>
                    <div className="flex-1">
                      <div className="h-4 w-32 rounded mb-2" style={{ backgroundColor: 'rgba(96, 190, 209, 0.2)' }}></div>
                      <div className="h-3 w-24 rounded" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="border-dashed border-2 border-gray-200 rounded-md h-64 flex items-center justify-center animate-pulse">
            <CardContent className="text-center">
              <div className="w-10 h-10 rounded-full mx-auto mb-3" style={{ backgroundColor: 'rgba(96, 190, 209, 0.2)' }}></div>
              <div className="h-4 w-40 rounded mx-auto" style={{ backgroundColor: 'rgba(96, 190, 209, 0.2)' }}></div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-[500px]">
          <div className="space-y-3 overflow-y-auto pr-2 pb-8" style={{ maxHeight: 'calc(100vh - 320px)' }}>
            {filteredTemplates.length === 0 ? (
              <Card className="border border-dashed border-gray-200 rounded-md">
                <CardContent className="p-4 text-center">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                    <Search className="w-4 h-4 text-gray-700" />
                  </div>
                  <p className="text-sm text-gray-600">
                    Nenhum template encontrado
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Tente ajustar os filtros de busca
                  </p>
                </CardContent>
              </Card>
            ) : (
              <Accordion
                type="multiple"
                value={expandedGroups}
                onValueChange={setExpandedGroups}
                className="space-y-2"
              >
                {Object.entries(TEMPLATE_GROUPS).map(([groupKey, group]) => {
                  const groupTemplates = groupedTemplates[groupKey] || []
                  if (groupTemplates.length === 0) return null
                  
                  return (
                    <AccordionItem key={groupKey} value={groupKey} className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
                      <AccordionTrigger className="px-3 py-2.5 hover:no-underline hover:bg-gray-50 dark:hover:bg-gray-800/50">
                        <div className="flex items-center gap-2 text-left">
                          <span className="text-lg">{group.icon}</span>
                          <span className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                            {group.label}
                          </span>
                          <Badge variant="outline" className="text-xs ml-1">
                            {groupTemplates.length}
                          </Badge>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-2 pb-2">
                        <div className="space-y-2">
                          {groupTemplates.map((template) => (
                            <Card 
                              key={template.id}
                              className={`border cursor-pointer transition-all rounded-md ${
                                selectedTemplate?.id === template.id 
                                  ? 'border-gray-900 dark:border-gray-50' 
                                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                              }`}
                              style={selectedTemplate?.id === template.id ? { boxShadow: '0 0 0 2px rgba(96, 190, 209, 0.2)' } : {}}
                              onClick={() => setSelectedTemplate(template)}
                            >
                              <CardContent className="p-2.5">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <div className={`w-7 h-7 rounded-md ${CHANNEL_LABELS[template.channel || 'email']?.color || 'bg-gray-50 text-gray-600'} flex items-center justify-center flex-shrink-0`}>
                                      {getChannelIcon(template.channel || 'email')}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-1.5">
                                        <p className="text-xs font-medium text-gray-950 dark:text-gray-50 truncate">
                                          {template.name}
                                        </p>
                                        {template.priority && (
                                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${PRIORITY_COLORS[template.priority]}`} title={`Prioridade: ${template.priority}`} />
                                        )}
                                      </div>
                                      <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                                        <Badge className={`text-micro px-1.5 py-0 ${CHANNEL_LABELS[template.channel || 'email']?.color || ''}`}>
                                          {CHANNEL_LABELS[template.channel || 'email']?.label || template.channel}
                                        </Badge>
                                        {template.trigger_type && (
                                          <Badge className={`text-micro px-1.5 py-0 ${TRIGGER_TYPE_LABELS[template.trigger_type]?.color || ''}`}>
                                            {TRIGGER_TYPE_LABELS[template.trigger_type]?.label || template.trigger_type}
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                  <Badge variant={template.isActive ? "default" : "outline"} className="text-micro flex-shrink-0" style={template.isActive ? { backgroundColor: 'var(--gray-950)' } : {}}>
                                    {template.isActive ? 'Ativo' : 'Inativo'}
                                  </Badge>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  )
                })}
              </Accordion>
            )}
          </div>

          <div className="space-y-3 lg:sticky lg:top-0 overflow-y-auto pb-20" style={{ maxHeight: 'calc(100vh - 260px)' }}>
            {selectedTemplate ? (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                    {editingTemplate ? 'Editando Template' : 'Visualização'}
                  </h3>
                  <div className="flex items-center gap-2">
                    {editingTemplate ? (
                      <>
                        <Button variant="ghost" size="sm" onClick={() => setEditingTemplate(null)}>
                          <X className="w-3.5 h-3.5" />
                        </Button>
                        <Button size="sm" className="py-1.5 px-2 text-xs bg-gray-900 text-white" onClick={handleSaveTemplate}>
                          <Save className="w-3.5 h-3.5 mr-1" />
                          {saving ? 'Salvando...' : 'Salvar'}
                        </Button>
                      </>
                    ) : (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setEditingTemplate({ ...selectedTemplate })}
                        className="rounded-md py-1.5 px-2 text-xs border-gray-300"
                      >
                        <Edit className="w-3.5 h-3.5 mr-1" />
                        Editar
                      </Button>
                    )}
                  </div>
                </div>

                <Card className="border border-gray-200/50 dark:border-gray-700/50 bg-white/80 dark:bg-gray-800/80 rounded-md">
                  <CardContent className="p-4 space-y-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge className={`${CHANNEL_LABELS[selectedTemplate.channel || 'email']?.color || ''}`}>
                        {CHANNEL_LABELS[selectedTemplate.channel || 'email']?.label || selectedTemplate.channel}
                      </Badge>
                      <Badge variant="outline">{selectedTemplate.category}</Badge>
                      {selectedTemplate.trigger_type && (
                        <Badge className={`${TRIGGER_TYPE_LABELS[selectedTemplate.trigger_type]?.color || ''}`}>
                          {TRIGGER_TYPE_LABELS[selectedTemplate.trigger_type]?.label}
                        </Badge>
                      )}
                    </div>

                    {selectedTemplate.subject && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Assunto</label>
                        {editingTemplate ? (
                          <input
                            type="text"
                            value={editingTemplate.subject}
                            onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, subject: e.target.value } : null)}
                            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-white focus:ring-2 focus:outline-none"
                          />
                        ) : (
                          <p className="text-sm text-gray-950 dark:text-gray-50 bg-gray-50 rounded-md px-3 py-2">{selectedTemplate.subject}</p>
                        )}
                      </div>
                    )}

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block text-xs font-medium text-gray-600">Conteúdo</label>
                        {editingTemplate && (
                          <VariableSelector 
                            onSelect={insertVariableAtCursor}
                            disabled={!editingTemplate}
                          />
                        )}
                      </div>
                      {editingTemplate ? (
                        <textarea
                          ref={bodyTextareaRef}
                          value={editingTemplate.body}
                          onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, body: e.target.value } : null)}
                          rows={12}
                          className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-white focus:ring-2 focus:outline-none font-mono"
                        />
                      ) : (
                        <div className="bg-gray-50 rounded-md p-3">
                          <pre className="text-sm text-gray-950 dark:text-gray-50 whitespace-pre-wrap font-sans">
                            {selectedTemplate.body}
                          </pre>
                        </div>
                      )}
                    </div>

                    {selectedTemplate.variables && selectedTemplate.variables.length > 0 && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-2">Variáveis Disponíveis</label>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedTemplate.variables.map((variable, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs font-mono">
                              {`{{${variable}}}`}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedTemplate.used_in && selectedTemplate.used_in.length > 0 && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-2">Usado em</label>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedTemplate.used_in.map((usage, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {usage}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {editingTemplate && (
                  <Card className="rounded-md border border-gray-200 bg-white">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                          <Brain className="w-4 h-4 text-wedo-cyan" />
                        </div>
                        <div>
                          <span className="text-base-ui font-semibold text-gray-900">Ajustar com a LIA</span>
                          <p className="text-xs text-gray-500">
                            Descreva as alterações desejadas
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={aiPrompt}
                          onChange={(e) => setAiPrompt(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && !isGenerating && aiPrompt.trim() && handleAdjustWithAI()}
                          placeholder="Ex: Torne mais formal e adicione contexto técnico..."
                          disabled={isGenerating}
                          className="flex-1 px-3 py-2 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
                         
                        />
                        <Button 
                          onClick={handleAdjustWithAI}
                          disabled={isGenerating || !aiPrompt.trim()}
                          className="gap-1.5 rounded-md py-2 px-3 text-xs min-w-[100px]"
                          style={{ backgroundColor: isGenerating ? 'var(--wedo-cyan)' : 'var(--gray-600)', color: 'white' }}
                        >
                          {isGenerating ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              Ajustando...
                            </>
                          ) : (
                            <>
                              <Wand2 className="w-3.5 h-3.5" />
                              Ajustar
                            </>
                          )}
                        </Button>
                      </div>
                      {isGenerating && (
                        <div className="flex items-center gap-2 p-2 rounded-md" style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)' }}>
                          <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-gray-900" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-gray-900" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-gray-900" style={{ animationDelay: '300ms' }}></span>
                          </div>
                          <span className="text-xs" style={{ color: 'var(--wedo-cyan-dark)' }}>
                            A LIA está analisando e ajustando o template...
                          </span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {aiResultModal?.show && (
                  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-md bg-white">
                      <div className="border-b border-gray-100 p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                              <Brain className="w-5 h-5 text-wedo-cyan" />
                            </div>
                            <div>
                              <h3 className="text-sm font-semibold text-gray-900">
                                Ajustes da LIA
                              </h3>
                              <p className="text-xs text-gray-500">
                                Revise as alterações sugeridas
                              </p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" onClick={handleCancelAIAdjustment} className="rounded-md">
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      <CardContent className="p-4 space-y-4 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 180px)' }}>
                        <div>
                          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                            Alterações Realizadas
                          </label>
                          <div className="flex flex-wrap gap-1.5">
                            {aiResultModal.changesMade.map((change, idx) => (
                              <Badge key={idx} className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', color: 'var(--wedo-cyan-dark)' }}>
                                <Check className="w-3 h-3 mr-1" />
                                {change}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        {aiResultModal.newSubject && (
                          <div>
                            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                              Novo Assunto
                            </label>
                            <div className="p-3 bg-gray-50 rounded-md text-xs text-gray-900">
                              {aiResultModal.newSubject}
                            </div>
                          </div>
                        )}

                        <div>
                          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                            Novo Conteúdo
                          </label>
                          <div className="p-3 bg-gray-50 rounded-md text-xs text-gray-900 whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                            {aiResultModal.newBody}
                          </div>
                        </div>

                        <div className="p-3 rounded-md border border-status-warning/30 bg-status-warning/10">
                          <div className="flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
                            <p className="text-xs text-status-warning">
                              Ao aplicar os ajustes, o texto será atualizado no editor. Lembre-se de clicar em <strong>"Salvar"</strong> para confirmar as alterações definitivamente.
                            </p>
                          </div>
                        </div>
                      </CardContent>
                      <div className="border-t border-gray-100 p-4 flex items-center justify-end gap-3">
                        <Button variant="outline" onClick={handleCancelAIAdjustment} className="rounded-md px-4 py-2 text-xs">
                          Cancelar
                        </Button>
                        <Button 
                          onClick={handleConfirmAIAdjustment}
                          className="rounded-md px-4 py-2 text-xs gap-1.5 bg-gray-900" style={{ color: 'white' }}
                        >
                          <Check className="w-3.5 h-3.5" />
                          Aplicar Ajustes
                        </Button>
                      </div>
                    </Card>
                  </div>
                )}
              </>
            ) : (
              <Card className="border-dashed border-2 border-gray-200 rounded-md h-96 flex items-center justify-center">
                <CardContent className="text-center">
                  <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                    <Settings className="w-6 h-6 text-gray-700" />
                  </div>
                  <p className="text-sm text-gray-600 mb-1">
                    Selecione um template
                  </p>
                  <p className="text-xs text-gray-400">
                    Clique em um template à esquerda para visualizar e editar
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
