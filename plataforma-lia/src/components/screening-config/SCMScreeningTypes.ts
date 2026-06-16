export interface ScreeningQuestionItem {
  id: string
  question?: string
  text?: string
  category?: string
  type?: string
  weight?: number
  skill_targeted?: string
  block_id?: number
  required?: boolean
  bloom_level?: number
  bloom_label?: string
  dreyfus_level?: number | string
  dreyfus_label?: string
  big_five_trait?: string
  question_type?: string
  framework?: string
  expected_answer?: string
  expected_signals?: string[]
  scoring_criteria?: Record<string, string>
  scoring_rubric?: Record<string, string>
  trait?: string
  skill?: string
  is_eliminatory?: boolean
  generated?: boolean
  [key: string]: unknown
}
