import {
  Mail, Bell, MessageSquare, FileText, Brain,
} from "lucide-react"

export const TEMPLATE_GROUPS: Record<string, { label: string; icon: string; situations: string[] }> = {
  'alertas': { label: 'Alertas', icon: '🔔', situations: ['critical_alert', 'sla_violated', 'no_show_alert', 'approval_pending', 'approval_expired', 'goal_at_risk', 'goal_missed', 'ats_sync_failed', 'credits_low', 'workforce_variance'] },
  'relatorios': { label: 'Relatórios', icon: '📊', situations: ['briefing', 'end_of_day_summary', 'weekly_summary', 'monthly_summary', 'monthly_report', 'team_report', 'job_executive_report', 'weekly_performance', 'daily_briefing'] },
  'workflow': { label: 'Workflow', icon: '⚙️', situations: ['approval_pending', 'approval_expired', 'screening_completed'] },
  'parecer': { label: 'Parecer LIA', icon: '🤖', situations: ['lia_opinion_compact', 'lia_opinion_detailed'] },
  'integrações': { label: 'Integrações', icon: '🔗', situations: ['ats_sync_failed', 'welcome_user'] },
  'outros': { label: 'Outros', icon: '📌', situations: [] }
}

export const TRIGGER_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  'automatic': { label: 'Automático', color: 'bg-wedo-cyan/15 text-wedo-cyan-dark dark:text-wedo-cyan-dark' },
  'manual': { label: 'Manual', color: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' },
  'both': { label: 'Ambos', color: 'bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple' }
}

export const PRIORITY_COLORS: Record<string, string> = {
  'high': 'bg-status-error',
  'medium': 'bg-status-warning',
  'low': 'bg-lia-border-medium'
}

export const CHANNEL_LABELS: Record<string, { label: string; color: string }> = {
  'email': { label: 'Email', color: 'bg-wedo-cyan/10 text-wedo-cyan-dark dark:text-wedo-cyan-dark' },
  'whatsapp': { label: 'WhatsApp', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  'bell': { label: 'Bell', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
  'teams': { label: 'Teams', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' },
  'briefing': { label: 'Briefing', color: 'bg-lia-bg-secondary text-lia-text-primary dark:bg-lia-bg-secondary' },
  'parecer': { label: 'Parecer', color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple' },
  'report': { label: 'Report', color: 'bg-wedo-magenta/10 text-wedo-magenta dark:bg-wedo-magenta/20 dark:text-wedo-magenta' },
  'chat_lia': { label: 'Chat LIA', color: 'bg-wedo-cyan/10 text-wedo-cyan dark:bg-wedo-cyan/20 dark:text-wedo-cyan' }
}

export interface EmailTemplate {
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

export type ChannelFilter = 'all' | 'email' | 'whatsapp' | 'teams' | 'bell' | 'briefing' | 'parecer' | 'report'
export type TriggerTypeFilter = 'all' | 'automatic' | 'manual' | 'both'

export interface AIResultModal {
  show: boolean
  newSubject: string
  newBody: string
  changesMade: string[]
}

export const stripHtmlTags = (html: string): string => {
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
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+/g, ' ')
    .trim()
  
  return text
}

export const getChannelIcon = (channel: string) => {
  switch (channel) {
    case 'whatsapp': return MessageSquare
    case 'teams': return MessageSquare
    case 'bell': return Bell
    case 'briefing': return FileText
    case 'parecer': return Brain
    case 'report': return FileText
    case 'chat_lia': return MessageSquare
    default: return Mail
  }
}
