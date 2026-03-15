export interface SystemTemplate {
  id: string
  name: string
  category: 'approval' | 'rejection' | 'scheduling' | 'followup' | 'feedback' | 'system'
  subject: string
  body: string
  variables: string[]
  isActive: boolean
  channel: 'email' | 'whatsapp'
  lastUpdated: string
  usedByCompanies: number
}

export interface ApiTemplate {
  id: string
  name: string
  category: string | null
  subject: string | null
  body_html: string
  body_text: string | null
  channel: string
  situation: string | null
  variables: string[]
  is_active: boolean
  is_system_template: boolean
  version: number
  created_at: string
  updated_at: string
}

export interface WebhookConfig {
  id: string
  name: string
  url: string
  description?: string
  events: string[]
  isActive: boolean
  secret: string
  headers?: Record<string, string>
  retryCount: number
  timeoutSeconds: number
  lastTriggered?: string
  successRate: number
  totalDeliveries?: number
  successfulDeliveries?: number
}

export interface ApiWebhook {
  id: string
  company_id: string
  name: string
  description: string | null
  url: string
  events: string[]
  secret_key: string
  headers: Record<string, string> | null
  is_active: boolean
  retry_count: number
  timeout_seconds: number
  total_deliveries: number
  successful_deliveries: number
  last_triggered_at: string | null
  created_at: string
  updated_at: string
}

export interface WebhookLog {
  id: string
  webhook_id: string
  event_type: string
  payload: Record<string, unknown>
  response_status: number | null
  response_body: string | null
  status: 'success' | 'failed' | 'pending'
  attempts: number
  last_attempt_at: string | null
  created_at: string
}

export interface WebhookEvent {
  name: string
  description: string
  category: string
  payload_example?: Record<string, unknown>
}

export interface GlobalPolicy {
  id: string
  name: string
  type: 'rate_limit' | 'blacklist' | 'whitelist' | 'content_filter'
  value: Record<string, unknown>
  description: string
  isActive: boolean
  scope: 'platform' | 'company'
  companyId?: string
}

export interface ApiPolicy {
  id: string
  company_id: string | null
  name: string
  description: string | null
  policy_type: string
  value: Record<string, unknown>
  scope: string
  is_active: boolean
  created_by: string | null
  updated_by: string | null
  created_at: string
  updated_at: string
}

export interface PolicyType {
  type: string
  description: string
  value_schema: Record<string, unknown>
}

export interface PolicyScope {
  scope: string
  description: string
}

export interface TechnicalAlert {
  id: string
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  channels: ('email' | 'slack' | 'webhook')[]
  threshold?: number
  thresholdUnit?: string
}

export interface AutomationRule {
  id: string
  name: string
  description: string
  trigger: string
  action: string
  templateId?: string
  isActive: boolean
  conditions?: string[]
  lastTriggered?: string
  triggerCount: number
}

export interface ApiAutomation {
  id: string
  name: string
  description: string | null
  trigger_type: string
  trigger_config: Record<string, unknown>
  action_type: string
  action_config: Record<string, unknown>
  conditions: Array<Record<string, unknown>>
  is_active: boolean
  priority: string
  cooldown_minutes: number
  execution_count: number
  last_executed_at: string | null
  created_by: string | null
  updated_by: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CommunicationLogEntry {
  id: string
  timestamp: string
  channel: 'email' | 'whatsapp' | 'sms'
  type: 'outbound' | 'inbound'
  status: 'sent' | 'delivered' | 'read' | 'failed' | 'bounced' | 'pending'
  recipient: string
  recipientName: string
  subject?: string
  templateName?: string
  companyId: string
  companyName: string
  candidateId?: string
  jobId?: string
  jobTitle?: string
  sentBy: string
  errorMessage?: string
  messagePreview?: string
  communicationType?: string
}

export interface ApiCommunication {
  id: string
  candidate_id: string
  candidate_name: string
  candidate_email?: string
  candidate_phone?: string
  vacancy_id?: string
  vacancy_title?: string
  communication_type: string
  channel: string
  direction: string
  subject?: string
  message_content?: string
  message_preview?: string
  template_id?: string
  template_name?: string
  attachments?: Array<Record<string, unknown>>
  status: string
  sent_by: string
  sent_by_name?: string
  company_id: string
  error_message?: string
  created_at: string
  sent_at?: string
  delivered_at?: string
  read_at?: string
  failed_at?: string
}

export interface MatrixEntry {
  id: string
  module: string
  triggerName: string
  triggerDescription: string
  recipientType: string
  channels: string[]
  isAutomatic: boolean
  templateId: string | null
  requiresApproval: boolean
  isActive: boolean
  displayOrder: number
}

export interface MatrixModule {
  module: string
  label: string
  description: string
  icon: string
  entries: MatrixEntry[]
  totalEntries: number
  activeEntries: number
}

export interface ApiMatrixEntry {
  id: string
  company_id: string | null
  module: string
  trigger_name: string
  trigger_description: string | null
  recipient_type: string
  channels: string[]
  is_automatic: boolean
  template_id: string | null
  requires_approval: boolean
  is_active: boolean
  display_order: number
  created_at: string
  updated_at: string
}

export type TemplateChannelFilter = 'email' | 'whatsapp' | 'bell' | 'teams' | 'chat_lia' | 'report' | 'briefing' | 'parecer'

export type HistoryChannelFilter = 'all' | 'email' | 'whatsapp' | 'sms'

export type HistoryStatusFilter = 'all' | 'sent' | 'delivered' | 'read' | 'failed' | 'bounced' | 'pending'

export type HistoryPeriodFilter = 'today' | '7days' | '30days' | 'custom'
