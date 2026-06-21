import {
  BACKEND_URL,
  getAuthHeaders,
  checkPaymentRequired,
  fetchWithRetry,
  HttpError,
  parseRetryAfterMs,
} from './base'
import { unwrapEnvelopeSuccess } from '@/lib/api/unwrapEnvelope'
import type {
  JobVacancy,
  JobVacancyCreateRequest,
  JobVacancyListResponse,
  JobVacancyMetrics,
  PublishJobResponse,
  GlobalSearchConfirmResponse,
  SourcingStatusResponse,
  VacancySearchCriteria,
  VacancySearchResponse,
  VacancyFullDetails,
  VacancyAdjustments,
  PublishFastTrackResponse,
} from './types'

export async function healthCheck(): Promise<{ status: string; app: string; environment: string }> {
  const response = await fetch(`${BACKEND_URL}/health`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`)
  }
  return response.json()
}

export async function listJobVacancies(status?: string, skip: number = 0, limit: number = 50): Promise<JobVacancyListResponse> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  params.set('skip', String(skip))
  params.set('limit', String(limit))

  const url = `${BACKEND_URL}/job-vacancies?${params}`

  const response = await fetchWithRetry(
    url,
    { headers: getAuthHeaders() },
    { timeoutMs: 20000, attempts: 1 },
  )

  if (!response.ok) {
    const retryAfterMs = parseRetryAfterMs(response.headers.get('Retry-After')) ?? undefined
    const detail = response.statusText || `HTTP ${response.status}`
    throw new HttpError(
      response.status,
      `Failed to fetch job vacancies: ${detail}`,
      { retryAfterMs },
    )
  }

  return response.json()
}

export async function getJobVacancy(id: string): Promise<JobVacancy> {
  // Hard timeout so a hanging backend (e.g. Rails bridge stuck) never leaves
  // the detail page spinner stuck forever (Task #241).
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15000)

  try {
    const response = await fetch(`${BACKEND_URL}/job-vacancies/${id}`, {
      headers: getAuthHeaders(),
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch job vacancy: ${response.statusText}`)
    }

    return unwrapEnvelopeSuccess(await response.json()) as JobVacancy
  } finally {
    clearTimeout(timeout)
  }
}

export async function createJobVacancy(data: JobVacancyCreateRequest): Promise<JobVacancy> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  await checkPaymentRequired(response)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to create job vacancy')
  }

  return unwrapEnvelopeSuccess(await response.json()) as JobVacancy
}

export async function updateJobVacancy(id: string, data: Partial<JobVacancyCreateRequest>): Promise<JobVacancy> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to update job vacancy')
  }

  return unwrapEnvelopeSuccess(await response.json()) as JobVacancy
}

export async function deleteJobVacancy(id: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to delete job vacancy')
  }

  return response.json()
}

export async function updateJobVacancyStatus(
  id: string,
  status: string,
  options?: {
    close_reason?: string
    notify_stages?: string[]
    notification_channel?: string
    notification_message?: string
    notification_subject?: string
    pause_reason?: string
  }
): Promise<{ success: boolean; old_status: string; new_status: string; notifications_sent?: { success_count: number; failure_count: number; details?: Array<{ candidate_id: string; success?: boolean; error?: string }> } }> {
  const body: Record<string, unknown> = { status, ...options }
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${id}/status`, {
    method: 'PATCH',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to update job vacancy status')
  }

  return response.json()
}

export async function updateJobVacancyStatusWithOutcome(
  id: string,
  status: string,
  companyId: string
): Promise<{ success: boolean; old_status: string; new_status: string }> {
  const result = await updateJobVacancyStatus(id, status)

  if (result.success) {
    type OutcomeStatus = 'cancelled' | 'hired' | 'closed' | 'filled' | 'expired'
    const outcomeStatusMap: Record<string, OutcomeStatus | 'paused'> = {
      'Cancelada': 'cancelled',
      'Fechada (preenchida)': 'hired',
      'Concluída': 'closed',
      'Paralisada': 'paused',
    }

    const outcomeStatus = outcomeStatusMap[status]
    if (outcomeStatus && outcomeStatus !== 'paused') {
      updateJobOutcome({
        company_id: companyId,
        job_id: id,
        outcome_status: outcomeStatus,
      }).catch((err) => { console.warn('[jobs-api] updateJobOutcome fire-and-forget failed', err) })
    }
  }

  return result
}

export async function sendRecruiterActionNotification(data: {
  recruiter_ids: string[]
  action: string
  job_titles: string[]
  job_ids: string[]
  channels: string[]
  reason?: string
  cancelled_screenings?: boolean
  cancelled_interviews?: boolean
  cancelled_tests?: boolean
  notified_candidates_count?: number
  performed_by?: string
}): Promise<{ success: boolean; message: string; data: { notifications_sent: number; channels: string[] } }> {
  const response = await fetch(`${BACKEND_URL}/notifications/recruiter-action`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to send recruiter notification')
  }

  return response.json()
}

export async function transferCommunications(data: {
  job_ids: string[]
  from_recruiter_ids: string[]
  to_recruiter_id: string
}): Promise<{ success: boolean; transferred_count: number }> {
  const response = await fetch(`${BACKEND_URL}/communications/transfer`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to transfer communications')
  }

  return response.json()
}

export async function generatePublicLink(vacancyId: string, regenerate: boolean = false): Promise<{ success: boolean; public_url: string; slug: string; message: string }> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${vacancyId}/generate-public-link`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ regenerate }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to generate public link')
  }

  return response.json()
}

