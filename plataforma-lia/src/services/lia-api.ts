/**
 * LIA Backend API Client
 * 
 * Service layer para comunicação com o backend FastAPI (porta 8000)
 * Integra LIA conversational agent, Pearch AI search, e Microsoft Graph
 */

import type { CompanyBenefit } from '@/types/benefits'
import { checkPaymentRequired } from '@/lib/api/handle-payment-required'

const BACKEND_URL = '/api/backend-proxy'

export interface ChatMessage {
  conversation_id?: string
  content: string
  user_id?: string
  attachments?: File[]
  audio?: Blob
}

export interface ChatResponse {
  message: {
    id: string
    conversation_id: string
    role: string
    content: string
    message_metadata: Record<string, any>
    created_at: string
  }
  conversation: {
    id: string
    user_id: string
    user_role: string
    title?: string
    intent?: string
    workflow_type?: string
    workflow_step: number
    workflow_data?: Record<string, any>
    status: string
    created_at: string
    updated_at: string
  }
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface CandidateSearchRequest {
  query: string
  search_type?: 'fast' | 'deep'
  limit?: number
  timeout?: number
}

export interface CandidateProfile {
  id: string | null
  name: string | null
  headline: string | null
  current_title: string | null
  current_company: string | null
  location: string | null
  contact: {
    email?: string
    phone?: string
    linkedin_url?: string
  } | null
  experience: any[]
  education: any[]
  skills: string[]
  summary: string | null
  match_score: number | null
  match_reasoning: string | null
}

export interface CandidateSearchResponse {
  query: string
  total_results: number
  candidates: CandidateProfile[]
  search_time_seconds: number
  credits_used: number | null
}

export interface CalibrationCandidateExperience {
  id: string
  company: string
  role: string
  period: string
  duration: string
  location?: string
  isPromotion?: boolean
  skills: string[]
}

export interface CalibrationCandidateEducation {
  id: string
  institution: string
  degree: string
  field: string
  period: string
}

export interface CalibrationMatchCriteria {
  id: string
  criteria: string
  met: boolean
  score?: number
}

export interface CalibrationCandidate {
  id: string
  name: string
  photoUrl?: string
  linkedinUrl?: string
  currentRole: string
  currentCompany: string
  location: string
  education: string
  highlights: {
    icon: string
    label: string
    value: string
  }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: {
    category: string
    skills: string[]
  }[]
  languages: string[]
  additionalSkills: string[]
  matchCriteria: CalibrationMatchCriteria[]
  overallScore: number
  averageTenure: string
  currentTenure: string
}

export interface StartCalibrationSessionRequest {
  job_vacancy_id: string
  job_description: string
  technical_skills: string[]
  behavioral_competencies: string[]
  location?: string
  limit?: number
}

export interface StartCalibrationSessionResponse {
  session_id: string
  candidates: CalibrationCandidate[]
  total_found: number
}

export interface SubmitCalibrationFeedbackRequest {
  session_id: string
  candidate_id: string
  job_id: string
  approved: boolean
  lia_score?: number
  feedback_reason?: string
}

export interface CalibrationStatusResponse {
  approved_count: number
  rejected_count: number
  is_complete: boolean
}

export interface AddCandidatesToPipelineRequest {
  candidate_ids: string[]
  job_vacancy_id: string
  source?: string
}

export interface AddCandidatesToPipelineResponse {
  success: boolean
  added_count: number
}

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

export interface JobCreatedNotificationRequest {
  job_id: string
  job_title: string
  department?: string
  location?: string
  work_model?: string
  seniority_level?: string
  job_description: string
  technical_requirements: { name: string; level: string; required: boolean }[]
  behavioral_competencies: { name: string; weight: string }[]
  languages: { name: string; level: string }[]
  salary_range?: { min?: number; max?: number; currency?: string }
  benefits: string[]
  deadline_screening: string
  deadline_shortlist: string
  deadline_closing: string
  interview_stages: { stageName: string; order: number; sla?: number }[]
  publishing_platforms: { linkedin: boolean; indeed: boolean; website: boolean }
  urgency_level: number
  is_confidential: boolean
  is_affirmative: boolean
  recruiter_email: string
  recruiter_name?: string
  manager_email?: string
  manager_name?: string
  channels: ('email' | 'teams')[]
}

export interface JobCreatedNotificationResponse {
  success: boolean
  notifications_sent: {
    recruiter: { email: boolean; teams: boolean }
    manager: { email: boolean; teams: boolean }
  }
  errors?: string[]
}

class LIAApiClient {
  private baseUrl: string

  constructor(baseUrl: string = BACKEND_URL) {
    this.baseUrl = baseUrl
  }

  private getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  private getAuthHeaders(): HeadersInit {
    const token = this.getAccessToken()
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  }

  private getAuthHeadersForFormData(): HeadersInit {
    const token = this.getAccessToken()
    return {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  }

  /**
   * Check backend health status
   */
  async healthCheck(): Promise<{ status: string; app: string; environment: string }> {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * List company departments
   */
  async listDepartments(companyId?: string): Promise<{ id: string; name: string; description?: string }[]> {
    try {
      const params = companyId ? `?company_id=${companyId}` : ''
      const response = await fetch(`${this.baseUrl}/company/departments${params}`, {
        headers: this.getAuthHeaders(),
      })
      if (!response.ok) {
        console.warn(`Failed to fetch departments: ${response.status}`)
        return []
      }
      return response.json()
    } catch (error) {
      console.warn('Failed to fetch departments:', error)
      return []
    }
  }

  /**
   * List company benefits
   */
  async listBenefits(companyId?: string): Promise<CompanyBenefit[]> {
    try {
      const params = companyId ? `?company_id=${companyId}` : ''
      const response = await fetch(`${this.baseUrl}/company/benefits${params}`, {
        headers: this.getAuthHeaders(),
      })
      if (!response.ok) {
        console.warn(`Failed to fetch benefits: ${response.status}`)
        return []
      }
      return response.json()
    } catch (error) {
      console.warn('Failed to fetch benefits:', error)
      return []
    }
  }

  async createBenefit(benefit: Partial<CompanyBenefit>, companyId?: string): Promise<CompanyBenefit | null> {
    try {
      const params = companyId ? `?company_id=${companyId}` : ''
      const response = await fetch(`${this.baseUrl}/company/benefits${params}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify(benefit)
      })
      if (!response.ok) {
        console.warn(`Failed to create benefit: ${response.status}`)
        return null
      }
      return await response.json()
    } catch (error) {
      console.warn('Failed to create benefit:', error)
      return null
    }
  }

  /**
   * Send message to LIA conversational agent
   * Supports text messages with optional file attachments and audio
   */
  async sendMessage(data: ChatMessage): Promise<ChatResponse> {
    const hasFiles = (data.attachments && data.attachments.length > 0) || data.audio
    
    if (hasFiles) {
      const formData = new FormData()
      formData.append('content', data.content)
      if (data.user_id) formData.append('user_id', data.user_id)
      if (data.conversation_id) formData.append('conversation_id', data.conversation_id)
      
      if (data.attachments) {
        data.attachments.forEach((file, index) => {
          formData.append(`attachments`, file, file.name)
        })
      }
      
      if (data.audio) {
        formData.append('audio', data.audio, 'recording.webm')
      }
      
      const response = await fetch(`${this.baseUrl}/chat/with-attachments`, {
        method: 'POST',
        headers: this.getAuthHeadersForFormData(),
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(error.detail || 'Failed to send message with attachments')
      }

      return response.json()
    }
    
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        content: data.content,
        user_id: data.user_id,
        conversation_id: data.conversation_id
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to send message')
    }

    return response.json()
  }

  /**
   * Get all conversations for a user
   */
  async getConversations(userId: string): Promise<Conversation[]> {
    const response = await fetch(`${this.baseUrl}/chat/?user_id=${userId}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch conversations: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get conversation history
   */
  async getConversationHistory(conversationId: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/chat/?conversation_id=${conversationId}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch conversation history: ${response.statusText}`)
    }

    const data = await response.json()
    return data.messages || []
  }

  /**
   * Process message through multi-agent orchestrator
   * Routes to 9 specialized agents based on intent detection
   */
  async orchestratorProcess(request: OrchestratorProcessRequest): Promise<OrchestratorProcessResponse> {
    const response = await fetch(`${this.baseUrl}/orchestrator/process`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      console.error('Orchestrator process error:', error)
      return {
        success: false,
        error: error.detail || 'Orchestrator process failed',
      }
    }

    return response.json()
  }

  /**
   * Search candidates using Pearch AI (via proxy)
   * Note: Will be updated to support local DB first, then Pearch as fallback
   */
  async searchCandidates(request: CandidateSearchRequest): Promise<CandidateSearchResponse> {
    const params = new URLSearchParams({
      query: request.query,
      search_type: request.search_type || 'fast',
      limit: String(request.limit || 10),
      timeout: String(request.timeout || 60),
    })

    const response = await fetch(`${this.baseUrl}/candidates/search?${params}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Candidate search failed')
    }

    return response.json()
  }

  /**
   * Search candidates in local database (FREE - no credits consumed)
   * This searches the proprietary PostgreSQL database only
   */
  async searchCandidatesLocal(request: { query: string; limit?: number }): Promise<CandidateSearchResponse> {
    const response = await fetch(`${this.baseUrl}/candidates/search/local/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        filters: {
          query: request.query,
          limit: request.limit || 15,
          is_active: true
        }
      }),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Local candidate search failed')
    }

    return response.json()
  }

  /**
   * Search candidates by job description (Pearch AI)
   * Note: Will be updated to support local DB first, then Pearch as fallback
   */
  async searchCandidatesByJobDescription(
    jobDescription: string,
    location?: string,
    limit: number = 10
  ): Promise<CandidateSearchResponse> {
    const response = await fetch(`${this.baseUrl}/candidates/search/by-job-description`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
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

  /**
   * Check Pearch AI integration health
   */
  async checkPearchHealth(): Promise<{ service: string; status: string; api_key_set: boolean }> {
    const response = await fetch(`${this.baseUrl}/candidates/health`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Pearch health check failed: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get salary benchmark for a job role from backend
   * Combines internal company data with market data
   */
  async getSalaryBenchmark(request: {
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
      const response = await fetch(`${this.baseUrl}/lia/job-wizard/salary-benchmark`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(request),
      })
      
      if (!response.ok) {
        console.warn(`Salary benchmark endpoint not available (${response.status})`)
        return {}
      }

      return response.json()
    } catch (error) {
      console.warn('Salary benchmark fetch failed:', error)
      return {}
    }
  }

  /**
   * Get credit balance for current user
   * Returns default values if the endpoint is not available
   */
  async getCreditBalance(userId: string = "demo-user"): Promise<{
    available_credits: number
    total_consumed: number
    total_searches: number
    last_updated: string | null
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/credits/balance?user_id=${userId}`, {
        headers: this.getAuthHeaders(),
      })
      
      if (!response.ok) {
        console.warn(`Credit balance endpoint not available (${response.status}), using defaults`)
        return {
          available_credits: 10000,
          total_consumed: 0,
          total_searches: 0,
          last_updated: null
        }
      }

      return response.json()
    } catch (error) {
      console.warn('Credit balance fetch failed, using defaults:', error)
      return {
        available_credits: 10000,
        total_consumed: 0,
        total_searches: 0,
        last_updated: null
      }
    }
  }

  async wsiGenerateQuestions(request: GenerateQuestionsRequest): Promise<GenerateQuestionsResponse> {
    const response = await fetch(`/api/lia/api/wsi/generate-questions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to generate WSI questions')
    }
    return response.json()
  }

  async wsiAnalyzeResponse(request: AnalyzeResponseRequest): Promise<AnalyzeResponseResponse> {
    const response = await fetch(`/api/lia/api/wsi/analyze-response`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to analyze response')
    }
    return response.json()
  }

  async wsiCalculateScore(request: CalculateWSIRequest): Promise<CalculateWSIResponse> {
    const response = await fetch(`/api/lia/api/wsi/calculate-wsi`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to calculate WSI')
    }
    return response.json()
  }

  async wsiGetSession(sessionId: string): Promise<WSISessionResponse> {
    const response = await fetch(`/api/lia/api/wsi/sessions/${sessionId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get WSI session: ${response.statusText}`)
    }
    return response.json()
  }

  async wsiGetCandidateResults(candidateId: string, limit: number = 10): Promise<WSIResultsResponse> {
    const response = await fetch(`/api/lia/api/wsi/results/candidate/${candidateId}?limit=${limit}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get candidate WSI results: ${response.statusText}`)
    }
    return response.json()
  }

  async wsiGetResultDetails(resultId: string): Promise<WSIResultDetails> {
    const response = await fetch(`/api/lia/api/wsi/results/${resultId}/details`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get WSI result details: ${response.statusText}`)
    }
    return response.json()
  }

  async wsiGetVacancyRanking(jobVacancyId: string): Promise<WSIVacancyRanking> {
    const response = await fetch(`/api/lia/api/wsi/ranking/${jobVacancyId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get vacancy ranking: ${response.statusText}`)
    }
    return response.json()
  }

  async wsiGetCandidateRanking(candidateId: string, jobVacancyId: string): Promise<WSICandidateRanking> {
    const response = await fetch(`/api/lia/api/wsi/candidate/${candidateId}/ranking/${jobVacancyId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get candidate ranking: ${response.statusText}`)
    }
    return response.json()
  }

  async wsiStartVoiceScreening(request: StartVoiceScreeningRequest): Promise<StartVoiceScreeningResponse> {
    const response = await fetch(`/api/lia/api/wsi/start-voice-screening`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to start voice screening')
    }
    return response.json()
  }

  async wsiGetVoiceScreeningStatus(sessionId: string): Promise<VoiceScreeningStatusResponse> {
    const response = await fetch(`/api/lia/api/wsi/voice-screening/${sessionId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get voice screening status: ${response.statusText}`)
    }
    return response.json()
  }

