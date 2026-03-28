import { BACKEND_URL, getAuthHeaders } from './base'
import type {
  CompanyBenefit,
  CompanyUsersResponse,
  NotificationsResponse,
  NotificationSummaryResponse,
  NotificationActionResponse,
  SendNotificationRequest,
  SendNotificationResponse,
  JobCreatedNotificationRequest,
  JobCreatedNotificationResponse,
  EmailTemplate,
  EmailTemplateCreateRequest,
  EmailTemplateUpdateRequest,
  EmailTemplateListResponse,
  EmailPreviewRequest,
  EmailPreviewResponse,
  EmailSendRequest,
  EmailSendResponse,
  EmailCategory,
  BulkUpdateStatusRequest,
  BulkAssignJobRequest,
  BulkSendEmailRequest,
  BulkStartScreeningRequest,
  BulkExportRequest,
  BulkDeleteRequest,
  BulkOperationResult,
  PipelineReportResponse,
  PipelineActionResponse,
  CandidateList,
  CandidateListDetail,
  CandidateListsResponse,
  AddCandidatesResult,
  RemoveCandidatesResult,
  AssignJobsResult,
  DirectEmailRequest,
  DirectEmailResponse,
  EmailHistoryResponse,
  EmailSystemStatus,
  CreateInterviewRequest,
  InterviewApiResponse,
  InterviewListResponse,
  SchedulingStatus,
  CommunicationHistoryCreate,
  CommunicationHistoryRecord,
  CommunicationHistoryListResponse,
  SharedSearch,
  SharedSearchDetail,
  CreateSharedSearchRequest,
  AddToJobRequest,
  GenerateInterviewQuestionsRequest,
  GenerateInterviewQuestionsResponse,
  GenerateInterviewParecerRequest,
  GenerateInterviewParecerResponse,
  InterviewAnalysisStatus,
  InterviewAnalysisResult,
  PendingAISuggestionsResponse,
  AISuggestionActionResponse,
  BulkAISuggestionActionResponse,
} from './types'

export async function listDepartments(companyId?: string): Promise<{ id: string; name: string; description?: string }[]> {
  try {
    const params = companyId ? `?company_id=${companyId}` : ''
    const response = await fetch(`${BACKEND_URL}/company/departments${params}`, {
      headers: getAuthHeaders(),
    })
    if (!response.ok) {
      return []
    }
    return response.json()
  } catch {
    return []
  }
}

export async function listBenefits(companyId?: string): Promise<CompanyBenefit[]> {
  try {
    const params = companyId ? `?company_id=${companyId}` : ''
    const response = await fetch(`${BACKEND_URL}/company/benefits${params}`, {
      headers: getAuthHeaders(),
    })
    if (!response.ok) {
      return []
    }
    return response.json()
  } catch {
    return []
  }
}

