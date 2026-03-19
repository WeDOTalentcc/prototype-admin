// License Manager - Sistema de controle de módulos premium
export type LicenseModule =
  | 'onboarding_automation'
  | 'communication_center'
  | 'ml_prediction'
  | 'ats_integrations'
  | 'workflow_automation'
  | 'advanced_analytics'

interface ModuleInfo {
  id: LicenseModule
  name: string
  description: string
  price: string
  features: string[]
  category: 'automation' | 'analytics' | 'integrations' | 'premium'
}

// Para desenvolvimento/demo, todos os módulos estão disponíveis
const DEMO_MODE = true

// Módulos disponíveis na licença atual (em produção, viria de API)
const availableModules: LicenseModule[] = DEMO_MODE ? [
  'onboarding_automation',
  'communication_center',
  'ml_prediction',
  'ats_integrations',
  'workflow_automation',
  'advanced_analytics'
] : []

// Informações dos módulos
const moduleInfo: Record<LicenseModule, ModuleInfo> = {
  onboarding_automation: {
    id: 'onboarding_automation',
    name: 'Onboarding Automatizado',
    description: 'Sistema completo de integração de novos colaboradores',
    price: 'R$ 299/mês',
    features: [
      'Fluxos de onboarding personalizados',
      'Automação de documentos',
      'Acompanhamento de progresso',
      'Integração com HRIS'
    ],
    category: 'automation'
  },
  communication_center: {
    id: 'communication_center',
    name: 'Central de Comunicação',
    description: 'Sistema unificado de comunicação multi-canal',
    price: 'R$ 199/mês',
    features: [
      'Chat omnichannel',
      'Templates personalizados',
      'Automação de mensagens',
      'Analytics de comunicação'
    ],
    category: 'premium'
  },
  ml_prediction: {
    id: 'ml_prediction',
    name: 'Analytics com ML',
    description: 'Predição inteligente e analytics avançado',
    price: 'R$ 499/mês',
    features: [
      'Predição de sucesso',
      'Analytics preditivo',
      'Machine Learning',
      'Insights automatizados'
    ],
    category: 'analytics'
  },
  ats_integrations: {
    id: 'ats_integrations',
    name: 'Integrações ATS',
    description: 'Conecte com principais ATS do mercado',
    price: 'R$ 149/mês',
    features: [
      'Integração com ATS populares',
      'Sincronização automática',
      'API unificada',
      'Suporte técnico'
    ],
    category: 'integrations'
  },
  workflow_automation: {
    id: 'workflow_automation',
    name: 'Automação de Workflows',
    description: 'Automações inteligentes para RH',
    price: 'R$ 249/mês',
    features: [
      'Workflows personalizados',
      'Triggers automáticos',
      'Regras de negócio',
      'Integrações avançadas'
    ],
    category: 'automation'
  },
  advanced_analytics: {
    id: 'advanced_analytics',
    name: 'Analytics Avançado',
    description: 'Relatórios e dashboards personalizados',
    price: 'R$ 199/mês',
    features: [
      'Dashboards personalizados',
      'Relatórios avançados',
      'Exportação de dados',
      'APIs de analytics'
    ],
    category: 'analytics'
  }
}

// Funções de verificação de acesso
export function hasModuleAccess(moduleId: LicenseModule): boolean {
  return DEMO_MODE || availableModules.includes(moduleId)
}

export function canAccessOnboarding(): boolean {
  return hasModuleAccess('onboarding_automation')
}

export function canAccessMLAnalytics(): boolean {
  return hasModuleAccess('ml_prediction')
}

export function canAccessATSIntegrations(): boolean {
  return hasModuleAccess('ats_integrations')
}

export function canAccessCommunicationCenter(): boolean {
  return hasModuleAccess('communication_center')
}

export function canAccessWorkflowAutomation(): boolean {
  return hasModuleAccess('workflow_automation')
}

export function canAccessAdvancedAnalytics(): boolean {
  return hasModuleAccess('advanced_analytics')
}

// Obter informações de um módulo
export function getModuleInfo(moduleId: LicenseModule): ModuleInfo {
  return moduleInfo[moduleId]
}

// Obter todos os módulos disponíveis
export function getAvailableModules(): LicenseModule[] {
  return availableModules
}

// Obter módulos por categoria
export function getModulesByCategory(category: ModuleInfo['category']): ModuleInfo[] {
  return Object.values(moduleInfo).filter(module => module.category === category)
}

// Verificar se usuário tem acesso premium geral
export function hasPremiumAccess(): boolean {
  return DEMO_MODE || availableModules.length > 0
}

// Simular upgrade de módulo (em produção, faria chamada de API)
export async function upgradeModule(moduleId: LicenseModule): Promise<boolean> {
  if (DEMO_MODE) {
    // Em modo demo, sempre sucesso
    if (!availableModules.includes(moduleId)) {
      availableModules.push(moduleId)
    }
    return true
  }

  // Em produção, faria chamada para API de billing
  throw new Error('Upgrade não implementado em produção')
}

// Export default para compatibilidade
export default {
  hasModuleAccess,
  canAccessOnboarding,
  canAccessMLAnalytics,
  canAccessATSIntegrations,
  canAccessCommunicationCenter,
  canAccessWorkflowAutomation,
  canAccessAdvancedAnalytics,
  getModuleInfo,
  getAvailableModules,
  getModulesByCategory,
  hasPremiumAccess,
  upgradeModule
}