  async updateScreeningStatus(jobId: string, status: string, extraData?: { pause_reason?: string; scheduled_end_date?: string }): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/vagas/${jobId}/screening-status`, {
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

  async wsiGetCandidatesScores(jobVacancyId: string): Promise<WSICandidatesScores> {
    const response = await fetch(`/api/lia/api/wsi/candidates/${jobVacancyId}/scores`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to get candidates WSI scores: ${response.statusText}`)
    }
    return response.json()
  }

  async wsiTriggerFeedback(resultId: string): Promise<any> {
    const response = await fetch(`/api/lia/api/wsi/results/${resultId}/trigger-feedback`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to trigger feedback')
    }
    return response.json()
  }

  async wsiGetFeedbackStatus(resultId: string): Promise<any> {
    const response = await fetch(`/api/lia/api/wsi/results/${resultId}/feedback-status`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to get feedback status')
    }
    return response.json()
  }

  async generateJobScreeningQuestions(request: {
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
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to generate screening questions')
    }
    return response.json()
  }

  async listJobVacancies(status?: string, skip: number = 0, limit: number = 500): Promise<JobVacancyListResponse> {
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    params.set('skip', String(skip))
    params.set('limit', String(limit))
    
    const url = `${this.baseUrl}/job-vacancies?${params}`
    
    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job vacancies: ${response.statusText}`)
    }
    
    return response.json()
  }

  async getJobVacancy(id: string): Promise<JobVacancy> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${id}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job vacancy: ${response.statusText}`)
    }
    
    return response.json()
  }

  async createJobVacancy(data: JobVacancyCreateRequest): Promise<JobVacancy> {
    const response = await fetch(`${this.baseUrl}/job-vacancies`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })

    await checkPaymentRequired(response)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to create job vacancy')
    }

    return response.json()
  }

  async updateJobVacancy(id: string, data: Partial<JobVacancyCreateRequest>): Promise<JobVacancy> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to update job vacancy')
    }
    
    return response.json()
  }

  async deleteJobVacancy(id: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to delete job vacancy')
    }
    
    return response.json()
  }

  async updateJobVacancyStatus(id: string, status: string): Promise<{ success: boolean; old_status: string; new_status: string }> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${id}/status?status=${encodeURIComponent(status)}`, {
      method: 'PATCH',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to update job vacancy status')
    }
    
    return response.json()
  }

  async updateJobVacancyStatusWithOutcome(
    id: string, 
    status: string, 
    companyId: string
  ): Promise<{ success: boolean; old_status: string; new_status: string }> {
    const result = await this.updateJobVacancyStatus(id, status)
    
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
        this.updateJobOutcome({
          company_id: companyId,
          job_id: id,
          outcome_status: outcomeStatus,
        }).catch(err => console.error('Non-blocking: Job outcome update failed:', err))
      }
    }
    
    return result
  }

  async sendRecruiterActionNotification(data: {
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
    const response = await fetch(`${this.baseUrl}/notifications/recruiter-action`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to send recruiter notification')
    }
    
    return response.json()
  }

  async transferCommunications(data: {
    job_ids: string[]
    from_recruiter_ids: string[]
    to_recruiter_id: string
  }): Promise<{ success: boolean; transferred_count: number }> {
    const response = await fetch(`${this.baseUrl}/communications/transfer`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to transfer communications')
    }
    
    return response.json()
  }

  async generatePublicLink(vacancyId: string, regenerate: boolean = false): Promise<{ success: boolean; public_url: string; slug: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${vacancyId}/generate-public-link`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ regenerate }),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to generate public link')
    }
    
    return response.json()
  }

  async publishToLinkedIn(jobId: string): Promise<{
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
    const response = await fetch(`${this.baseUrl}/job-boards/linkedin/publish/${jobId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to publish to LinkedIn')
    }
    
    return response.json()
  }

  async publishToIndeed(jobId: string): Promise<{
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
    const response = await fetch(`${this.baseUrl}/job-boards/indeed/publish/${jobId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to publish to Indeed')
    }
    
    return response.json()
  }

  async getJobPublishingStatus(jobId: string): Promise<{
    job_id: string
    job_title: string
    platforms: {
      linkedin: { published: boolean; post_id?: string; url?: string }
      indeed: { published: boolean; job_id?: string; feed_url?: string }
      website: { published: boolean; url?: string }
    }
    last_published_at?: string
  }> {
    const response = await fetch(`${this.baseUrl}/job-boards/status/${jobId}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to get publishing status')
    }
    
    return response.json()
  }

  async unpublishFromPlatform(jobId: string, platform: 'linkedin' | 'indeed'): Promise<{
    success: boolean
    message: string
    platform: string
    job_id: string
    old_post_id?: string
    old_indeed_id?: string
  }> {
    const response = await fetch(`${this.baseUrl}/job-boards/unpublish/${jobId}/${platform}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || `Failed to unpublish from ${platform}`)
    }
    
    return response.json()
  }

  async publishToMultiplePlatforms(jobIds: string[], platforms: string[]): Promise<{
    success: boolean
    results: Array<{
      job_id: string
      platforms?: Record<string, any>
      success?: boolean
      error?: string
    }>
    summary: {
      total_jobs: number
      platforms: string[]
    }
  }> {
    const response = await fetch(`${this.baseUrl}/job-boards/publish-batch`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ job_ids: jobIds, platforms }),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to publish to platforms')
    }
    
    return response.json()
  }

  async getJobVacanciesOverview(recruiterEmail?: string): Promise<{
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
    const url = `${this.baseUrl}/job-vacancies/stats/overview/${queryString ? `?${queryString}` : ''}`
    
    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to fetch job vacancies overview')
    }
    
    return response.json()
  }

  async listCandidates(search?: string, source?: string, skip: number = 0, limit: number = 50): Promise<CandidateListResponse> {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (source) params.set('source', source)
    params.set('skip', String(skip))
    params.set('limit', String(limit))
    
    const response = await fetch(`${this.baseUrl}/candidates/?${params}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch candidates: ${response.statusText}`)
    }
    
    return response.json()
  }

  async getCandidate(id: string): Promise<CandidateLocal> {
    const response = await fetch(`${this.baseUrl}/candidates/${id}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch candidate: ${response.statusText}`)
    }
    
    return response.json()
  }

  async createCandidate(data: CandidateCreateRequest): Promise<CandidateLocal> {
    const response = await fetch(`${this.baseUrl}/candidates`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to create candidate')
    }
    
    return response.json()
  }

  async updateCandidate(id: string, data: Partial<CandidateCreateRequest>): Promise<CandidateLocal> {
    const response = await fetch(`${this.baseUrl}/candidates/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to update candidate')
    }
    
    return response.json()
  }

  async deleteCandidate(id: string): Promise<{ message: string; id: string }> {
    const response = await fetch(`${this.baseUrl}/candidates/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to delete candidate')
    }
    
    return response.json()
  }

  async listEmailTemplates(
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
    
    const response = await fetch(`${this.baseUrl}/email-templates?${params}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch email templates: ${response.statusText}`)
    }
    
    return response.json()
  }

  async getEmailTemplate(id: string): Promise<EmailTemplate> {
    const response = await fetch(`${this.baseUrl}/email-templates/${id}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch email template: ${response.statusText}`)
    }
    
    return response.json()
  }

  async createEmailTemplate(data: EmailTemplateCreateRequest): Promise<EmailTemplate> {
    const response = await fetch(`${this.baseUrl}/email-templates`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to create email template')
    }
    
    return response.json()
  }

  async updateEmailTemplate(id: string, data: EmailTemplateUpdateRequest): Promise<EmailTemplate> {
    const response = await fetch(`${this.baseUrl}/email-templates/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to update email template')
    }
    
    return response.json()
  }

  async deleteEmailTemplate(id: string, hardDelete: boolean = false): Promise<{ message: string; id: string }> {
    const url = `${this.baseUrl}/email-templates/${id}${hardDelete ? '?hard_delete=true' : ''}`
    const response = await fetch(url, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to delete email template')
    }
    
    return response.json()
  }

  async previewEmail(request: EmailPreviewRequest): Promise<EmailPreviewResponse> {
    const response = await fetch(`${this.baseUrl}/email-templates/preview`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to preview email')
    }
    
    return response.json()
  }

  async sendEmail(templateId: string, request: EmailSendRequest): Promise<EmailSendResponse> {
    const response = await fetch(`${this.baseUrl}/email-templates/${templateId}/send`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to send email')
    }
    
    return response.json()
  }

  async getEmailCategories(): Promise<{ categories: EmailCategory[] }> {
    const response = await fetch(`${this.baseUrl}/email-templates/categories`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch email categories: ${response.statusText}`)
    }
    
    return response.json()
  }

  async bulkUpdateStatus(request: BulkUpdateStatusRequest): Promise<BulkOperationResult> {
    const response = await fetch('/api/backend-proxy/candidates/bulk/update-status', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao atualizar status')
    }
    
    return response.json()
  }

  async bulkAssignJob(request: BulkAssignJobRequest): Promise<BulkOperationResult> {
    const response = await fetch('/api/backend-proxy/candidates/bulk/assign-job', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao atribuir candidatos à vaga')
    }
    
    return response.json()
  }

  async bulkSendEmail(request: BulkSendEmailRequest): Promise<BulkOperationResult> {
    const response = await fetch('/api/backend-proxy/candidates/bulk/send-email', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao enviar emails')
    }
    
    return response.json()
  }

  async bulkStartScreening(request: BulkStartScreeningRequest): Promise<BulkOperationResult> {
    const response = await fetch('/api/backend-proxy/candidates/bulk/start-screening', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao iniciar triagem')
    }
    
    return response.json()
  }

  async bulkExport(request: BulkExportRequest): Promise<Blob | BulkOperationResult> {
    const response = await fetch('/api/backend-proxy/candidates/bulk/export', {
      method: 'POST',
      headers: this.getAuthHeaders(),
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

  async bulkDelete(request: BulkDeleteRequest): Promise<BulkOperationResult> {
    const response = await fetch('/api/backend-proxy/candidates/bulk/delete', {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao excluir candidatos')
    }
    
    return response.json()
  }

  async getStaleCandidates(staleDays: number = 3, limit: number = 50): Promise<PipelineReportResponse> {
    const response = await fetch(`/api/backend-proxy/pipeline/stale-candidates?stale_days=${staleDays}&limit=${limit}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao buscar candidatos parados')
    }
    
    return response.json()
  }

  async executePipelineAction(candidateId: string, actionId: string): Promise<PipelineActionResponse> {
    const response = await fetch('/api/backend-proxy/pipeline/action', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ candidate_id: candidateId, action_id: actionId }),
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string; error?: string }
      throw new Error(error.detail || error.error || 'Falha ao executar ação')
    }
    
    return response.json()
  }

  async getNotifications(
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
      const response = await fetch(`${this.baseUrl}/notifications/?${params.toString()}`, {
        headers: this.getAuthHeaders(),
      })

      if (!response.ok) {
        return { success: false, data: { notifications: [], total: 0 } } as any
      }

      return response.json()
    } catch {
      return { success: false, data: { notifications: [], total: 0 } } as any
    }
  }

  async getNotificationSummary(userId: string = 'default_user'): Promise<NotificationSummaryResponse> {
    const response = await fetch(`${this.baseUrl}/notifications/summary?user_id=${userId}`, {
      headers: this.getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch notification summary: ${response.statusText}`)
    }

    return response.json()
  }

  async getUnreadCount(userId: string = 'default_user'): Promise<{ success: boolean; data: { unread_count: number; urgent_count: number } }> {
    const response = await fetch(`${this.baseUrl}/notifications/unread-count?user_id=${userId}`, {
      headers: this.getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch unread count: ${response.statusText}`)
    }

    return response.json()
  }

  async markNotificationAsRead(notificationId: string, userId: string = 'default_user'): Promise<NotificationActionResponse> {
    const response = await fetch(`${this.baseUrl}/notifications/${notificationId}/read?user_id=${userId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to mark notification as read: ${response.statusText}`)
    }

    return response.json()
  }

  async markAllNotificationsAsRead(userId: string = 'default_user', category?: string): Promise<NotificationActionResponse> {
    const params = new URLSearchParams()
    params.set('user_id', userId)
    if (category) params.set('category', category)

    const response = await fetch(`${this.baseUrl}/notifications/read-all?${params.toString()}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to mark all notifications as read: ${response.statusText}`)
    }

    return response.json()
  }

  async dismissNotification(notificationId: string, userId: string = 'default_user'): Promise<NotificationActionResponse> {
    const response = await fetch(`${this.baseUrl}/notifications/${notificationId}/dismiss?user_id=${userId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Failed to dismiss notification: ${response.statusText}`)
    }

    return response.json()
  }

  // =============================================
  // CANDIDATE LISTS METHODS
  // =============================================

  async getCandidateLists(params?: { skip?: number; limit?: number; search?: string }): Promise<CandidateListsResponse> {
    const searchParams = new URLSearchParams()
    if (params?.skip) searchParams.set('skip', params.skip.toString())
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.search) searchParams.set('search', params.search)
    
    const response = await fetch(`${this.baseUrl}/candidate-lists?${searchParams.toString()}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      return { items: [], total: 0 } as CandidateListsResponse
    }
    return response.json()
  }

  async createCandidateList(data: { name: string; description?: string; color?: string }): Promise<CandidateList> {
    const response = await fetch(`${this.baseUrl}/candidate-lists`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`Failed to create list: ${response.statusText}`)
    return response.json()
  }

  async getCandidateList(listId: string, params?: { skip?: number; limit?: number }): Promise<CandidateListDetail> {
    const searchParams = new URLSearchParams()
    if (params?.skip) searchParams.set('skip', params.skip.toString())
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    
    const response = await fetch(`${this.baseUrl}/candidate-lists/${listId}?${searchParams.toString()}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to get list: ${response.statusText}`)
    return response.json()
  }

  async updateCandidateList(listId: string, data: { name?: string; description?: string; color?: string }): Promise<CandidateList> {
    const response = await fetch(`${this.baseUrl}/candidate-lists/${listId}`, {
      method: 'PATCH',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`Failed to update list: ${response.statusText}`)
    return response.json()
  }

  async deleteCandidateList(listId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/candidate-lists/${listId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to delete list: ${response.statusText}`)
    return response.json()
  }

  async addCandidatesToList(listId: string, candidateIds: string[], notes?: string): Promise<AddCandidatesResult> {
    const response = await fetch(`${this.baseUrl}/candidate-lists/${listId}/candidates`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ candidate_ids: candidateIds, notes }),
    })
    if (!response.ok) throw new Error(`Failed to add candidates: ${response.statusText}`)
    return response.json()
  }

  async removeCandidatesFromList(listId: string, candidateIds: string[]): Promise<RemoveCandidatesResult> {
    const response = await fetch(`${this.baseUrl}/candidate-lists/${listId}/candidates`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ candidate_ids: candidateIds }),
    })
    if (!response.ok) throw new Error(`Failed to remove candidates: ${response.statusText}`)
    return response.json()
  }

  async assignListToJobs(listId: string, jobVacancyIds: string[], candidateIds?: string[]): Promise<AssignJobsResult> {
    const response = await fetch(`${this.baseUrl}/candidate-lists/${listId}/assign-jobs`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ job_vacancy_ids: jobVacancyIds, candidate_ids: candidateIds }),
    })
    if (!response.ok) throw new Error(`Failed to assign to jobs: ${response.statusText}`)
    return response.json()
  }

  async sendDirectEmail(request: DirectEmailRequest): Promise<DirectEmailResponse> {
    const response = await fetch(`${this.baseUrl}/email/send`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to send email')
    }
    return response.json()
  }

  async getEmailHistory(candidateId: string, skip: number = 0, limit: number = 50): Promise<EmailHistoryResponse> {
    const response = await fetch(`${this.baseUrl}/email/history/${candidateId}?skip=${skip}&limit=${limit}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to get email history: ${response.statusText}`)
    return response.json()
  }

  async getEmailSystemStatus(): Promise<EmailSystemStatus> {
    const response = await fetch(`${this.baseUrl}/email/status`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to get email status: ${response.statusText}`)
    return response.json()
  }

  async createInterview(request: CreateInterviewRequest): Promise<InterviewApiResponse> {
    const response = await fetch(`${this.baseUrl}/scheduling/interviews`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to create interview')
    }
    return response.json()
  }

  async listScheduledInterviews(params?: {
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

    const response = await fetch(`${this.baseUrl}/scheduling/interviews?${searchParams.toString()}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to list interviews: ${response.statusText}`)
    return response.json()
  }

  async getScheduledInterview(interviewId: string): Promise<InterviewApiResponse> {
    const response = await fetch(`${this.baseUrl}/scheduling/interviews/${interviewId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to get interview: ${response.statusText}`)
    return response.json()
  }

  async updateScheduledInterview(interviewId: string, request: Partial<CreateInterviewRequest>): Promise<InterviewApiResponse> {
    const response = await fetch(`${this.baseUrl}/scheduling/interviews/${interviewId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to update interview')
    }
    return response.json()
  }

  async cancelScheduledInterview(interviewId: string, reason?: string): Promise<{ success: boolean; message: string }> {
    const params = reason ? `?reason=${encodeURIComponent(reason)}` : ''
    const response = await fetch(`${this.baseUrl}/scheduling/interviews/${interviewId}${params}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to cancel interview')
    }
    return response.json()
  }

  async downloadInterviewIcs(interviewId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/scheduling/interviews/${interviewId}/ics`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to download ICS: ${response.statusText}`)
    return response.blob()
  }

  async getSchedulingStatus(): Promise<SchedulingStatus> {
    const response = await fetch(`${this.baseUrl}/scheduling/status`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to get scheduling status: ${response.statusText}`)
    return response.json()
  }

  async logCommunication(data: CommunicationHistoryCreate): Promise<CommunicationHistoryRecord> {
    const response = await fetch(`/api/lia/api/v1/communications`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to log communication')
    }
    return response.json()
  }

  async listCommunications(params: {
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
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to list communications: ${response.statusText}`)
    return response.json()
  }

  async getCandidateCommunications(params: {
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
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to get candidate communications: ${response.statusText}`)
    return response.json()
  }

  async updateCommunicationStatus(params: {
    communication_id: string
    status: string
    error_message?: string
  }): Promise<CommunicationHistoryRecord> {
    const response = await fetch(`/api/lia/api/v1/communications/${params.communication_id}/status`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
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

  async createActivity(data: {
    company_id: string
    activity_type: string
    description: string
    candidate_id?: string
    vacancy_id?: string
    performed_by?: string
    metadata?: Record<string, any>
  }): Promise<{ id: string; created_at: string }> {
    const response = await fetch(`${this.baseUrl}/activities`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to create activity')
    }
    return response.json()
  }

  async publishJobVacancy(jobId: string, triggerSourcing: boolean = true): Promise<PublishJobResponse> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${jobId}/publish`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ trigger_sourcing: triggerSourcing })
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to publish job')
    }
    return response.json()
  }

  async duplicateJobVacancy(jobId: string, options: {
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
    const response = await fetch(`${this.baseUrl}/job-vacancies/${jobId}/duplicate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
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

  async confirmGlobalSearch(jobId: string, creditsToUse: number = 20): Promise<GlobalSearchConfirmResponse> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${jobId}/confirm-global-search`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ credits_to_use: creditsToUse })
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to confirm global search')
    }
    return response.json()
  }

  async getSourcingStatus(jobId: string): Promise<SourcingStatusResponse> {
    const response = await fetch(`${this.baseUrl}/job-vacancies/${jobId}/sourcing-status`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText })) as { detail?: string }
      throw new Error(error.detail || 'Failed to get sourcing status')
    }
    return response.json()
  }

  async generateInterviewQuestions(request: GenerateInterviewQuestionsRequest): Promise<GenerateInterviewQuestionsResponse> {
    const response = await fetch(`${this.baseUrl}/interview-notes/generate-questions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      throw new Error(`Failed to generate interview questions: ${response.statusText}`)
    }
    return response.json()
  }

  async generateInterviewParecer(request: GenerateInterviewParecerRequest): Promise<GenerateInterviewParecerResponse> {
    const response = await fetch(`${this.baseUrl}/interview-notes/generate-parecer`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) {
      throw new Error(`Failed to generate interview parecer: ${response.statusText}`)
    }
    return response.json()
  }

  async saveInterviewNote(note: any): Promise<{ id: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/interview-notes`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(note),
    })
    if (!response.ok) {
      throw new Error(`Failed to save interview note: ${response.statusText}`)
    }
    return response.json()
  }

  async getInterviewAnalysisStatus(interviewId: string): Promise<InterviewAnalysisStatus> {
    const response = await fetch(`${this.baseUrl}/interview-analysis/status/${interviewId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error('Failed to get analysis status')
    }
    return response.json()
  }

  async getInterviewAnalysisResults(interviewId: string): Promise<InterviewAnalysisResult> {
    const response = await fetch(`${this.baseUrl}/interview-analysis/results/${interviewId}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error('Failed to get analysis results')
    }
    return response.json()
  }

  async triggerInterviewAnalysis(interviewId: string, forceRefresh = false): Promise<InterviewAnalysisStatus> {
    const response = await fetch(`${this.baseUrl}/interview-analysis/analyze/${interviewId}?force_refresh=${forceRefresh}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error('Failed to trigger analysis')
    }
    return response.json()
  }

  async executeAction(params: {
    action_type: 'email' | 'whatsapp' | 'triagem_wsi' | 'agendar_entrevista' | 'apenas_mover'
    candidate_id: string
    vacancy_id: string
    company_id: string
    channel?: 'email' | 'whatsapp'
    template_id?: string
    subject?: string
    message?: string
    metadata?: Record<string, any>
  }): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/automation/execute-action`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
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
      console.error('Error executing action:', error)
      return { success: false, error: String(error) }
    }
  }

  async screenCandidate(params: {
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
      const response = await fetch(`${this.baseUrl}/automation/screen-candidate`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          candidate_id: params.candidate_id,
          vacancy_id: params.vacancy_id,
          company_id: params.company_id
        })
      })
      return await response.json()
    } catch (error) {
      console.error('Error screening candidate:', error)
      return { success: false, error: String(error) }
    }
  }

  async triggerEvent(params: {
    event_type: string
    entity_id: string
    company_id: string
    entity_type?: string
    metadata?: Record<string, any>
  }): Promise<{ success: boolean; data?: { event_type: string; entity_id: string; agents_notified: string[]; message: string }; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/automation/trigger-event`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
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
      console.error('Error triggering event:', error)
      return { success: false, error: String(error) }
    }
  }

  // =============================================
  // AI SUGGESTIONS / APPROVAL METHODS
  // =============================================

  async getPendingAISuggestions(companyId: string): Promise<PendingAISuggestionsResponse> {
    const response = await fetch(`${this.baseUrl}/automation/pending-suggestions?company_id=${companyId}`, {
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to fetch AI suggestions: ${response.statusText}`)
    }
    
    return response.json()
  }

  async approveAISuggestion(suggestionId: string): Promise<AISuggestionActionResponse> {
    const response = await fetch(`${this.baseUrl}/automation/approve-suggestion/${suggestionId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to approve suggestion: ${response.statusText}`)
    }
    
    return response.json()
  }

  async rejectAISuggestion(suggestionId: string): Promise<AISuggestionActionResponse> {
    const response = await fetch(`${this.baseUrl}/automation/reject-suggestion/${suggestionId}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to reject suggestion: ${response.statusText}`)
    }
    
    return response.json()
  }

  async bulkApproveAISuggestions(suggestionIds: string[]): Promise<BulkAISuggestionActionResponse> {
    const response = await fetch(`${this.baseUrl}/automation/bulk-approve-suggestions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ suggestion_ids: suggestionIds }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to bulk approve suggestions: ${response.statusText}`)
    }
    
    return response.json()
  }

  async bulkRejectAISuggestions(suggestionIds: string[]): Promise<BulkAISuggestionActionResponse> {
    const response = await fetch(`${this.baseUrl}/automation/bulk-reject-suggestions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ suggestion_ids: suggestionIds }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to bulk reject suggestions: ${response.statusText}`)
    }
    
    return response.json()
  }

  async getJobVacancyMetrics(jobId: string): Promise<JobVacancyMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/job-vacancies/${jobId}/metrics`, {
        headers: this.getAuthHeaders(),
      })
      
      if (!response.ok) {
        console.warn(`Job vacancy metrics endpoint not available (${response.status}), using defaults`)
        return this.getDefaultJobVacancyMetrics(jobId)
      }
      
      return response.json()
    } catch (error) {
      console.warn('Job vacancy metrics fetch failed, using defaults:', error)
      return this.getDefaultJobVacancyMetrics(jobId)
    }
  }

  private getDefaultJobVacancyMetrics(jobId: string): JobVacancyMetrics {
    return {
      job_id: jobId,
      funnel: { total: 0, screening: 0, interview: 0, offer: 0, hired: 0, rejected: 0 },
      performance: { time_to_fill_days: null, avg_time_in_stage_days: null, conversion_rate: 0, source_breakdown: {} },
      activity: { views_7d: 0, applications_7d: 0, interviews_scheduled: 0, last_activity: null },
      sla: { within_sla: true, days_remaining: null, deadline: null }
    }
  }

  async getCompanyUsers(options?: { role?: string; isActive?: boolean }): Promise<CompanyUsersResponse> {
    try {
      const params = new URLSearchParams()
      if (options?.role) params.set('role', options.role)
      if (options?.isActive !== undefined) params.set('is_active', String(options.isActive))
      
      const queryString = params.toString()
      const url = `${this.baseUrl}/company/users/list${queryString ? `?${queryString}` : ''}`
      
      const response = await fetch(url, {
        headers: this.getAuthHeaders(),
      })
      
      if (!response.ok) {
        console.warn(`Company users endpoint not available (${response.status}), using empty list`)
        return { users: [], total: 0 }
      }
      
      return response.json()
    } catch (error) {
      console.warn('Company users fetch failed, using empty list:', error)
      return { users: [], total: 0 }
    }
  }

  /**
   * Start a calibration session for a job vacancy
   * POST /search/calibration/start
   */
  async startCalibrationSession(request: StartCalibrationSessionRequest): Promise<StartCalibrationSessionResponse> {
    const response = await fetch(`${this.baseUrl}/search/calibration/start`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to start calibration session')
    }

    return response.json()
  }

  /**
   * Submit calibration feedback for a candidate
   * POST /search/calibration/feedback
   */
  async submitCalibrationFeedback(request: SubmitCalibrationFeedbackRequest): Promise<{ success: boolean }> {
    const response = await fetch(`${this.baseUrl}/search/calibration/feedback`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to submit calibration feedback')
    }

    return response.json()
  }

  /**
   * Get the status of a calibration session
   * GET /search/calibration/{session_id}/status
   */
  async getCalibrationStatus(sessionId: string): Promise<CalibrationStatusResponse> {
    const response = await fetch(`${this.baseUrl}/search/calibration/${sessionId}/status`, {
      headers: this.getAuthHeaders(),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to get calibration status')
    }

    return response.json()
  }

  /**
   * Add candidates to a job vacancy pipeline in bulk
   * POST /candidates/bulk/assign-job
   */
  async addCandidatesToPipeline(request: AddCandidatesToPipelineRequest): Promise<AddCandidatesToPipelineResponse> {
    const response = await fetch(`${this.baseUrl}/candidates/bulk/assign-job`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
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

  /**
   * Send a notification to a user
   * POST /notifications/send
   */
  async sendNotification(request: SendNotificationRequest): Promise<SendNotificationResponse> {
    const response = await fetch(`${this.baseUrl}/notifications/send`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to send notification')
    }

    return response.json()
  }

  async sendJobCreatedNotification(request: JobCreatedNotificationRequest): Promise<JobCreatedNotificationResponse> {
    const response = await fetch(`${this.baseUrl}/notifications/job-created`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to send job created notification')
    }

    return response.json()
  }

  // =============================================
  // SHARED SEARCHES
  // =============================================

  async getSharedSearches(params?: { status?: string; share_type?: string; limit?: number; offset?: number }): Promise<{ total: number; items: SharedSearch[] }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.share_type) searchParams.set('share_type', params.share_type)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    const response = await fetch(`${this.baseUrl}/shared-searches?${searchParams}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error('Failed to fetch shared searches')
    return response.json()
  }

  async createSharedSearch(data: CreateSharedSearchRequest): Promise<SharedSearch> {
    const response = await fetch(`${this.baseUrl}/shared-searches`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error('Failed to create shared search')
    return response.json()
  }

  async getSharedSearchDetail(id: string): Promise<SharedSearchDetail> {
    const response = await fetch(`${this.baseUrl}/shared-searches/${id}`, {
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error('Failed to fetch shared search details')
    return response.json()
  }

  async resendSharedSearchInvite(id: string, email: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/shared-searches/${id}/resend`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ email })
    })
    if (!response.ok) throw new Error('Failed to resend invite')
    return response.json()
  }

  async revokeSharedSearch(id: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/shared-searches/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    })
    if (!response.ok) throw new Error('Failed to revoke shared search')
    return response.json()
  }

  async addSharedCandidatesToJob(sharedSearchId: string, data: AddToJobRequest): Promise<any> {
    const response = await fetch(`${this.baseUrl}/shared-searches/${sharedSearchId}/add-to-job`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error('Failed to add candidates to job')
    return response.json()
  }

  async searchPreviousVacancies(criteria: VacancySearchCriteria): Promise<VacancySearchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/job-vacancies/search`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(criteria)
      })
      if (!response.ok) {
        console.warn(`Failed to search previous vacancies: ${response.status}`)
        return { vacancies: [], total: 0 }
      }
      return response.json()
    } catch (error) {
      console.warn('Failed to search previous vacancies:', error)
      return { vacancies: [], total: 0 }
    }
  }

  async getVacancyFullDetails(vacancyId: string): Promise<VacancyFullDetails | null> {
    try {
      const response = await fetch(`${this.baseUrl}/job-vacancies/${vacancyId}`, {
        headers: this.getAuthHeaders()
      })
      if (!response.ok) {
        console.warn(`Failed to get vacancy details: ${response.status}`)
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
        technical_skills: (data.technical_skills || data.requirements?.technical_skills || []).map((s: any) => ({
          name: s.name || s.skill,
          level: s.level || 'Intermediário',
          weight: s.weight || 3,
          required: s.required ?? true
        })),
        behavioral_competencies: (data.behavioral_competencies || data.requirements?.behavioral_competencies || []).map((c: any) => ({
          name: c.name || c.competency,
          weight: c.weight || 3
        })),
        screening_questions: (data.screening_questions || []).map((q: any) => ({
          question: q.question || q.text,
          type: q.type || 'open',
          expected_answer: q.expected_answer || q.expectedAnswer
        })),
        job_description: data.job_description || data.description || '',
        manager: data.hiring_manager || data.manager || '',
        manager_email: data.hiring_manager_email || data.manager_email || ''
      }
    } catch (error) {
      console.warn('Failed to get vacancy details:', error)
      return null
    }
  }

  async publishFastTrackVacancy(vacancyId: string, adjustments: VacancyAdjustments): Promise<PublishFastTrackResponse> {
    try {
      const updatePayload: any = {}
      if (adjustments.salary_min !== undefined) updatePayload.salary_min = adjustments.salary_min
      if (adjustments.salary_max !== undefined) updatePayload.salary_max = adjustments.salary_max
      if (adjustments.location !== undefined) updatePayload.location = adjustments.location
      if (adjustments.work_model !== undefined) updatePayload.work_model = adjustments.work_model
      if (adjustments.benefits !== undefined) updatePayload.benefits = adjustments.benefits

      const createResponse = await fetch(`${this.baseUrl}/job-vacancies`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
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
    } catch (error) {
      console.error('Failed to publish fast track vacancy:', error)
      return {
        success: false,
        message: 'Erro ao publicar a vaga. Tente novamente.'
      }
    }
  }

  async recordFastTrackUsage(params: {
    company_id: string
    source_job_id: string
    new_job_id: string
    modified_fields: string[]
    was_published: boolean
  }): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/job-embeddings/fast-track/record-usage`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(params)
      })
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        console.error('Failed to record Fast Track usage:', error)
        return { success: false, error: error.detail }
      }
      
      return { success: true }
    } catch (error) {
      console.error('Error recording Fast Track usage:', error)
      return { success: false, error: String(error) }
    }
  }

  async updateJobOutcome(params: {
    company_id: string
    job_id: string
    outcome_status: 'filled' | 'hired' | 'cancelled' | 'expired' | 'closed'
    time_to_fill_days?: number
    hire_quality_score?: number
  }): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/job-embeddings/outcome`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(params)
      })
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
        console.error('Failed to update job outcome:', error)
        return { success: false, error: error.detail }
      }
      
      return { success: true }
    } catch (error) {
      console.error('Error updating job outcome:', error)
      return { success: false, error: String(error) }
    }
  }

  /**
   * List candidates with filters and pagination
   */
  async getCandidates(params: CandidateListParams): Promise<CandidatePaginatedResponse> {
    try {
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
      const response = await fetch(
        `${this.baseUrl}/candidates${qs ? `?${qs}` : ''}`,
        { headers: this.getAuthHeaders() }
      )
      if (!response.ok) {
        console.warn(`getCandidates failed: ${response.status}`)
        return { candidates: [], total: 0, page: 1, per_page: params.limit ?? 20 }
      }
      return response.json()
    } catch (error) {
      console.warn('getCandidates error:', error)
      return { candidates: [], total: 0, page: 1, per_page: params.limit ?? 20 }
    }
  }
}

