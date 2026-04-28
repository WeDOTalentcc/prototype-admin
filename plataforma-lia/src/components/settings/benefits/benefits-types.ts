import type { LucideIcon } from "lucide-react"

export interface BenefitTabRecord {
  id?: string
  name: string
  description: string
  category: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
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

export const defaultBenefit: BenefitTabRecord = {
  name: "",
  description: "",
  category: "health",
  value_type: "monetary",
  value: undefined,
  percentage_value: undefined,
  value_details: "",
  seniority_levels: ["all"],
  waiting_period_days: 0,
  is_mandatory: false,
  is_active: true,
  is_highlighted: false,
  is_discount: false,
  provider: "",
}