export async function publishToLinkedIn(jobId: string): Promise<{
  success: boolean
  message: string
  platform: string
  job_id: string
  post_id?: string
  job_title?: string
  published_at?: string
  job_url?: string
  mock?: boolean
}> {
  const response = await fetch(`${BACKEND_URL}/job-boards/linkedin/publish/${jobId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to publish to LinkedIn')
  }

  return response.json()
}

export async function publishToIndeed(jobId: string): Promise<{
  success: boolean
  message: string
  platform: string
  job_id: string
  vacancy_id?: string
  job_title?: string
  published_at?: string
  feed_url?: string
  job_url?: string
  note?: string
}> {
  const response = await fetch(`${BACKEND_URL}/job-boards/indeed/publish/${jobId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to publish to Indeed')
  }

  return response.json()
}

export async function getJobPublishingStatus(jobId: string): Promise<{
  job_id: string
  job_title: string
  platforms: {
    linkedin: { published: boolean; post_id?: string; url?: string }
    indeed: { published: boolean; job_id?: string; feed_url?: string }
    website: { published: boolean; url?: string }
  }
  last_published_at?: string
}> {
  const response = await fetch(`${BACKEND_URL}/job-boards/status/${jobId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to get publishing status')
  }

  return response.json()
}

export async function unpublishFromPlatform(jobId: string, platform: 'linkedin' | 'indeed'): Promise<{
  success: boolean
  message: string
  platform: string
  job_id: string
  old_post_id?: string
  old_indeed_id?: string
}> {
  const response = await fetch(`${BACKEND_URL}/job-boards/unpublish/${jobId}/${platform}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || `Failed to unpublish from ${platform}`)
  }

  return response.json()
}

export async function publishToMultiplePlatforms(jobIds: string[], platforms: string[]): Promise<{
  success: boolean
  results: Array<{
    job_id: string
    platforms?: Record<string, unknown>
    success?: boolean
    error?: string
  }>
  summary: {
    total_jobs: number
    platforms: string[]
  }
}> {
  const response = await fetch(`${BACKEND_URL}/job-boards/publish-batch`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ job_ids: jobIds, platforms }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to publish to platforms')
  }

  return response.json()
}

export async function getJobVacanciesOverview(recruiterEmail?: string): Promise<{
  my_jobs: {
    active: number
    completed: number
    time_to_fill_avg: number
    candidates_interviewed: number
    conversion_rate: number
    candidates_in_funnel: number
    interviews_last_7d: number
    offers_sent: number
  }
  active_jobs: {
    total: number
    avg_days_open: number
    at_risk: number
    by_urgency: Record<string, number>
    empty_pipeline: number
    deadline_soon: number
  }
  all_jobs: {
    time_to_fill_avg_90d: number
    success_rate: number
    hired_last_30d: number
    hired_last_90d: number
    within_sla_pct: number
    by_department: Record<string, number>
    trend_weeks: Array<{ week: string; hired: number; opened: number }>
  }
  insights: Array<{
    type: string
    message: string
    severity: string
    action?: string
  }>
}> {
  const params = new URLSearchParams()
  if (recruiterEmail) params.set('recruiter_email', recruiterEmail)

  const queryString = params.toString()
  const url = `${BACKEND_URL}/job-vacancies/stats/overview${queryString ? `?${queryString}` : ''}`

  const response = await fetchWithRetry(
    url,
    { headers: getAuthHeaders() },
    { timeoutMs: 15000 },
  )

  if (!response.ok) {
    const retryAfterMs = parseRetryAfterMs(response.headers.get('Retry-After')) ?? undefined
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new HttpError(
      response.status,
      error.detail || `Failed to fetch job vacancies overview: HTTP ${response.status}`,
      { retryAfterMs },
    )
  }

  return response.json()
}

