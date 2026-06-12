import { BACKEND_URL, getAuthHeaders } from './base'
import { throwLiaApiError } from './session'
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

// Bug #303 / Task #305: every `/api/lia/*` call below funnels its non-OK
// response through `throwLiaApiError`, which:
//   - attaches `err.status` so consumers can branch on 401/403 vs 5xx,
//   - preserves `detail`/`error` from the backend payload,
//   - on 401/403 fires the same relogin redirect used by `useSessionRefresh`
//     (`/login?reason=session_expired`), preventing the Next dev overlay
//     and silent failures in production when the WorkOS session expires.
// `updateScreeningStatus` hits `BACKEND_URL` directly (intentional: custom
// bearer token). `regenerateWSIQuestions` now routes through the proxy.


export async function wsiGenerateQuestions(request: GenerateQuestionsRequest): Promise<GenerateQuestionsResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/generate-questions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to generate WSI questions')
  return response.json()
}

export async function wsiAnalyzeResponse(request: AnalyzeResponseRequest): Promise<AnalyzeResponseResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/analyze-response`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to analyze response')
  return response.json()
}

export async function wsiCalculateScore(request: CalculateWSIRequest): Promise<CalculateWSIResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/calculate-wsi`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to calculate WSI')
  return response.json()
}

export async function wsiGetSession(sessionId: string): Promise<WSISessionResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/sessions/${sessionId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get WSI session')
  return response.json()
}

export async function wsiGetCandidateResults(candidateId: string, limit: number = 10): Promise<WSIResultsResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/results/${candidateId}?limit=${limit}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get candidate WSI results')
  return response.json()
}

export async function wsiGetResultDetails(resultId: string): Promise<WSIResultDetails> {
  const response = await fetch(`/api/backend-proxy/api/wsi/results/${resultId}/details`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get WSI result details')
  return response.json()
}

export async function wsiGetVacancyRanking(jobVacancyId: string): Promise<WSIVacancyRanking> {
  const response = await fetch(`/api/backend-proxy/api/wsi/ranking/${jobVacancyId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get vacancy ranking')
  return response.json()
}

export async function wsiGetCandidateRanking(candidateId: string, jobVacancyId: string): Promise<WSICandidateRanking> {
  const response = await fetch(`/api/backend-proxy/api/wsi/candidate/${candidateId}/ranking/${jobVacancyId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get candidate ranking')
  return response.json()
}

export async function wsiStartVoiceScreening(request: StartVoiceScreeningRequest): Promise<StartVoiceScreeningResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/start-voice-screening`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to start voice screening')
  return response.json()
}

export async function wsiGetVoiceScreeningStatus(sessionId: string): Promise<VoiceScreeningStatusResponse> {
  const response = await fetch(`/api/backend-proxy/api/wsi/voice-screening/${sessionId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get voice screening status')
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

export async function wsiGetCandidatesScores(jobVacancyId: string): Promise<WSICandidatesScores> {
  const response = await fetch(`/api/backend-proxy/api/wsi/candidates/${jobVacancyId}/scores`, {
    headers: getAuthHeaders(),
    credentials: 'include',
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get candidates WSI scores')
  return response.json()
}

export async function wsiTriggerFeedback(resultId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/backend-proxy/api/wsi/results/${resultId}/trigger-feedback`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to trigger feedback')
  return response.json()
}

export async function wsiGetFeedbackStatus(resultId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`/api/backend-proxy/api/wsi/results/${resultId}/feedback-status`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to get feedback status')
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
  const response = await fetch(`/api/backend-proxy/api/wsi/generate-job-screening-questions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  })
  if (!response.ok) await throwLiaApiError(response, 'Failed to generate screening questions')
  return response.json()
}

export async function regenerateWSIQuestions(
  request: RegenerateWSIQuestionsRequest
): Promise<RegenerateWSIQuestionsResponse> {
  try {
    const response = await fetch(`/api/backend-proxy/wsi/regenerate-questions`, {
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
