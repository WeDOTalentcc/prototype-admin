export interface AlertConfig {
  id: string
  name: string
  description: string
  enabled: boolean
  channel: 'email' | 'teams' | 'both'
}

export interface EmailTemplate {
  id: string
  name: string
  category: 'approval' | 'rejection' | 'scheduling' | 'followup' | 'feedback'
  subject: string
  body: string
  variables: string[]
  isActive: boolean
  lastUpdated: string
  channel?: 'email' | 'whatsapp' | 'teams' | 'bell'
  situation?: string
  trigger_type?: 'automatic' | 'manual' | 'both'
  used_in?: string[]
  priority?: 'high' | 'medium' | 'low'
}

export interface CommunicationHubProps {
  activeSubsection?: string
  visibleTabs?: string[]
  /**
   * Quando true, todas as `visibleTabs` são renderizadas empilhadas
   * (sem pill nav), uma abaixo da outra. Usado pela tab
   * "Templates & Assinatura" do menu Configurações para preservar o
   * layout do antigo `TemplatesAssinaturaHub`.
   */
  stacked?: boolean
}

export interface AiResultModal {
  show: boolean
  newSubject: string
  newBody: string
  changesMade: string[]
}