// =============================================
// COMMUNICATION HISTORY TYPES
// =============================================

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
  metadata?: Record<string, any>
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

export interface ScreeningQuestion {
  id: string | number
  question: string
  type?: string
  options?: string[]
  weight?: number
  required?: boolean
}

export interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  work_model?: string
  employment_type?: string
  seniority_level?: string
  description?: string
  requirements?: string[]
  technical_requirements?: Record<string, any>[]
  languages?: Record<string, any>[]
  behavioral_competencies?: Record<string, any>[]
  salary?: string
  salary_range?: Record<string, any>
  bonus_range?: Record<string, any>
  benefits?: string[]
  manager?: string
  manager_email?: string
  recruiter?: string
  recruiter_email?: string
  is_confidential: boolean
  visibility?: 'public' | 'internal' | 'confidential' | 'hidden'
  public_slug?: string
  status: string
  stage?: string
  priority: string
  created_at?: string
  updated_at?: string
  open_date?: string
  deadline?: string
  deadline_screening?: string
  deadline_shortlist?: string
  deadline_closing?: string
  funnel_data?: {
    total?: number
    screening?: number
    interview?: number
    final?: number
    hired?: number
  }
  lia_metrics?: {
    pipeline_lia?: number
    triagens_agendadas?: number
    triagens_realizadas?: number
    sem_resposta?: number
    entrevistas_agendadas?: number
  }
  nps?: number
  budget?: number
  budget_used?: number
  published_linkedin?: boolean
  published_website?: boolean
  published_indeed?: boolean
  is_affirmative?: boolean
  affirmative_type?: 'pcd' | 'racial' | 'gender' | 'age' | 'lgbtqia+'
  next_actions?: string[]
  urgency_level?: number
  approval_status?: string
  tags?: string[]
  screening_questions?: ScreeningQuestion[]
  interview_stages?: Record<string, any>[]
  organizational_structure?: Record<string, any>
  timeline?: Record<string, any>
  governance_rules?: Record<string, any>
  whatsapp_template_type?: string
  target_sector?: string
  target_segment?: string
  target_audience?: string
  masked_company_name?: string
  access_list?: string[]
  hiring_process?: string[]
  conversation_id?: string
  screening_config?: {
    channels?: {
      whatsapp?: { enabled: boolean; label?: string }
      chat_web?: { enabled: boolean; label?: string }
      phone?: { enabled: boolean; label?: string }
    }
    settings?: {
      min_score?: number
      response_timeout_hours?: number
    }
    metrics?: {
      screened_count?: number
      completion_rate?: number
      average_rating?: number
    }
    scheduling?: {
      auto_enabled?: boolean
      min_score_for_auto?: number
      calendar_provider?: string
      available_hours?: string
      interview_duration_min?: number
    }
    feedback_templates?: {
      approved?: string
      rejected?: string
    }
    screening_status?: string
  }
  eligibility_questions?: {
    id?: string
    type: string
    question: string
    required?: boolean
    disqualify_on_fail?: boolean
    expected_answer?: string
    order?: number
  }[]
  confidentiality_config?: {
    can_reveal_company_name?: boolean
    masked_intro?: string
    can_discuss_salary?: boolean
    can_discuss_benefits?: boolean
  }
  published_at?: string
  last_published_at?: string
  closed_at?: string
  created_by?: string
  created_by_email?: string
}

