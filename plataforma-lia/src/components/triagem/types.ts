export type TriagemStatus =
  | "invited"
  | "started"
  | "in_progress"
  | "completed"
  | "expired"
  | "cancelled"

export type TriagemMessageRole = "lia" | "candidate"

export type TriagemMessageType =
  | "text"
  | "multiple_choice"
  | "likert_scale"
  | "audio"
  | "system"

export interface WSIProgress {
  currentBlock: number
  totalBlocks: number
  currentBlockName: string
  questionsAnswered: number
  totalQuestions: number
  estimatedMinutesRemaining: number
}

export interface TriagemSession {
  id: string
  token: string
  status: TriagemStatus
  candidateId: string
  candidateName: string
  jobId: string
  jobTitle: string
  companyName: string
  companyLogoUrl: string | null
  progress: WSIProgress
  createdAt: string
  expiresAt: string
  startedAt: string | null
  completedAt: string | null
  wsiFinalNota?: number | null
  /** Alias canonical em camelCase usado pelos mappers de backend. */
  wsiFinalScore?: number | null
  recommendation: "approved" | "pending" | "rejected" | null
}

export interface TriagemMessageOption {
  id: string
  label: string
  value: string
}

export interface TriagemMessage {
  id: string
  sessionId: string
  role: TriagemMessageRole
  type: TriagemMessageType
  content: string
  options: TriagemMessageOption[] | null
  selectedOption: string | null
  likertValue: number | null
  likertLabels: string[] | null
  timestamp: string
  blockIndex: number | null
  blockName: string | null
  audioUrl: string | null
}

export interface TriagemSalaryRange {
  min?: number
  max?: number
  currency?: string
}

export interface TriagemConfig {
  companyName: string
  companyLogoUrl: string | null
  jobTitle: string
  candidateName: string
  estimatedMinutes: number
  privacyPolicyUrl: string
  audioEnabled: boolean
  feedbackEnabled: boolean
  welcomeMessage: string
  voiceMode: boolean
  jobDescription?: string | null
  location?: string | null
  workModel?: string | null
  salaryRange?: TriagemSalaryRange | null
  benefits?: string[] | null
  showSalary?: boolean
  showBenefits?: boolean
  /** Task #425: per-channel availability gated by master toggle. */
  chatWebEnabled?: boolean
  whatsappEnabled?: boolean
  phoneEnabled?: boolean
  /** Voice-in-browser channel availability (Gemini Live). Task #425. */
  voiceWebEnabled?: boolean
  /** Recruiter-known candidate phone (E.164 or national format) for pre-fill. */
  candidatePhone?: string | null
}

export interface TriagemError {
  code: "TOKEN_INVALID" | "TOKEN_EXPIRED" | "SESSION_COMPLETED" | "RATE_LIMITED" | "SERVER_ERROR"
  message: string
}

export type TriagemPageState =
  | "loading"
  | "error"
  | "welcome"
  | "chat"
  | "confirmation"
  | "completion"

export interface TriagemCompletionSummary {
  questionsAnswered: number
  durationMinutes: number
  nextSteps: string[]
}

export interface SendMessagePayload {
  content: string
  type: TriagemMessageType
  selectedOption?: string
  likertValue?: number
  voiceMode?: boolean
}

export interface UseTriagemChatReturn {
  pageState: TriagemPageState
  session: TriagemSession | null
  config: TriagemConfig | null
  messages: TriagemMessage[]
  progress: WSIProgress | null
  error: TriagemError | null
  completionSummary: TriagemCompletionSummary | null
  isLiaTyping: boolean
  isSending: boolean
  isLoadingHistory: boolean
  initSession: () => Promise<void>
  startChat: (voiceMode?: boolean) => Promise<void>
  sendMessage: (payload: SendMessagePayload) => Promise<void>
  completeSession: () => Promise<void>
  reviewSession: () => void
  loadHistory: () => Promise<void>
}
