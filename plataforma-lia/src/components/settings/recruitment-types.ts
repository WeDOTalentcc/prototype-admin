import type {
  RecruitmentStage,
  SubStatus,
} from "@/components/settings/RecruitmentJourneyConfig"

export interface RawPipelineStage {
  id: string
  name: string
  display_name: string
  stage_order?: number
  is_active?: boolean
  description?: string
  sla_hours?: number
  stage_category?: string
  color?: string
  icon?: string
  action_behavior?: string
  default_channel?: string
  sub_statuses?: unknown[]
  catalog_id?: string
}

export interface RawScreeningQuestion {
  id: string
  question_text?: string
  question?: string
  question_type?: string
  is_required?: boolean
  order?: number
  is_default?: boolean
  options?: string[]
  is_eliminatory?: boolean
  expected_answer?: string
  category?: string
}

export interface ScreeningQuestion {
  id: string
  question: string
  type: 'text' | 'yes_no' | 'scale' | 'multiple'
  required: boolean
  order: number
  isDefault: boolean
  options?: string[]
  is_eliminatory?: boolean
  expected_answer?: string
  /** P0-W1-09: categoria canonical do backend */
  category?: string
}

export interface NewQuestionForm {
  question: string
  type: 'text' | 'yes_no' | 'scale' | 'multiple'
  required: boolean
  is_eliminatory: boolean
  expected_answer: string
}

export function mapRawPipelineStage(
  s: RawPipelineStage,
  idx: number
): RecruitmentStage {
  return {
    id: s.id,
    name: s.name,
    display_name: s.display_name,
    order: s.stage_order || idx + 1,
    isActive: s.is_active ?? true,
    notes: s.description || "",
    sla: s.sla_hours ? Math.round(s.sla_hours / 24) : 0,
    type:
      s.stage_category === 'system'
        ? 'system'
        : s.stage_category === 'catalog'
        ? 'default'
        : 'custom',
    color: s.color,
    icon: s.icon,
    action_behavior: s.action_behavior,
    default_channel: s.default_channel || 'email',
    stage_category: s.stage_category,
    sub_statuses: (s.sub_statuses || []) as SubStatus[],
  }
}

export function mapRawScreeningQuestion(
  q: RawScreeningQuestion
): ScreeningQuestion {
  const rawType = q.question_type || 'text'
  const safeType: ScreeningQuestion['type'] =
    rawType === 'text' || rawType === 'yes_no' || rawType === 'scale' || rawType === 'multiple'
      ? rawType
      : 'text'
  return {
    id: q.id,
    question: q.question_text || q.question || '',
    type: safeType,
    required: q.is_required ?? true,
    order: q.order || 0,
    isDefault: q.is_default ?? false,
    options: q.options || [],
    is_eliminatory: q.is_eliminatory ?? false,
    expected_answer: q.expected_answer || undefined,
    category: q.category || undefined,
  }
}
