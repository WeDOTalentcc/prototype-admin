export interface SendNotificationRequest {
  user_id: string
  title: string
  message: string
  notification_type: string
  related_job_id?: string
  action_url?: string
}

export interface SendNotificationResponse {
  success: boolean
  notification_id: string
}

export interface CommunicationHistoryCreate {
  company_id: string
  candidate_id: string
  candidate_name?: string
  candidate_email?: string
  candidate_phone?: string
  vacancy_id?: string
  communication_type: 'email' | 'whatsapp' | 'triagem' | 'agendamento' | 'feedback' | 'phone' | 'sms'
  channel: 'email' | 'whatsapp' | 'phone' | 'sms' | 'chat'
  direction: 'inbound' | 'outbound'
  subject?: string
  message_content: string
  sent_by?: string
  template_id?: string
  metadata?: Record<string, unknown>
}

export interface CommunicationHistoryRecord extends CommunicationHistoryCreate {
  id: string
  status: 'pending' | 'sent' | 'delivered' | 'read' | 'failed' | 'bounced'
  sent_at?: string
  delivered_at?: string
  read_at?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface CommunicationHistoryListResponse {
  total: number
  items: CommunicationHistoryRecord[]
  limit: number
  offset: number
}

// =============================================
// JOB VACANCIES TYPES
// =============================================

export interface BackendNotification {
  id: string
  user_id: string
  title: string
  message: string | null
  notification_type: string
  proactive_type: string | null
  category: string | null
  priority: string
  source_agent: string | null
  source_trigger: string | null
  related_job_id: string | null
  related_candidate_id: string | null
  related_task_id: string | null
  action_url: string | null
  action_label: string | null
  is_read: boolean
  read_at: string | null
  is_dismissed: boolean
  channels: string[]
  channels_sent: string[]
  extra_data: Record<string, unknown>
  created_at: string
  expires_at: string | null
}

export interface NotificationsResponse {
  success: boolean
  data: {
    notifications: BackendNotification[]
    total: number
    unread_count: number
    urgent_count: number
    has_more: boolean
  }
}

export interface NotificationSummaryResponse {
  success: boolean
  data: {
    unread_count: number
    urgent_count: number
    by_category?: Record<string, number>
    by_type?: Record<string, number>
  }
}

export interface NotificationActionResponse {
  success: boolean
  message: string
}

// =============================================
// CANDIDATE LISTS TYPES
// =============================================
