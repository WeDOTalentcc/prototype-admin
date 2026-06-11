export type QueryInsight = {
  match_level?: string
  subquery?: string
}

export type KanbanCandidate = {
  id: string
  name: string
  stage?: string
  etapa?: string
  stageId?: string
  candidateCode?: string
  score?: number | null
  liaScore?: number | null
  skillsMatch?: number | null
  fitScore?: number | null
  technicalTestScore?: number | null
  englishTestScore?: number | null
  bigFive?: Record<string, number> | null
  bigFiveScores?: Record<string, number> | null
  agendada?: string | boolean
  interviewDate?: string
  status?: string
  sub_status?: string
  needsAction?: boolean
  avatar?: string
  role?: string
  position?: string
  currentCompany?: string
  source?: string
  isDemo?: boolean
  is_opentowork?: boolean
  is_open_to_work?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_hiring?: boolean
  headline?: string
  expertise?: string | string[]
  linkedin_followers_count?: number
  linkedin_connections_count?: number
  outreach_message?: string
  best_personal_email?: string
  phone_types?: Record<string, boolean>
  estimated_age?: number
  pearch_insights?: {
    overall_summary?: string
    query_insights?: QueryInsight[]
    match_reasoning?: string
  }
  middle_name?: string
  best_business_email?: string
  personal_emails?: string[]
  business_emails?: string[]
  company_followers_count?: number
  company_keywords?: string[]
  liaAnalysis?: unknown
  cvAnalysis?: unknown
  triagemHistory?: unknown
  screeningHistory?: unknown
  [key: string]: unknown
}

export interface DynamicStageItem {
  id: string
  name: string
  displayName: string
  color?: string
}

export interface KanbanTableCellRendererProps {
  t: (key: string, values?: Record<string, string>) => string
  dynamicStages: DynamicStageItem[]
  jobVacancyId?: string
  viewedCandidateIds: Set<string>
  calculateNotaLiaGeral: (candidate: KanbanCandidate) => number | null
  getLiaAlerts: (candidate: KanbanCandidate) => Record<string, unknown>[]
  getDataRequestForCandidate: (candidateId: string) => Record<string, unknown> | null | undefined
  onDataRequestResend: (candidateId: string) => void
  onDataRequestViewDetails: (candidateId: string) => void
  onOpenTriagem: (candidate: KanbanCandidate) => void
  onOpenAnalysis: (candidate: KanbanCandidate) => void
  onSetSelectedCandidateForModal: (candidate: KanbanCandidate) => void
  onSetActiveModal: (modal: string) => void
  onSetShowBigFiveModal: (show: boolean) => void
  onSetScoreModalCandidate: (candidate: KanbanCandidate) => void
  onApproveFromScreening: (candidate: KanbanCandidate) => void
  onRejectFromScreening: (candidate: KanbanCandidate) => void
  onApproveCandidate: (candidate: KanbanCandidate) => void
  onRejectCandidate: (candidate: KanbanCandidate) => void
  openDecisionFlowModal: (candidate: KanbanCandidate, action: "approve" | "reject") => void
  onSetTransitionInitialPrompt: (prompt: string) => void
  onSetTransitionAllowStageSelection: (allow: boolean) => void
  onSetTransitionInterviewAlert: (alert: { name: string; date: string }) => void
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  onTransitionRequired: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  onStatusChange: (candidateId: string, newSubStatus: string, stage: string, jobVacancyId?: string) => Promise<boolean>
  onCandidateClick: (candidate: KanbanCandidate) => void
}
