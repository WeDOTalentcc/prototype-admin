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
