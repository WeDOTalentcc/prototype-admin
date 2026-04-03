export interface PlanConfig {
  name: string
  price: string
  period: string
  features: string[]
  cta: string
  highlighted: boolean
}

export const PLANS: PlanConfig[] = [
  {
    name: 'Starter',
    price: 'R$ 990',
    period: '/mês',
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
    name: 'Pro',
    price: 'R$ 2.490',
    period: '/mês',
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
    name: 'Enterprise',
    price: 'Sob consulta',
    period: '',
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
