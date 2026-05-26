/**
 * useCompanyBlocks.ts — pure transform layer (Sprint 2.2, Sessão E 2026-05-26)
 *
 * Extraído de use-company-settings-cards.ts. Responsabilidade única:
 * receber dados da empresa e derivar o array de CardBlock[] que alimenta
 * o MinhaEmpresaHub. Sem side-effects, sem fetch, sem state — testável
 * em isolamento com vitest puro.
 *
 * Consumidores: use-company-settings-cards.ts (thin wrapper),
 *               useCompanyData (futuro migrate Sprint 2.3).
 */

import type { CompanyData } from "@/hooks/settings/department-types"
import type { CompanyBenefit } from "@/types/benefits"
import { useMemo } from "react"

// ─── Exported types ─────────────────────────────────────────────────────────

export interface BlockProgress {
  filled: number
  total: number
  missingLabels: string[]
}

export interface CardBlock {
  key: string
  title: string
  subtitle?: string
  iconName: string
  fields: CardField[]
  status: "configured" | "partial" | "pending"
  progress: BlockProgress
}

export interface CardField {
  key: string
  label: string
  value: unknown
  type: "text" | "number" | "boolean" | "list" | "currency" | "time-range"
  editable: boolean
  block: string
}

export type BenefitItem = Partial<CompanyBenefit> & {
  id?: string
  name?: string
  category?: string
  is_active?: boolean
}

export interface HiringPolicyData {
  pipeline_rules?: PipelineRules
  scheduling_rules?: SchedulingRules
  communication_rules?: CommunicationRules
  screening_rules?: ScreeningRules
  automation_rules?: AutomationRules
  setup_progress?: number
  [key: string]: unknown
}

interface PipelineRules {
  min_interviews_before_offer?: number
  manager_approval_for_offer?: boolean
  max_days_in_stage?: Record<string, number>
}

interface SchedulingRules {
  allowed_days?: string[]
  allowed_hours?: { start?: string; end?: string }
  default_duration_minutes?: number
  self_scheduling_enabled?: boolean
}

interface CommunicationRules {
  auto_rejection_feedback?: boolean
  rejection_feedback_deadline_hours?: number
  preferred_channel?: string
  lia_tone?: string
}

interface AutomationRules {
  auto_screening?: boolean
  auto_scheduling?: boolean
  auto_stage_advance?: boolean
  autonomy_level?: string
}

interface ScreeningRules {
  salary_expectation_filter?: boolean
  salary_tolerance_percent?: number
  experience_policy?: string
  default_screening_questions?: string[]
}

// ─── Internal constants ──────────────────────────────────────────────────────

/** Fields that are UI actions (buttons), not data — excluded from progress. */
export const ACTION_FIELD_KEYS = new Set(["import_spreadsheet", "handbook", "org_chart"])

/** Maps each hiring-policy leaf field to its sub-block key. */
export const POLICY_FIELD_TO_BLOCK: Record<string, string> = {
  min_interviews_before_offer: "pipeline_rules",
  manager_approval_for_offer: "pipeline_rules",
  allowed_days: "scheduling_rules",
  allowed_hours: "scheduling_rules",
  default_duration_minutes: "scheduling_rules",
  self_scheduling_enabled: "scheduling_rules",
  auto_rejection_feedback: "communication_rules",
  rejection_feedback_deadline_hours: "communication_rules",
  preferred_channel: "communication_rules",
  lia_tone: "communication_rules",
  salary_expectation_filter: "screening_rules",
  salary_tolerance_percent: "screening_rules",
  experience_policy: "screening_rules",
  auto_screening: "automation_rules",
  auto_scheduling: "automation_rules",
  auto_stage_advance: "automation_rules",
  autonomy_level: "automation_rules",
}

// ─── Pure helper functions ───────────────────────────────────────────────────

export function isFieldFilled(f: CardField): boolean {
  if (f.value === null || f.value === undefined || f.value === "") return false
  if (Array.isArray(f.value) && f.value.length === 0) return false
  return true
}

