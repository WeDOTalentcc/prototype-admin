// Auto-extracted constants from setup-empresa/page.tsx
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import {
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Stethoscope,
  Shield,
  DollarSign,
  Percent,
  Info,
} from "lucide-react"
import type { Benefit } from "./setup-empresa.types"

export const BENEFIT_CATEGORIES = [
  { id: "health", name: "Saúde & Bem-estar", icon: Stethoscope, color: "text-status-error" },
  { id: "food", name: "Alimentação", icon: Utensils, color: "text-wedo-orange" },
  { id: "transport", name: "Transporte", icon: Car, color: "text-lia-text-secondary dark:text-lia-text-tertiary" },
  { id: "education", name: "Educação & Desenvolvimento", icon: GraduationCap, color: "text-wedo-purple" },
  { id: "financial", name: "Financeiro", icon: Wallet, color: "text-status-success" },
  { id: "quality_life", name: "Qualidade de Vida", icon: Home, color: "text-lia-text-primary dark:text-lia-text-secondary" },
  { id: "family", name: "Família", icon: Baby, color: "text-wedo-magenta" },
  { id: "security", name: "Segurança", icon: Shield, color: "text-lia-text-secondary" },
]

export const SENIORITY_LEVELS = [
  { id: "all", name: "Todos os Níveis" },
  { id: "junior", name: "Júnior" },
  { id: "pleno", name: "Pleno" },
  { id: "senior", name: "Sênior" },
  { id: "coordinator", name: "Coordenação+" },
  { id: "manager", name: "Gerência+" },
  { id: "director", name: "Diretoria" },
  { id: "c-level", name: "C-Level" },
]

export const VALUE_TYPES = [
  { id: "monetary", name: "Valor Monetário", icon: DollarSign, description: `Valor fixo em ${CURRENCY_SYMBOL}` },
  { id: "percentage", name: "Percentual", icon: Percent, description: "Porcentagem (ex: 5% contribuição)" },
  { id: "informative", name: "Informativo", icon: Info, description: "Apenas descrição, sem valor" },
]

export const WAITING_PERIODS = [
  { id: 0, name: "Imediato" },
  { id: 30, name: "30 dias" },
  { id: 60, name: "60 dias" },
  { id: 90, name: "90 dias" },
  { id: 180, name: "6 meses" },
  { id: 365, name: "1 ano" },
]

export const defaultBenefit: Benefit = {
  name: "",
  description: "",
  category: "health",
  value_type: "monetary",
  value: undefined,
  percentage_value: undefined,
  value_details: "",
  applicable_to: [],
  seniority_levels: ["all"],
  contract_types: [],
  departments: [],
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  provider: "",
  order: 0,
}
