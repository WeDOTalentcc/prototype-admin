import { type Job } from "@/components/jobs"
import { type ScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"
import { type JobVacancyMetrics } from "@/services/lia-api"

export type TechnicalRequirement = string | { technology?: string; name?: string; [key: string]: unknown }
export type BehavioralCompetency = string | { competency?: string; name?: string; [key: string]: unknown }
export type Requirement = string | { requirement?: string; text?: string; name?: string; [key: string]: unknown }
export type Benefit = string | { name?: string; [key: string]: unknown }
export type InterviewStage = { order?: number; stageName?: string; liaAssisted?: boolean; [key: string]: unknown }
export type Language = { language?: string; level?: string; required?: boolean; [key: string]: unknown }

export type ScreeningQuestion = {
  id?: string
  category?: string
  type?: string
  required?: boolean
  block_id?: number
  time_limit?: number
  text?: string
  question?: string
  skill_targeted?: string
  [key: string]: unknown
}

export interface JobPreviewPanelProps {
  showJobPreview: boolean
  previewJob: Job | null
  activePreviewTab: 'screening' | 'pipeline'
  onTabChange: (tab: 'screening' | 'pipeline') => void
  previewWidth: number
  onResize: (width: number) => void
  onResizeStart: () => void
  onResizeEnd: () => void
  onClose: () => void
  onJobClick: (job: Job) => void
  screeningConfig: ScreeningConfig | undefined
  isLoadingScreeningConfig: boolean
  jobMetrics: JobVacancyMetrics | null
  isLoadingJobMetrics: boolean
}