export async function createBenefit(benefit: Partial<CompanyBenefit>, companyId?: string): Promise<CompanyBenefit | null> {
  try {
    const params = companyId ? `?company_id=${companyId}` : ''
    const response = await fetch(`${BACKEND_URL}/company/benefits${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(benefit)
    })
    if (!response.ok) {
      return null
    }
    return await response.json()
  } catch {
    return null
  }
}

export async function getCompanyUsers(options?: { role?: string; isActive?: boolean }): Promise<CompanyUsersResponse> {
  try {
    const params = new URLSearchParams()
    if (options?.role) params.set('role', options.role)
    if (options?.isActive !== undefined) params.set('is_active', String(options.isActive))

    const queryString = params.toString()
    const url = `${BACKEND_URL}/company/users/list${queryString ? `?${queryString}` : ''}`

    const response = await fetch(url, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      return { users: [], total: 0 }
    }

    return response.json()
  } catch {
    return { users: [], total: 0 }
  }
}

export async function listEmailTemplates(
  category?: string,
  is_active?: boolean,
  search?: string,
  skip: number = 0,
  limit: number = 50,
  channel?: 'email' | 'whatsapp',
  visibility?: 'recruiter' | 'admin' | 'all'
): Promise<EmailTemplateListResponse> {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  if (is_active !== undefined) params.set('is_active', String(is_active))
  if (search) params.set('search', search)
  if (channel) params.set('channel', channel)
  if (visibility) params.set('visibility', visibility)
  params.set('skip', String(skip))
  params.set('limit', String(limit))

  const response = await fetch(`${BACKEND_URL}/email-templates?${params}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch email templates: ${response.statusText}`)
  }

  return response.json()
}

export async function getEmailTemplate(id: string): Promise<EmailTemplate> {
  const response = await fetch(`${BACKEND_URL}/email-templates/${id}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch email template: ${response.statusText}`)
  }
  return response.json()
}

export async function createEmailTemplate(data: EmailTemplateCreateRequest): Promise<EmailTemplate> {
  const response = await fetch(`${BACKEND_URL}/email-templates`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to create email template')
  }
  return response.json()
}

export async function updateEmailTemplate(id: string, data: EmailTemplateUpdateRequest): Promise<EmailTemplate> {
  const response = await fetch(`${BACKEND_URL}/email-templates/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to update email template')
  }
  return response.json()
}

export async function deleteEmailTemplate(id: string, hardDelete: boolean = false): Promise<{ message: string; id: string }> {
  const url = `${BACKEND_URL}/email-templates/${id}${hardDelete ? '?hard_delete=true' : ''}`
  const response = await fetch(url, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to delete email template')
  }
  return response.json()
}

export async function previewEmail(request: EmailPreviewRequest): Promise<EmailPreviewResponse> {
  const response = await fetch(`${BACKEND_URL}/email-templates/preview`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to preview email')
  }
  return response.json()
}

export async function sendEmail(templateId: string, request: EmailSendRequest): Promise<EmailSendResponse> {
  const response = await fetch(`${BACKEND_URL}/email-templates/${templateId}/send`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to send email')
  }
  return response.json()
}

export async function getEmailCategories(): Promise<{ categories: EmailCategory[] }> {
  const response = await fetch(`${BACKEND_URL}/email-templates/categories`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch email categories: ${response.statusText}`)
  }
  return response.json()
}

export async function bulkUpdateStatus(request: BulkUpdateStatusRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/update-status', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao atualizar status')
  }
  return response.json()
}

export async function bulkAssignJob(request: BulkAssignJobRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/assign-job', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao atribuir candidatos à vaga')
  }
  return response.json()
}

export async function bulkSendEmail(request: BulkSendEmailRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/send-email', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao enviar emails')
  }
  return response.json()
}

export async function bulkStartScreening(request: BulkStartScreeningRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/start-screening', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao iniciar triagem')
  }
  return response.json()
}

export async function bulkExport(request: BulkExportRequest): Promise<Blob | BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/export', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao exportar candidatos')
  }
  const contentType = response.headers.get('content-type')
  if (contentType?.includes('text/csv') || contentType?.includes('application/vnd.openxmlformats')) {
    return response.blob()
  }
  return response.json()
}

export async function bulkDelete(request: BulkDeleteRequest): Promise<BulkOperationResult> {
  const response = await fetch('/api/backend-proxy/candidates/bulk/delete', {
    method: 'DELETE',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao excluir candidatos')
  }
  return response.json()
}

export async function getStaleCandidates(staleDays: number = 3, limit: number = 50): Promise<PipelineReportResponse> {
  const response = await fetch(`/api/backend-proxy/pipeline/stale-candidates?stale_days=${staleDays}&limit=${limit}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao buscar candidatos parados')
  }
  return response.json()
}

export async function executePipelineAction(candidateId: string, actionId: string): Promise<PipelineActionResponse> {
  const response = await fetch('/api/backend-proxy/pipeline/action', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ candidate_id: candidateId, action_id: actionId }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
    throw new Error(error.detail || error.error || 'Falha ao executar ação')
  }
  return response.json()
}

export async function getNotifications(
  userId: string = 'default_user',
  unreadOnly: boolean = false,
  category?: string,
  limit: number = 50
): Promise<NotificationsResponse> {
  const params = new URLSearchParams()
  params.set('user_id', userId)
  params.set('limit', String(limit))
  if (unreadOnly) params.set('unread_only', 'true')
  if (category) params.set('category', category)

  try {
    const response = await fetch(`${BACKEND_URL}/notifications/?${params.toString()}`, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      return { success: false, data: { notifications: [], total: 0, unread_count: 0, urgent_count: 0, has_more: false } }
    }

    return response.json()
  } catch {
    return { success: false, data: { notifications: [], total: 0, unread_count: 0, urgent_count: 0, has_more: false } }
  }
}

