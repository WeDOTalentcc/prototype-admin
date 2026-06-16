// Sistema de gerenciamento de licenças e módulos da plataforma
export interface LicenseModule {
  id: string
  name: string
  description: string
  isActive: boolean
  features: string[]
  price: number
  category: 'core' | 'premium' | 'enterprise'
}

export interface UserLicense {
  companyId: string
  companyName: string
  plan: 'starter' | 'professional' | 'enterprise' | 'custom'
  modules: LicenseModule[]
  expirationDate: string
  maxUsers: number
  currentUsers: number
}

// Módulos disponíveis na plataforma
export const AVAILABLE_MODULES: LicenseModule[] = [
  {
    id: 'core_recruitment',
    name: 'Recrutamento Core',
    description: 'Funcionalidades básicas de recrutamento e seleção',
    isActive: true,
    features: ['Gestão de vagas', 'Candidatos', 'Entrevistas', 'Chat LIA básico'],
    price: 0,
    category: 'core'
  },
  {
    id: 'advanced_analytics',
    name: 'Analytics Avançado',
    description: 'Relatórios detalhados e dashboard executivo',
    isActive: true,
    features: ['Dashboard executivo', 'Relatórios PDF', 'Métricas avançadas', 'Exportação'],
    price: 299,
    category: 'premium'
  },
  {
    id: 'ml_prediction',
    name: 'Predição com IA',
    description: 'Machine learning para predição de sucesso',
    isActive: true,
    features: ['Modelos de ML', 'Predição de sucesso', 'Análise preditiva', 'Recomendações IA'],
    price: 599,
    category: 'enterprise'
  },
  {
    id: 'onboarding_automation',
    name: 'Onboarding Automatizado',
    description: 'Sistema completo de integração de novos colaboradores',
    isActive: true,
    features: [
      'Kanban de onboarding',
      'Templates customizáveis',
      'Comunicação WhatsApp/Email',
      'Coleta de documentos',
      'Agendamento de exames',
      'Primeiro dia automatizado',
      'Fluxos personalizados',
      'Integrações médicas'
    ],
    price: 399,
    category: 'premium'
  },
  {
    id: 'communication_center',
    name: 'Central de Comunicação Omnichannel',
    description: 'Sistema unificado de comunicação multi-canal',
    isActive: true,
    features: [
      'WhatsApp Business API',
      'Email automatizado',
      'SMS em lote',
      'Templates dinâmicos',
      'Campanhas automatizadas',
      'Analytics de comunicação',
      'Histórico unificado',
      'Integração com IA'
    ],
    price: 499,
    category: 'premium'
  },
  {
    id: 'workflow_automation',
    name: 'Automação Avançada de Workflows',
    description: 'Workflow builder visual com automações inteligentes',
    isActive: true,
    features: [
      'Workflow Builder visual',
      'Triggers inteligentes',
      'Condições complexas',
      'Ações automatizadas',
      'Templates pré-configurados',
      'Analytics de performance',
      'Integração com IA',
      'API de webhooks'
    ],
    price: 699,
    category: 'enterprise'
  },
  {
    id: 'ats_integrations',
    name: 'Integrações ATS Enterprise',
    description: 'Conectores bidirecionais para sistemas HR externos',
    isActive: true,
    features: [
      'SAP SuccessFactors',
      'Workday HCM',
      'BambooHR',
      'Greenhouse',
      'API personalizada',
      'Webhooks em tempo real',
      'Mapeamento automático',
      'Logs detalhados',
      'Sincronização bidirecional',
      'Dashboard de status'
    ],
    price: 999,
    category: 'enterprise'
  }
]

// Mock da licença atual do usuário (normalmente viria da API)
export const getCurrentUserLicense = (): UserLicense => {
  return {
    companyId: 'sodexo_brasil',
    companyName: 'Sodexo Brasil',
    plan: 'enterprise',
    modules: AVAILABLE_MODULES.filter(m => m.isActive),
    expirationDate: '2024-12-31',
    maxUsers: 50,
    currentUsers: 23
  }
}

// Verificar se um módulo está ativo
export const hasModuleAccess = (moduleId: string): boolean => {
  const license = getCurrentUserLicense()
  return license.modules.some(module => module.id === moduleId && module.isActive)
}

// Verificar se uma feature específica está disponível
export const hasFeatureAccess = (featureName: string): boolean => {
  const license = getCurrentUserLicense()
  return license.modules.some(module =>
    module.isActive && module.features.some(feature =>
      feature.toLowerCase().includes(featureName.toLowerCase())
    )
  )
}

// Obter informações de um módulo específico
export const getModuleInfo = (moduleId: string): LicenseModule | null => {
  return AVAILABLE_MODULES.find(module => module.id === moduleId) || null
}

// Obter módulos por categoria
export const getModulesByCategory = (category: 'core' | 'premium' | 'enterprise') => {
  return AVAILABLE_MODULES.filter(module => module.category === category)
}

// Verificar se o usuário pode acessar a página de onboarding
export const canAccessOnboarding = (): boolean => {
  return hasModuleAccess('onboarding_automation')
}

// Verificar se o usuário pode acessar analytics ML
export const canAccessMLAnalytics = (): boolean => {
  return hasModuleAccess('ml_prediction')
}

// Verificar se o usuário pode acessar integrações ATS
export const canAccessATSIntegrations = (): boolean => {
  return hasModuleAccess('ats_integrations')
}
