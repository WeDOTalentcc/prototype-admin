export interface SubStatus {
  id: string
  stage_id: string
  name: string
  display_name: string
  description?: string
  is_active: boolean
  is_default: boolean
  is_waiting: boolean
  waiting_for?: string
  sla_hours?: number
  sub_status_order: number
  color?: string
  icon?: string
}

/** Minimal shape used by kanban/wizard when sub_statuses are embedded in pipeline response */
export interface SubStatusOption {
  id?: string
  name: string
  display_name: string
  is_default?: boolean
  is_waiting?: boolean
  waiting_for?: string
  category?: string
}

export interface StageDataField {
  id: string
  displayName: string
  category: 'basic' | 'document' | 'financial' | 'admissional'
  required: boolean
  auto_collect: boolean
}

export interface RecruitmentStage {
  id: string
  name: string
  display_name: string
  order: number
  isActive: boolean
  notes: string
  sla: number
  type: 'system' | 'default' | 'custom'
  color?: string
  icon?: string
  action_behavior?: string
  default_channel?: string
  stage_category?: string
  catalog_id?: string
  sub_statuses?: SubStatus[]
  data_fields?: StageDataField[]
}

export interface RecruitmentJourneyConfigProps {
  stages: RecruitmentStage[]
  onChange: (stages: RecruitmentStage[]) => void
  isEditMode?: boolean
  hideHeader?: boolean
  onToggleSubStatus?: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
}
