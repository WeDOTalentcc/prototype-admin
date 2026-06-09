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
  classification:
    | 'excepcional'
    | 'excelente'
    | 'alto'
    | 'medio'
    | 'regular'
    | 'abaixo_da_media'
    | 'baixo'
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
    decision?: string
  }
  session: {
    screening_type: string
    mode: string
    started_at?: string
    completed_at?: string
    duration_minutes?: number
    session_id?: string
    seniority_label?: string
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
      star?: Record<string, unknown>
      bloom_expected?: number
    }
    star?: Record<string, unknown>
    gap_status?: string
    is_critical?: boolean
    bloom_expected?: number
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
    // Audit task #528 (G23-02 / G23-03) — transparência LGPD/EU AI Act.
    // Modal/kanban consomem para mostrar banner degraded e breakdown granular.
    flags_structured?: Record<string, boolean>
    penalty_breakdown?: Record<string, number>
    bonus_breakdown?: Record<string, number>
    degraded_quality?: boolean
    degraded_reasons?: string[]
    layer2_degraded_reason?: string | null
  }[]
  // Agregação cross-respostas para banner global do relatório.
  degraded_quality?: boolean
  degraded_reasons?: string[]
  degraded_count?: number
  report?: {
    executive_summary?: string
    technical_analysis: Record<string, unknown>
    behavioral_analysis: Record<string, unknown>
    cultural_fit: Record<string, unknown>
    recommendation: Record<string, unknown>
  }
  feedback?: {
    decision?: string
    main_message?: string
    technical_strengths: string[]
    development_opportunities: string[]
    behavioral_strengths: string[]
    next_steps?: string
    personalized_tip?: string
    development_plan: Record<string, unknown>
    recommended_resources: Record<string, unknown>[]
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
    // Audit task #530 (G23-02 frontend) — flag de modo degradado por candidato
    // (agregada das respostas da última sessão WSI). Usado pelo kanban e tabela
    // para exibir um indicador de atenção ao lado do score de triagem.
    degraded_quality?: boolean
  }>
}

// =============================================
// COMPANY USERS TYPES
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
// TRIAGEM SESSION RESPONSE (eligibility + WSI)
// =============================================

/** Shape do response de GET /triagem/sessions?candidate_id=X&job_id=Y */
export interface TriagemSessionEligibilityResponse {
  /** True quando o candidato foi eliminado na fase de elegibilidade */
  eliminated?: boolean
  /** Texto legível descrevendo a razão da eliminação, ex: "O candidato não atendeu ao critério de disponibilidade presencial." */
  elimination_reason_text?: string | null
  eligibility_results?: EligibilityResultItemRaw[]
}

/** Shape bruto do item de elegibilidade conforme retornado pelo backend */
export interface EligibilityResultItemRaw {
  id?: string | number
  question: string
  answer?: string | null
  passed: boolean
  is_eliminatory?: boolean
  reconsideration?: string | null
}

// =============================================
// AI SUGGESTIONS / AUTOMATION TYPES
// =============================================
