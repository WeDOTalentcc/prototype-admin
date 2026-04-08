import { MODULE_PRICES } from '@/lib/pricing'

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
function buildModuleInfo(): Record<LicenseModule, ModuleInfo> {
  const entries = Object.entries(MODULE_PRICES).map(([id, mp]) => [
    id,
    {
      id: id as LicenseModule,
      name: mp.name,
      description: mp.description,
      price: mp.price.formatted,
      features: mp.features,
      category: mp.category as ModuleInfo['category'],
    },
  ])
  return Object.fromEntries(entries) as Record<LicenseModule, ModuleInfo>
}

const moduleInfo: Record<LicenseModule, ModuleInfo> = buildModuleInfo()

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
const licenseManager = {
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
export default licenseManager
