import {
  Mail, Clock, Edit, Save, X, Eye, Trash2, Plus,
  Check, AlertCircle, Bell, Shield, Loader2, CheckCircle,
  Webhook, FileText, Globe, Server, Activity, RefreshCw,
  Copy, ExternalLink, Lock, Unlock, AlertTriangle, Users, Send,
  Zap, Play, MessageSquare, UserCheck, Calendar, Gift, ClipboardCheck,
  Grid3X3, Briefcase, Target, Settings, CheckSquare, BarChart3, Bot
} from "lucide-react"
import type { AutomationRule } from './types'

export const categoryLabels: Record<string, { label: string, color: string }> = {
  approval: { label: 'Aprovação', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  rejection: { label: 'Rejeição', color: 'bg-status-error/10 text-status-error dark:bg-status-error/20 dark:text-status-error' },
  scheduling: { label: 'Agendamento', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  followup: { label: 'Follow-up', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
  feedback: { label: 'Feedback', color: 'bg-wedo-cyan/10 text-wedo-cyan-dark dark:bg-wedo-cyan-dark/20 dark:text-wedo-cyan' },
  system: { label: 'Sistema', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' }
}

export const severityColors: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  medium: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  high: 'bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange',
  critical: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error'
}

export const moduleIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  candidate_journey: Users,
  pipeline: Briefcase,
  goals: Target,
  briefing: MessageSquare,
  system: Settings,
  approvals: CheckSquare,
  workforce: Calendar
}

export const moduleLabels: Record<string, { label: string, emoji: string }> = {
  candidate_journey: { label: 'Jornada do Candidato', emoji: '🎯' },
  pipeline: { label: 'Vagas e Pipeline', emoji: '📋' },
  goals: { label: 'Metas e Performance', emoji: '📊' },
  briefing: { label: 'Briefing da LIA', emoji: '🤖' },
  system: { label: 'Sistema e Integrações', emoji: '⚙️' },
  approvals: { label: 'Gestores e Aprovações', emoji: '✅' },
  workforce: { label: 'Planejamento de Contratações', emoji: '📅' }
}

export const recipientLabels: Record<string, { label: string, color: string }> = {
  candidate: { label: 'Candidato', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
  recruiter: { label: 'Recrutador', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' },
  manager: { label: 'Gestor', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
  admin: { label: 'Admin', color: 'bg-status-error/10 text-status-error dark:bg-status-error/20 dark:text-status-error' },
  rh: { label: 'RH', color: 'bg-teal-50 text-teal-600 dark:bg-teal-900/20 dark:text-teal-400' },
  interviewer: { label: 'Entrevistador', color: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400' },
  stakeholders: { label: 'Stakeholders', color: 'bg-pink-50 text-pink-600 dark:bg-pink-900/20 dark:text-pink-400' }
}

export const channelConfig: Record<string, { label: string, color: string, activeColor: string }> = {
  email: { label: 'Email', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
  whatsapp: { label: 'WhatsApp', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' },
  bell: { label: 'Bell', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning' },
  teams: { label: 'Teams', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple' },
  chat: { label: 'Chat', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-wedo-cyan/20 text-wedo-cyan-dark dark:bg-wedo-cyan-dark/30 dark:text-wedo-cyan' },
  log: { label: 'Log', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
  briefing: { label: 'Briefing', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning' },
  parecer: { label: 'Parecer', color: 'bg-gray-100 text-gray-500', activeColor: 'bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple' }
}

export const tabs = [
  { id: 'templates', label: 'Templates', icon: FileText },
  { id: 'matrix', label: 'Matriz', icon: Grid3X3 },
  { id: 'briefings', label: 'Briefings & Pareceres', icon: ClipboardCheck },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
  { id: 'policies', label: 'Políticas', icon: Shield },
  { id: 'alerts', label: 'Alertas Técnicos', icon: Bell },
  { id: 'automations', label: 'Automações', icon: Zap },
  { id: 'history', label: 'Histórico', icon: Clock }
]

export const defaultAutomations: AutomationRule[] = [
  {
    id: 'auto-1',
    name: 'Lembrete Triagem 24h',
    description: 'Envia lembrete por email quando candidato não completa triagem em 24h',
    trigger: 'screening_reminder_24h',
    action: 'send_email',
    templateId: 'tpl-screening-reminder',
    isActive: true,
    conditions: ['screening_not_completed', 'time_elapsed_24h'],
    lastTriggered: '2025-01-15T08:30:00',
    triggerCount: 156
  },
  {
    id: 'auto-2',
    name: 'Lembrete Entrevista 24h',
    description: 'Envia lembrete por email/WhatsApp 24h antes da entrevista',
    trigger: 'interview_reminder_24h',
    action: 'send_email',
    templateId: 'tpl-interview-reminder-24h',
    isActive: true,
    conditions: ['interview_scheduled', 'time_before_24h'],
    lastTriggered: '2025-01-15T10:00:00',
    triggerCount: 342
  },
  {
    id: 'auto-3',
    name: 'Lembrete Entrevista 1h',
    description: 'Envia lembrete por WhatsApp 1h antes da entrevista',
    trigger: 'interview_reminder_1h',
    action: 'send_whatsapp',
    templateId: 'tpl-interview-reminder-1h',
    isActive: true,
    conditions: ['interview_scheduled', 'time_before_1h'],
    lastTriggered: '2025-01-15T14:00:00',
    triggerCount: 289
  },
  {
    id: 'auto-4',
    name: 'Alerta No-Show',
    description: 'Notifica recrutador quando candidato não comparece à entrevista',
    trigger: 'no_show_alert',
    action: 'notify_recruiter',
    isActive: true,
    conditions: ['interview_time_passed', 'candidate_not_present'],
    lastTriggered: '2025-01-14T16:30:00',
    triggerCount: 23
  },
  {
    id: 'auto-5',
    name: 'Solicitação de Feedback',
    description: 'Solicita feedback do entrevistador 48h após entrevista',
    trigger: 'feedback_request_48h',
    action: 'send_email',
    templateId: 'tpl-feedback-request',
    isActive: true,
    conditions: ['interview_completed', 'time_elapsed_48h', 'feedback_not_submitted'],
    lastTriggered: '2025-01-15T09:00:00',
    triggerCount: 178
  },
  {
    id: 'auto-6',
    name: 'Prazo de Proposta',
    description: 'Lembra candidato sobre prazo de resposta da proposta',
    trigger: 'offer_deadline_reminder',
    action: 'send_email',
    templateId: 'tpl-offer-deadline',
    isActive: false,
    conditions: ['offer_sent', 'deadline_approaching'],
    lastTriggered: '2025-01-10T11:00:00',
    triggerCount: 45
  },
  {
    id: 'auto-7',
    name: 'Confirmação de Candidatura',
    description: 'Envia confirmação automática quando CV é recebido',
    trigger: 'application_received',
    action: 'send_email',
    templateId: 'tpl-application-confirmation',
    isActive: true,
    conditions: ['cv_uploaded'],
    lastTriggered: '2025-01-15T15:45:00',
    triggerCount: 1247
  },
  {
    id: 'auto-8',
    name: 'Boas-vindas Novo Usuário',
    description: 'Envia email de boas-vindas para novos usuários da plataforma',
    trigger: 'welcome_new_user',
    action: 'send_email',
    templateId: 'tpl-welcome-user',
    isActive: true,
    conditions: ['user_registered'],
    lastTriggered: '2025-01-15T12:20:00',
    triggerCount: 89
  }
]
