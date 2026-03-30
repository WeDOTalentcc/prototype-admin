// Auto-extracted types from setup-empresa/page.tsx

export interface Benefit {
  id?: string
  name: string
  description: string
  category: string
  icon?: string
  value?: number
  value_type: string
  value_details?: string
  percentage_value?: number
  applicable_to: string[]
  seniority_levels: string[]
  contract_types: string[]
  departments: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
  order: number
}

export interface CompanyProfile {
  id?: string
  name: string
  trading_name?: string
  website?: string
  cnpj?: string
  industry?: string
  sector?: string
  company_size?: string
  description?: string
  headquarters_city?: string
  headquarters_state?: string
  linkedin_url?: string
  mission?: string
  vision?: string
  values?: string
  tagline?: string
  additional_data?: Record<string, unknown>
}

export interface EnrichmentResult {
  success: boolean
  linkedin_data: Record<string, unknown>
  glassdoor_data: Record<string, unknown>
  enriched_culture: Record<string, unknown>
  errors: string[]
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

export interface EVPPillar {
  name: string
  description: string
  evidence: string
}

export interface EVPAnalysis {
  statement: string
  pillars: EVPPillar[]
  tone_guidance: string[]
  candidate_promise: string
  generated_at: string
  sources: string[]
}

export interface BenefitsContentProps {
  isLoading: boolean
  benefits: Benefit[]
  expandedCategories: string[]
  showImportModal: boolean
  setShowImportModal: (show: boolean) => void
  setShowTemplateModal: (show: boolean) => void
  setEditingBenefit: (benefit: Benefit | null) => void
  setShowBenefitModal: (show: boolean) => void
  toggleCategory: (categoryId: string) => void
  handleToggleBenefitStatus: (benefit: Benefit) => void
  handleDeleteBenefit: (id: string) => void
  defaultBenefit: Benefit
}
