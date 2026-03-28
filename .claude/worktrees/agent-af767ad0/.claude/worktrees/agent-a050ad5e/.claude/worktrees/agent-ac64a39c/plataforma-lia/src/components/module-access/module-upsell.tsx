"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Lock, Star, Zap, Crown, Check, X, ArrowRight,
  Mail, Phone, CreditCard, Calendar, Users,
  MessageSquare, FileText, Settings, Building,
  Clock, Brain, BarChart3, Workflow
} from "lucide-react"
import { LicenseModule, getModuleInfo } from "@/utils/license-manager"

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
      case 'ml_prediction': return <Brain className="w-8 h-8 text-wedo-cyan" />
      case 'ats_integrations': return <Building className="w-8 h-8" />
      case 'advanced_analytics': return <BarChart3 className="w-8 h-8" />
      default: return <Star className="w-8 h-8" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'premium': return 'bg-gray-700 dark:bg-gray-300'
      case 'enterprise': return 'bg-purple-600'
      default: return 'bg-gray-600'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-6">
      <div className="max-w-4xl w-full">
        {/* Main Upsell Card */}
        <Card className="">
          <CardContent className="p-0">
            {/* Header with solid color */}
            <div className={`${getCategoryColor(moduleInfo.category)} p-8 text-white rounded-t-lg`}>
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-white/20 rounded-md flex items-center justify-center">
                  {getModuleIcon(moduleId)}
                </div>
                <div>
                  <h1 className="text-3xl font-bold">{moduleInfo.name}</h1>
                  <p className="text-white text-lg">{moduleInfo.description}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <Badge variant="secondary" className="bg-white/20 text-white">
                  <Crown className="w-4 h-4 mr-1" />
                  {moduleInfo.category === 'premium' ? 'Premium' : 'Enterprise'}
                </Badge>
                <Badge variant="secondary" className="bg-white/20 text-white">
                  R$ {moduleInfo.price}/mês
                </Badge>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Features List */}
                <div>
                  <h3 className="text-xl font-semibold text-gray-950 dark:text-gray-50 mb-4">
                    Funcionalidades Incluídas
                  </h3>
                  <div className="space-y-3">
                    {moduleInfo.features.map((feature, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-green-600" />
                        </div>
                        <span className="text-gray-800 dark:text-gray-200">{feature}</span>
                      </div>
                    ))}
                  </div>

                  {/* Additional Info for Onboarding */}
                  {moduleId === 'onboarding_automation' && (
                    <div className="mt-6 p-4 bg-wedo-cyan/10 dark:bg-wedo-cyan/15 rounded-md">
                      <h4 className="font-medium text-wedo-cyan-dark dark:text-gray-400 mb-2">
                        🚀 Onboarding Automatizado Premium
                      </h4>
                      <ul className="text-sm text-wedo-cyan-dark dark:text-gray-400 space-y-1">
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
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-6 mb-6">
                    <div className="text-center mb-4">
                      <div className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                        R$ {moduleInfo.price}
                        <span className="text-lg font-normal text-gray-800 dark:text-gray-200">/mês</span>
                      </div>
                      <p className="text-gray-800 dark:text-gray-200">por empresa</p>
                    </div>

                    <div className="space-y-3 mb-6">
                      <Button
                        className="w-full gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
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
                      <p className="text-sm text-gray-800 dark:text-gray-200 mb-2">
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
                  <div className="rounded-md p-4 bg-gray-50 dark:bg-gray-800">
                    <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-3">
                      ✨ Benefícios Enterprise
                    </h4>
                    <ul className="text-sm text-gray-800 dark:text-gray-200 space-y-2">
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-600" />
                        Implementação dedicada
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-600" />
                        Suporte prioritário 24/7
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-600" />
                        Customizações personalizadas
                      </li>
                      <li className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-600" />
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
            <ArrowRight className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
          </Button>

          {showDetails && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="">
                <CardHeader>
                  <CardTitle className="text-lg">Starter</CardTitle>
                  <p className="text-gray-800 dark:text-gray-200">Funcionalidades básicas</p>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-4">R$ 99/mês</div>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Recrutamento Core
                    </li>
                    <li className="flex items-center gap-2">
                      <X className="w-4 h-4 text-red-500" />
                      Onboarding Automatizado
                    </li>
                    <li className="flex items-center gap-2">
                      <X className="w-4 h-4 text-red-500" />
                      Analytics ML
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="ring-2 ring-gray-900/20 dark:ring-gray-50/20">
                <CardHeader>
                  <CardTitle className="text-lg text-gray-600 dark:text-gray-400">Professional</CardTitle>
                  <p className="text-gray-800 dark:text-gray-200">Recomendado</p>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-4">R$ 299/mês</div>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Recrutamento Core
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Onboarding Automatizado
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Analytics Avançado
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="">
                <CardHeader>
                  <CardTitle className="text-lg">Enterprise</CardTitle>
                  <p className="text-gray-800 dark:text-gray-200">Recursos completos</p>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-4">R$ 699/mês</div>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Todos os módulos
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Analytics ML
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600" />
                      Integrações ATS
                    </li>
                  </ul>
                </CardContent>
              </Card>
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
    <div className="bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 p-4 rounded-md mb-6">
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
          className="gap-2 bg-white text-gray-600 dark:text-gray-400 hover:bg-gray-100"
          onClick={onUpgrade}
        >
          <Crown className="w-4 h-4" />
          Fazer Upgrade
        </Button>
      </div>
    </div>
  )
}