export interface JobVacancyCreateRequest {
  title: string
  department?: string
  location?: string
  work_model?: string
  employment_type?: string
  seniority_level?: string
  description?: string
  requirements?: string[]
  technical_requirements?: Record<string, any>[]
  languages?: Record<string, any>[]
  behavioral_competencies?: Record<string, any>[]
  salary?: string
  salary_range?: {
    min?: number
    max?: number
    currency?: string
    bonus_min?: number
    bonus_max?: number
  }
  benefits?: string[]
  manager?: string
  manager_email?: string
  recruiter?: string
  recruiter_email?: string
  is_confidential?: boolean
  is_affirmative?: boolean
  visibility?: 'public' | 'internal' | 'confidential'
  urgency_level?: number
  open_date?: string
  status?: string
  priority?: string
  screening_questions?: Record<string, any>[]
  eligibility_questions?: Record<string, any>[]
  interview_stages?: Record<string, any>[]
  conversation_id?: string
  published_linkedin?: boolean
  published_indeed?: boolean
  published_website?: boolean
}

export interface JobVacancyListResponse {
  total: number
  skip: number
  limit: number
  items: JobVacancy[]
}

export interface PublishJobResponse {
  success: boolean
  job_id: string
  status: string
  message: string
  sourcing_result?: {
    local_candidates_found: number
    local_candidates_added: number
    global_search_available: boolean
    credits_required: number
    awaiting_global_confirmation: boolean
  }
}

