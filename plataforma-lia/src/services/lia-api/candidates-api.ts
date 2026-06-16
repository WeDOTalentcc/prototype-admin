import { BACKEND_URL, fetchWithRetry, getAuthHeaders } from './base'
import type {
  CandidateSearchRequest,
  CandidateSearchResponse,
  CandidateLocal,
  CandidateCreateRequest,
  CandidateListResponse,
  CandidateListParams,
  CandidatePaginatedResponse,
  StartCalibrationSessionRequest,
  StartCalibrationSessionResponse,
  SubmitCalibrationFeedbackRequest,
  CalibrationStatusResponse,
  AddCandidatesToPipelineRequest,
  AddCandidatesToPipelineResponse,
} from './types'

export async function searchCandidates(request: CandidateSearchRequest): Promise<CandidateSearchResponse> {
  const params = new URLSearchParams({
    query: request.query,
    search_type: request.search_type || 'fast',
    limit: String(request.limit || 10),
    timeout: String(request.timeout || 60),
  })

  const response = await fetchWithRetry(
    `${BACKEND_URL}/candidates/search?${params}`,
    { headers: getAuthHeaders() },
    { attempts: 2, timeoutMs: 25000 },
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Candidate search failed (${response.status})`)
  }

  return response.json()
}

export async function searchCandidatesLocal(request: { query: string; limit?: number }): Promise<CandidateSearchResponse> {
  const response = await fetchWithRetry(
    `${BACKEND_URL}/candidates/search/local/`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        filters: {
          query: request.query,
          limit: request.limit || 15,
          is_active: true
        }
      }),
    },
    { attempts: 2, timeoutMs: 25000 },
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Local candidate search failed')
  }

  return response.json()
}

export async function searchCandidatesByJobDescription(
  jobDescription: string,
  location?: string,
  limit: number = 10
): Promise<CandidateSearchResponse> {
  const response = await fetch(`${BACKEND_URL}/candidates/search/by-job-description`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      job_description: jobDescription,
      location,
      limit,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Job description search failed')
  }

  return response.json()
}

export async function checkPearchHealth(): Promise<{ service: string; status: string; api_key_set: boolean }> {
  const response = await fetch(`${BACKEND_URL}/candidates/health`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Pearch health check failed: ${response.statusText}`)
  }

  return response.json()
}

export async function getSalaryBenchmark(request: {
  job_title: string
  seniority?: string
  location?: string
  department?: string
  company_id?: string
}): Promise<{
  internal?: { min: number; max: number; median: number; sample_size: number; trend?: string }
  market?: { min: number; max: number; median: number; sources: string[]; confidence: string; learning_adjusted?: boolean }
  combined?: { min: number; max: number; median: number; confidence: string; recommendation: string }
}> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/job-wizard/salary-benchmark`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      return {}
    }

    return response.json()
  } catch {
    return {}
  }
}

export async function getCreditBalance(userId: string = "demo-user"): Promise<{
  available_credits: number
  total_consumed: number
  total_searches: number
  last_updated: string | null
}> {
  const response = await fetch(`${BACKEND_URL}/credits/balance?user_id=${userId}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Erro ao obter saldo de créditos (${response.status})`)
  }

  return response.json()
}

export async function listCandidates(search?: string, source?: string, skip: number = 0, limit: number = 50, vacancyId?: string): Promise<CandidateListResponse> {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (source) params.set('source', source)
  params.set('skip', String(skip))
  params.set('limit', String(limit))
  if (vacancyId) params.set('vacancy_id', vacancyId)

  const response = await fetch(`${BACKEND_URL}/candidates/?${params}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch candidates: ${response.statusText}`)
  }

  return response.json()
}

export async function getCandidate(id: string): Promise<CandidateLocal> {
  const response = await fetch(`${BACKEND_URL}/candidates/${id}`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch candidate: ${response.statusText}`)
  }

  return response.json()
}

export async function createCandidate(data: CandidateCreateRequest): Promise<CandidateLocal> {
  const response = await fetch(`${BACKEND_URL}/candidates`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to create candidate')
  }

  return response.json()
}

