export interface EmailTemplate {
  id: string
  name: string
  subject: string
  body_html: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables: string[]
  is_active: boolean
  cc_emails?: string[]
  created_by?: string
  created_at: string
  updated_at: string
}

export interface EmailTemplateCreateRequest {
  name: string
  subject: string
  body_html: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables?: string[]
  cc_emails?: string[]
  created_by?: string
}

export interface EmailTemplateUpdateRequest {
  name?: string
  subject?: string
  body_html?: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables?: string[]
  cc_emails?: string[]
  is_active?: boolean
}

export interface EmailTemplateListResponse {
  total: number
  items: EmailTemplate[]
}

export interface EmailPreviewRequest {
  template_id?: string
  subject?: string
  body_html?: string
  body_text?: string
  variables: Record<string, unknown>
}

export interface EmailPreviewResponse {
  subject: string
  body_html: string
  body_text?: string
  variables_used: Record<string, unknown>
  missing_variables: string[]
}

export interface EmailSendRequest {
  recipient_email: string
  recipient_name?: string
  candidate_id?: string
  variables: Record<string, unknown>
  send_immediately?: boolean
  subject_override?: string
  body_override?: string
}

export interface EmailSendResponse {
  success: boolean
  email_log_id: string
  status: string
  message: string
  recipient_email: string
  subject: string
}

export interface EmailCategory {
  value: string
  label: string
  description: string
}

// =============================================
// PIPELINE TYPES
// =============================================

export interface DirectEmailRequest {
  recipient_email: string
  recipient_name?: string
  subject: string
  body_html: string
  body_text?: string
  candidate_id?: string
  vacancy_id?: string
  metadata?: Record<string, unknown>
}

export interface DirectEmailResponse {
  success: boolean
  email_id: string
  status: string
  message: string
  recipient_email: string
  subject: string
  queued_at: string
  smtp_configured: boolean
}

export interface EmailHistoryItem {
  id: string
  recipient_email: string
  subject: string
  status: string
  body_preview?: string
  template_id?: string
  sent_at?: string
  created_at: string
  error_message?: string
}

export interface EmailHistoryResponse {
  total: number
  candidate_id?: string
  items: EmailHistoryItem[]
}

export interface EmailSystemStatus {
  status: string
  mode: string
  providers: {
    smtp: { configured: boolean; host?: string }
    mailgun: { configured: boolean }
    resend: { configured: boolean }
  }
  message: string
  database_logging: boolean
  audit_trail: boolean
}
