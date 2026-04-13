export type GoalStatus = "exceeded" | "achieved" | "on_track" | "behind"

export interface MonthlyGoal {
  target: number
  current: number
  status: GoalStatus
}

export interface QuarterlyGoal {
  target: number
  current: number
  status: GoalStatus
}

export interface RecruiterGoals {
  monthly: {
    hires: MonthlyGoal
    timeToFill: MonthlyGoal
    nps: MonthlyGoal
    interviews: MonthlyGoal
  }
  quarterly: {
    qualityScore: QuarterlyGoal
    conversionRate: QuarterlyGoal
  }
}

export interface RecruiterData {
  name: string
  role: string
  avatar: string
  department: string
  activeJobs: number
  totalJobs: number
  totalCandidates: number
  scheduledInterviews: number
  completedInterviews: number
  totalHires: number
  avgTimeToFill: number
  conversionRate: number
  npsScore: number
  interviewsPerWeek: number
  candidateResponseRate: number
  offerAcceptanceRate: number
  qualityOfHireScore: number
  ranking: number
  totalScore: number
  goals: RecruiterGoals
  monthlyTrends: {
    interviews: number[]
    hires: number[]
    sourceQuality: number[]
    nps: number[]
    timeToFill: number[]
  }
  sourcing: {
    linkedin: number
    referrals: number
    jobBoards: number
    headhunting: number
  }
}

export interface TeamMetrics {
  activeJobs: number
  totalCandidates: number
  totalHires: number
  completedInterviews: number
  avgConversionRate: string
  avgTimeToFill: number
  avgNPS: number
  avgQualityScore: string
  totalRecruiters: number
}

export type ActiveTab =
  | "strategic"
  | "recruiters"
  | "alerts"
  | "predictions"
  | "agent_control"

export type ViewMode = "cards" | "ranking" | "goals" | "comparison"