export async function updateCandidate(id: string, data: Partial<CandidateCreateRequest>): Promise<CandidateLocal> {
  const response = await fetch(`${BACKEND_URL}/candidates/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to update candidate')
  }

  return response.json()
}

export async function deleteCandidate(id: string): Promise<{ message: string; id: string }> {
  const response = await fetch(`${BACKEND_URL}/candidates/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
    throw new Error(error.detail || 'Failed to delete candidate')
  }

  return response.json()
}

export async function screenCandidate(params: {
  candidate_id: string
  vacancy_id: string
  company_id: string
}): Promise<{
  success: boolean
  data?: {
    candidate_id: string
    candidate_name: string
    vacancy_id: string
    job_title: string
    rubric_score: number
    cv_fit: {
      cv_fit_score: number
      rubric_percentage: number
      classification: string
      is_preliminary: boolean
      note: string
    }
    recommendation: string
    recommendation_label: string
    sub_status: string
    strengths: string[]
    concerns: string[]
    reasoning: string
    evaluations: Array<{
      requirement: string
      level: string
      points: number
      weighted_points: number
      evidence?: string
    }>
    evaluated_at: string
    methodology: {
      name: string
      reference: string
      scoring_formula: string
      note: string
    }
  }
  error?: string
}> {
  try {
    const response = await fetch(`${BACKEND_URL}/automation/screen-candidate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        candidate_id: params.candidate_id,
        vacancy_id: params.vacancy_id,
        company_id: params.company_id
      })
    })
    return await response.json()
  } catch (error) {
    return { success: false, error: String(error) }
  }
}

export async function startCalibrationSession(request: StartCalibrationSessionRequest): Promise<StartCalibrationSessionResponse> {
  const response = await fetch(`${BACKEND_URL}/search/calibration/start`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to start calibration session')
  }

  return response.json()
}

export async function submitCalibrationFeedback(request: SubmitCalibrationFeedbackRequest): Promise<{ success: boolean }> {
  const response = await fetch(`${BACKEND_URL}/search/calibration/feedback`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to submit calibration feedback')
  }

  return response.json()
}

export async function getCalibrationStatus(sessionId: string): Promise<CalibrationStatusResponse> {
  const response = await fetch(`${BACKEND_URL}/search/calibration/${sessionId}/status`, {
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to get calibration status')
  }

  return response.json()
}

export async function addCandidatesToPipeline(request: AddCandidatesToPipelineRequest): Promise<AddCandidatesToPipelineResponse> {
  const response = await fetch(`${BACKEND_URL}/candidates/bulk/assign-job`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      candidate_ids: request.candidate_ids,
      job_id: request.job_vacancy_id,
      source: request.source
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to add candidates to pipeline')
  }

  return response.json()
}

export async function getCandidates(params: CandidateListParams): Promise<CandidatePaginatedResponse> {
  const query = new URLSearchParams()
  if (params.search) query.set('search', params.search)
  if (params.status) query.set('status', params.status)
  if (params.tags) query.set('tags', params.tags)
  if (params.seniority) query.set('seniority', params.seniority)
  if (params.ids) query.set('ids', params.ids)
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))
  if (params.sort_by) query.set('sort_by', params.sort_by)
  if (params.sort_order) query.set('sort_order', params.sort_order)
  const qs = query.toString()
  const url = `${BACKEND_URL}/candidates${qs ? `?${qs}` : ''}`
  const response = await fetchWithRetry(
    url,
    { headers: getAuthHeaders() },
    { attempts: 3, timeoutMs: 20000, retryDelaysMs: [0, 1000, 3000] },
  )
  if (!response.ok) {
    // BUG #274: anexar status ao Error pra que o hook possa diferenciar
    // 401/403 (relogar) de 5xx (retry manual via refresh()).
    const err = new Error(`Backend retornou ${response.status}: ${response.statusText}`) as Error & { status?: number }
    err.status = response.status
    throw err
  }
  const data = await response.json()
  const rawCandidates = data?.candidates ?? data?.items ?? []
  return {
    candidates: Array.isArray(rawCandidates) ? rawCandidates : [],
    total: typeof data?.total === 'number' ? data.total : 0,
    page: typeof data?.page === 'number' ? data.page : 1,
    per_page: data?.per_page ?? data?.limit ?? params.limit ?? 20,
  }
}