export async function getNotificationSummary(userId: string = 'default_user'): Promise<NotificationSummaryResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/summary?user_id=${userId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch notification summary: ${response.statusText}`)
  }
  return response.json()
}

export async function getUnreadCount(userId: string = 'default_user'): Promise<{ success: boolean; data: { unread_count: number; urgent_count: number } }> {
  const response = await fetch(`${BACKEND_URL}/notifications/unread-count?user_id=${userId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch unread count: ${response.statusText}`)
  }
  return response.json()
}

export async function markNotificationAsRead(notificationId: string, userId: string = 'default_user'): Promise<NotificationActionResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/${notificationId}/read?user_id=${userId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to mark notification as read: ${response.statusText}`)
  }
  return response.json()
}

export async function markAllNotificationsAsRead(userId: string = 'default_user', category?: string): Promise<NotificationActionResponse> {
  const params = new URLSearchParams()
  params.set('user_id', userId)
  if (category) params.set('category', category)

  const response = await fetch(`${BACKEND_URL}/notifications/read-all?${params.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to mark all notifications as read: ${response.statusText}`)
  }
  return response.json()
}

export async function dismissNotification(notificationId: string, userId: string = 'default_user'): Promise<NotificationActionResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/${notificationId}/dismiss?user_id=${userId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to dismiss notification: ${response.statusText}`)
  }
  return response.json()
}

export async function sendNotification(request: SendNotificationRequest): Promise<SendNotificationResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/send`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to send notification')
  }
  return response.json()
}

export async function sendJobCreatedNotification(request: JobCreatedNotificationRequest): Promise<JobCreatedNotificationResponse> {
  const response = await fetch(`${BACKEND_URL}/notifications/job-created`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to send job created notification')
  }
  return response.json()
}

export async function getCandidateLists(params?: { skip?: number; limit?: number; search?: string }): Promise<CandidateListsResponse> {
  const searchParams = new URLSearchParams()
  if (params?.skip) searchParams.set('skip', params.skip.toString())
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.search) searchParams.set('search', params.search)

  const response = await fetch(`${BACKEND_URL}/candidate-lists?${searchParams.toString()}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    return { items: [], total: 0, skip: 0, limit: 50 }
  }
  return response.json()
}

export async function createCandidateList(data: { name: string; description?: string; color?: string }): Promise<CandidateList> {
  const response = await fetch(`${BACKEND_URL}/candidate-lists`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to create list: ${response.statusText}`)
  return response.json()
}

export async function getCandidateList(listId: string, params?: { skip?: number; limit?: number }): Promise<CandidateListDetail> {
  const searchParams = new URLSearchParams()
  if (params?.skip) searchParams.set('skip', params.skip.toString())
  if (params?.limit) searchParams.set('limit', params.limit.toString())

  const response = await fetch(`${BACKEND_URL}/candidate-lists/${listId}?${searchParams.toString()}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to get list: ${response.statusText}`)
  return response.json()
}

export async function updateCandidateList(listId: string, data: { name?: string; description?: string; color?: string }): Promise<CandidateList> {
  const response = await fetch(`${BACKEND_URL}/candidate-lists/${listId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to update list: ${response.statusText}`)
  return response.json()
}

