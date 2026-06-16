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
  job_draft?: Record<string, unknown>
}

export interface VoiceStatusResponse {
  transcription_available: boolean
  synthesis_available: boolean
  streaming_available?: boolean
  voice_provider?: string
  voice_strategy?: string
}

export interface VoiceStreamMessage {
  type: 'audio' | 'transcript' | 'status' | 'metrics' | 'error' | 'turn_complete' | 'timeout'
  data?: string
  text?: string
  role?: 'candidate' | 'lia'
  mime_type?: string
  status?: string
  session_id?: string
  voice_provider?: string
  message?: string
  latency_ms?: number
  tokens?: Record<string, number>
  metadata?: Record<string, unknown>
}

export interface VoiceStreamSessionResponse {
  success: boolean
  session_id: string
  status: string
  voice_provider: string
  voice_strategy?: string
  gemini_available?: boolean
  ws_token?: string
  error?: string
}

export interface ImageAnalysisResponse {
  analysis: string
  extracted_text?: string
  confidence: number
}

export interface DocumentAnalysisResponse {
  text_content: string
  structure: Record<string, unknown>
  formatting_quality: number
}

export interface ResumeContactInfo {
  email?: string
  phone?: string
  location?: string
  linkedin?: string
  [key: string]: string | undefined
}

export interface ResumeAnalysisResponse {
  candidate_name: string
  contact_info: ResumeContactInfo
  layout_score: number
  improvement_suggestions: string[]
}

export interface MultimodalStatusResponse {
  image_analysis: boolean
  video_analysis: boolean
  document_analysis: boolean
}

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
  suggested_action: Record<string, unknown>
  created_at: string
}

export interface CreateJobResponse {
  job_id: string
  status: string
}

export interface ExecuteJobResponse {
  status: string
  result: Record<string, unknown>
}

export interface ActionResponse {
  status: string
}