export interface GlobalSearchConfirmResponse {
  success: boolean
  candidates_found: number
  candidates_added: number
  credits_used: number
  message: string
}

export interface SourcingStatusResponse {
  job_id: string
  total_candidates: number
  qualified_candidates: number
  pipeline_status: string
  recommended_action?: string
}

export interface JobVacancyMetrics {
  job_id: string
  funnel: {
    total: number
    screening: number
    interview: number
    offer: number
    hired: number
    rejected: number
  }
  performance: {
    time_to_fill_days: number | null
    avg_time_in_stage_days: number | null
    conversion_rate: number
    source_breakdown: Record<string, number>
  }
  activity: {
    views_7d: number
    applications_7d: number
    interviews_scheduled: number
    last_activity: string | null
  }
  sla: {
    within_sla: boolean
    days_remaining: number | null
    deadline: string | null
  }
}


// =============================================
// CANDIDATES TYPES
// =============================================

export interface CandidateLocal {
  id: string
  name: string
  email?: string | null
  secondary_email?: string | null
  phone?: string | null
  mobile_phone?: string | null
  secondary_phone?: string | null
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  avatar_url?: string
  
  date_of_birth?: string | null
  gender?: string | null
  nationality?: string | null
  marital_status?: string | null
  cpf?: string | null
  
  current_title?: string
  current_company?: string
  seniority_level?: string
  years_of_experience?: number
  self_introduction?: string | null
  
  technical_skills: string[]
  soft_skills: string[]
  languages: Record<string, string> | { language: string; level: string }[]
  certifications: string[]
  interests?: string[]
  
  location_city?: string
  location_state?: string
  location_country?: string
  address_street?: string | null
  address_number?: string | null
  address_district?: string | null
  address_zip?: string | null
  address_complement?: string | null
  
  is_remote: boolean
  willing_to_relocate: boolean
  mobility?: boolean
  work_model_preference?: string
  contract_type_preference?: string
  
  current_salary?: number | null
  salary_currency?: string
  desired_salary_min?: number
  desired_salary_max?: number
  salary_expectation_clt?: number | null
  salary_expectation_pj?: number | null
  salary_expectation_freelance?: number | null
  
  resume_url?: string | null
  resume_text?: string | null
  cover_letter?: string | null
  
  source: string
  ats_source_name?: string | null
  ats_candidate_id?: string | null
  pearch_profile_id?: string | null
  
  lia_score?: number
  lia_insights: Record<string, any>
  skills_match_percentage?: number
  
  status: string
  is_active: boolean
  is_blacklisted?: boolean
  blacklist_reason?: string | null
  
  preferred_contact_method?: string | null
  best_time_to_contact?: string | null
  communication_consent?: boolean
  
  completed_register?: boolean
  accept_terms?: boolean
  
  tags: string[]
  notes?: string
  additional_data?: Record<string, any>
  
  created_at?: string
  updated_at?: string
  last_contacted_at?: string
  last_activity_at?: string
  
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  company_info?: Record<string, any>
  expertise?: string[]
  outreach_message?: string
}

export interface CandidateCreateRequest {
  name: string
  email?: string | null
  phone?: string | null
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  current_title?: string
  current_company?: string
  seniority_level?: string
  years_of_experience?: number
  technical_skills?: string[]
  soft_skills?: string[]
  languages?: Record<string, string>
  certifications?: string[]
  location_city?: string
  location_state?: string
  location_country?: string
  is_remote?: boolean
  willing_to_relocate?: boolean
  desired_salary_min?: number
  desired_salary_max?: number
  salary_currency?: string
  work_model_preference?: string
  contract_type_preference?: string
  source: string
  tags?: string[]
  notes?: string
}

export interface CandidateListResponse {
  total: number
  skip: number
  limit: number
  items: CandidateLocal[]
}


// =============================================
// WSI (WeDoTalent Skill Index) TYPES
// =============================================

export interface WSICompetency {
  name: string
  type: 'technical' | 'behavioral' | 'cultural'
  level?: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  weight: number
}

export interface WSIQuestion {
  id: string
  competency: string
  framework: string
  question_type: string
  question_text: string
  weight: number
  sequence_order: number
}

export interface GenerateQuestionsRequest {
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  competencies: WSICompetency[]
  mode?: 'compact' | 'compact_plus'
}