export async function deleteCandidateList(listId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${BACKEND_URL}/candidate-lists/${listId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to delete list: ${response.statusText}`)
  return response.json()
}

export async function addCandidatesToList(listId: string, candidateIds: string[], notes?: string): Promise<AddCandidatesResult> {
  const response = await fetch(`${BACKEND_URL}/candidate-lists/${listId}/candidates`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ candidate_ids: candidateIds, notes }),
  })
  if (!response.ok) throw new Error(`Failed to add candidates: ${response.statusText}`)
  return response.json()
}

export async function removeCandidatesFromList(listId: string, candidateIds: string[]): Promise<RemoveCandidatesResult> {
  const response = await fetch(`${BACKEND_URL}/candidate-lists/${listId}/candidates`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
    body: JSON.stringify({ candidate_ids: candidateIds }),
  })
  if (!response.ok) throw new Error(`Failed to remove candidates: ${response.statusText}`)
  return response.json()
}

export async function assignListToJobs(listId: string, jobVacancyIds: string[], candidateIds?: string[]): Promise<AssignJobsResult> {
  const response = await fetch(`${BACKEND_URL}/candidate-lists/${listId}/assign-jobs`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ job_vacancy_ids: jobVacancyIds, candidate_ids: candidateIds }),
  })
  if (!response.ok) throw new Error(`Failed to assign to jobs: ${response.statusText}`)
  return response.json()
}

export async function sendDirectEmail(request: DirectEmailRequest): Promise<DirectEmailResponse> {
  const response = await fetch(`${BACKEND_URL}/email/send`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to send email')
  }
  return response.json()
}

export async function getEmailHistory(candidateId: string, skip: number = 0, limit: number = 50): Promise<EmailHistoryResponse> {
  const response = await fetch(`${BACKEND_URL}/email/history/${candidateId}?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to get email history: ${response.statusText}`)
  return response.json()
}

export async function getEmailSystemStatus(): Promise<EmailSystemStatus> {
  const response = await fetch(`${BACKEND_URL}/email/status`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to get email status: ${response.statusText}`)
  return response.json()
}

export async function createInterview(request: CreateInterviewRequest): Promise<InterviewApiResponse> {
  const response = await fetch(`${BACKEND_URL}/scheduling/interviews`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to create interview')
  }
  return response.json()
}

export async function listScheduledInterviews(params?: {
  candidate_id?: string
  vacancy_id?: string
  status?: string
  from_date?: string
  to_date?: string
  skip?: number
  limit?: number
}): Promise<InterviewListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.candidate_id) searchParams.set('candidate_id', params.candidate_id)
  if (params?.vacancy_id) searchParams.set('vacancy_id', params.vacancy_id)
  if (params?.status) searchParams.set('status', params.status)
  if (params?.from_date) searchParams.set('from_date', params.from_date)
  if (params?.to_date) searchParams.set('to_date', params.to_date)
  if (params?.skip) searchParams.set('skip', params.skip.toString())
  if (params?.limit) searchParams.set('limit', params.limit.toString())

  const response = await fetch(`${BACKEND_URL}/scheduling/interviews?${searchParams.toString()}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to list interviews: ${response.statusText}`)
  return response.json()
}

export async function getScheduledInterview(interviewId: string): Promise<InterviewApiResponse> {
  const response = await fetch(`${BACKEND_URL}/scheduling/interviews/${interviewId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to get interview: ${response.statusText}`)
  return response.json()
}

export async function updateScheduledInterview(interviewId: string, request: Partial<CreateInterviewRequest>): Promise<InterviewApiResponse> {
  const response = await fetch(`${BACKEND_URL}/scheduling/interviews/${interviewId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to update interview')
  }
  return response.json()
}

export async function cancelScheduledInterview(interviewId: string, reason?: string): Promise<{ success: boolean; message: string }> {
  const params = reason ? `?reason=${encodeURIComponent(reason)}` : ''
  const response = await fetch(`${BACKEND_URL}/scheduling/interviews/${interviewId}${params}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to cancel interview')
  }
  return response.json()
}

export async function downloadInterviewIcs(interviewId: string): Promise<Blob> {
  const response = await fetch(`${BACKEND_URL}/scheduling/interviews/${interviewId}/ics`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to download ICS: ${response.statusText}`)
  return response.blob()
}

export async function getSchedulingStatus(): Promise<SchedulingStatus> {
  const response = await fetch(`${BACKEND_URL}/scheduling/status`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to get scheduling status: ${response.statusText}`)
  return response.json()
}

export async function logCommunication(data: CommunicationHistoryCreate): Promise<CommunicationHistoryRecord> {
  const response = await fetch(`/api/lia/api/v1/communications`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to log communication')
  }
  return response.json()
}

