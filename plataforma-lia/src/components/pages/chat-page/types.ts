import type React from "react"
import type { ChatCardType } from "@/components/ui-actions/types"

interface Message {
  id: number
  sender: "lia" | "user"
  content: string
  timestamp: string
  type?: "text" | "action" | "structured" | "file" | "system" | "approval" | "thinking" | "progress" | "command" | "file-creation" | "completion" | "flow"
  actions?: Array<{ label: string; icon?: React.ElementType; variant?: "default" | "outline" | "secondary" }>
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
  chatCardType?: ChatCardType
  chatCardData?: Record<string, unknown>
  // Novos campos para status indicators
  thinkingMessage?: string
  progressSteps?: Array<{
    id: string
    label: string
    status: "pending" | "processing" | "completed" | "error"
    details?: string
    icon?: React.ElementType
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

interface ContextPanelData {
  type: "candidate" | "candidates" | "job" | "schedule" | "shortlist" | "report" | "comparison" | "analytics" | "job-details" | "position" | "recruitment-strategy" | "recruitment-process" | "job-final" | "job-description" | "compensation-package" | "search-strategy" | "candidate-suggestions" | "job-launch" | "evaluation-format" | "journey-progress" | "search-analytics" | "executive-report" | "proposal-template" | "final-report" | "shortlist-approval" | "screening-guide" | "org-structure-analysis" | "hierarchy-definition" | "technical-competencies" | "behavioral-competencies" | "complete-job-description" | "role-scope-definition" | "work-arrangement" | "sourcing-strategy" | "final-job-description" | "job-publishing" | "sourcing-progress" | "interview-management" | "final-selection" | "onboarding-plan" | "performance-management" | "journey-summary" | "predictive-insights" | "offer-letter" | "interview-scheduling" | "technical-matrix" | "timeline" | "interview-flow" | "org-chart" | "job-creation-progress" | "pipeline-report"
  title: string
  data: Record<string, unknown>
}

interface AgentData {
  id: string
  name: string
  icon: string
  description: string
  status: "active" | "idle" | "error"
  actionsToday: number
  lastActivity: string
  lastActivityTime: string
}

interface AgentActivity {
  id: string
  agentId: string
  agentIcon: string
  agentName: string
  action: string
  timestamp: string
  status: "success" | "pending" | "error"
}

export type { Message, ContextPanelData, AgentData, AgentActivity }