export interface GenerateQuestionsResponse {
  session_id: string
  questions: WSIQuestion[]
  total_questions: number
}

export interface AnalyzeResponseRequest {
  session_id: string
  question_id: string
  candidate_id: string
  job_vacancy_id: string
  question_text: string
  response_text: string
  response_audio_url?: string
  competency: string
  framework: string
}

export interface AnalyzeResponseResponse {
  analysis_id: string
  competency: string
  autodeclaration_score?: number
  context_score?: number
  bloom_level?: number
  dreyfus_level?: number
  evidences: string[]
  red_flags: string[]
  final_score: number
  justification: string
}

export interface CalculateWSIRequest {
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  weights: Record<string, number>
}

export interface CalculateWSIResponse {
  result_id: string
  candidate_id: string
  job_vacancy_id: string
  technical_wsi: number
  behavioral_wsi: number
  overall_wsi: number
  classification: 'excelente' | 'alto' | 'medio' | 'regular' | 'baixo'
  percentile?: number
}

export interface StartVoiceScreeningRequest {
  candidate_id: string
  job_vacancy_id: string
  competencies: WSICompetency[]
  candidate_phone: string
  candidate_name: string
  job_title?: string
  job_description?: string
  mode?: 'compact' | 'compact_plus'
}

export interface StartVoiceScreeningResponse {
  session_id: string
  call_id: string
  agent_id: string
  candidate_id: string
  job_vacancy_id: string
  status: string
  questions_generated: number
}

export interface VoiceScreeningStatusResponse {
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  screening_type: string
  mode: string
  status: 'pending' | 'in_progress' | 'processing' | 'completed' | 'failed'
  call_id?: string
  agent_id?: string
  started_at?: string
  completed_at?: string
  result?: CalculateWSIResponse
}

export interface WSIResultsResponse {
  candidate_id: string
  total_screenings: number
  results: {
    result_id: string
    job_vacancy_id: string
    overall_wsi: number
    technical_wsi: number
    behavioral_wsi: number
    classification: string
    percentile?: number
    created_at: string
    screening_type: string
  }[]
}

export interface WSISessionResponse {
  session: {
    id: string
    candidate_id: string
    job_vacancy_id: string
    screening_type: string
    mode: string
    status: string
    started_at?: string
    completed_at?: string
  }
  questions: WSIQuestion[]
  responses: {
    question_id: string
    competency: string
    final_score: number
    justification: string
  }[]
}

export interface WSIResultDetails {
  result_id: string
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  scores: {
    technical_wsi: number
    behavioral_wsi: number
    overall_wsi: number
    classification: string
    percentile?: number
  }
  session: {
    screening_type: string
    mode: string
    started_at?: string
    completed_at?: string
    duration_minutes?: number
  }
  responses: {
    competency: string
    response_text: string
    scores: {
      autodeclaration?: number
      context?: number
      bloom_level?: number
      dreyfus_level?: number
      final_score: number
    }
    evidences: string[]
    red_flags: string[]
    consistency_penalty: number
    justification: string
    question: {
      text: string
      framework: string
      type: string
      weight: number
      expected_signals: string[]
      sequence: number
    }
  }[]
  report?: {
    executive_summary?: string
    technical_analysis: Record<string, any>
    behavioral_analysis: Record<string, any>
    cultural_fit: Record<string, any>
    recommendation: Record<string, any>
  }
  feedback?: {
    decision?: string
    main_message?: string
    technical_strengths: string[]
    development_opportunities: string[]
    behavioral_strengths: string[]
    next_steps?: string
    personalized_tip?: string
    development_plan: Record<string, any>
    recommended_resources: any[]
  }
  created_at?: string
}

export interface WSIVacancyRanking {
  job_vacancy_id: string
  total_screened: number
  averages: {
    overall: number
    technical: number
    behavioral: number
  }
  ranking: {
    rank: number
    total: number
    result_id: string
    candidate_id: string
    candidate_name: string
    candidate_title?: string
    overall_wsi: number
    technical_wsi: number
    behavioral_wsi: number
    classification: string
    percentile?: number
    screening_type: string
    created_at?: string
  }[]
}

export interface WSICandidateRanking {
  candidate_id: string
  job_vacancy_id: string
  ranked: boolean
  rank?: number
  total?: number
  overall_wsi?: number
}

export interface WSICandidatesScores {
  candidates: Record<string, {
    overall_wsi: number
    technical_wsi: number
    behavioral_wsi: number
    classification: string
    percentile: number
  }>
}

// =============================================
// COMPANY USERS TYPES
// =============================================

export interface CompanyUser {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
  active_jobs_count: number
  performance_score: number
}

export interface CompanyUsersResponse {
  users: CompanyUser[]
  total: number
}

// =============================================
// EMAIL TEMPLATES TYPES
// =============================================

export interface EmailTemplate {
  id: string
  name: string
  subject: string
  body_html: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables: string[]
  is_active: boolean
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
  created_by?: string
}

export interface EmailTemplateUpdateRequest {
  name?: string
  subject?: string
  body_html?: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables?: string[]
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
  variables: Record<string, any>
}

export interface EmailPreviewResponse {
  subject: string
  body_html: string
  body_text?: string
  variables_used: Record<string, any>
  missing_variables: string[]
}

export interface EmailSendRequest {
  recipient_email: string
  recipient_name?: string
  candidate_id?: string
  variables: Record<string, any>
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

export interface PipelineAction {
  id: string
  label: string
  icon: string
  action: string
  variant?: string
}

export interface StaleCandidateData {
  id: string
  name: string
  email: string
  current_title: string
  current_company: string
  status: string
  status_label: string
  days_stale: number
  stale_message: string
  urgency: "critical" | "high" | "normal"
  lia_score: number | null
  actions: PipelineAction[]
  last_activity: string | null
}

export interface PipelineGroup {
  job_id: string | null
  job_title: string
  job_department: string
  candidates: StaleCandidateData[]
}

export interface PipelineReportResponse {
  total_stale: number
  critical_count: number
  stale_threshold_days: number
  generated_at: string
  groups: PipelineGroup[]
  summary: {
    message: string
    urgency: "high" | "medium" | "low"
  }
}

export interface PipelineActionResponse {
  success: boolean
  candidate_id: string
  candidate_name: string
  message: string
  new_status?: string
  open_modal?: string
  navigate?: string
  action?: string
}


// =============================================
// BULK ACTIONS TYPES
// =============================================

export interface BulkOperationResult {
  success: boolean
  processed: number
  failed: number
  errors: Array<{
    id: string
    error: string
  }>
  results?: Array<{
    id: string
    status: string
    success: boolean
    error?: string
  }>
}

export interface BulkUpdateStatusRequest {
  candidate_ids: string[]
  new_status: string
}

export interface BulkAssignJobRequest {
  candidate_ids: string[]
  job_id: string
}

export interface BulkSendEmailRequest {
  candidate_ids: string[]
  template_id: string
  custom_data?: Record<string, any>
}

export interface BulkStartScreeningRequest {
  candidate_ids: string[]
  screening_type?: string
}

export interface BulkExportRequest {
  candidate_ids: string[]
  format: 'csv' | 'xlsx'
  fields?: string[]
}

export interface BulkDeleteRequest {
  candidate_ids: string[]
  hard_delete?: boolean
}

// =============================================
// NOTIFICATION TYPES
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
  extra_data: Record<string, any>
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

export interface CandidateList {
  id: string
  name: string
  description: string | null
  color: string | null
  created_by: string
  created_at: string | null
  updated_at: string | null
  candidate_count: number
}

export interface CandidateListMember {
  member_id: string
  added_at: string | null
  added_by: string
  notes: string | null
  source: string
  candidate: CandidateLocal
}

export interface CandidateListDetail extends CandidateList {
  candidates: {
    total: number
    skip: number
    limit: number
    items: CandidateListMember[]
  }
}

export interface CandidateListsResponse {
  total: number
  skip: number
  limit: number
  items: CandidateList[]
}

export interface AddCandidatesResult {
  success: boolean
  added: number
  already_exists: number
  errors: Array<{ candidate_id: string; error: string }>
  total_in_list: number
}

export interface RemoveCandidatesResult {
  success: boolean
  removed: number
  total_in_list: number
}

export interface AssignJobsResult {
  success: boolean
  assigned: number
  already_in_job: number
  jobs_count: number
  candidates_count: number
}

export interface DirectEmailRequest {
  recipient_email: string
  recipient_name?: string
  subject: string
  body_html: string
  body_text?: string
  candidate_id?: string
  vacancy_id?: string
  metadata?: Record<string, any>
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
    sendgrid: { configured: boolean }
    resend: { configured: boolean }
  }
  message: string
  database_logging: boolean
  audit_trail: boolean
}

export interface CreateInterviewRequest {
  candidate_id: string
  candidate_name: string
  candidate_email: string
  interviewer_name: string
  interviewer_email: string
  start_time: string
  duration_minutes?: number
  interview_type?: string
  interview_mode?: string
  job_title?: string
  job_vacancy_id?: string
  location?: string
  notes?: string
  additional_interviewers?: Array<{ name?: string; email?: string }>
}

export interface InterviewApiResponse {
  id: string
  title: string
  candidate_id?: string
  candidate_name: string
  candidate_email: string
  interviewer_name: string
  interviewer_email: string
  additional_interviewers: Array<{ name?: string; email?: string }>
  start_time: string
  end_time: string
  duration_minutes: number
  interview_type: string
  interview_mode: string
  location?: string
  meeting_url?: string
  job_title?: string
  job_vacancy_id?: string
  status: string
  confirmation_status: string
  notes?: string
  is_synced_to_calendar: boolean
  created_at: string
  updated_at: string
}

export interface InterviewListResponse {
  total: number
  items: InterviewApiResponse[]
  calendar_status: string
}

export interface SchedulingStatus {
  status: string
  mode: string
  providers: {
    microsoft_graph: { configured: boolean; features: string[] }
    google_calendar: { configured: boolean; features: string[] }
  }
  local_features: {
    database_storage: boolean
    ics_generation: boolean
    email_notifications: string
  }
  message: string
}

// =============================================
// SHARED SEARCH TYPES
// =============================================

export interface SharedSearchRecipient {
  email: string
  name?: string
  role?: string
}

export interface CreateSharedSearchRequest {
  share_type: 'search' | 'list'
  title: string
  description?: string
  source_query?: string
  source_list_id?: string
  candidate_ids: string[]
  recipients: SharedSearchRecipient[]
  expires_at?: string
  message?: string
}

export interface SharedSearchFeedbackSummary {
  approved: number
  maybe: number
  rejected: number
  pending: number
}

export interface SharedSearchRecipientSummary {
  email: string
  name?: string
  role: string
  first_accessed_at?: string
  last_accessed_at?: string
  total_views: number
  feedback_count: number
}

export interface SharedSearch {
  id: string
  company_id: string
  share_type: 'search' | 'list'
  title: string
  description?: string
  status: 'active' | 'expired' | 'revoked'
  expires_at?: string
  created_at: string
  candidate_count: number
  feedback_summary: SharedSearchFeedbackSummary
  recipients: SharedSearchRecipientSummary[]
}

export interface CandidateFeedback {
  id: string
  candidate_id: string
  reviewer_email: string
  decision: 'approved' | 'maybe' | 'rejected'
  rating?: number
  comment?: string
  created_at: string
}