export function computeBlockStatus(fields: CardField[]): "configured" | "partial" | "pending" {
  const dataFields = fields.filter(f => !ACTION_FIELD_KEYS.has(f.key))
  if (dataFields.length === 0) return "pending"
  const filled = dataFields.filter(isFieldFilled).length
  if (filled === 0) return "pending"
  if (filled === dataFields.length) return "configured"
  return "partial"
}

export function computeBlockProgress(fields: CardField[]): BlockProgress {
  const dataFields = fields.filter(f => !ACTION_FIELD_KEYS.has(f.key))
  const filled = dataFields.filter(isFieldFilled).length
  const missingLabels = dataFields.filter(f => !isFieldFilled(f)).map(f => f.label)
  return { filled, total: dataFields.length, missingLabels }
}

/** Pure transform: company + benefits + policy → CardBlock[]. No side-effects. */
export function buildBlocks(
  company: CompanyData | null,
  benefits: BenefitItem[],
  hiringPolicy: HiringPolicyData | null,
): CardBlock[] {
  if (!company) return []

  const basicFields: CardField[] = [
    { key: "name", label: "Nome da Empresa", value: company.name, type: "text", editable: true, block: "basic" },
    { key: "tradeName", label: "Nome Fantasia", value: company.tradeName, type: "text", editable: true, block: "basic" },
    { key: "logo", label: "Logo (URL)", value: company.logo || null, type: "text", editable: true, block: "basic" },
    { key: "cnpj", label: "CNPJ", value: company.cnpj, type: "text", editable: true, block: "basic" },
    { key: "website", label: "Website", value: company.website, type: "text", editable: true, block: "basic" },
    { key: "industry", label: "Setor", value: company.industry, type: "text", editable: true, block: "basic" },
    { key: "size", label: "Porte", value: company.company_size || company.size, type: "text", editable: true, block: "basic" },
    { key: "employee_count", label: "Funcionarios", value: company.employee_count, type: "number", editable: true, block: "basic" },
    { key: "headquarters", label: "Sede", value: company.headquarters, type: "text", editable: true, block: "basic" },
    { key: "founded_year", label: "Ano de Fundacao", value: company.founded_year, type: "number", editable: true, block: "basic" },
    { key: "linkedin_url", label: "LinkedIn", value: company.linkedin_url, type: "text", editable: true, block: "basic" },
    { key: "email", label: "Email RH", value: company.email, type: "text", editable: true, block: "basic" },
    { key: "phone", label: "Telefone", value: company.phone, type: "text", editable: true, block: "basic" },
  ]

  const cultureFields: CardField[] = [
    { key: "mission", label: "Missao", value: company.mission, type: "text", editable: true, block: "culture" },
    { key: "vision", label: "Visao", value: company.vision, type: "text", editable: true, block: "culture" },
    { key: "values", label: "Valores", value: company.values, type: "list", editable: true, block: "culture" },
    { key: "work_model", label: "Modelo de Trabalho", value: company.work_model, type: "text", editable: true, block: "culture" },
    { key: "dei_initiatives", label: "DEI", value: company.dei_initiatives, type: "text", editable: true, block: "culture" },
    { key: "sustainability", label: "Sustentabilidade", value: company.sustainability, type: "text", editable: true, block: "culture" },
    { key: "social_impact", label: "Impacto Social", value: company.social_impact, type: "text", editable: true, block: "culture" },
    { key: "leadership_style", label: "Estilo de Lideranca", value: company.leadership_style, type: "text", editable: true, block: "culture" },
    { key: "growth_opportunities", label: "Oportunidades de Crescimento", value: company.growth_opportunities, type: "text", editable: true, block: "culture" },
    { key: "team_dynamics", label: "Dinamica de Equipe", value: company.team_dynamics, type: "text", editable: true, block: "culture" },
    { key: "evp_bullets", label: "EVP", value: company.evp_bullets, type: "list", editable: true, block: "culture" },
  ]

  const techFields: CardField[] = [
    { key: "tech_stack", label: "Stack Tecnologico", value: company.tech_stack, type: "list", editable: true, block: "tech" },
    { key: "engineering_culture", label: "Cultura de Engenharia", value: company.engineering_culture, type: "text", editable: true, block: "tech" },
    { key: "default_languages", label: "Idiomas", value: company.default_languages, type: "list", editable: true, block: "tech" },
  ]

  const activeBenefits = benefits.filter((b) => b.is_active !== false)
  const benefitNames = benefits.slice(0, 5).map((b) => b.name).filter(Boolean)
  const benefitsSubtitle =
    benefits.length === 0
      ? "Nenhum benefício cadastrado"
      : `${benefits.length} cadastrado${benefits.length === 1 ? "" : "s"} · ${activeBenefits.length} ativo${activeBenefits.length === 1 ? "" : "s"}`
  const benefitsFields: CardField[] = [
    { key: "benefits_count", label: "Total de Beneficios", value: benefits.length > 0 ? `${benefits.length} cadastrado(s)` : null, type: "text", editable: false, block: "benefits" },
    { key: "benefits_active", label: "Beneficios Ativos", value: activeBenefits.length || null, type: "number", editable: false, block: "benefits" },
    { key: "benefits_list", label: "Pacote", value: benefitNames.length > 0 ? benefitNames : null, type: "list", editable: false, block: "benefits" },
  ]

  const pr = hiringPolicy?.pipeline_rules
  const sr = hiringPolicy?.scheduling_rules
  const cr = hiringPolicy?.communication_rules
  const scr = hiringPolicy?.screening_rules
  const ar = hiringPolicy?.automation_rules
  const hours = sr?.allowed_hours as { start?: string; end?: string } | undefined

  const policyFields: CardField[] = [
    { key: "min_interviews_before_offer", label: "Min. Entrevistas p/ Oferta", value: pr?.min_interviews_before_offer ?? null, type: "number", editable: true, block: "policy" },
    { key: "manager_approval_for_offer", label: "Aprovacao Gestor", value: pr?.manager_approval_for_offer ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "max_days_in_stage", label: "Max. Dias por Etapa", value: pr?.max_days_in_stage ?? null, type: "text", editable: false, block: "policy" },
    { key: "allowed_days", label: "Dias Permitidos", value: sr?.allowed_days ?? null, type: "list", editable: true, block: "policy" },
    { key: "allowed_hours", label: "Horario Permitido", value: hours ? `${hours.start || ""} - ${hours.end || ""}` : null, type: "time-range", editable: true, block: "policy" },
    { key: "default_duration_minutes", label: "Duracao Padrao (min)", value: sr?.default_duration_minutes ?? null, type: "number", editable: true, block: "policy" },
    { key: "self_scheduling_enabled", label: "Auto-agendamento", value: sr?.self_scheduling_enabled ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "auto_rejection_feedback", label: "Feedback Auto Rejeicao", value: cr?.auto_rejection_feedback ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "rejection_feedback_deadline_hours", label: "Prazo Feedback Rejeicao (h)", value: cr?.rejection_feedback_deadline_hours ?? null, type: "number", editable: true, block: "policy" },
    { key: "preferred_channel", label: "Canal Preferido", value: cr?.preferred_channel ?? null, type: "text", editable: true, block: "policy" },
    { key: "salary_expectation_filter", label: "Filtro Pretensao Salarial", value: scr?.salary_expectation_filter ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "salary_tolerance_percent", label: "Tolerancia Salarial (%)", value: scr?.salary_tolerance_percent ?? null, type: "number", editable: true, block: "policy" },
    { key: "experience_policy", label: "Politica de Experiencia", value: scr?.experience_policy ?? null, type: "text", editable: true, block: "policy" },
    { key: "auto_screening", label: "Triagem Automatica", value: ar?.auto_screening ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "auto_scheduling", label: "Agendamento Automatico (Em breve)", value: ar?.auto_scheduling ?? null, type: "boolean", editable: false, block: "policy" },
    { key: "auto_stage_advance", label: "Avanco Automatico Etapas", value: ar?.auto_stage_advance ?? null, type: "boolean", editable: true, block: "policy" },
    { key: "autonomy_level", label: "Nivel de Autonomia LIA", value: ar?.autonomy_level ?? null, type: "text", editable: true, block: "policy" },
    { key: "setup_progress", label: "Progresso Configuracao", value: hiringPolicy?.setup_progress ? `${hiringPolicy.setup_progress}%` : null, type: "text", editable: false, block: "policy" },
  ]

  const additionalData = company.additional_data
  const workforcePlan = (additionalData as Record<string, unknown> | undefined)?.workforce_plan as Record<string, unknown> | undefined
  const workforceFields: CardField[] = [
    { key: "hiring_volume", label: "Volume de Contratacao", value: additionalData?.hiring_volume ?? workforcePlan?.hiring_volume, type: "number", editable: true, block: "workforce" },
    { key: "job_types", label: "Tipos de Vaga", value: additionalData?.job_types ?? workforcePlan?.job_types, type: "list", editable: true, block: "workforce" },
    { key: "current_ats", label: "ATS Atual", value: additionalData?.current_ats ?? workforcePlan?.current_ats, type: "text", editable: true, block: "workforce" },
    { key: "main_challenges", label: "Principais Desafios", value: additionalData?.main_challenges ?? workforcePlan?.main_challenges, type: "list", editable: true, block: "workforce" },
    { key: "main_priority", label: "Prioridade Principal", value: additionalData?.main_priority ?? workforcePlan?.main_priority, type: "text", editable: true, block: "workforce" },
    { key: "communication_channels", label: "Canais de Comunicacao", value: additionalData?.communication_channels ?? workforcePlan?.communication_channels, type: "list", editable: true, block: "workforce" },
    { key: "import_spreadsheet", label: "Importar Planilha", value: null, type: "text", editable: false, block: "workforce" },
  ]

  const documentFields: CardField[] = [
    { key: "onboarding_completed", label: "Onboarding Concluido", value: additionalData?.onboarding_completed_at ? "Sim" : null, type: "text", editable: false, block: "documents" },
    { key: "responsible_name", label: "Responsavel", value: additionalData?.responsible_name, type: "text", editable: true, block: "documents" },
    { key: "responsible_position", label: "Cargo do Responsavel", value: additionalData?.responsible_position, type: "text", editable: true, block: "documents" },
    { key: "additional_notes", label: "Notas Adicionais", value: additionalData?.additional_notes, type: "text", editable: true, block: "documents" },
    { key: "compensation_structure", label: "Políticas de PRV", value: company.default_salary_ranges && company.default_salary_ranges.length > 0 ? `${company.default_salary_ranges.length} faixa(s)` : null, type: "text", editable: false, block: "documents" },
    { key: "handbook", label: "Manual do Colaborador", value: null, type: "text", editable: false, block: "documents" },
    { key: "org_chart", label: "Organograma", value: null, type: "text", editable: false, block: "documents" },
  ]

  return [
    { key: "basic", title: "Perfil da Empresa", iconName: "Building2", fields: basicFields, status: computeBlockStatus(basicFields), progress: computeBlockProgress(basicFields) },
    { key: "culture", title: "Cultura & Valores", iconName: "Heart", fields: cultureFields, status: computeBlockStatus(cultureFields), progress: computeBlockProgress(cultureFields) },
    { key: "tech", title: "Stack Tecnológico", iconName: "Code2", fields: techFields, status: computeBlockStatus(techFields), progress: computeBlockProgress(techFields) },
    { key: "benefits", title: "Benefícios", subtitle: benefitsSubtitle, iconName: "Gift", fields: benefitsFields, status: computeBlockStatus(benefitsFields), progress: computeBlockProgress(benefitsFields) },
    { key: "policy", title: "Políticas de Recrutamento", iconName: "FileText", fields: policyFields, status: computeBlockStatus(policyFields), progress: computeBlockProgress(policyFields) },
    { key: "workforce", title: "Workforce Planning", iconName: "Users", fields: workforceFields, status: computeBlockStatus(workforceFields), progress: computeBlockProgress(workforceFields) },
    { key: "documents", title: "Remuneração Variável", iconName: "TrendingUp", fields: documentFields, status: computeBlockStatus(documentFields), progress: computeBlockProgress(documentFields) },
  ]
}

