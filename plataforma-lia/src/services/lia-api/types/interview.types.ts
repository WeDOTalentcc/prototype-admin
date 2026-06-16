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
