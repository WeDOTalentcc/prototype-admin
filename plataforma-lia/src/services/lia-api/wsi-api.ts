import { BACKEND_URL, getAuthHeaders } from './base'
import type {
  GenerateQuestionsRequest,
  GenerateQuestionsResponse,
  AnalyzeResponseRequest,
  AnalyzeResponseResponse,
  CalculateWSIRequest,
  CalculateWSIResponse,
  WSISessionResponse,
  WSIResultsResponse,
  WSIResultDetails,
  WSIVacancyRanking,
  WSICandidateRanking,
  StartVoiceScreeningRequest,
  StartVoiceScreeningResponse,
  VoiceScreeningStatusResponse,
  WSICandidatesScores,
  RegenerateWSIQuestionsRequest,
  RegenerateWSIQuestionsResponse,
} from './types'

export async function wsiGenerateQuestions(request: GenerateQuestionsRequest): Promise<GenerateQuestionsResponse> {
  const response = await fetch(`/api/lia/api/wsi/generate-questions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to generate WSI questions')
  }
  return response.json()
}

export async function wsiAnalyzeResponse(request: AnalyzeResponseRequest): Promise<AnalyzeResponseResponse> {
  const response = await fetch(`/api/lia/api/wsi/analyze-response`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to analyze response')
  }
  return response.json()
}

export async function wsiCalculateScore(request: CalculateWSIRequest): Promise<CalculateWSIResponse> {
  const response = await fetch(`/api/lia/api/wsi/calculate-wsi`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to calculate WSI')
  }
  return response.json()
}

export async function wsiGetSession(sessionId: string): Promise<WSISessionResponse> {
  const response = await fetch(`/api/lia/api/wsi/sessions/${sessionId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get WSI session: ${response.statusText}`)
  }
  return response.json()
}

export async function wsiGetCandidateResults(candidateId: string, limit: number = 10): Promise<WSIResultsResponse> {
  const response = await fetch(`/api/lia/api/wsi/results/candidate/${candidateId}?limit=${limit}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get candidate WSI results: ${response.statusText}`)
  }
  return response.json()
}

export async function wsiGetResultDetails(resultId: string): Promise<WSIResultDetails> {
  const response = await fetch(`/api/lia/api/wsi/results/${resultId}/details`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get WSI result details: ${response.statusText}`)
  }
  return response.json()
}

export async function wsiGetVacancyRanking(jobVacancyId: string): Promise<WSIVacancyRanking> {
  const response = await fetch(`/api/lia/api/wsi/ranking/${jobVacancyId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get vacancy ranking: ${response.statusText}`)
  }
  return response.json()
}

export async function wsiGetCandidateRanking(candidateId: string, jobVacancyId: string): Promise<WSICandidateRanking> {
  const response = await fetch(`/api/lia/api/wsi/candidate/${candidateId}/ranking/${jobVacancyId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get candidate ranking: ${response.statusText}`)
  }
  return response.json()
}

export async function wsiStartVoiceScreening(request: StartVoiceScreeningRequest): Promise<StartVoiceScreeningResponse> {
  const response = await fetch(`/api/lia/api/wsi/start-voice-screening`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to start voice screening')
  }
  return response.json()
}

export async function wsiGetVoiceScreeningStatus(sessionId: string): Promise<VoiceScreeningStatusResponse> {
  const response = await fetch(`/api/lia/api/wsi/voice-screening/${sessionId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to get voice screening status: ${response.statusText}`)
  }
  return response.json()
}

export async function updateScreeningStatus(jobId: string, status: string, extraData?: { pause_reason?: string; scheduled_end_date?: string }): Promise<Record<string, unknown>> {
  const response = await fetch(`${BACKEND_URL}/api/v1/vagas/${jobId}/screening-status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      screening_status: status,
      ...extraData,
    }),
  })
  if (!response.ok) {
    throw new Error(`Failed to update screening status: ${response.statusText}`)
  }
  return response.json()
}

// Bug #303: 401 do middleware no `/api/lia/*` (sessão expirada) era convertido
// num `Error` cru, estourando no overlay do Next. Agora:
//   - Anexa `err.status` para que consumers possam diferenciar 401/403 de 5xx.
//   - Em 401, dispara o mesmo fluxo de relogin usado pelo restante do app
//     (mesmo handler do `useSessionRefresh` → `/login?reason=session_expired`),
//     evitando que o usuário fique preso numa página sem dados.
//   - Preserva `detail` do backend quando presente.
//
// As demais funções deste módulo continuam com o tratamento legado; só foi
// normalizado o caminho usado pelo kanban (escopo da task #303).
function handleSessionExpiredRedirect(): void {
  if (typeof window === 'undefined') return
  if (window.location.pathname.startsWith('/login')) return
  window.location.href = '/login?reason=session_expired'
}

async function buildWsiError(response: Response, fallbackMessage: string): Promise<Error & { status: number }> {
  let message = fallbackMessage
  try {
    const body = await response.json()
    if (body?.detail && typeof body.detail === 'string') message = body.detail
    else if (body?.error && typeof body.error === 'string') message = body.error
  } catch {
    if (response.statusText) message = `${fallbackMessage}: ${response.statusText}`
  }
  const err = new Error(message) as Error & { status: number }
  err.status = response.status
  return err
}

export async function wsiGetCandidatesScores(jobVacancyId: string): Promise<WSICandidatesScores> {
  const response = await fetch(`/api/lia/api/wsi/candidates/${jobVacancyId}/scores`, {
    headers: getAuthHeaders(),
    credentials: 'include',
  })
  if (!response.ok) {
    const err = await buildWsiError(response, 'Failed to get candidates WSI scores')
    if (response.status === 401 || response.status === 403) {
      handleSessionExpiredRedirect()
    }
    throw err
  }
  return response.json()
}

export async function wsiTriggerFeedback(resultId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/lia/api/wsi/results/${resultId}/trigger-feedback`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to trigger feedback')
  }
  return response.json()
}

export async function wsiGetFeedbackStatus(resultId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/lia/api/wsi/results/${resultId}/feedback-status`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to get feedback status')
  }
  return response.json()
}

export async function generateJobScreeningQuestions(request: {
  job_title: string
  job_description?: string
  technical_skills?: string[]
  behavioral_competencies?: string[]
  seniority_level?: string
  work_model?: string
  location?: string
  count?: number
  category?: 'technical' | 'behavioral'
}): Promise<{
  questions: Array<{
    id: string
    question: string
    type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
    required: boolean
    options?: string[]
    expected_answer?: string | number | boolean
    correct_option_index?: number
    competency?: string
    framework?: string
    category?: 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
  }>
  total_generated: number
  methodology: string
}> {
  const response = await fetch(`/api/lia/api/wsi/generate-job-screening-questions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to generate screening questions')
  }
  return response.json()
}

export async function regenerateWSIQuestions(
  request: RegenerateWSIQuestionsRequest
): Promise<RegenerateWSIQuestionsResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/wsi/regenerate-questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      return {
        success: false,
        questions: request.current_questions,
        questions_added: 0,
        questions_removed: 0,
        quality_warnings: ['Failed to regenerate questions']
      }
    }

    return response.json()
  } catch {
    return {
      success: false,
      questions: request.current_questions,
      questions_added: 0,
      questions_removed: 0,
      quality_warnings: ['Network error during regeneration']
    }
  }
}
