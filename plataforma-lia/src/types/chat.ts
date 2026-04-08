"use client"

export interface Message {
  id: number
  sender: "lia" | "user"
  content: string
  timestamp: string
  type?: "text" | "action" | "structured" | "file" | "system" | "approval" | "thinking" | "progress" | "command" | "file-creation" | "completion" | "flow"
  actions?: Array<{ label: string; icon?: React.ComponentType<{ className?: string }>; variant?: "default" | "outline" | "secondary" }>
  data?: Record<string, unknown>
  step?: string
  contextData?: Record<string, unknown>
  needsApproval?: boolean
  approvalStatus?: "pending" | "approved" | "rejected"
  approvalRequest?: {
    title: string
    description: string
    manager: string
    items: Array<{ label: string; value: string }>
  }
  chatCardType?: import("@/components/ui-actions/types").ChatCardType
  chatCardData?: Record<string, unknown>
  thinkingMessage?: string
  flowSteps?: Array<{ id: string; label: string; icon?: string; status: "completed" | "in_progress" | "pending"; detail?: string }>
  flowQuestion?: string
  progressSteps?: Array<{
    id: string
    label: string
    status: "pending" | "processing" | "completed" | "error"
    details?: string
    icon?: React.ComponentType<{ className?: string }>
  }>
  currentStep?: string
  command?: {
    text: string
    status: "executing" | "completed" | "error"
    output?: string
  }
  fileCreation?: {
    fileName: string
    fileType: string
    status: "creating" | "created"
  }
  completion?: {
    message: string
    allowRating?: boolean
    allowFollowUp?: boolean
  }
}

export interface ContextPanelData {
  type:
    | "candidate"
    | "candidates"
    | "job"
    | "schedule"
    | "shortlist"
    | "report"
    | "comparison"
    | "analytics"
    | "job-details"
    | "position"
    | "recruitment-strategy"
    | "recruitment-process"
    | "job-final"
    | "job-description"
    | "compensation-package"
    | "search-strategy"
    | "candidate-suggestions"
    | "job-launch"
    | "evaluation-format"
    | "journey-progress"
    | "search-analytics"
    | "executive-report"
    | "proposal-template"
    | "final-report"
    | "shortlist-approval"
    | "screening-guide"
    | "org-structure-analysis"
    | "hierarchy-definition"
    | "technical-competencies"
    | "behavioral-competencies"
    | "complete-job-description"
    | "role-scope-definition"
    | "work-arrangement"
    | "sourcing-strategy"
    | "final-job-description"
    | "job-publishing"
    | "sourcing-progress"
    | "interview-management"
    | "final-selection"
    | "onboarding-plan"
    | "performance-management"
    | "journey-summary"
    | "predictive-insights"
    | "offer-letter"
    | "interview-scheduling"
    | "technical-matrix"
    | "timeline"
    | "interview-flow"
    | "org-chart"
    | "job-creation-progress"
    | "pipeline-report"
  title: string
  data: Record<string, unknown>
}