export async function listCommunications(params: {
  company_id: string
  candidate_id?: string
  vacancy_id?: string
  communication_type?: string
  channel?: string
  status?: string
  limit?: number
  offset?: number
}): Promise<CommunicationHistoryListResponse> {
  const searchParams = new URLSearchParams()
  searchParams.set('company_id', params.company_id)
  if (params.candidate_id) searchParams.set('candidate_id', params.candidate_id)
  if (params.vacancy_id) searchParams.set('vacancy_id', params.vacancy_id)
  if (params.communication_type) searchParams.set('communication_type', params.communication_type)
  if (params.channel) searchParams.set('channel', params.channel)
  if (params.status) searchParams.set('status', params.status)
  if (params.limit) searchParams.set('limit', params.limit.toString())
  if (params.offset) searchParams.set('offset', params.offset.toString())

  const response = await fetch(`/api/lia/api/v1/communications?${searchParams.toString()}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to list communications: ${response.statusText}`)
  return response.json()
}

export async function getCandidateCommunications(params: {
  candidate_id: string
  company_id: string
  limit?: number
  offset?: number
}): Promise<CommunicationHistoryListResponse> {
  const searchParams = new URLSearchParams()
  searchParams.set('company_id', params.company_id)
  if (params.limit) searchParams.set('limit', params.limit.toString())
  if (params.offset) searchParams.set('offset', params.offset.toString())

  const response = await fetch(`/api/lia/api/v1/candidates/${params.candidate_id}/communications?${searchParams.toString()}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error(`Failed to get candidate communications: ${response.statusText}`)
  return response.json()
}

export async function updateCommunicationStatus(params: {
  communication_id: string
  status: string
  error_message?: string
}): Promise<CommunicationHistoryRecord> {
  const response = await fetch(`/api/lia/api/v1/communications/${params.communication_id}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      status: params.status,
      error_message: params.error_message,
    }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to update communication status')
  }
  return response.json()
}

export async function createActivity(data: {
  company_id: string
  activity_type: string
  description: string
  candidate_id?: string
  vacancy_id?: string
  performed_by?: string
  metadata?: Record<string, unknown>
}): Promise<{ id: string; created_at: string }> {
  const response = await fetch(`${BACKEND_URL}/activities`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to create activity')
  }
  return response.json()
}

export async function generateInterviewQuestions(request: GenerateInterviewQuestionsRequest): Promise<GenerateInterviewQuestionsResponse> {
  const response = await fetch(`${BACKEND_URL}/interview-notes/generate-questions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Failed to generate interview questions: ${response.statusText}`)
  }
  return response.json()
}

export async function generateInterviewParecer(request: GenerateInterviewParecerRequest): Promise<GenerateInterviewParecerResponse> {
  const response = await fetch(`${BACKEND_URL}/interview-notes/generate-parecer`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`Failed to generate interview parecer: ${response.statusText}`)
  }
  return response.json()
}

export async function saveInterviewNote(note: Record<string, unknown>): Promise<{ id: string; status: string }> {
  const response = await fetch(`${BACKEND_URL}/interview-notes`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(note),
  })
  if (!response.ok) {
    throw new Error(`Failed to save interview note: ${response.statusText}`)
  }
  return response.json()
}

export async function getInterviewAnalysisStatus(interviewId: string): Promise<InterviewAnalysisStatus> {
  const response = await fetch(`${BACKEND_URL}/interview-analysis/status/${interviewId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error('Failed to get analysis status')
  }
  return response.json()
}

export async function getInterviewAnalysisResults(interviewId: string): Promise<InterviewAnalysisResult> {
  const response = await fetch(`${BACKEND_URL}/interview-analysis/results/${interviewId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error('Failed to get analysis results')
  }
  return response.json()
}

export async function triggerInterviewAnalysis(interviewId: string, forceRefresh = false): Promise<InterviewAnalysisStatus> {
  const response = await fetch(`${BACKEND_URL}/interview-analysis/analyze/${interviewId}?force_refresh=${forceRefresh}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error('Failed to trigger analysis')
  }
  return response.json()
}

export async function executeAction(params: {
  action_type: 'email' | 'whatsapp' | 'triagem_wsi' | 'agendar_entrevista' | 'apenas_mover'
  candidate_id: string
  vacancy_id: string
  company_id: string
  channel?: 'email' | 'whatsapp'
  template_id?: string
  subject?: string
  message?: string
  metadata?: Record<string, unknown>
}): Promise<{ success: boolean; data?: Record<string, unknown>; error?: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/automation/execute-action`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action_type: params.action_type,
        candidate_id: params.candidate_id,
        vacancy_id: params.vacancy_id,
        company_id: params.company_id,
        channel: params.channel,
        template_id: params.template_id,
        subject: params.subject,
        message: params.message,
        metadata: params.metadata
      })
    })
    return await response.json()
  } catch (error) {
    return { success: false, error: String(error) }
  }
}