export interface CandidateSnapshot {
  id: string
  name: string
  title?: string
  company?: string
  location?: string
  experience_years?: number
  skills: string[]
  wsi_score?: number
  feedback?: CandidateFeedback
}

export interface SharedSearchDetail extends SharedSearch {
  candidates: CandidateSnapshot[]
  feedbacks: CandidateFeedback[]
}

export interface AddToJobRequest {
  job_id: string
  candidate_ids?: string[]
  all_approved?: boolean
  include_notes?: boolean
}

// =============================================
// INTERVIEW NOTES TYPES
// =============================================

export interface GenerateInterviewQuestionsRequest {
  jobId: string
  candidateId: string
  includeVagaQuestions: boolean
  includeGapQuestions: boolean
  includeFitCultural: boolean
  wsiLevel?: string
}

export interface GenerateInterviewQuestionsResponse {
  questions: Array<{
    id: string
    text: string
    category: string
    subcategory?: string
    rationale?: string
    expectedResponse?: string
    wsiLevel?: string
  }>
  totalCount: number
  generatedAt: string
}

export interface GenerateInterviewParecerRequest {
  interviewNoteId: string
  candidateId?: string
  jobId?: string
  questions: Array<{
    id?: string
    questionId?: string
    text?: string
    questionText?: string
    starRating?: number | null
    rating?: number | null
    likertRating?: string | null
    notes?: string
    answer?: string
    skipped?: boolean
    category?: string
    source?: string
  }>
  generalNotes?: string
  transcription?: string | null
}

export interface GenerateInterviewParecerResponse {
  parecer: string
  recommendation: string
  strengths: string[]
  concerns: string[]
  overallScore?: number | null
  generatedAt: string
}

// =============================================
// INTERVIEW ANALYSIS TYPES
// =============================================

export interface InterviewAnalysisStatus {
  interview_id: string
  status: 'awaiting_transcript' | 'transcript_ready' | 'analyzed' | 'scheduled' | 'completed'
  has_transcript: boolean
  has_analysis: boolean
  analysis_result?: InterviewAnalysisResult
  error?: string
}

export interface InterviewAnalysisResult {
  overall_wsi_score: number
  recommendation: 'approve' | 'reject' | 'pending_review'
  bloom_scores: Record<string, number>
  dreyfus_scores: Record<string, number>
  big_five_profile: Record<string, number>
  star_completeness: number
  key_insights: string[]
  concerns: string[]
}

// =============================================
// AI SUGGESTIONS / AUTOMATION TYPES
// =============================================

export interface AISuggestion {
  id: string
  trigger: string
  candidate_id: string
  candidate_name: string
  vacancy_id: string
  vacancy_title: string
  suggested_action: string
  confidence: number
  reasoning: string[]
  created_at: string
  status: 'pending' | 'approved' | 'rejected' | 'modified'
}

export interface PendingAISuggestionsResponse {
  suggestions: AISuggestion[]
  total: number
}

export interface AISuggestionActionResponse {
  success: boolean
  suggestion_id: string
  new_status: string
  message?: string
}

export interface BulkAISuggestionActionResponse {
  success: boolean
  processed: number
  failed: number
  results: Array<{
    id: string
    success: boolean
    error?: string
  }>
}

// =============================================
// FAST TRACK VACANCY TYPES
// =============================================

export interface VacancySummary {
  id: string
  title: string
  department: string
  manager: string
  hired_candidate?: string
  date_closed: string
  salary_range: { min: number; max: number }
  work_model: string
  status: 'hired' | 'cancelled'
}

export interface VacancyFullDetails {
  id: string
  title: string
  department: string
  location: string
  work_model: string
  employment_type: string
  salary_range: { min: number; max: number; bonus_min?: number; bonus_max?: number }
  benefits: string[]
  technical_skills: Array<{ name: string; level: string; weight: number; required: boolean }>
  behavioral_competencies: Array<{ name: string; weight: number }>
  screening_questions: Array<{ question: string; type: string; expected_answer: any }>
  job_description: string
  manager: string
  manager_email: string
}

export interface VacancySearchCriteria {
  title?: string
  department?: string
  manager?: string
  location?: string
  work_model?: string
  status?: 'hired' | 'cancelled' | 'all'
  date_from?: string
  date_to?: string
  limit?: number
}

export interface VacancySearchResponse {
  vacancies: VacancySummary[]
  total: number
}

export interface VacancyAdjustments {
  salary_min?: number
  salary_max?: number
  location?: string
  work_model?: string
  benefits?: string[]
}

export interface PublishFastTrackResponse {
  success: boolean
  vacancy_id?: string
  message: string
}

// =============================================
// ORCHESTRATOR TYPES
// =============================================

export interface OrchestratorProcessRequest {
  user_id: string
  message: string
  conversation_id?: string
  context_type?: 'general' | 'wizard' | 'pipeline' | string  // Context type for routing
  context_id?: string  // ID related to context (e.g., job_id)
  conversation_context?: {
    conversation_id: string
    context_type: string
    context_id?: string
    summary?: string
    recent_messages: Array<{ role: string; content: string; intent?: string }>
  }  // Previous conversation context for memory
}

export interface OrchestratorProcessResponse {
  success: boolean
  conversation_id?: string
  intent?: string
  agent?: string
  confidence?: number
  result?: Record<string, any>
  message?: string
  error?: string
  suggested_tool_call?: {
    tool_name: string
    parameters?: Record<string, any>
    requires_confirmation?: boolean
    confirmation_message?: string
  }
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  draft_updates?: Record<string, unknown>
}

// =============================================
// CANDIDATE LIST TYPES
// =============================================

export interface CandidateListParams {
  search?: string
  status?: string
  tags?: string
  seniority?: string
  ids?: string
  limit?: number
  offset?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface CandidatePaginatedResponse {
  candidates: CandidateLocal[]
  total: number
  page: number
  per_page: number
}

export const liaApi = new LIAApiClient()

// Orchestrator exports
export const orchestratorProcess = (request: OrchestratorProcessRequest): Promise<OrchestratorProcessResponse> => {
  return liaApi.orchestratorProcess(request)
}

// Interview Analysis exports
export const getInterviewAnalysisStatus = (interviewId: string): Promise<InterviewAnalysisStatus> => {
  return liaApi.getInterviewAnalysisStatus(interviewId)
}

export const triggerInterviewAnalysis = (interviewId: string, forceRefresh = false): Promise<InterviewAnalysisStatus> => {
  return liaApi.triggerInterviewAnalysis(interviewId, forceRefresh)
}

// Intelligent Message Interpretation
export type InterpretMessageAction = 
  | 'advance_stage'
  | 'go_back'
  | 'confirm'
  | 'reject'
  | 'update_field'
  | 'ask_question'
  | 'provide_data'
  | 'help'
  | 'other'

export interface InterpretMessageRequest {
  message: string
  current_stage: string
  context?: Record<string, any>
}

export interface InterpretMessageResponse {
  action: InterpretMessageAction
  confidence: number
  extracted_entities?: Record<string, any>
  lia_response?: string
  should_advance: boolean
  target_stage?: string
  clarification_needed: boolean
  clarification_question?: string
  reasoning?: string
}

export async function interpretMessage(request: InterpretMessageRequest): Promise<InterpretMessageResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/job-wizard/interpret`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      console.error('Interpret message failed:', response.status)
      return {
        action: 'other',
        confidence: 0.5,
        should_advance: false,
        clarification_needed: false,
        lia_response: 'Não consegui interpretar a mensagem. Pode reformular?'
      }
    }

    return await response.json()
  } catch (error) {
    console.error('Error interpreting message:', error)
    return {
      action: 'other',
      confidence: 0.5,
      should_advance: false,
      clarification_needed: false,
      lia_response: 'Ocorreu um erro. Por favor, tente novamente.'
    }
  }
}

export interface ConversationalRequest {
  message: string
  context?: string
  mode?: string
}

export interface ConversationalResponse {
  response: string
  understood_intent: string
  suggested_action?: string
  can_help: boolean
}

export async function getConversationalResponse(request: ConversationalRequest): Promise<ConversationalResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/conversational`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      console.error('Conversational response failed:', response.status)
      return {
        response: "Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?",
        understood_intent: "fallback",
        can_help: true
      }
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting conversational response:', error)
    return {
      response: "Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?",
      understood_intent: "fallback",
      can_help: true
    }
  }
}

export type WizardOrchestratorAction = 
  | 'respond' 
  | 'advance_stage' 
  | 'update_fields' 
  | 'request_clarification' 
  | 'provide_suggestion' 
  | 'validate_data'

export interface WizardOrchestratorRequest {
  message: string
  current_stage: string
  collected_data: Record<string, any>
  conversation_history?: Array<{ role: string; content: string }>
  company_id?: string
  conversation_id?: string
  user_id?: string
}

export interface WizardOrchestratorResponse {
  success: boolean
  lia_message: string
  detected_criteria: Record<string, any>
  next_stage?: string
  auto_transition: boolean
  tool_results: Array<any>
  confidence: number
  reasoning_steps: string[]
  intent?: string
  error?: string
  awaiting_confirmation?: boolean
  job_vacancy_id?: string
  job_published?: boolean
  action?: WizardOrchestratorAction
  response?: string
  updated_fields?: Record<string, any>
  target_stage?: string
  reasoning?: string
  suggestions?: Array<{ field: string; value: any; reason: string }>
  validation_errors?: string[]
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  draft_updates?: Record<string, unknown>
}

