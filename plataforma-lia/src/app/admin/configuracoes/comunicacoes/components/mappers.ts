import type {
  SystemTemplate,
  ApiTemplate,
  WebhookConfig,
  ApiWebhook,
  GlobalPolicy,
  ApiPolicy,
  AutomationRule,
  ApiAutomation,
  CommunicationLogEntry,
  ApiCommunication,
  MatrixEntry,
  ApiMatrixEntry
} from './types'

export function mapApiTemplateToLocal(apiTemplate: ApiTemplate): SystemTemplate {
  const validCategories = ['approval', 'rejection', 'scheduling', 'followup', 'feedback', 'system'] as const
  const category = validCategories.includes(apiTemplate.category as (typeof validCategories)[number]) 
    ? (apiTemplate.category as SystemTemplate['category'])
    : 'system'
  
  return {
    id: apiTemplate.id,
    name: apiTemplate.name,
    category,
    subject: apiTemplate.subject || '',
    body: apiTemplate.body_html || '',
    variables: apiTemplate.variables || [],
    isActive: apiTemplate.is_active,
    channel: (apiTemplate.channel === 'whatsapp' ? 'whatsapp' : 'email') as 'email' | 'whatsapp',
    lastUpdated: apiTemplate.updated_at ? new Date(apiTemplate.updated_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
    usedByCompanies: 0
  }
}

export function mapApiWebhookToLocal(apiWebhook: ApiWebhook): WebhookConfig {
  const totalDeliveries = apiWebhook.total_deliveries || 0
  const successfulDeliveries = apiWebhook.successful_deliveries || 0
  const successRate = totalDeliveries > 0 ? (successfulDeliveries / totalDeliveries) * 100 : 100
  
  return {
    id: apiWebhook.id,
    name: apiWebhook.name,
    url: apiWebhook.url,
    description: apiWebhook.description || undefined,
    events: apiWebhook.events || [],
    isActive: apiWebhook.is_active,
    secret: apiWebhook.secret_key,
    headers: apiWebhook.headers || undefined,
    retryCount: apiWebhook.retry_count || 3,
    timeoutSeconds: apiWebhook.timeout_seconds || 30,
    lastTriggered: apiWebhook.last_triggered_at || undefined,
    successRate: Math.round(successRate * 10) / 10,
    totalDeliveries,
    successfulDeliveries
  }
}

export function mapApiPolicyToLocal(apiPolicy: ApiPolicy): GlobalPolicy {
  const validTypes = ['rate_limit', 'blacklist', 'whitelist', 'content_filter'] as const
  const policyType = validTypes.includes(apiPolicy.policy_type as typeof validTypes[number])
    ? (apiPolicy.policy_type as GlobalPolicy['type'])
    : 'rate_limit'
  
  const validScopes = ['platform', 'company'] as const
  const scope = validScopes.includes(apiPolicy.scope as typeof validScopes[number])
    ? (apiPolicy.scope as GlobalPolicy['scope'])
    : 'company'
  
  return {
    id: apiPolicy.id,
    name: apiPolicy.name,
    type: policyType,
    value: apiPolicy.value || {},
    description: apiPolicy.description || '',
    isActive: apiPolicy.is_active,
    scope,
    companyId: apiPolicy.company_id || undefined
  }
}

export function mapApiAutomationToLocal(apiAutomation: ApiAutomation): AutomationRule {
  const conditionStrings = (apiAutomation.conditions || []).map(c => {
    if (typeof c === 'string') return c
    if (c.field && c.value) return `${c.field}_${c.value}`
    return JSON.stringify(c)
  })
  
  return {
    id: apiAutomation.id,
    name: apiAutomation.name,
    description: apiAutomation.description || '',
    trigger: apiAutomation.trigger_type,
    action: apiAutomation.action_type,
    templateId: apiAutomation.action_config?.template_id as string | undefined,
    isActive: apiAutomation.is_active,
    conditions: conditionStrings,
    lastTriggered: apiAutomation.last_executed_at || undefined,
    triggerCount: apiAutomation.execution_count || 0
  }
}

export function mapApiCommunicationToLocal(api: ApiCommunication): CommunicationLogEntry {
  const validChannels = ['email', 'whatsapp', 'sms'] as const
  const channel = validChannels.includes(api.channel as typeof validChannels[number])
    ? (api.channel as CommunicationLogEntry['channel'])
    : 'email'
  
  const validStatuses = ['sent', 'delivered', 'read', 'failed', 'bounced', 'pending'] as const
  const status = validStatuses.includes(api.status as typeof validStatuses[number])
    ? (api.status as CommunicationLogEntry['status'])
    : 'pending'

  return {
    id: api.id,
    timestamp: api.created_at,
    channel,
    type: api.direction === 'inbound' ? 'inbound' : 'outbound',
    status,
    recipient: api.candidate_email || api.candidate_phone || api.candidate_name,
    recipientName: api.candidate_name,
    subject: api.subject,
    templateName: api.template_name,
    companyId: api.company_id,
    companyName: api.company_id,
    candidateId: api.candidate_id,
    jobId: api.vacancy_id,
    jobTitle: api.vacancy_title,
    sentBy: api.sent_by_name || api.sent_by,
    errorMessage: api.error_message,
    messagePreview: api.message_preview,
    communicationType: api.communication_type
  }
}

export function mapApiMatrixEntryToLocal(entry: ApiMatrixEntry): MatrixEntry {
  return {
    id: entry.id,
    module: entry.module,
    triggerName: entry.trigger_name,
    triggerDescription: entry.trigger_description || '',
    recipientType: entry.recipient_type,
    channels: entry.channels || [],
    isAutomatic: entry.is_automatic,
    templateId: entry.template_id,
    requiresApproval: entry.requires_approval,
    isActive: entry.is_active,
    displayOrder: entry.display_order
  }
}

export function stripHtmlToText(html: string): string {
  if (!html) return ''
  return html
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<\/div>/gi, '\n')
    .replace(/<\/h[1-6]>/gi, '\n\n')
    .replace(/<\/li>/gi, '\n')
    .replace(/<li[^>]*>/gi, '• ')
    .replace(/<\/tr>/gi, '\n')
    .replace(/<\/td>/gi, ' | ')
    .replace(/<hr[^>]*>/gi, '\n---\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
