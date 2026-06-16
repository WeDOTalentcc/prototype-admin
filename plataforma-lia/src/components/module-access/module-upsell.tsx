"use client"

import { useState } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Lock, Star, Zap, Crown, Check, X, ArrowRight,
  Mail, Phone, CreditCard, Calendar, Users,
  MessageSquare, FileText, Settings, Building,
  Clock, Brain, BarChart3, Workflow
} from"lucide-react"
import { LicenseModule, getModuleInfo } from"@/utils/license-manager"
import { MODULE_TIERS } from"@/lib/pricing"

interface ModuleUpsellProps {
  moduleId: string
  title: string
  description: string
  onUpgrade?: () => void
}

export function ModuleUpsell({ moduleId, title, description, onUpgrade }: ModuleUpsellProps) {
  const [showDetails, setShowDetails] = useState(false)
  const moduleInfo = getModuleInfo(moduleId)

  if (!moduleInfo) {
    return null
  }

  const getModuleIcon = (moduleId: string) => {
    switch (moduleId) {
      case 'onboarding_automation': return <Clock className="w-8 h-8" />
      case 'ml_prediction': return <Brain className="w-8 h-8 text-wedo-cyan-text" />
      case 'ats_integrations': return <Building className="w-8 h-8" />
      case 'advanced_analytics': return <BarChart3 className="w-8 h-8" />
      default: return <Star className="w-8 h-8" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'premium': return 'bg-lia-bg-inverse'
      case 'enterprise': return 'bg-wedo-purple/10'
      default: return 'bg-lia-border-medium'
    }
  }

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex items-center justify-center p-6">
      <div className="max-w-4xl w-full">
        {/* Main Upsell Card */}
        <Card >
          <CardContent className="p-0">
            {/* Header with solid color */}
            <div className={`${getCategoryColor(moduleInfo.category)} p-8 text-white rounded-t-lg`}>
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-lia-bg-primary/20 rounded-xl flex items-center justify-center">
                  {getModuleIcon(moduleId)}
                </div>
                <div>
                  <h1 className="text-3xl font-semibold">{moduleInfo.name}</h1>
                  <p className="text-white text-lg">{moduleInfo.description}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <Chip variant="neutral" muted className="bg-lia-bg-primary/20 text-white">
                  <Crown className="w-4 h-4 mr-1" />
                  {moduleInfo.category === 'premium' ? 'Premium' : 'Enterprise'}
                </Chip>
                <Chip variant="neutral" muted className="bg-lia-bg-primary/20 text-white">
                  {moduleInfo.price}
                </Chip>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Features List */}
                <div>
                  <h3 className="text-xl font-semibold text-lia-text-primary mb-4">
                    Funcionalidades Incluídas
                  </h3>
                  <div className="space-y-3">
                    {moduleInfo.features.map((feature, index) => (
                      <div key={`feature-${index}`} className="flex items-center gap-3">
                        <div className="w-6 h-6 bg-status-success/10 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-status-success" />
                        </div>
                        <span className="text-lia-text-primary">{feature}</span>
                      </div>
                    ))}
                  </div>

                  {/* Additional Info for Onboarding */}
                  {moduleId === 'onboarding_automation' && (
                    <div className="mt-6 p-4 bg-wedo-cyan/10 dark:bg-wedo-cyan/15 rounded-xl">
                      <h4 className="font-medium text-lia-text-primary mb-2">
                        🚀 Onboarding Automatizado Premium
                      </h4>
                      <ul className="text-sm text-lia-text-secondary space-y-1">
                        <li>• Kanban visual para novos colaboradores</li>
                        <li>• Templates customizáveis por departamento</li>
                        <li>• Integração WhatsApp Business API</li>
                        <li>• Coleta automática de documentos</li>
                        <li>• Agendamento de exames médicos</li>
                        <li>• Workflows personalizados</li>
                        <li>• Analytics de onboarding</li>
                      </ul>
                    </div>
                  )}
                </div>

                {/* Pricing and CTA */}
                <div>
                  <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl p-6 mb-6">
                    <div className="text-center mb-4">
                      <div className="text-3xl font-semibold text-lia-text-primary">
                        {moduleInfo.price}
                      </div>
                      <p className="text-lia-text-primary">por empresa</p>
                    </div>

                    <div className="space-y-3 mb-6">
                      <Button
                        className="w-full gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                        onClick={onUpgrade}
                      >
                        <CreditCard className="w-4 h-4" />
                        Ativar Módulo Agora
                      </Button>
                      <Button variant="outline" className="w-full gap-2">
                        <Calendar className="w-4 h-4" />
                        Agendar Demonstração
                      </Button>
                    </div>

                    <div className="text-center">
                      <p className="text-sm text-lia-text-primary mb-2">
                        Precisa de ajuda?
                      </p>
                      <div className="flex justify-center gap-4">
                        <Button variant="ghost" size="sm" className="gap-2">
                          <Phone className="w-4 h-4" />
                          Falar com Vendas
                        </Button>
                        <Button variant="ghost" size="sm" className="gap-2">
                          <Mail className="w-4 h-4" />
                          Email
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Enterprise Benefits */}
                  <div className="rounded-xl p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                    <h4 className="font-medium text-lia-text-primary mb-3">
                      ✨ Benefícios Enterprise
                    </h4>
                    <ul className="text-sm text-lia-text-primary space-y-2">
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-status-success" />
                        Implementação dedicada
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-status-success" />
                        Suporte prioritário 24/7
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-status-success" />
                        Customizações personalizadas
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-status-success" />
                        Treinamento da equipe
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alternative: Module comparison */}
        <div className="mt-8 text-center">
          <Button variant="ghost" className="gap-2" onClick={() => setShowDetails(!showDetails)}>
            <Settings className="w-4 h-4" />
            {showDetails ? 'Ocultar' : 'Ver'} Comparação de Planos
            <ArrowRight className={`w-4 h-4 transition-transform motion-reduce:transition-none ${showDetails ? 'rotate-90' : ''}`} />
          </Button>

          {showDetails && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              {MODULE_TIERS.map((tier) => (
              <Card key={tier.id} className={tier.recommended ?"ring-2 ring-lia-btn-primary-bg/20 dark:ring-lia-border-subtle/20" :""}>
                <CardHeader>
                  <CardTitle className={`text-lg ${tier.recommended ? 'text-lia-text-secondary' : ''}`}>{tier.name}</CardTitle>
                  <p className="text-lia-text-primary">{tier.label}</p>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-semibold mb-4">{tier.price.formatted}</div>
                  <ul className="space-y-2 text-sm">
                    {tier.features.map((f) => (
                      <li key={f.name} className="flex items-center gap-2">
                        {f.included
                          ? <Check className="w-4 h-4 text-status-success" />
                          : <X className="w-4 h-4 text-status-error" />}
                        {f.name}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Componente para mostrar aviso de módulo desabilitado
export function ModuleLockedBanner({ moduleName, onUpgrade }: { moduleName: string, onUpgrade?: () => void }) {
  return (
    <div className="bg-lia-btn-primary-bg text-lia-btn-primary-text p-4 rounded-xl mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Lock className="w-6 h-6" />
          <div>
            <h3 className="font-semibold">Módulo {moduleName} não ativo</h3>
            <p className="text-white text-sm">Ative este módulo para acessar todas as funcionalidades</p>
          </div>
        </div>
        <Button
          variant="secondary"
          className="gap-2 bg-lia-bg-primary text-lia-text-secondary hover:bg-lia-bg-tertiary"
          onClick={onUpgrade}
        >
          <Crown className="w-4 h-4" />
          Fazer Upgrade
        </Button>
      </div>
    </div>
  )
}
