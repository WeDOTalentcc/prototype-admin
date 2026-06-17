import { BACKEND_URL, getAuthHeaders, fetchWithRetry } from './base'
import type {
  EmailTemplate,
  EmailTemplateCreateRequest,
  EmailTemplateUpdateRequest,
  EmailTemplateListResponse,
  EmailPreviewRequest,
  EmailPreviewResponse,
  EmailSendRequest,
  EmailSendResponse,
  EmailCategory,
  DirectEmailRequest,
  DirectEmailResponse,
  EmailHistoryResponse,
  EmailSystemStatus,
} from './types'

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

  let response: Response
  try {
    response = await fetchWithRetry(
      `${BACKEND_URL}/email-templates?${params}`,
      { headers: getAuthHeaders() },
      { timeoutMs: 15000 },
    )
  } catch {
    throw new Error('Network error fetching email templates (server may be starting)')
  }

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
