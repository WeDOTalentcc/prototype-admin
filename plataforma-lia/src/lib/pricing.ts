export type PlanTier = 'starter' | 'pro' | 'enterprise'
export type ModuleTier = 'starter' | 'professional' | 'enterprise'

export interface PriceValue {
  amount: number
  currency: string
  formatted: string
  period?: string
}

export interface PlanDefinition {
  id: PlanTier
  name: string
  price: PriceValue | null
  features: string[]
  cta: string
  highlighted: boolean
}

export interface ModuleTierDefinition {
  id: ModuleTier
  name: string
  label: string
  price: PriceValue
  recommended?: boolean
  features: { name: string; included: boolean }[]
}

export interface ModulePriceEntry {
  id: string
  name: string
  description: string
  price: PriceValue
  features: string[]
  category: string
}

function brl(amount: number, period?: string): PriceValue {
  const formatted = amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 })
  return {
    amount,
    currency: 'BRL',
    formatted: period ? `${formatted}/${period}` : formatted,
    period,
  }
}

export const CURRENCY_SYMBOL = 'R$'
export const CURRENCY_PLACEHOLDER = 'R$ 0,00'

export function formatBRL(amount: number): string {
  return amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

export function formatBRLDecimal(amount: number): string {
  return amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function formatBRLCompact(amount: number): string {
  if (amount >= 1_000_000) return `R$ ${(amount / 1_000_000).toFixed(1)}M`
  if (amount >= 1_000) return `R$ ${(amount / 1_000).toFixed(0)}k`
  return formatBRL(amount)
}

export function formatSalaryRange(min: number, max: number): string {
  return `${formatBRL(min)} - ${formatBRL(max)}`
}

export function formatCurrencyLabel(label: string): string {
  return `${label} (${CURRENCY_SYMBOL})`
}

export const PLAN_PRICES: Record<PlanTier, PriceValue | null> = {
  starter: brl(990, 'mês'),
  pro: brl(2490, 'mês'),
  enterprise: null,
}

export const PLANS: PlanDefinition[] = [
  {
    id: 'starter',
    name: 'Starter',
    price: PLAN_PRICES.starter,
    features: [
      '5 vagas ativas simultâneas',
      'Até 3 recrutadores',
      '500 candidatos/mês',
      'Triagem WSI básica',
      'Suporte por email',
    ],
    cta: 'Assinar Starter',
    highlighted: false,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: PLAN_PRICES.pro,
    features: [
      '20 vagas ativas simultâneas',
      'Até 10 recrutadores',
      '5.000 candidatos/mês',
      'Triagem WSI completa + Big Five',
      'Integrações ATS (Gupy, Pandapé)',
      'Suporte prioritário',
    ],
    cta: 'Assinar Pro',
    highlighted: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: PLAN_PRICES.enterprise,
    features: [
      'Vagas e recrutadores ilimitados',
      'White-label / RPO',
      'BYOK (Bring Your Own Key)',
      'SLA garantido',
      'Gerente de conta dedicado',
      'Compliance BCB 498 / SOX',
    ],
    cta: 'Falar com vendas',
    highlighted: false,
  },
]

export const MODULE_TIER_PRICES: Record<ModuleTier, PriceValue> = {
  starter: brl(99, 'mês'),
  professional: brl(299, 'mês'),
  enterprise: brl(699, 'mês'),
}

export const MODULE_TIERS: ModuleTierDefinition[] = [
  {
    id: 'starter',
    name: 'Starter',
    label: 'Funcionalidades básicas',
    price: MODULE_TIER_PRICES.starter,
    features: [
      { name: 'Recrutamento Core', included: true },
      { name: 'Onboarding Automatizado', included: false },
      { name: 'Analytics ML', included: false },
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    label: 'Recomendado',
    price: MODULE_TIER_PRICES.professional,
    recommended: true,
    features: [
      { name: 'Recrutamento Core', included: true },
      { name: 'Onboarding Automatizado', included: true },
      { name: 'Analytics Avançado', included: true },
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    label: 'Recursos completos',
    price: MODULE_TIER_PRICES.enterprise,
    features: [
      { name: 'Todos os módulos', included: true },
      { name: 'Analytics ML', included: true },
      { name: 'Integrações ATS', included: true },
    ],
  },
]

export const MODULE_PRICES: Record<string, ModulePriceEntry> = {
  onboarding_automation: {
    id: 'onboarding_automation',
    name: 'Onboarding Automatizado',
    description: 'Sistema completo de integração de novos colaboradores',
    price: brl(299, 'mês'),
    features: [
      'Fluxos de onboarding personalizados',
      'Automação de documentos',
      'Acompanhamento de progresso',
      'Integração com HRIS',
    ],
    category: 'automation',
  },
  communication_center: {
    id: 'communication_center',
    name: 'Central de Comunicação',
    description: 'Sistema unificado de comunicação multi-canal',
    price: brl(199, 'mês'),
    features: [
      'Chat omnichannel',
      'Templates personalizados',
      'Automação de mensagens',
      'Analytics de comunicação',
    ],
    category: 'premium',
  },
  ml_prediction: {
    id: 'ml_prediction',
    name: 'Analytics com ML',
    description: 'Predição inteligente e analytics avançado',
    price: brl(499, 'mês'),
    features: [
      'Predição de sucesso',
      'Analytics preditivo',
      'Machine Learning',
      'Insights automatizados',
    ],
    category: 'analytics',
  },
  ats_integrations: {
    id: 'ats_integrations',
    name: 'Integrações ATS',
    description: 'Conecte com principais ATS do mercado',
    price: brl(149, 'mês'),
    features: [
      'Integração com ATS populares',
      'Sincronização automática',
      'API unificada',
      'Suporte técnico',
    ],
    category: 'integrations',
  },
  workflow_automation: {
    id: 'workflow_automation',
    name: 'Automação de Workflows',
    description: 'Automações inteligentes para RH',
    price: brl(249, 'mês'),
    features: [
      'Workflows personalizados',
      'Triggers automáticos',
      'Regras de negócio',
      'Integrações avançadas',
    ],
    category: 'automation',
  },
  advanced_analytics: {
    id: 'advanced_analytics',
    name: 'Analytics Avançado',
    description: 'Relatórios e dashboards personalizados',
    price: brl(199, 'mês'),
    features: [
      'Dashboards personalizados',
      'Relatórios avançados',
      'Exportação de dados',
      'APIs de analytics',
    ],
    category: 'analytics',
  },
}

export const DEMO_VALUES = {
  AI_CONSUMPTION_MONTHLY: formatBRL(850),
  GLOBAL_SEARCH_MONTHLY: formatBRL(420),
  OFFER_SALARY_EXAMPLE: 'R$ 12.000,00',
  SALARY_PLACEHOLDER_CURRENT: 'R$ 8.000',
  SALARY_PLACEHOLDER_EXPECTED: 'R$ 10.000',
} as const

export function getModulePrice(moduleId: string): PriceValue | undefined {
  return MODULE_PRICES[moduleId]?.price
}

export function getPlanDisplayPrice(tier: PlanTier): string {
  const price = PLAN_PRICES[tier]
  return price ? price.formatted : 'Sob consulta'
}
