/**
 * Types para Política de Remuneração Variável (PRV).
 *
 * Schema-alvo: 1:1 com Rails canonical (20250715000009_create_compensation_policies.rb)
 * + updated_by (auditabilidade). Backend: libs/models/lia_models/compensation_policy.py.
 *
 * variable_compensation.items[].kind discriminator:
 *   plr | ppr | bonus | commission | spot_bonus | equity
 */

export interface SalaryBand {
  level: string   // junior | pleno | senior | staff | principal
  min: number
  mid: number
  max: number
  currency: string  // BRL (default)
}

export interface VariableCompItem {
  kind: "plr" | "ppr" | "bonus" | "commission" | "spot_bonus" | "equity"
  name: string
  base?: string          // salary_anual | salary_mensal | revenue | result | custom
  value_pct?: number
  min_pct?: number
  max_pct?: number
  frequency?: string     // monthly | quarterly | annual | biannual | one_off | on_target_achievement
  trigger?: string       // goal_achievement | kpi | discretionary
  trigger_details?: Record<string, unknown>
  applicable_seniority?: string[]
  tiers?: Array<{ from_pct: number; to_pct: number; commission_pct: number }>
}

export interface VariableCompensation {
  items: VariableCompItem[]
}

export interface CompensationPolicyRecord {
  id?: string

  // Identificação
  name: string
  description: string
  policy_type: string    // hierarchical_bands | mixed | variable_only
  currency: string       // BRL

  // Estrutura jsonb
  salary_bands: SalaryBand[]
  bonus_structure: Record<string, unknown>
  equity_rules: Record<string, unknown>
  benefits_package: Record<string, unknown>
  variable_compensation: VariableCompensation

  // Elegibilidade (arrays)
  applicable_departments: string[]
  applicable_seniority: string[]
  applicable_roles: string[]

  // Estado
  is_active: boolean
  is_default: boolean

  // Vigência + Aprovação
  effective_from?: string
  effective_until?: string
  approved_by?: string
  approved_at?: string

  // Versionamento + Audit
  version: number
  revision_history: Array<Record<string, unknown>>
  created_by?: string
  updated_by?: string

  // Timestamps
  created_at?: string
  updated_at?: string
}

export const defaultPolicy: CompensationPolicyRecord = {
  name: "",
  description: "",
  policy_type: "mixed",
  currency: "BRL",
  salary_bands: [
    { level: "junior", min: 4000, mid: 6000, max: 8000, currency: "BRL" },
    { level: "pleno",  min: 7000, mid: 9500, max: 12000, currency: "BRL" },
    { level: "senior", min: 11000, mid: 14000, max: 17000, currency: "BRL" },
  ],
  bonus_structure: {},
  equity_rules: {},
  benefits_package: {},
  variable_compensation: { items: [] },
  applicable_departments: [],
  applicable_seniority: [],
  applicable_roles: [],
  is_active: true,
  is_default: false,
  version: 1,
  revision_history: [],
}

// ---------------------------------------------------------------------------
// Constantes UI
// ---------------------------------------------------------------------------

export const POLICY_TYPE_OPTIONS = [
  { id: "hierarchical_bands", label: "Bandas Salariais" },
  { id: "variable_only",      label: "Variável Puro" },
  { id: "mixed",              label: "Misto (Bandas + Variável)" },
] as const

export const SENIORITY_LEVEL_OPTIONS = [
  { id: "junior",    label: "Junior" },
  { id: "pleno",     label: "Pleno" },
  { id: "senior",    label: "Senior" },
  { id: "staff",     label: "Staff" },
  { id: "principal", label: "Principal" },
  { id: "manager",   label: "Gerente" },
  { id: "director",  label: "Diretor" },
  { id: "c-level",   label: "C-Level" },
] as const

export const VARIABLE_KIND_OPTIONS = [
  { id: "plr",        label: "PLR",        desc: "Participação nos Lucros (Lei 10.101/2000)" },
  { id: "ppr",        label: "PPR",        desc: "Participação nos Resultados" },
  { id: "bonus",      label: "Bônus",      desc: "Bônus por meta / desempenho" },
  { id: "commission", label: "Comissão",   desc: "Comissão sobre vendas / receita" },
  { id: "spot_bonus", label: "Spot Bonus", desc: "Bônus pontual / discricionário" },
  { id: "equity",     label: "Equity",     desc: "Stock options, RSUs, phantom shares" },
] as const

export const FREQUENCY_OPTIONS = [
  { id: "monthly",               label: "Mensal" },
  { id: "quarterly",             label: "Trimestral" },
  { id: "biannual",              label: "Semestral" },
  { id: "annual",                label: "Anual" },
  { id: "one_off",               label: "Pontual" },
  { id: "on_target_achievement", label: "Por atingimento de meta" },
] as const

export const SALARY_LEVEL_ROWS = [
  "junior", "pleno", "senior", "staff", "principal",
] as const
