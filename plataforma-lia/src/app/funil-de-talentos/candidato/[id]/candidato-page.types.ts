// candidato-page.types.ts
// All TypeScript types and interfaces for the candidato page

export type ActiveTab = 'profile' | 'activities' | 'files' | 'opinions'
export type ActivityCategory = 'all' | 'interview' | 'screening' | 'general'
export type ActivityFilter = 'all' | 'emails' | 'interviews' | 'lia' | 'applications' | 'tests' | 'offers' | 'notes'
export type NoteCategory = 'general' | 'interview' | 'screening' | 'feedback' | 'technical'
export type PeriodFilter = '7days' | '30days' | '3months' | 'all'
export type ActivityView = 'list' | 'timeline'
export type OpinionsSubTab = 'pareceres' | 'analises'

export interface OpinionData {
  current_general_opinion?: Record<string, unknown>
  vacancy_opinions?: Array<Record<string, unknown>>
}

export interface ActivityItem extends Record<string, unknown> {
  id: string
  type?: string
  activity_type?: string
  itemType?: string
  created_at?: string
  timestamp?: string
  content?: string
  description?: string
  details?: string
  title?: string
  user_name?: string
  source?: string
  category?: string
}

export interface CandidatoFileItem extends Record<string, unknown> {
  id: string
  file_name: string
  file_url: string
  file_type?: string
  file_size?: number
  mime_type?: string
  created_at?: string
}

export interface FileCategoryItem extends Record<string, unknown> {
  category: string
  label: string
  icon: string
  count: number
}