/** Creates a snapshot of field values for change detection. */
export function snapshotFieldValues(blocks: CardBlock[]): Map<string, string> {
  const snap = new Map<string, string>()
  for (const block of blocks) {
    for (const field of block.fields) {
      snap.set(field.key, JSON.stringify(field.value))
    }
  }
  return snap
}

// ─── React hook wrapper ──────────────────────────────────────────────────────

/**
 * Thin React hook wrapping buildBlocks with useMemo.
 * Stable identity: only recomputes when inputs change.
 */
export function useCompanyBlocks(
  company: CompanyData | null,
  benefits: BenefitItem[],
  hiringPolicy: HiringPolicyData | null,
): CardBlock[] {
  return useMemo(
    () => buildBlocks(company, benefits, hiringPolicy),
    [company, benefits, hiringPolicy],
  )
}

// ─── Profile + Culture merge helper ─────────────────────────────────────────

/**
 * Merges raw API responses (profile + culture) into a typed CompanyData object.
 * Pure function — no side effects, fully testable.
 */
export function mergeToCompanyData(
  rawProfile: Record<string, unknown> | null,
  rawCulture: Record<string, unknown> | null,
): CompanyData | null {
  if (!rawProfile) return null
  return {
    name: (rawProfile.name as string) || "",
    tradeName: (rawProfile.trading_name as string) || (rawProfile.name as string) || "",
    cnpj: (rawProfile.cnpj as string) || "",
    website: (rawProfile.website as string) || "",
    email: (rawProfile.hr_email as string) || (rawProfile.main_email as string) || "",
    phone: (rawProfile.hr_phone as string) || (rawProfile.main_phone as string) || "",
    address: (rawProfile.address as string) || "",
    logo: (rawProfile.logo_url as string) || undefined,
    industry: (rawProfile.industry as string) || "",
    size: (rawProfile.size as string) || "",
    employee_count: rawProfile.employee_count as number | undefined,
    company_size: (rawProfile.company_size as string) || "",
    headquarters: rawProfile.headquarters_city
      ? `${rawProfile.headquarters_city}${rawProfile.headquarters_state ? `, ${rawProfile.headquarters_state}` : ""}`
      : (rawCulture?.headquarters as string) || "",
    founded_year: rawProfile.founded_year as number | undefined,
    linkedin_url: (rawProfile.linkedin_url as string) || "",
    mission: (rawCulture?.mission as string) || "",
    vision: (rawCulture?.vision as string) || "",
    values: (rawCulture?.values as string[]) || [],
    coreCompetencies: (rawCulture?.core_competencies as string[]) || [],
    evp_bullets: (rawCulture?.evp_bullets as string[]) || [],
    work_model: (rawCulture?.work_model as string) || "",
    dei_initiatives: (rawCulture?.dei_initiatives as string) || "",
    sustainability: (rawCulture?.sustainability as string) || "",
    social_impact: (rawCulture?.social_impact as string) || "",
    leadership_style: (rawCulture?.leadership_style as string) || "",
    growth_opportunities: (rawCulture?.growth_opportunities as string) || "",
    team_dynamics: (rawCulture?.team_dynamics as string) || "",
    tech_stack: (rawCulture?.tech_stack as string[]) || [],
    engineering_culture: (rawCulture?.engineering_culture as string) || "",
    default_languages: (rawCulture?.default_languages as string[]) || [],
    additional_data: (rawCulture?.additional_data as Record<string, unknown>) || (rawProfile?.additional_data as Record<string, unknown>) || undefined,
    default_salary_ranges: (rawProfile?.default_salary_ranges as unknown[]) || [],
  }
}
