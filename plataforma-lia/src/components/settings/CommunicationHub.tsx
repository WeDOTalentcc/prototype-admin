"use client"

import React, { useState, useMemo, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { VariableSelector } from "@/components/ui/variable-selector"
import {
  Mail, Clock, Edit, Save, X, Eye, Brain, Send, FileText,
  Check, AlertCircle, MessageSquare, PenTool, RefreshCw, Copy,
  Bell, Shield, Calendar, Timer, Wand2, Zap, Loader2, CheckCircle,
  Search, Filter
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles, tabStyles, actionButtonStyles } from '@/lib/design-tokens'

// [OPT-043] TODO: revisar inline styles dinâmicos (17 ocorrências)
const TEMPLATE_GROUPS: Record<string, { label: string; icon: string; situations: string[] }> = {
  'primeiro_contato': { label: 'Primeiro Contato', icon: '👋', situations: ['contato_inicial', 'follow_up', 'initial_contact', 'contato_rapido'] },
  'triagem': { label: 'Triagem', icon: '📋', situations: ['triagem', 'screening_reminder', 'screening_passed', 'screening_failed', 'screening_completed', 'lembrete'] },
  'entrevista': { label: 'Entrevista', icon: '🎤', situations: ['agendamento', 'interview_scheduled', 'interview_reminder', 'rejection_post_interview'] },
  'feedback': { label: 'Feedback', icon: '💬', situations: ['feedback_positivo', 'feedback_construtivo'] },
  'proposta': { label: 'Proposta', icon: '📝', situations: ['proposta', 'proposta_aceita', 'offer_accepted', 'offer_rejected'] },
  'encerramento': { label: 'Encerramento', icon: '✅', situations: ['vaga_fechada', 'process_closed', 'job_paused', 'job_reactivated'] },
  'alertas': { label: 'Alertas', icon: '🔔', situations: ['critical_alert', 'sla_violated', 'no_show_alert', 'approval_pending', 'approval_expired', 'ats_sync_failed', 'credits_low'] },
  'relatorios': { label: 'Relatórios', icon: '📊', situations: ['briefing', 'end_of_day_summary', 'weekly_summary', 'monthly_summary', 'monthly_report', 'team_report', 'job_executive_report', 'weekly_performance', 'goal_at_risk', 'goal_missed'] },
  'outros': { label: 'Outros', icon: '📌', situations: [] }
}

const TRIGGER_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  'automatic': { label: 'Automático', color: 'bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary' },
  'manual': { label: 'Manual', color: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' },
  'both': { label: 'Ambos', color: 'bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary' }
}

const PRIORITY_COLORS: Record<string, string> = {
  'high': 'bg-status-error',
  'medium': 'bg-status-warning',
  'low': 'bg-gray-400'
}

interface AlertConfig {
  id: string
  name: string
  description: string
  enabled: boolean
  channel: 'email' | 'teams' | 'both'
}

interface EmailTemplate {
  id: string
  name: string
  category: 'approval' | 'rejection' | 'scheduling' | 'followup' | 'feedback'
  subject: string
  body: string
  variables: string[]
  isActive: boolean
  lastUpdated: string
  channel?: 'email' | 'whatsapp' | 'teams' | 'bell'
  situation?: string
  trigger_type?: 'automatic' | 'manual' | 'both'
  used_in?: string[]
  priority?: 'high' | 'medium' | 'low'
}

interface CommunicationHubProps {
  activeSubsection?: string
}

const stripHtmlTags = (html: string): string => {
  if (!html) return ''
  const isHtml = /<[a-z][\s\S]*>/i.test(html)
  if (!isHtml) return html
  
  const text = html
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
    .replace(/&rsquo;/g, "'")
    .replace(/&lsquo;/g, "'")
    .replace(/&rdquo;/g, '"')
    .replace(/&ldquo;/g, '"')
    .replace(/&mdash;/g, '—')
    .replace(/&ndash;/g, '–')
    .replace(/&#\d+;/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n /g, '\n')
    .replace(/ \n/g, '\n')
    .trim()
  
  return text
}

const defaultAlerts: AlertConfig[] = [
  { id: '1', name: 'SLA Próximo do Vencimento', description: 'Alerta quando um candidato está há 80% do SLA na mesma etapa', enabled: true, channel: 'both' },
  { id: '2', name: 'Meta Mensal em Risco', description: 'Notifica quando a meta de contratações do mês pode não ser atingida', enabled: true, channel: 'email' },
  { id: '3', name: 'Candidato Sem Interação', description: 'Alerta para candidatos sem contato há mais de 5 dias', enabled: true, channel: 'teams' },
  { id: '4', name: 'Entrevista Não Confirmada', description: 'Lembrete 24h antes de entrevistas sem confirmação', enabled: true, channel: 'both' },
  { id: '5', name: 'Feedback Pendente', description: 'Solicita feedback após 48h de entrevista realizada', enabled: false, channel: 'email' }
]

const defaultTemplates: EmailTemplate[] = [
  // Email Templates
  {
    id: '1',
    name: 'Contato Inicial (Email)',
    category: 'followup',
    subject: 'Oportunidade - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Identificamos seu perfil e gostaríamos de conversar sobre uma excelente oportunidade para a posição de {{vaga}}.

Sua experiência e qualificações são muito alinhadas com o que buscamos.

Podemos agendar uma conversa?

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'contato_inicial',
    trigger_type: 'manual',
    used_in: ['Sourcing', 'Pipeline'],
    priority: 'high'
  },
  {
    id: '2',
    name: 'Follow-up (Email)',
    category: 'followup',
    subject: 'Acompanhamento - {{vaga}}',
    body: `Olá {{candidato_nome}},

Espero que esteja bem! Gostaria de fazer um acompanhamento sobre sua candidatura para a posição de {{vaga}}.

Tem alguma dúvida sobre o processo ou a vaga?

Fico à disposição.

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'follow_up',
    trigger_type: 'automatic',
    used_in: ['Pipeline'],
    priority: 'medium'
  },
  {
    id: '3',
    name: 'Convite Triagem (Email)',
    category: 'scheduling',
    subject: 'Próximo passo: Avaliação - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Estamos avançando em nosso processo seletivo para a posição de {{vaga}} e gostaríamos de convidá-lo(a) para a próxima etapa: uma triagem rápida com a nossa assistente LIA.

📋 Sobre a triagem:
• Duração estimada: 15-20 minutos
• Formato: Conversa por chat ou WhatsApp com a LIA
• Objetivo: Conhecer melhor sua forma de pensar e resolver problemas

🔗 Para iniciar, escolha uma das opções:
• INICIAR VIA CHAT WEB - Clique aqui para conversar pelo navegador
• INICIAR VIA WHATSAPP - Clique aqui para conversar pelo WhatsApp

⚠️ Ao iniciar, você será apresentado aos termos de uso e política de privacidade (LGPD).

Essa avaliação nos ajuda a entender melhor seu perfil e garantir que a vaga seja compatível com suas habilidades e expectativas.

Qualquer dúvida, estamos à disposição!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome', 'link_triagem', 'duracao_triagem'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'triagem',
    trigger_type: 'automatic',
    used_in: ['Triagem Automática', 'Pipeline'],
    priority: 'high'
  },
  {
    id: '4',
    name: 'Convite Entrevista (Email)',
    category: 'scheduling',
    subject: 'Convite para Entrevista - {{vaga}}',
    body: `Olá {{candidato_nome}},

Parabéns por avançar no processo seletivo para {{vaga}}! 🎉

Gostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista {{formato_entrevista}}.

📅 Detalhes da Entrevista:
• Tipo: Entrevista {{formato_entrevista}}
• Duração: {{duracao_entrevista}} minutos
• Plataforma: {{link_entrevista}}
• Entrevistador: {{entrevistador_nome}}

🗓️ Escolha o melhor horário:
Clique no link abaixo para visualizar as disponibilidades e escolher o horário que melhor funciona para você:

{{link_calendario}}

Após a confirmação, você receberá:
✅ Email de confirmação com todos os detalhes
✅ Convite do Outlook/Google Calendar
✅ Link da plataforma de vídeo (se aplicável)

Qualquer dúvida, estamos à disposição!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'entrevistador_nome', 'link_entrevista', 'link_calendario', 'data_entrevista', 'horario_entrevista'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'agendamento',
    trigger_type: 'both',
    used_in: ['Agendamento', 'Calendário'],
    priority: 'high'
  },
  {
    id: '5',
    name: 'Feedback Positivo (Email)',
    category: 'feedback',
    subject: 'Atualização - Processo Seletivo {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

É com grande satisfação que compartilhamos o feedback sobre sua participação no processo seletivo para {{vaga}}.

✅ Pontos Positivos:
• Sua experiência e conhecimento técnico impressionaram nossa equipe
• Demonstrou excelente comunicação e clareza nas respostas
• Alinhamento com os valores e cultura da empresa

📈 Próximos Passos:
{{proximos_passos}}

Agradecemos seu interesse e dedicação ao processo!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'pontos_positivos', 'proximos_passos', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'feedback_positivo',
    trigger_type: 'manual',
    used_in: ['Entrevistas', 'Feedback'],
    priority: 'medium'
  },
  {
    id: '6',
    name: 'Feedback Construtivo (Email)',
    category: 'feedback',
    subject: 'Retorno - Processo Seletivo {{vaga}}',
    body: `Olá {{candidato_nome}},

Agradecemos sua participação no processo seletivo para {{vaga}}.

Gostaríamos de compartilhar nosso feedback:

📝 Observações:
{{areas_desenvolvimento}}

Agradecemos seu tempo e interesse. Mantemos seu perfil em nosso banco de talentos para futuras oportunidades que sejam mais alinhadas com seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'areas_desenvolvimento', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'feedback_construtivo',
    trigger_type: 'manual',
    used_in: ['Rejeição', 'Feedback'],
    priority: 'low'
  },
  // WhatsApp Templates
  {
    id: '7',
    name: 'Contato Rápido (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Olá {{candidato_nome}}! 👋

Sou da equipe de recrutamento. Temos uma oportunidade que pode interessar você.

Podemos conversar? 😊`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'contato_rapido',
    trigger_type: 'manual',
    used_in: ['Sourcing', 'WhatsApp'],
    priority: 'high'
  },
  {
    id: '8',
    name: 'Lembrete (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Olá {{candidato_nome}}! 📅

Passando para confirmar nossa conversa de hoje.

Nos vemos em breve! 🚀`,
    variables: ['candidato_nome', 'vaga'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'lembrete',
    trigger_type: 'automatic',
    used_in: ['Agendamento', 'Lembretes'],
    priority: 'medium'
  },
  {
    id: '9',
    name: 'Convite Triagem (WhatsApp)',
    category: 'scheduling',
    subject: '',
    body: `Olá {{candidato_nome}}! 👋

Esperamos que esteja bem!

Estamos avançando no processo seletivo para {{vaga}} e gostaríamos de convidá-lo(a) para uma triagem rápida.

📋 *Sobre a triagem:*
• Duração: 15-20 min
• Formato: Conversa com a LIA, nossa assistente

⚠️ *Aviso LGPD*
Antes de iniciar, você receberá informações sobre como seus dados serão tratados e os termos de uso do processo.

Podemos começar? Ao confirmar, a LIA iniciará a conversa! 🎯

Responda "SIM" para começar 😊`,
    variables: ['candidato_nome', 'vaga', 'link_triagem'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'triagem',
    trigger_type: 'automatic',
    used_in: ['Triagem', 'WhatsApp'],
    priority: 'high'
  },
  {
    id: '10',
    name: 'Convite Entrevista (WhatsApp)',
    category: 'scheduling',
    subject: '',
    body: `Olá {{candidato_nome}}! 🎉

Parabéns por avançar no processo seletivo para {{vaga}}!

Gostaríamos de agendar uma entrevista {{formato_entrevista}} com você.

📅 *Detalhes:*
• Duração: {{duracao_entrevista}} min
• Formato: {{link_entrevista}}

🗓️ *Escolha seu horário preferido:*
A LIA vai te mostrar as opções disponíveis!

✅ Após confirmar:
• Você receberá email de confirmação
• Convite para calendário
• Link da videochamada

Vamos agendar? 😊`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'link_entrevista'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'agendamento',
    trigger_type: 'both',
    used_in: ['Agendamento', 'WhatsApp'],
    priority: 'high'
  }
]

const categoryLabels = {
  approval: { label: 'Aprovação', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  rejection: { label: 'Rejeição', color: 'bg-status-error/10 text-status-error dark:bg-status-error/20 dark:text-status-error' },
  scheduling: { label: 'Agendamento', color: 'bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary' },
  followup: { label: 'Follow-up', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
  feedback: { label: 'Feedback', color: 'bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary' }
}

export function CommunicationHub({ activeSubsection }: CommunicationHubProps) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'templates')
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiResultModal, setAiResultModal] = useState<{
    show: boolean
    newSubject: string
    newBody: string
    changesMade: string[]
  } | null>(null)
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
  
  const [alerts, setAlerts] = useState<AlertConfig[]>(defaultAlerts)
  const [briefingFrequency, setBriefingFrequency] = useState<'twice_daily' | 'daily' | 'weekly' | 'monthly'>('daily')
  const [channelFilter, setChannelFilter] = useState<'all' | 'email' | 'whatsapp'>('all')
  const [triggerTypeFilter, setTriggerTypeFilter] = useState<'all' | 'automatic' | 'manual' | 'both'>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [expandedGroups, setExpandedGroups] = useState<string[]>(['primeiro_contato', 'triagem', 'entrevista'])
  const [companyId, setCompanyId] = useState<string>('')
  
  const [isEditingSignature, setIsEditingSignature] = useState(false)
  const [isEditingSchedule, setIsEditingSchedule] = useState(false)
  const [isEditingAlerts, setIsEditingAlerts] = useState(false)
  
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

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        
        // First get company profile to obtain company_id for subsequent requests
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
        } catch (e) {
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
            body: t.body || t.body_text || (t.body_html ? t.body_html.replace(/<[^>]*>/g, '') : ''),
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
        } else if (alertsResponse.status === 403) {
        }
      } catch (err) {
        setError('Erro ao carregar dados. Por favor, tente novamente.')
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])
  
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
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar configurações')
      setTimeout(() => setError(null), 5000)
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
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const tabs = [
    { id: 'templates', label: 'Templates', icon: Mail },
    { id: 'signature', label: 'Assinatura', icon: PenTool },
    { id: 'schedule', label: 'Horários LGPD', icon: Clock },
    { id: 'alerts', label: 'Alertas', icon: Bell }
  ]

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
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
      setTimeout(() => setError(null), 5000)
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
        setTimeout(() => setError(null), 5000)
      }
    } catch (err) {
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

  const handleSaveTemplate = async () => {
    if (!editingTemplate) return
    
    const updatedTemplate = { ...editingTemplate, lastUpdated: new Date().toISOString().split('T')[0] }
    setTemplates(prev => prev.map(t => 
      t.id === editingTemplate.id ? updatedTemplate : t
    ))
    setEditingTemplate(null)
    await saveTemplateToAPI(updatedTemplate)
  }

  const renderTemplates = () => (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-4 h-4" />
          <span >{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span >{error}</span>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className={textStyles.h4}>
            Templates de Comunicação
          </h3>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 lia-text-400 dark:lia-text-500" />
            <Input
              placeholder="Buscar templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 text-xs h-9 rounded-md"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'Todos', icon: null },
              { key: 'email', label: 'Email', icon: Mail },
              { key: 'whatsapp', label: 'WhatsApp', icon: MessageSquare }
            ].map(({ key, label, icon: Icon }) => (
              <button 
                key={key}
                onClick={() => handleChannelFilterChange(key as 'all' | 'email' | 'whatsapp')}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  channelFilter === key 
                    ? 'bg-gray-900 text-white dark:lia-bg-50 dark:lia-text-900' 
                    : 'bg-gray-100 lia-text-600 hover:bg-gray-200 dark:bg-lia-bg-elevated dark:text-lia-text-secondary'
                }`}
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
              className="px-2.5 py-1.5 rounded-full text-xs font-medium border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary lia-text-700 dark:text-lia-text-secondary"
            >
              <option value="all">Todos Tipos</option>
              <option value="automatic">Automático</option>
              <option value="manual">Manual</option>
              <option value="both">Ambos</option>
            </select>
          </div>
        </div>

        <div className="text-xs lia-text-500 dark:text-lia-text-tertiary flex items-center gap-2">
          <Filter className="w-3.5 h-3.5" />
          {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} encontrado{filteredTemplates.length !== 1 ? 's' : ''}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="space-y-3">
            <div className="h-5 w-32 rounded-md animate-pulse bg-gray-200 dark:bg-lia-bg-elevated"></div>
            {[1, 2, 3].map((i) => (
              <Card key={i} className="rounded-md animate-pulse backdrop-blur-sm">
                <CardContent className="p-3">
                  <div className="flex items-start gap-2">
                    <div className="w-8 h-8 rounded-md bg-gray-200 dark:bg-lia-bg-elevated"></div>
                    <div className="flex-1">
                      <div className="h-4 w-32 rounded-md mb-2 bg-gray-200 dark:bg-lia-bg-elevated"></div>
                      <div className="h-3 w-24 rounded-md bg-gray-200 dark:bg-lia-bg-elevated"></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="border-dashed border-2 border-lia-border-subtle dark:border-lia-border-subtle rounded-md h-64 flex items-center justify-center animate-pulse backdrop-blur-sm">
            <CardContent className="text-center">
              <div className="w-10 h-10 rounded-full mx-auto mb-3 bg-gray-200 dark:bg-lia-bg-elevated"></div>
              <div className="h-4 w-40 rounded-md mx-auto bg-gray-200 dark:bg-lia-bg-elevated"></div>
            </CardContent>
          </Card>
        </div>
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 h-[calc(100vh-280px)] min-h-[400px]">
        <div className="space-y-3 overflow-y-auto pr-2 pb-8" style={{maxHeight: 'calc(100vh - 280px)'}}>
          {filteredTemplates.length === 0 ? (
            <Card className="border border-dashed border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
              <CardContent className="p-4 text-center">
                <div className="w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2 bg-gray-100 dark:bg-lia-bg-secondary">
                  <Search className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
                <p className="text-xs lia-text-600 dark:text-lia-text-tertiary" >
                  Nenhum template encontrado
                </p>
                <p className="text-xs lia-text-400 dark:lia-text-500 mt-1" >
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
                  <AccordionItem key={groupKey} value={groupKey} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md overflow-hidden">
                    <AccordionTrigger className="px-3 py-2.5 hover:no-underline hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <div className="flex items-center gap-2 text-left">
                        <span className="text-lg">{group.icon}</span>
                        <span className="text-xs font-semibold lia-text-950 dark:lia-text-50" >
                          {group.label}
                        </span>
                        <Badge variant="outline" className="text-micro ml-1">
                          {groupTemplates.length}
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="px-2 pb-2">
                      <div className="space-y-2">
                        {groupTemplates.map((template) => (
                          <Card 
                            key={template.id}
                            className={`border cursor-pointer transition-colors rounded-md backdrop-blur-sm ${
                              selectedTemplate?.id === template.id 
                                ? 'border-gray-900 dark:lia-border-50' 
                                : 'border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default hover:'
                            }`}
                            onClick={() => setSelectedTemplate(template)}
                          >
                            <CardContent className="p-2.5">
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                  <div className={`w-7 h-7 rounded-md ${categoryLabels[template.category]?.color || 'bg-gray-50 lia-text-600'} flex items-center justify-center flex-shrink-0`}>
                                    {template.channel === 'whatsapp' ? <MessageSquare className="w-3.5 h-3.5" /> : 
                                     template.channel === 'teams' ? <MessageSquare className="w-3.5 h-3.5" /> :
                                     template.channel === 'bell' ? <Bell className="w-3.5 h-3.5" /> :
                                     <Mail className="w-3.5 h-3.5" />}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1.5">
                                      <p className="text-xs font-medium lia-text-950 dark:lia-text-50 truncate" >
                                        {template.name}
                                      </p>
                                      {template.priority && (
                                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${PRIORITY_COLORS[template.priority]}`} title={`Prioridade: ${template.priority}`} />
                                      )}
                                    </div>
                                    <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                                      {template.trigger_type && (
                                        <Badge className={`text-micro px-1.5 py-0 ${TRIGGER_TYPE_LABELS[template.trigger_type]?.color || ''}`}>
                                          {TRIGGER_TYPE_LABELS[template.trigger_type]?.label || template.trigger_type}
                                        </Badge>
                                      )}
                                      {template.used_in && template.used_in.slice(0, 2).map((usage, idx) => (
                                        <Badge key={idx} variant="outline" className="text-micro px-1.5 py-0">
                                          {usage}
                                        </Badge>
                                      ))}
                                      {template.used_in && template.used_in.length > 2 && (
                                        <Badge variant="outline" className="text-micro px-1.5 py-0">
                                          +{template.used_in.length - 2}
                                        </Badge>
                                      )}
                                    </div>
                                  </div>
                                </div>
                                <Badge variant={template.isActive ? "default" : "outline"} className="text-micro flex-shrink-0 bg-gray-900 text-white dark:lia-bg-50 dark:lia-text-900">
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

        <div className="space-y-3 lg:sticky lg:top-0 overflow-y-auto pb-20" style={{maxHeight: 'calc(100vh - 220px)'}}>
          {selectedTemplate ? (
            <>
              <div className="flex items-center justify-between">
                <h3 className={textStyles.h4}>
                  {editingTemplate ? 'Editando Template' : 'Visualização'}
                </h3>
                <div className="flex items-center gap-2">
                  {editingTemplate ? (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => setEditingTemplate(null)}>
                        <X className="w-3.5 h-3.5" />
                      </Button>
                      <Button size="sm" className="py-1.5 px-2 text-xs bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200" onClick={handleSaveTemplate}>
                        <Save className="w-3.5 h-3.5 mr-1" />
                        Salvar
                      </Button>
                    </>
                  ) : (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setEditingTemplate({ ...selectedTemplate })}
                      className="rounded-full py-1.5 px-2 text-xs border-gray-900 lia-text-900 hover:bg-gray-50 dark:lia-border-50 dark:lia-text-50 dark:hover:bg-gray-900"
                    >
                      <Edit className="w-3.5 h-3.5 mr-1" />
                      Editar
                    </Button>
                  )}
                </div>
              </div>

              <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
                <CardContent className="p-3 space-y-3">
                  {channelFilter === 'email' && (
                  <div>
                    <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1" >Assunto</label>
                    {editingTemplate ? (
                      <input
                        type="text"
                        value={editingTemplate.subject}
                        onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, subject: e.target.value } : null)}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary focus:ring-2 focus:outline-none"
                        
                      />
                    ) : (
                      <p className="text-xs lia-text-950 dark:lia-text-50 bg-gray-50 rounded-full px-2 py-1.5" >{selectedTemplate.subject}</p>
                    )}
                  </div>
                  )}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary" >
                        {channelFilter === 'email' ? 'Corpo do Email' : 'Mensagem WhatsApp'}
                      </label>
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
                        rows={10}
                        className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary focus:ring-2 focus:outline-none font-mono"
                      />
                    ) : channelFilter === 'whatsapp' ? (
                      <div className="rounded-md p-3 bg-whatsapp-bg">
                        <div className="flex justify-end">
                          <div className="bg-whatsapp-bubble rounded-md p-3 max-w-[85%]">
                            <div className="text-xs lia-text-950 dark:lia-text-50 whitespace-pre-wrap" >
                              {stripHtmlTags(selectedTemplate.body)}
                            </div>
                            <div className="text-micro lia-text-500 dark:text-lia-text-tertiary text-right mt-1" >
                              {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} ✓✓
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs lia-text-950 dark:lia-text-50 bg-gray-50 rounded-md px-3 py-2.5 whitespace-pre-wrap max-h-[300px] overflow-y-auto" >
                        {stripHtmlTags(selectedTemplate.body)}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1" >Variáveis Disponíveis</label>
                    <div className="flex flex-wrap gap-1">
                      {selectedTemplate.variables.map((v) => (
                        <Badge key={v} variant="outline" className="text-micro font-mono rounded-full border-lia-border-default lia-text-700 dark:border-lia-border-default dark:text-lia-text-secondary">
                          {`{{${v}}}`}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {editingTemplate && (
                <Card className="rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-secondary">
                        <Brain className="w-4 h-4 text-wedo-cyan" />
                      </div>
                      <div>
                        <span className={textStyles.h4}>Ajustar com a LIA</span>
                        <p className="text-xs lia-text-500 dark:text-lia-text-tertiary" >
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
                        placeholder="Ex: Torne mais formal e adicione agradecimento..."
                        disabled={isGenerating}
                        className="flex-1 px-3 py-2 text-xs border border-lia-border-subtle rounded-md bg-white focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 focus:outline-none disabled:bg-gray-50 disabled:lia-text-400 dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:focus:ring-gray-50/10 dark:focus:border-gray-50"
                        
                      />
                      <Button 
                        onClick={handleAdjustWithAI}
                        disabled={isGenerating || !aiPrompt.trim()}
                        className="gap-1.5 rounded-md py-2 px-3 text-xs min-w-[100px] bg-gray-900 text-white hover:bg-gray-800 disabled:bg-gray-400 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 dark:disabled:bg-gray-600"
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
                      <div className="flex items-center gap-2 p-2 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
                        <div className="flex gap-1">
                          <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-gray-900 dark:lia-bg-50" style={{animationDelay: '0ms'}}></span>
                          <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-gray-900 dark:lia-bg-50" style={{animationDelay: '150ms'}}></span>
                          <span className="w-1.5 h-1.5 rounded-full animate-bounce bg-gray-900 dark:lia-bg-50" style={{animationDelay: '300ms'}}></span>
                        </div>
                        <span className="text-xs lia-text-700 dark:text-lia-text-secondary" >
                          A LIA está analisando e ajustando o template...
                        </span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {aiResultModal?.show && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                  <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-md bg-lia-bg-primary">
                    <CardHeader className="border-b border-lia-border-subtle dark:border-lia-border-subtle pb-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-secondary">
                            <Brain className="w-5 h-5 text-wedo-cyan" />
                          </div>
                          <div>
                            <CardTitle className={textStyles.h3}>
                              Ajustes da LIA
                            </CardTitle>
                            <p className="text-xs lia-text-500 dark:text-lia-text-tertiary" >
                              Revise as alterações sugeridas
                            </p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={handleCancelAIAdjustment} className="rounded-md">
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="p-4 space-y-4 overflow-y-auto" style={{maxHeight: 'calc(90vh - 180px)'}}>
                      <div>
                        <label className="block text-xs font-medium lia-text-500 dark:text-lia-text-tertiary uppercase tracking-wide mb-2" >
                          Alterações Realizadas
                        </label>
                        <div className="flex flex-wrap gap-1.5">
                          {aiResultModal.changesMade.map((change, idx) => (
                            <Badge key={idx} className="text-xs px-2 py-0.5 rounded-full bg-status-success/15 text-status-success dark:bg-status-success dark:text-status-success">
                              <Check className="w-3 h-3 mr-1" />
                              {change}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      {aiResultModal.newSubject && (
                        <div>
                          <label className="block text-xs font-medium lia-text-500 dark:text-lia-text-tertiary uppercase tracking-wide mb-2" >
                            Novo Assunto
                          </label>
                          <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md text-xs lia-text-900 dark:text-lia-text-primary" >
                            {aiResultModal.newSubject}
                          </div>
                        </div>
                      )}

                      <div>
                        <label className="block text-xs font-medium lia-text-500 dark:text-lia-text-tertiary uppercase tracking-wide mb-2" >
                          Novo Conteúdo
                        </label>
                        <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md text-xs lia-text-900 dark:text-lia-text-primary whitespace-pre-wrap max-h-[300px] overflow-y-auto font-mono" >
                          {aiResultModal.newBody}
                        </div>
                      </div>

                      <div className="p-3 rounded-md border border-status-warning/30 bg-status-warning/10">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
                          <p className="text-xs text-status-warning" >
                            Ao aplicar os ajustes, o texto será atualizado no editor. Lembre-se de clicar em <strong>"Salvar"</strong> para confirmar as alterações definitivamente.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-4 flex items-center justify-end gap-3">
                      <Button variant="outline" onClick={handleCancelAIAdjustment} className="rounded-md px-4 py-2 text-xs">
                        Cancelar
                      </Button>
                      <Button 
                        onClick={handleConfirmAIAdjustment}
                        className="rounded-md px-4 py-2 text-xs gap-1.5 bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
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
            <Card className="border-dashed border-2 border-lia-border-subtle dark:border-lia-border-subtle rounded-md h-full flex items-center justify-center backdrop-blur-sm">
              <CardContent className="text-center py-8">
                <Mail className="w-10 h-10 lia-text-300 dark:lia-text-600 mx-auto mb-3" />
                <p className="text-xs lia-text-600 dark:text-lia-text-tertiary" >Selecione um template para visualizar</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      )}
    </div>
  )

  const renderSignature = () => (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs" >{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-md flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs" >{error}</span>
        </div>
      )}
      <Card className="border-0 rounded-md backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
              <PenTool className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
              Assinatura Padrão de Email
            </CardTitle>
            {!isEditingSignature ? (
              <button
                onClick={() => setIsEditingSignature(true)}
                className={actionButtonStyles.smOutline}
              >
                <Edit className={actionButtonStyles.icon} />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditingSignature(false)}
                  className={actionButtonStyles.smSecondary}
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await saveCommunicationSettings()
                    setIsEditingSignature(false)
                  }}
                  disabled={savingSettings}
                  className={actionButtonStyles.smPrimary}
                >
                  {savingSettings ? <Loader2 className={actionButtonStyles.icon} /> : <Save className={actionButtonStyles.icon} />}
                  Salvar Alterações
                </button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1" >
              Template de Assinatura
            </label>
            <textarea
              value={signature}
              onChange={(e) => setSignature(e.target.value)}
              rows={5}
              disabled={!isEditingSignature}
              className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary focus:ring-2 focus:outline-none font-mono disabled:bg-gray-50 disabled:lia-text-500"
            />
          </div>
          
          <div>
            <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1" >
              Variáveis Disponíveis
            </label>
            <div className="flex flex-wrap gap-1">
              {['recrutador_nome', 'cargo', 'empresa_nome', 'email', 'telefone', 'website', 'linkedin'].map((v) => (
                <Badge key={v} variant="outline" className="text-micro font-mono cursor-pointer hover:bg-gray-100 rounded-full border-lia-border-default lia-text-700 dark:border-lia-border-default dark:text-lia-text-secondary">
                  {`{{${v}}}`}
                </Badge>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md p-3">
            <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1.5" >
              Prévia
            </label>
            <div className="text-xs lia-text-800 dark:text-lia-text-primary whitespace-pre-wrap" >
              {signature
                .replace('{{recrutador_nome}}', 'Ana Silva')
                .replace('{{cargo}}', 'Recrutadora Sênior')
                .replace('{{empresa_nome}}', 'WedoTalent')
                .replace('{{email}}', 'ana.silva@wedotalent.com')
                .replace('{{telefone}}', '+55 11 99999-0000')
                .replace('{{website}}', 'www.wedotalent.com')}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSchedule = () => (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs" >{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-md flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs" >{error}</span>
        </div>
      )}
      <Card className="border-0 rounded-md backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
              <Clock className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
              Horários de Envio (Conformidade LGPD)
            </CardTitle>
            {!isEditingSchedule ? (
              <button
                onClick={() => setIsEditingSchedule(true)}
                className={actionButtonStyles.smOutline}
              >
                <Edit className={actionButtonStyles.icon} />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditingSchedule(false)}
                  className={actionButtonStyles.smSecondary}
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await saveCommunicationSettings()
                    setIsEditingSchedule(false)
                  }}
                  disabled={savingSettings}
                  className={actionButtonStyles.smPrimary}
                >
                  {savingSettings ? <Loader2 className={actionButtonStyles.icon} /> : <Save className={actionButtonStyles.icon} />}
                  Salvar Alterações
                </button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-status-warning/10 dark:bg-status-warning/20 rounded-md p-3 border border-status-warning/30 dark:border-status-warning/30">
            <div className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5" />
              <div>
                <p className={`${textStyles.subtitle} text-status-warning dark:text-status-warning`}>Conformidade LGPD</p>
                <p className="text-xs text-status-warning dark:text-status-warning mt-0.5" >
                  De acordo com as boas práticas de LGPD, mensagens só podem ser enviadas entre 8h e 20h em dias úteis. 
                  A LIA respeita automaticamente estes horários.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1.5" >
                Horário de Início
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={6}
                  max={12}
                  value={sendingHours.start}
                  onChange={(e) => setSendingHours(prev => ({ ...prev, start: parseInt(e.target.value) }))}
                  disabled={!isEditingSchedule}
                  className="flex-1 disabled:opacity-50 accent-gray-700"
                />
                <div className="w-14 text-center">
                  <span className="text-xs font-semibold lia-text-950 dark:lia-text-50" >{sendingHours.start}:00</span>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-micro font-medium lia-text-600 dark:text-lia-text-tertiary mb-1.5" >
                Horário de Fim
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={18}
                  max={22}
                  value={sendingHours.end}
                  onChange={(e) => setSendingHours(prev => ({ ...prev, end: parseInt(e.target.value) }))}
                  disabled={!isEditingSchedule}
                  className="flex-1 disabled:opacity-50 accent-gray-700"
                />
                <div className="w-14 text-center">
                  <span className="text-xs font-semibold lia-text-950 dark:lia-text-50" >{sendingHours.end}:00</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-micro font-medium lia-text-600" >Janela de Envio</span>
              <Badge variant="outline" className="text-micro rounded-full border-lia-border-default lia-text-700 dark:border-lia-border-default dark:text-lia-text-secondary">
                {sendingHours.end - sendingHours.start} horas/dia
              </Badge>
            </div>
            <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="absolute h-full rounded-full bg-gray-800" style={{left: `${((sendingHours.start - 6) / 18) * 100}%`, width: `${((sendingHours.end - sendingHours.start) / 18) * 100}%`}}
              />
              <div className="absolute inset-0 flex items-center justify-between px-2">
                <span className="text-micro lia-text-600" >6:00</span>
                <span className="text-micro lia-text-600" >24:00</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-micro font-semibold lia-text-600 uppercase tracking-wider" >
              Configurações Adicionais
            </h4>
            <div className="space-y-1.5">
              <label className={`flex items-center justify-between gap-3 p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md ${isEditingSchedule ? 'cursor-pointer' : 'cursor-default opacity-70'}`}>
                <span className="text-xs lia-text-800 dark:text-lia-text-primary" >Respeitar feriados nacionais</span>
                <input 
                  type="checkbox" 
                  checked={respectHolidays}
                  onChange={(e) => setRespectHolidays(e.target.checked)}
                  disabled={!isEditingSchedule}
                  className="rounded-md accent-gray-700" 
                />
              </label>
              <label className={`flex items-center justify-between gap-3 p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md ${isEditingSchedule ? 'cursor-pointer' : 'cursor-default opacity-70'}`}>
                <span className="text-xs lia-text-800 dark:text-lia-text-primary" >Não enviar nos finais de semana</span>
                <input 
                  type="checkbox" 
                  checked={respectWeekends}
                  onChange={(e) => setRespectWeekends(e.target.checked)}
                  disabled={!isEditingSchedule}
                  className="rounded-md accent-gray-700" 
                />
              </label>
              <label className={`flex items-center justify-between gap-3 p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md ${isEditingSchedule ? 'cursor-pointer' : 'cursor-default opacity-70'}`}>
                <span className="text-xs lia-text-800 dark:text-lia-text-primary" >Limite máximo de {maxMessagesPerDay} mensagens/dia por candidato</span>
                <input 
                  type="checkbox" 
                  checked={maxMessagesPerDay > 0}
                  onChange={(e) => setMaxMessagesPerDay(e.target.checked ? 3 : 0)}
                  disabled={!isEditingSchedule}
                  className="rounded-md accent-gray-700" 
                />
              </label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAlerts = () => (
    <div className="space-y-4">
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/15 border border-status-success/30 text-status-success dark:bg-status-success dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-3.5 h-3.5 text-status-success dark:text-status-success" />
          <span className="text-xs" >{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-2 py-1.5 rounded-md flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5" />
          <span className="text-xs" >{error}</span>
        </div>
      )}
      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <Bell className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
                Configuração de Alertas
              </CardTitle>
              <p className="text-xs lia-text-600 mt-0.5" >
                A LIA aprende com seus padrões e ajusta os alertas automaticamente
              </p>
            </div>
            {!isEditingAlerts ? (
              <button
                onClick={() => setIsEditingAlerts(true)}
                className={actionButtonStyles.smOutline}
              >
                <Edit className={actionButtonStyles.icon} />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditingAlerts(false)}
                  className={actionButtonStyles.smSecondary}
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await saveAlertsConfig()
                    setIsEditingAlerts(false)
                  }}
                  disabled={savingAlerts}
                  className={actionButtonStyles.smPrimary}
                >
                  {savingAlerts ? <Loader2 className={actionButtonStyles.icon} /> : <Save className={actionButtonStyles.icon} />}
                  Salvar Alterações
                </button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {alerts.map((alert) => (
            <div 
              key={alert.id}
              className={`p-2.5 rounded-md border transition-colors ${
                alert.enabled 
                  ? 'bg-white dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle' 
                  : 'bg-gray-50 dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:lia-border-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <div 
                    className="w-7 h-7 rounded-md flex items-center justify-center"
                    style={{backgroundColor: alert.enabled ? 'var(--gray-600-bg-10)' : undefined,
                      color: alert.enabled ? 'var(--gray-600)' : undefined}}
                  >
                    <Bell className="w-3.5 h-3.5" style={{color: alert.enabled ? 'var(--gray-600)' : undefined}} />
                  </div>
                  <div>
                    <p className={`text-xs font-medium ${alert.enabled ? 'lia-text-950 dark:lia-text-50' : 'lia-text-800'}`} >
                      {alert.name}
                    </p>
                    <p className="text-xs lia-text-600 mt-0.5" >{alert.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={alert.channel}
                    onChange={(e) => handleChangeChannel(alert.id, e.target.value as 'email' | 'teams' | 'both')}
                    disabled={!isEditingAlerts || !alert.enabled}
                    className="text-micro border border-lia-border-subtle dark:border-lia-border-subtle rounded-full px-1.5 py-1 bg-white dark:bg-lia-bg-secondary lia-text-900 dark:text-lia-text-primary disabled:bg-gray-50 disabled:lia-text-600"
                    
                  >
                    <option value="email">Email</option>
                    <option value="teams">Teams</option>
                    <option value="both">Ambos</option>
                  </select>
                  <button
                    onClick={() => isEditingAlerts && handleToggleAlert(alert.id)}
                    disabled={!isEditingAlerts}
                    className="relative w-9 h-5 rounded-full transition-colors disabled:opacity-60"
                    style={{backgroundColor: alert.enabled ? 'var(--gray-600)' : 'var(--gray-200)'}}
                  >
                    <span className={`absolute top-0.5 w-4 h-4 bg-lia-bg-secondary rounded-full transition-transform ${
                      alert.enabled ? 'left-4' : 'left-0.5'
                    }`} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
            <MessageSquare className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
            Frequência do Briefing da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setBriefingFrequency('twice_daily')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''}`}
              style={{borderColor: briefingFrequency === 'twice_daily' ? 'var(--gray-600)' : 'var(--gray-200)',
                backgroundColor: briefingFrequency === 'twice_daily' ? 'var(--gray-600-bg-10)' : undefined}}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <RefreshCw className="w-3.5 h-3.5" style={{color: briefingFrequency === 'twice_daily' ? 'var(--gray-600)' : undefined}} />
                <span className="text-xs font-medium" >2x ao Dia</span>
              </div>
              <p className="text-xs lia-text-600" >
                Resumo às 8h e às 14h
              </p>
            </button>
            <button
              onClick={() => setBriefingFrequency('daily')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''}`}
              style={{borderColor: briefingFrequency === 'daily' ? 'var(--gray-600)' : 'var(--gray-200)',
                backgroundColor: briefingFrequency === 'daily' ? 'var(--gray-600-bg-10)' : undefined}}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Clock className="w-3.5 h-3.5 lia-text-600 dark:text-lia-text-tertiary" />
                <span className="text-xs font-medium" >Diário</span>
              </div>
              <p className="text-xs lia-text-600" >
                Resumo todas as manhãs às 8h
              </p>
            </button>
            <button
              onClick={() => setBriefingFrequency('weekly')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''}`}
              style={{borderColor: briefingFrequency === 'weekly' ? 'var(--gray-600)' : 'var(--gray-200)',
                backgroundColor: briefingFrequency === 'weekly' ? 'var(--gray-600-bg-10)' : undefined}}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Calendar className="w-3.5 h-3.5" style={{color: (briefingFrequency === 'weekly' || briefingFrequency === 'monthly') ? 'var(--gray-600)' : undefined}} />
                <span className="text-xs font-medium" >Semanal</span>
              </div>
              <p className="text-xs lia-text-600" >
                Resumo toda segunda-feira
              </p>
            </button>
            <button
              onClick={() => setBriefingFrequency('monthly')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''}`}
              style={{borderColor: briefingFrequency === 'monthly' ? 'var(--gray-600)' : 'var(--gray-200)',
                backgroundColor: briefingFrequency === 'monthly' ? 'var(--gray-600-bg-10)' : undefined}}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Calendar className="w-3.5 h-3.5" style={{color: (briefingFrequency === 'weekly' || briefingFrequency === 'monthly') ? 'var(--gray-600)' : undefined}} />
                <span className="text-xs font-medium" >Mensal</span>
              </div>
              <p className="text-xs lia-text-600" >
                Resumo no 1º dia útil do mês
              </p>
            </button>
          </div>

          <div className="rounded-md p-2.5 bg-wedo-cyan/[.08]">
            <div className="flex items-start gap-2">
              <Brain className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-wedo-cyan" />
              <div>
                <p className={`${textStyles.subtitle} lia-text-800 dark:text-lia-text-primary`}>A LIA aprende com você</p>
                <p className="text-xs lia-text-600 mt-0.5" >
                  Quanto mais você interage, melhor ela entende quais alertas são relevantes. 
                  Alertas ignorados consistentemente serão automaticamente desativados.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderContent = () => {
    switch (activeTab) {
      case 'templates':
        return renderTemplates()
      case 'signature':
        return renderSignature()
      case 'schedule':
        return renderSchedule()
      case 'alerts':
        return renderAlerts()
      default:
        return renderTemplates()
    }
  }

  return (
    <div className="space-y-4">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  )
}