export async function publishJobVacancy(jobId: string, triggerSourcing: boolean = true): Promise<PublishJobResponse> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${jobId}/publish`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ trigger_sourcing: triggerSourcing })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to publish job')
  }
  return response.json()
}

export async function duplicateJobVacancy(jobId: string, options: {
  copies?: number
  includeCandiates?: boolean
  candidateFilter?: 'all' | 'approved' | null
  overrides?: {
    title?: string
    recruiter?: string
    recruiter_email?: string
    status?: string
    deadline_shortlist?: string
    deadline_screening?: string
    deadline_closing?: string
  }
} = {}): Promise<{
  success: boolean
  total_jobs_created: number
  total_candidates_cloned: number
  jobs: Array<{ id: string; job_id: string; title: string }>
}> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${jobId}/duplicate`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      copies: options.copies || 1,
      include_candidates: options.includeCandiates ?? false,
      candidate_filter: options.candidateFilter || null,
      overrides: options.overrides
    })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to duplicate job')
  }
  return response.json()
}

export async function confirmGlobalSearch(jobId: string, creditsToUse: number = 20): Promise<GlobalSearchConfirmResponse> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${jobId}/confirm-global-search`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ credits_to_use: creditsToUse })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to confirm global search')
  }
  return response.json()
}

export async function getSourcingStatus(jobId: string): Promise<SourcingStatusResponse> {
  const response = await fetch(`${BACKEND_URL}/job-vacancies/${jobId}/sourcing-status`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to get sourcing status')
  }
  return response.json()
}

function getDefaultJobVacancyMetrics(jobId: string): JobVacancyMetrics {
  return {
    job_id: jobId,
    funnel: { total: 0, screening: 0, interview: 0, offer: 0, hired: 0, rejected: 0 },
    performance: { time_to_fill_days: null, avg_time_in_stage_days: null, conversion_rate: 0, source_breakdown: {} },
    activity: { views_7d: 0, applications_7d: 0, interviews_scheduled: 0, last_activity: null },
    sla: { within_sla: true, days_remaining: null, deadline: null }
  }
}

export async function getJobVacancyMetrics(jobId: string): Promise<JobVacancyMetrics> {
  try {
    const response = await fetch(`${BACKEND_URL}/job-vacancies/${jobId}/metrics`, {
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      return getDefaultJobVacancyMetrics(jobId)
    }

    return response.json()
  } catch {
    return getDefaultJobVacancyMetrics(jobId)
  }
}

export async function searchPreviousVacancies(criteria: VacancySearchCriteria): Promise<VacancySearchResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/job-vacancies/search`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(criteria)
    })
    if (!response.ok) {
      return { vacancies: [], total: 0 }
    }
    return response.json()
  } catch {
    return { vacancies: [], total: 0 }
  }
}

