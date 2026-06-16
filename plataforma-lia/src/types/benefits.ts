export type BenefitCategory =
  | 'health'
  | 'food'
  | 'transport'
  | 'education'
  | 'wellness'
  | 'financial'
  | 'quality_life'
  | 'family'
  | 'flexibility'
  | 'security'
  | 'other'

export type BenefitValueType = 'monetary' | 'percentage' | 'informative'

export interface CompanyBenefit {
  id?: string
  name: string
  description: string
  category: BenefitCategory
  value_type: BenefitValueType
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

export interface JobBenefit extends CompanyBenefit {
  enabled: boolean
}

export function toCompanyBenefit(input: string | { name: string; category?: string; [key: string]: unknown }): CompanyBenefit {
  if (typeof input === 'string') {
    return {
      name: input,
      description: '',
      category: 'quality_life',
      value_type: 'informative',
      seniority_levels: ['all'],
      waiting_period_days: 0,
      is_mandatory: false,
      is_active: true,
      is_highlighted: false,
      is_discount: false,
    }
  }
  return {
    name: input.name,
    description: (input.description as string) || '',
    category: (input.category as BenefitCategory) || 'quality_life',
    value_type: (input.value_type as BenefitValueType) || 'informative',
    value: input.value as number | undefined,
    percentage_value: input.percentage_value as number | undefined,
    value_details: input.value_details as string | undefined,
    seniority_levels: (input.seniority_levels as string[]) || ['all'],
    waiting_period_days: (input.waiting_period_days as number) || 0,
    is_mandatory: (input.is_mandatory as boolean) || false,
    is_active: input.is_active !== undefined ? (input.is_active as boolean) : true,
    is_highlighted: (input.is_highlighted as boolean) || false,
    is_discount: (input.is_discount as boolean) || false,
    provider: input.provider as string | undefined,
    id: input.id as string | undefined,
  }
}

export function toJobBenefit(benefit: CompanyBenefit, enabled: boolean = false): JobBenefit {
  return { ...benefit, enabled }
}

export const BENEFIT_CATEGORY_META: Record<BenefitCategory, { name: string; icon: string }> = {
  health: { name: 'Saúde & Bem-estar', icon: 'Stethoscope' },
  food: { name: 'Alimentação', icon: 'Utensils' },
  transport: { name: 'Transporte', icon: 'Car' },
  education: { name: 'Educação & Desenvolvimento', icon: 'GraduationCap' },
  wellness: { name: 'Bem-estar', icon: 'HeartPulse' },
  financial: { name: 'Financeiro', icon: 'Wallet' },
  quality_life: { name: 'Qualidade de Vida', icon: 'Home' },
  family: { name: 'Família', icon: 'Baby' },
  flexibility: { name: 'Flexibilidade', icon: 'Clock' },
  security: { name: 'Segurança', icon: 'Shield' },
  other: { name: 'Outros', icon: 'Gift' },
}
