"use client"

// Types for Offer Proposals (PR-B)

export interface OfferBonusVariable {
  type: "commission" | "profit_sharing" | "project_bonus" | "other"
  value: number
  frequency: "monthly" | "quarterly" | "annual" | "one_time"
  conditions?: string
}

export interface OfferBenefit {
  name: string
  value?: string
  category?: string
}

export interface JobDataSnapshot {
  title?: string
  manager?: string
  manager_email?: string
  department?: string
  salary_range?: { min?: number; max?: number; currency?: string }
  benefits?: (string | OfferBenefit)[]
  contract_type?: string
  work_model?: string
  company_name?: string
}

export interface CandidateDataSnapshot {
  name?: string
  email?: string
  phone?: string
  current_title?: string
  current_company?: string
  desired_salary_min?: number
  desired_salary_max?: number
  current_salary?: number
}

export type OfferStatus = "draft" | "sent" | "accepted" | "declined" | "expired" | "cancelled"
export type OfferSendMode = "auto" | "manual"

export interface OfferDraft {
  id: string
  company_id: string
  candidate_id: string
  job_id: string
  template_id?: string

  // Snapshots
  job_data_snapshot: JobDataSnapshot
  candidate_data_snapshot: CandidateDataSnapshot

  // Offer fields
  offered_salary?: number
  offered_salary_currency: string
  offered_bonus_admission?: number
  offered_bonus_variable?: OfferBonusVariable
  offered_benefits?: OfferBenefit[]
  offered_start_date?: string   // ISO date "YYYY-MM-DD"
  validity_days: number
  expires_at?: string

  // Notes
  recruiter_notes?: string

  // State
  status: OfferStatus
  send_mode?: OfferSendMode
  email_log_id?: string

  // Audit
  created_by_user_id: string
  sent_by_user_id?: string
  sent_at?: string
  created_at: string
  updated_at: string
}

export interface OfferDraftCreate {
  candidate_id: string
  job_id: string
  template_id?: string
}

export interface OfferDraftUpdate {
  offered_salary?: number
  offered_salary_currency?: string
  offered_bonus_admission?: number
  offered_bonus_variable?: OfferBonusVariable
  offered_benefits?: OfferBenefit[]
  offered_start_date?: string
  validity_days?: number
  recruiter_notes?: string
  template_id?: string
}

export interface SalaryWarning {
  level: "warning" | "info"
  message: string
}
