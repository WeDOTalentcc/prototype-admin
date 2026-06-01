import {
  Target,
  TrendingUp,
  Percent,
  Zap,
  PieChart,
  MoreHorizontal,
  Award,
  type LucideIcon,
} from "lucide-react"

/** Verba variavel (espelha CompensationComponent do backend). */
export interface VariableCompRecord {
  id?: string
  kind: string
  name: string
  description?: string
  icon?: string
  value_type?: string // percent | currency
  target_pct?: number | null
  min_pct?: number | null
  max_pct?: number | null
  min_amount?: number | null
  max_amount?: number | null
  currency?: string | null
  frequency?: string | null
  trigger?: string | null
  spec?: Record<string, unknown> | null
  seniority_levels?: string[]
  contract_types?: string[]
  departments?: Record<string, unknown>
  subsidiaries?: unknown[]
  is_active?: boolean
  is_highlighted?: boolean
  order?: number
  // contexto de vaga (GET /active?with_matches=true)
  matches_vaga?: boolean | null
}

export interface CompKindGroup {
  id: string
  label: string
  icon: LucideIcon
  color: string
  bgColor: string
}

/** Tipos de verba variavel — ordem + visual + rotulo (PT hardcoded, igual compensation-policies). */
export const COMP_KIND_GROUPS: CompKindGroup[] = [
  { id: "bonus", label: "Bônus", icon: Target, color: "text-status-success", bgColor: "bg-status-success/10 dark:bg-status-success/20" },
  { id: "plr", label: "PLR / PPR", icon: TrendingUp, color: "text-wedo-purple", bgColor: "bg-wedo-purple/10 dark:bg-wedo-purple/20" },
  { id: "ppr", label: "PPR", icon: Award, color: "text-wedo-cyan", bgColor: "bg-wedo-cyan/10 dark:bg-wedo-cyan/20" },
  { id: "commission", label: "Comissão", icon: Percent, color: "text-wedo-orange", bgColor: "bg-wedo-orange/10 dark:bg-wedo-orange/20" },
  { id: "spot_bonus", label: "Bônus Pontual", icon: Zap, color: "text-status-warning", bgColor: "bg-status-warning/10 dark:bg-status-warning/20" },
  { id: "equity", label: "Stock Options / Equity", icon: PieChart, color: "text-wedo-magenta", bgColor: "bg-wedo-magenta/10 dark:bg-wedo-magenta/20" },
  { id: "other", label: "Outros", icon: MoreHorizontal, color: "text-lia-text-secondary", bgColor: "bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
]

export const COMP_KIND_OPTIONS = COMP_KIND_GROUPS.filter((g) => g.id !== "plr" || true).map((g) => ({ id: g.id, label: g.label }))

export const FREQUENCY_OPTIONS = [
  { id: "monthly", label: "Mensal" },
  { id: "quarterly", label: "Trimestral" },
  { id: "biannual", label: "Semestral" },
  { id: "annual", label: "Anual" },
  { id: "one_off", label: "Único" },
  { id: "on_target", label: "Ao atingir meta" },
]

export const defaultComponent: VariableCompRecord = {
  kind: "bonus",
  name: "",
  description: "",
  value_type: "percent",
  target_pct: undefined,
  min_pct: undefined,
  max_pct: undefined,
  min_amount: undefined,
  max_amount: undefined,
  currency: "BRL",
  frequency: "annual",
  trigger: undefined,
  spec: {},
  seniority_levels: [],
  contract_types: [],
  departments: {},
  subsidiaries: [],
  is_active: true,
  is_highlighted: false,
  order: 0,
}

export function kindLabel(kind: string): string {
  return COMP_KIND_GROUPS.find((g) => g.id === kind)?.label || kind
}

/** Resumo da faixa/alvo para exibir numa linha (por tipo de valor). */
export function formatCompTarget(c: VariableCompRecord): string {
  if (c.value_type === "currency") {
    const lo = c.min_amount, hi = c.max_amount
    if (lo != null && hi != null) return `R$ ${lo.toLocaleString("pt-BR")} – R$ ${hi.toLocaleString("pt-BR")}`
    if (hi != null) return `até R$ ${hi.toLocaleString("pt-BR")}`
    if (lo != null) return `R$ ${lo.toLocaleString("pt-BR")}`
  } else {
    const lo = c.min_pct, hi = c.max_pct, t = c.target_pct
    if (lo != null && hi != null) return `${lo}% – ${hi}%`
    if (t != null) return `${t}%`
    if (hi != null) return `até ${hi}%`
  }
  if (c.kind === "commission" && c.spec && typeof (c.spec as { base_pct?: number }).base_pct === "number") {
    return `${(c.spec as { base_pct?: number }).base_pct}% base`
  }
  return "—"
}