export async function orchestrateWizardMessage(request: WizardOrchestratorRequest): Promise<WizardOrchestratorResponse> {
  try {
    console.log('[SmartOrchestrate] Calling /api/v1/wizard/smart-orchestrate with:', {
      message: request.message,
      current_stage: request.current_stage,
      has_collected_data: Object.keys(request.collected_data).length > 0
    })
    
    const response = await fetch(`${BACKEND_URL}/wizard/smart-orchestrate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: request.message,
        current_stage: request.current_stage,
        collected_data: request.collected_data,
        conversation_history: request.conversation_history || [],
        conversation_id: request.conversation_id,
        company_id: request.company_id,
        user_id: request.user_id
      }),
    })

    if (!response.ok) {
      console.error('[SmartOrchestrate] Request failed:', response.status)
      return {
        success: false,
        lia_message: 'Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?',
        detected_criteria: {},
        auto_transition: false,
        tool_results: [],
        confidence: 0.3,
        reasoning_steps: [],
        error: `HTTP ${response.status}`
      }
    }

    const result = await response.json()
    console.log('[SmartOrchestrate] Response received:', {
      success: result.success,
      next_stage: result.next_stage,
      auto_transition: result.auto_transition,
      awaiting_confirmation: result.awaiting_confirmation,
      job_vacancy_id: result.job_vacancy_id,
      job_published: result.job_published,
      confidence: result.confidence,
      detected_criteria_count: result.detected_criteria ? Object.keys(result.detected_criteria).length : 0
    })
    
    return result
  } catch (error) {
    console.error('[SmartOrchestrate] Error:', error)
    return {
      success: false,
      lia_message: 'Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?',
      detected_criteria: {},
      auto_transition: false,
      tool_results: [],
      confidence: 0.3,
      reasoning_steps: [],
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// ============================================================================
// FEEDBACK API
// ============================================================================

export interface ThumbsFeedbackResponse {
  feedback_id: string
  status: string
}

export interface RatingFeedbackResponse {
  feedback_id: string
  status: string
}

export interface CorrectionFeedbackResponse {
  feedback_id: string
  status: string
}

export interface FeedbackMetrics {
  satisfaction_rate: number
  total_feedback: number
  rating_average: number
}

export async function submitThumbsFeedback(
  sessionId: string,
  messageId: string,
  thumbs: 'up' | 'down',
  userId?: string
): Promise<ThumbsFeedbackResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/feedback/thumbs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        thumbs,
        user_id: userId || 'default_user'
      })
    })
    if (!response.ok) {
      console.warn('Thumbs feedback submission failed:', response.status)
      return { feedback_id: '', status: 'error' }
    }
    return response.json()
  } catch (error) {
    console.warn('Thumbs feedback error:', error)
    return { feedback_id: '', status: 'error' }
  }
}

export async function submitRatingFeedback(
  sessionId: string,
  messageId: string,
  rating: number,
  feedbackText?: string,
  category?: string
): Promise<RatingFeedbackResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/feedback/rating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        rating,
        feedback_text: feedbackText,
        category
      })
    })
    if (!response.ok) {
      console.warn('Rating feedback submission failed:', response.status)
      return { feedback_id: '', status: 'error' }
    }
    return response.json()
  } catch (error) {
    console.warn('Rating feedback error:', error)
    return { feedback_id: '', status: 'error' }
  }
}

export async function submitCorrectionFeedback(
  sessionId: string,
  messageId: string,
  originalResponse: string,
  correction: string
): Promise<CorrectionFeedbackResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/feedback/correction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message_id: messageId,
        original_response: originalResponse,
        correction
      })
    })
    if (!response.ok) {
      console.warn('Correction feedback submission failed:', response.status)
      return { feedback_id: '', status: 'error' }
    }
    return response.json()
  } catch (error) {
    console.warn('Correction feedback error:', error)
    return { feedback_id: '', status: 'error' }
  }
}

export async function getFeedbackMetrics(days?: number): Promise<FeedbackMetrics> {
  try {
    const params = days ? `?days=${days}` : ''
    const response = await fetch(`${BACKEND_URL}/lia/feedback/metrics${params}`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Feedback metrics fetch failed:', response.status)
      return { satisfaction_rate: 0, total_feedback: 0, rating_average: 0 }
    }
    return response.json()
  } catch (error) {
    console.warn('Feedback metrics error:', error)
    return { satisfaction_rate: 0, total_feedback: 0, rating_average: 0 }
  }
}

// ============================================================================
// VOICE API
// ============================================================================

export interface TranscriptionResponse {
  text: string
  confidence: number
  duration: number
}

export interface VoiceChatResponse {
  transcription: string
  response_text: string
  response_audio_base64: string
  session_id: string
  job_draft?: Record<string, any>
}

export interface VoiceStatusResponse {
  transcription_available: boolean
  synthesis_available: boolean
}

export async function transcribeAudio(
  audioBlob: Blob,
  language?: string
): Promise<TranscriptionResponse> {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    if (language) formData.append('language', language)

    const response = await fetch(`${BACKEND_URL}/lia/voice/transcribe`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      console.warn('Audio transcription failed:', response.status)
      return { text: '', confidence: 0, duration: 0 }
    }
    return response.json()
  } catch (error) {
    console.warn('Audio transcription error:', error)
    return { text: '', confidence: 0, duration: 0 }
  }
}

export async function synthesizeSpeech(
  text: string,
  voice?: string
): Promise<Blob> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/voice/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice })
    })
    if (!response.ok) {
      console.warn('Speech synthesis failed:', response.status)
      return new Blob()
    }
    return response.blob()
  } catch (error) {
    console.warn('Speech synthesis error:', error)
    return new Blob()
  }
}

export async function voiceChat(
  audioBlob: Blob,
  sessionId?: string
): Promise<VoiceChatResponse> {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'audio.webm')
    if (sessionId) formData.append('session_id', sessionId)

    const response = await fetch(`${BACKEND_URL}/lia/voice/chat`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      console.warn('Voice chat failed:', response.status)
      return {
        transcription: '',
        response_text: 'Desculpe, não consegui processar o áudio.',
        response_audio_base64: '',
        session_id: sessionId || ''
      }
    }
    return response.json()
  } catch (error) {
    console.warn('Voice chat error:', error)
    return {
      transcription: '',
      response_text: 'Desculpe, ocorreu um erro ao processar o áudio.',
      response_audio_base64: '',
      session_id: sessionId || ''
    }
  }
}

export async function getVoiceStatus(): Promise<VoiceStatusResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/voice/status`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Voice status fetch failed:', response.status)
      return { transcription_available: false, synthesis_available: false }
    }
    return response.json()
  } catch (error) {
    console.warn('Voice status error:', error)
    return { transcription_available: false, synthesis_available: false }
  }
}

// ============================================================================
// MULTIMODAL API
// ============================================================================

export interface ImageAnalysisResponse {
  analysis: string
  extracted_text?: string
  confidence: number
}

export interface DocumentAnalysisResponse {
  text_content: string
  structure: Record<string, any>
  formatting_quality: number
}

export interface ResumeAnalysisResponse {
  candidate_name: string
  contact_info: Record<string, any>
  layout_score: number
  improvement_suggestions: string[]
}

export interface MultimodalStatusResponse {
  image_analysis: boolean
  video_analysis: boolean
  document_analysis: boolean
}

export async function analyzeImage(
  file: File,
  analysisType?: string,
  prompt?: string
): Promise<ImageAnalysisResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (analysisType) formData.append('analysis_type', analysisType)
    if (prompt) formData.append('prompt', prompt)

    const response = await fetch(`${BACKEND_URL}/lia/multimodal/analyze-image`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      console.warn('Image analysis failed:', response.status)
      return { analysis: '', confidence: 0 }
    }
    return response.json()
  } catch (error) {
    console.warn('Image analysis error:', error)
    return { analysis: '', confidence: 0 }
  }
}

export async function analyzeDocument(
  file: File,
  documentType?: string
): Promise<DocumentAnalysisResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (documentType) formData.append('document_type', documentType)

    const response = await fetch(`${BACKEND_URL}/lia/multimodal/analyze-document`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      console.warn('Document analysis failed:', response.status)
      return { text_content: '', structure: {}, formatting_quality: 0 }
    }
    return response.json()
  } catch (error) {
    console.warn('Document analysis error:', error)
    return { text_content: '', structure: {}, formatting_quality: 0 }
  }
}

export async function analyzeResume(file: File): Promise<ResumeAnalysisResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${BACKEND_URL}/lia/multimodal/analyze-resume`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      console.warn('Resume analysis failed:', response.status)
      return {
        candidate_name: '',
        contact_info: {},
        layout_score: 0,
        improvement_suggestions: []
      }
    }
    return response.json()
  } catch (error) {
    console.warn('Resume analysis error:', error)
    return {
      candidate_name: '',
      contact_info: {},
      layout_score: 0,
      improvement_suggestions: []
    }
  }
}

export async function getMultimodalStatus(): Promise<MultimodalStatusResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/multimodal/status`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Multimodal status fetch failed:', response.status)
      return { image_analysis: false, video_analysis: false, document_analysis: false }
    }
    return response.json()
  } catch (error) {
    console.warn('Multimodal status error:', error)
    return { image_analysis: false, video_analysis: false, document_analysis: false }
  }
}

// ============================================================================
// AUTONOMOUS JOBS API
// ============================================================================

export interface BackgroundJob {
  id: string
  job_type: string
  name: string
  status: string
  progress: number
  created_at: string
}

export interface ProactiveAction {
  id: string
  title: string
  description: string
  priority: string
  suggested_action: Record<string, any>
  created_at: string
}

export interface CreateJobResponse {
  job_id: string
  status: string
}

export interface ExecuteJobResponse {
  status: string
  result: Record<string, any>
}

export interface ActionResponse {
  status: string
}

export async function createBackgroundJob(
  jobType: string,
  name: string,
  config: Record<string, any>,
  schedule?: string
): Promise<CreateJobResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_type: jobType,
        name,
        config,
        schedule
      })
    })
    if (!response.ok) {
      console.warn('Background job creation failed:', response.status)
      return { job_id: '', status: 'error' }
    }
    return response.json()
  } catch (error) {
    console.warn('Background job creation error:', error)
    return { job_id: '', status: 'error' }
  }
}

export async function listBackgroundJobs(
  status?: string,
  limit?: number
): Promise<BackgroundJob[]> {
  try {
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    if (limit) params.set('limit', String(limit))
    const queryString = params.toString() ? `?${params.toString()}` : ''

    const response = await fetch(`${BACKEND_URL}/lia/autonomous/jobs${queryString}`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Background jobs list failed:', response.status)
      return []
    }
    return response.json()
  } catch (error) {
    console.warn('Background jobs list error:', error)
    return []
  }
}

export async function executeJob(jobId: string): Promise<ExecuteJobResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/jobs/${jobId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Job execution failed:', response.status)
      return { status: 'error', result: {} }
    }
    return response.json()
  } catch (error) {
    console.warn('Job execution error:', error)
    return { status: 'error', result: {} }
  }
}

export async function getProactiveActions(
  status?: string,
  limit?: number
): Promise<ProactiveAction[]> {
  try {
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    if (limit) params.set('limit', String(limit))
    const queryString = params.toString() ? `?${params.toString()}` : ''

    const response = await fetch(`${BACKEND_URL}/lia/autonomous/actions${queryString}`, {
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Proactive actions fetch failed:', response.status)
      return []
    }
    return response.json()
  } catch (error) {
    console.warn('Proactive actions error:', error)
    return []
  }
}

export async function acceptProactiveAction(actionId: string): Promise<ActionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/actions/${actionId}/accept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Action accept failed:', response.status)
      return { status: 'error' }
    }
    return response.json()
  } catch (error) {
    console.warn('Action accept error:', error)
    return { status: 'error' }
  }
}

export async function rejectProactiveAction(actionId: string): Promise<ActionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}/lia/autonomous/actions/${actionId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      console.warn('Action reject failed:', response.status)
      return { status: 'error' }
    }
    return response.json()
  } catch (error) {
    console.warn('Action reject error:', error)
    return { status: 'error' }
  }
}

// ============ WSI Question Regeneration ============

export interface WSIQuestionForRegeneration {
  id: string
  question_text: string
  question_type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  competency_validated: string | null
  competency_type: 'technical' | 'behavioral' | 'eligibility' | null
  expected_answer_pattern?: string
  follow_up_question?: string
  weight?: number
}

export interface RegenerateWSIQuestionsRequest {
  company_id: string
  job_title: string
  current_questions: WSIQuestionForRegeneration[]
  technical_skills: string[]
  behavioral_competencies: string[]
  seniority?: string
  max_questions?: number
}

export interface RegenerateWSIQuestionsResponse {
  success: boolean
  questions: WSIQuestionForRegeneration[]
  questions_added: number
  questions_removed: number
  quality_warnings: string[]
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
      console.error('WSI regeneration failed:', response.status)
      return {
        success: false,
        questions: request.current_questions,
        questions_added: 0,
        questions_removed: 0,
        quality_warnings: ['Failed to regenerate questions']
      }
    }
    
    return response.json()
  } catch (error) {
    console.error('WSI regeneration error:', error)
    return {
      success: false,
      questions: request.current_questions,
      questions_added: 0,
      questions_removed: 0,
      quality_warnings: ['Network error during regeneration']
    }
  }
}

export default liaApi