export async function triggerEvent(params: {
  event_type: string
  entity_id: string
  company_id: string
  entity_type?: string
  metadata?: Record<string, unknown>
}): Promise<{ success: boolean; data?: { event_type: string; entity_id: string; agents_notified: string[]; message: string }; error?: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/automation/trigger-event`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        event_type: params.event_type,
        entity_id: params.entity_id,
        company_id: params.company_id,
        entity_type: params.entity_type || 'job',
        metadata: params.metadata
      })
    })
    return await response.json()
  } catch (error) {
    return { success: false, error: String(error) }
  }
}

export async function getPendingAISuggestions(companyId: string): Promise<PendingAISuggestionsResponse> {
  const response = await fetch(`${BACKEND_URL}/automation/pending-suggestions?company_id=${companyId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch AI suggestions: ${response.statusText}`)
  }
  return response.json()
}

export async function approveAISuggestion(suggestionId: string): Promise<AISuggestionActionResponse> {
  const response = await fetch(`${BACKEND_URL}/automation/approve-suggestion/${suggestionId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to approve suggestion: ${response.statusText}`)
  }
  return response.json()
}

export async function rejectAISuggestion(suggestionId: string): Promise<AISuggestionActionResponse> {
  const response = await fetch(`${BACKEND_URL}/automation/reject-suggestion/${suggestionId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to reject suggestion: ${response.statusText}`)
  }
  return response.json()
}

export async function bulkApproveAISuggestions(suggestionIds: string[]): Promise<BulkAISuggestionActionResponse> {
  const response = await fetch(`${BACKEND_URL}/automation/bulk-approve-suggestions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ suggestion_ids: suggestionIds }),
  })
  if (!response.ok) {
    throw new Error(`Failed to bulk approve suggestions: ${response.statusText}`)
  }
  return response.json()
}

export async function bulkRejectAISuggestions(suggestionIds: string[]): Promise<BulkAISuggestionActionResponse> {
  const response = await fetch(`${BACKEND_URL}/automation/bulk-reject-suggestions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ suggestion_ids: suggestionIds }),
  })
  if (!response.ok) {
    throw new Error(`Failed to bulk reject suggestions: ${response.statusText}`)
  }
  return response.json()
}

export async function getSharedSearches(params?: { status?: string; share_type?: string; limit?: number; offset?: number }): Promise<{ total: number; items: SharedSearch[] }> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.share_type) searchParams.set('share_type', params.share_type)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())
  const response = await fetch(`${BACKEND_URL}/shared-searches?${searchParams}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to fetch shared searches')
  return response.json()
}

export async function createSharedSearch(data: CreateSharedSearchRequest): Promise<SharedSearch> {
  const response = await fetch(`${BACKEND_URL}/shared-searches`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to create shared search')
  return response.json()
}

export async function getSharedSearchDetail(id: string): Promise<SharedSearchDetail> {
  const response = await fetch(`${BACKEND_URL}/shared-searches/${id}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to fetch shared search details')
  return response.json()
}

export async function resendSharedSearchInvite(id: string, email: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${BACKEND_URL}/shared-searches/${id}/resend`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ email })
  })
  if (!response.ok) throw new Error('Failed to resend invite')
  return response.json()
}

export async function revokeSharedSearch(id: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${BACKEND_URL}/shared-searches/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to revoke shared search')
  return response.json()
}

export async function addSharedCandidatesToJob(sharedSearchId: string, data: AddToJobRequest): Promise<Record<string, unknown>> {
  const response = await fetch(`${BACKEND_URL}/shared-searches/${sharedSearchId}/add-to-job`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  })
  if (!response.ok) throw new Error('Failed to add candidates to job')
  return response.json()
}
