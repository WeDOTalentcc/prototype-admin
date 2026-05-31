import type { LucideIcon } from "lucide-react"

export interface SubsidiaryEntry {
  name: string
  cnpj?: string | null
}

/**
 * Schema-alvo: 1:1 com Rails canonical (ats-api-copia/db/migrate/20250715000005_create_benefits.rb).
 * Backend FastAPI espelha em libs/models/lia_models/company_benefit.py + Pydantic
 * em app/api/v1/company_benefits.py (Fase 1, plano Benefits+PRV).
 *
 * 20 campos editaveis pelo usuario (sem id, company_id, created_at, updated_at).
 */
export interface BenefitTabRecord {
  id?: string

  // Identificacao
  name: string
  description: string
  category: string
  icon?: string

  // Valor (3 modos: monetary | percentage | informative)
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string

  // Elegibilidade
  applicable_to: string[]
  seniority_levels: string[]
  contract_types: string[]
  departments: Record<string, unknown> | string[]

  // Regras operacionais
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean

  // Apresentacao
  order: number

  // Provider (PII em provider_contact — backend mascara em logs/JD publicada)
  provider?: string
  provider_contact?: string
  // Novos campos (P2 Benefits Expansion 2026-05-24)
  subsidiaries?: SubsidiaryEntry[]
  valid_from?: string | null       // ISO date "YYYY-MM-DD"
  valid_until?: string | null      // ISO date "YYYY-MM-DD"
  review_frequency_months?: number | null
  next_review_date?: string | null
  provider_cnpj?: string | null
  // Contexto de vaga: flag servidor (GET /company/benefits/active?with_matches=true).
  matches_vaga?: boolean | null
}

export interface BenefitTemplate {
  id: string
  name: string
  description: string
  category: string
  is_popular: boolean
  is_active: boolean
  order: number
}

export interface BenefitCategoryDescriptor {
  id: string
  name: string
  icon: LucideIcon
  color: string
  bgColor: string
}

/**
 * Defaults sensiveis para criacao de novo beneficio.
 * value_type='informative' e o caso mais permissivo (description basta).
 */
export const defaultBenefit: BenefitTabRecord = {
  name: "",
  description: "",
  category: "health",
  icon: undefined,
  value_type: "informative",
  value: undefined,
  percentage_value: undefined,
  value_details: "",
  applicable_to: ["all"],
  seniority_levels: ["all"],
  contract_types: [],
  departments: {},
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  order: 0,
  provider: "",
  provider_contact: "",
  subsidiaries: [],
  valid_from: null,
  valid_until: null,
  review_frequency_months: null,
  next_review_date: null,
  provider_cnpj: null,
}


export interface BenefitHistoryEntry {
  id: string
  changed_at: string
  changed_by: string | null
  change_type: "created" | "updated" | "deactivated" | "reactivated" | string
  previous_snapshot: Record<string, unknown> | null
  change_notes: string | null
}

// ---------------------------------------------------------------------------
// Constantes auxiliares para UI (multi-select chips)
// ---------------------------------------------------------------------------

export const SENIORITY_OPTIONS = [
  { id: "all", label: "Todos" },
  { id: "junior", label: "Junior" },
  { id: "pleno", label: "Pleno" },
  { id: "senior", label: "Senior" },
  { id: "staff", label: "Staff" },
  { id: "principal", label: "Principal" },
  { id: "coordinator", label: "Coordenador" },
  { id: "manager", label: "Gerente" },
  { id: "director", label: "Diretor" },
  { id: "c-level", label: "C-Level" },
] as const

export const APPLICABLE_TO_OPTIONS = [
  { id: "all", label: "Todos os colaboradores" },
  { id: "interns", label: "Estagiarios" },
  { id: "clt", label: "CLT" },
  { id: "pj", label: "PJ" },
  { id: "outsourced", label: "Terceirizados" },
  { id: "trainees", label: "Trainees" },
] as const

export const CONTRACT_TYPE_OPTIONS = [
  { id: "clt", label: "CLT" },
  { id: "pj", label: "PJ" },
  { id: "estagio", label: "Estagio" },
  { id: "temporario", label: "Temporario" },
  { id: "freelancer", label: "Freelancer" },
  { id: "trainee", label: "Trainee" },
] as const