export async function getVacancyFullDetails(vacancyId: string): Promise<VacancyFullDetails | null> {
  try {
    const response = await fetch(`${BACKEND_URL}/job-vacancies/${vacancyId}`, {
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      return null
    }
    const data = await response.json()
    return {
      id: data.id,
      title: data.title,
      department: data.department || '',
      location: data.location || '',
      work_model: data.work_model || 'onsite',
      employment_type: data.employment_type || 'full_time',
      salary_range: {
        min: data.salary_min || data.salary_range?.min || 0,
        max: data.salary_max || data.salary_range?.max || 0,
        bonus_min: data.bonus_min || data.salary_range?.bonus_min,
        bonus_max: data.bonus_max || data.salary_range?.bonus_max
      },
      benefits: data.benefits || [],
      technical_skills: (data.technical_skills || data.requirements?.technical_skills || []).map((s: Record<string, unknown>) => ({
        name: s.name || s.skill,
        level: s.level || 'Intermediário',
        weight: s.weight || 3,
        required: s.required ?? true
      })),
      behavioral_competencies: (data.behavioral_competencies || data.requirements?.behavioral_competencies || []).map((c: Record<string, unknown>) => ({
        name: c.name || c.competency,
        weight: c.weight || 3
      })),
      screening_questions: (data.screening_questions || []).map((q: Record<string, unknown>) => ({
        question: q.question || q.text,
        type: q.type || 'open',
        expected_answer: q.expected_answer || q.expectedAnswer
      })),
      job_description: data.job_description || data.description || '',
      manager: data.hiring_manager || data.manager || '',
      manager_email: data.hiring_manager_email || data.manager_email || ''
    }
  } catch {
    return null
  }
}

export async function publishFastTrackVacancy(vacancyId: string, adjustments: VacancyAdjustments): Promise<PublishFastTrackResponse> {
  try {
    const updatePayload: Record<string, unknown> = {}
    if (adjustments.salary_min !== undefined) updatePayload.salary_min = adjustments.salary_min
    if (adjustments.salary_max !== undefined) updatePayload.salary_max = adjustments.salary_max
    if (adjustments.location !== undefined) updatePayload.location = adjustments.location
    if (adjustments.work_model !== undefined) updatePayload.work_model = adjustments.work_model
    if (adjustments.benefits !== undefined) updatePayload.benefits = adjustments.benefits

    const createResponse = await fetch(`${BACKEND_URL}/job-vacancies`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        ...updatePayload,
        clone_from_id: vacancyId,
        status: 'published'
      })
    })

    if (!createResponse.ok) {
      const error = await createResponse.json().catch(() => ({ detail: createResponse.statusText }))
      return {
        success: false,
        message: error.detail || 'Falha ao publicar a vaga'
      }
    }

    const newVacancy = await createResponse.json()
    return {
      success: true,
      vacancy_id: newVacancy.id,
      message: 'Vaga publicada com sucesso!'
    }
  } catch {
    return {
      success: false,
      message: 'Erro ao publicar a vaga. Tente novamente.'
    }
  }
}

export async function recordFastTrackUsage(params: {
  company_id: string
  source_job_id: string
  new_job_id: string
  modified_fields: string[]
  was_published: boolean
}): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/job-embeddings/fast-track/record-usage`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(params)
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return { success: false, error: error.detail }
    }

    return { success: true }
  } catch (error) {
    return { success: false, error: String(error) }
  }
}

export async function updateJobOutcome(params: {
  company_id: string
  job_id: string
  outcome_status: 'filled' | 'hired' | 'cancelled' | 'expired' | 'closed' | 'closed_no_hire'
  time_to_fill_days?: number
  hire_quality_score?: number
}): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/job-embeddings/outcome`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(params)
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return { success: false, error: error.detail }
    }

    return { success: true }
  } catch (error) {
    return { success: false, error: String(error) }
  }
}

// ---------------------------------------------------------------------------
// bulk archive / unarchive — arquivamento em lote de vagas
// ---------------------------------------------------------------------------

export interface BulkJobActionRequest {
  job_ids: string[]
}

export interface BulkJobActionResponse {
  total_requested: number
  successful: number
  failed: number
  errors: Array<{ job_id: string; error_message: string }>
}

export async function archiveJobs(jobIds: string[]): Promise<BulkJobActionResponse> {
  const response = await fetch("/api/backend-proxy/job-vacancies/bulk/archive", {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ job_ids: jobIds } satisfies BulkJobActionRequest),
  })
  const payload = (await response.json().catch(() => ({}))) as BulkJobActionResponse
  if (!response.ok) {
    throw new Error((payload as Record<string, unknown>)?.detail as string || response.statusText || "Falha ao arquivar vagas")
  }
  return payload
}

export async function unarchiveJobs(jobIds: string[]): Promise<BulkJobActionResponse> {
  const response = await fetch("/api/backend-proxy/job-vacancies/bulk/unarchive", {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ job_ids: jobIds } satisfies BulkJobActionRequest),
  })
  const payload = (await response.json().catch(() => ({}))) as BulkJobActionResponse
  if (!response.ok) {
    throw new Error((payload as Record<string, unknown>)?.detail as string || response.statusText || "Falha ao desarquivar vagas")
  }
  return payload
}

