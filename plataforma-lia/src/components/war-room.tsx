"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
// import { Progress } from "@/components/ui/progress"
import {
  Target, Users, Calendar, Mail, Phone, Linkedin,
  Clock, TrendingUp, AlertTriangle, CheckCircle,
  Play, Pause, Settings, BarChart3, Zap, Brain,
  User, Building, ArrowRight, Plus, Eye, Star
} from "lucide-react"

// Mock de campanhas War Room ativas
const mockCampaigns = [
  {
    id: 'campaign-1',
    name: 'Operation Nubank Talent',
    target: 'Nubank',
    status: 'active',
    startDate: '2024-02-15',
    endDate: '2024-03-15',
    progress: 65,
    budget: 50000,
    spent: 32500,
    targets: [
      {
        id: 't1',
        name: 'João Silva',
        role: 'Principal Engineer',
        priority: 'high',
        status: 'contacted',
        lastContact: '2024-02-20',
        response: 'interested',
        linkedin: 'joao-silva-dev'
      },
      {
        id: 't2',
        name: 'Maria Costa',
        role: 'Staff Engineer',
        priority: 'high',
        status: 'approached',
        lastContact: '2024-02-18',
        response: 'pending',
        linkedin: 'maria-costa-eng'
      },
      {
        id: 't3',
        name: 'Pedro Santos',
        role: 'Tech Lead',
        priority: 'medium',
        status: 'research',
        lastContact: null,
        response: null,
        linkedin: 'pedro-santos-lead'
      }
    ],
    strategy: {
      approach: 'Headhunting direto via LinkedIn',
      message: 'Proposta de liderança técnica em fintech inovadora',
      budget_per_hire: 15000,
      timeline: 'Agressivo - 30 dias',
      success_rate: '67%'
    },
    metrics: {
      targets_identified: 15,
      contacts_made: 8,
      responses_received: 5,
      interviews_scheduled: 3,
      offers_made: 1,
      hires_completed: 0
    }
  },
  {
    id: 'campaign-2',
    name: 'iFood Mobile Raid',
    target: 'iFood',
    status: 'planning',
    startDate: '2024-02-25',
    endDate: '2024-03-25',
    progress: 25,
    budget: 30000,
    spent: 5000,
    targets: [
      {
        id: 't4',
        name: 'Lucas Oliveira',
        role: 'Senior Mobile Dev',
        priority: 'high',
        status: 'research',
        lastContact: null,
        response: null,
        linkedin: 'lucas-mobile-dev'
      },
      {
        id: 't5',
        name: 'Fernanda Rocha',
        role: 'Mobile Architect',
        priority: 'medium',
        status: 'research',
        lastContact: null,
        response: null,
        linkedin: 'fernanda-mobile'
      }
    ],
    strategy: {
      approach: 'Oferta salarial competitiva + equity',
      message: 'Oportunidade de liderar time mobile em crescimento',
      budget_per_hire: 12000,
      timeline: 'Padrão - 45 dias',
      success_rate: '45%'
    },
    metrics: {
      targets_identified: 6,
      contacts_made: 1,
      responses_received: 0,
      interviews_scheduled: 0,
      offers_made: 0,
      hires_completed: 0
    }
  }
]

interface WarRoomProps {
  isOpen: boolean
  onClose: () => void
}

export function WarRoom({ isOpen, onClose }: WarRoomProps) {
  const [campaigns] = useState(mockCampaigns)
  const [selectedCampaign, setSelectedCampaign] = useState<string | null>(campaigns[0]?.id || null)

  if (!isOpen) return null

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-status-success/15 text-status-success border-status-success/30'
      case 'planning': return 'bg-status-warning/15 text-status-warning border-status-warning/30'
      case 'paused': return 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-subtle'
      case 'completed': return 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-border-default dark:border-lia-border-default'
      default: return 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-subtle'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-status-error/15 text-status-error'
      case 'medium': return 'bg-status-warning/15 text-status-warning'
      case 'low': return 'bg-status-success/15 text-status-success'
      default: return 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary'
    }
  }

  const getContactStatusIcon = (status: string) => {
    switch (status) {
      case 'contacted': return <Mail className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
      case 'approached': return <Phone className="w-3 h-3 text-wedo-orange" />
      case 'research': return <Eye className="w-3 h-3 lia-text-base" />
      case 'scheduled': return <Calendar className="w-3 h-3 text-status-success" />
      default: return <User className="w-3 h-3 lia-text-base" />
    }
  }

  const selectedCampaignData = campaigns.find(c => c.id === selectedCampaign)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-lia-bg-primary rounded-md max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 bg-status-error/10 dark:bg-status-error/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold font-sans text-lia-text-primary flex items-center gap-2">
                ⚔️ War Room - Operações Estratégicas
              </h2>
              <p className="text-sm text-lia-text-primary dark:text-lia-text-primary mt-1">
                Campanhas focadas de aquisição de talentos competitivos
              </p>
            </div>
            <Button variant="outline" onClick={onClose}>
              Fechar
            </Button>
          </div>
        </div>

        <div className="flex h-[calc(90vh-120px)]">
          {/* Sidebar - Lista de Campanhas */}
          <div className="w-80 bg-white dark:bg-lia-bg-secondary overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium font-sans text-lia-text-primary">
                  Campanhas Ativas ({campaigns.length})
                </h3>
                <Button size="sm" className="h-7">
                  <Plus className="w-3 h-3 mr-1" />
                  Nova
                </Button>
              </div>

              <div className="space-y-3">
                {campaigns.map((campaign) => (
                  <Card
                    key={campaign.id}
                    className={`cursor-pointer transition-colors ${
 selectedCampaign === campaign.id ? 'border-gray-900 bg-gray-100 dark:bg-lia-bg-secondary' : ''
                    }`}
                    onClick={() => setSelectedCampaign(campaign.id)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-sm text-lia-text-primary">
                          {campaign.name}
                        </h4>
                        <Badge className={`text-xs ${getStatusColor(campaign.status)}`}>
                          {campaign.status}
                        </Badge>
                      </div>

                      <div className="text-xs text-lia-text-primary dark:text-lia-text-primary mb-2">
                        Target: {campaign.target}
                      </div>

                      <div className="mb-2">
                        <div className="flex justify-between text-xs mb-1">
                          <span>Progresso</span>
                          <span>{campaign.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div
                            className="bg-gray-700 h-1 rounded-full transition-[width,height]"
                            style={{width: `${campaign.progress}%`}}
                          />
                        </div>
                      </div>

                      <div className="flex justify-between text-xs">
                        <span>{campaign.targets.length} alvos</span>
                        <span>R$ {(campaign.budget / 1000).toFixed(0)}k budget</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content - Detalhes da Campanha */}
          <div className="flex-1 overflow-y-auto">
            {selectedCampaignData ? (
              <div className="p-6 space-y-6">
                {/* Campaign Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold font-sans text-lia-text-primary">
                      {selectedCampaignData.name}
                    </h3>
                    <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                      Empresa alvo: {selectedCampaignData.target} • {selectedCampaignData.targets.length} talentos identificados
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Settings className="w-3 h-3 mr-1" />
                      Configurar
                    </Button>
                    <Button size="sm" className="bg-status-error hover:bg-status-error">
                      <Play className="w-3 h-3 mr-1" />
                      Executar
                    </Button>
                  </div>
                </div>

                {/* Métricas da Campanha */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card className="">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                        <div>
                          <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">Alvos Identificados</p>
                          <p className="text-xl font-semibold text-lia-text-primary">
                            {selectedCampaignData.metrics.targets_identified}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-status-success" />
                        <div>
                          <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">Contatos Realizados</p>
                          <p className="text-xl font-semibold text-lia-text-primary">
                            {selectedCampaignData.metrics.contacts_made}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-wedo-purple" />
                        <div>
                          <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">Taxa Resposta</p>
                          <p className="text-xl font-semibold text-lia-text-primary">
                            {selectedCampaignData.metrics.contacts_made > 0
                              ? Math.round((selectedCampaignData.metrics.responses_received / selectedCampaignData.metrics.contacts_made) * 100)
                              : 0}%
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-wedo-orange" />
                        <div>
                          <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">ROI Estimado</p>
                          <p className="text-xl font-semibold text-lia-text-primary">
                            {selectedCampaignData.strategy.success_rate}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Estratégia da Campanha */}
                <Card className="">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 font-sans">
                      <Brain className="w-5 h-5 text-wedo-cyan" />
                      Estratégia de Campanha
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium font-sans text-lia-text-primary mb-2">Abordagem</h4>
                        <p className="text-sm text-lia-text-primary dark:text-lia-text-primary mb-4">
                          {selectedCampaignData.strategy.approach}
                        </p>

                        <h4 className="font-medium font-sans text-lia-text-primary mb-2">Mensagem Principal</h4>
                        <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                          "{selectedCampaignData.strategy.message}"
                        </p>
                      </div>

                      <div>
                        <h4 className="font-medium font-sans text-lia-text-primary mb-2">Métricas Estratégicas</h4>
                        <div className="space-y-2 text-sm text-lia-text-primary dark:text-lia-text-primary">
                          <div className="flex justify-between">
                            <span>Budget por contratação:</span>
                            <span className="font-medium">R$ {selectedCampaignData.strategy.budget_per_hire.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Timeline:</span>
                            <span className="font-medium">{selectedCampaignData.strategy.timeline}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Taxa de sucesso estimada:</span>
                            <span className="font-medium">{selectedCampaignData.strategy.success_rate}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Lista de Talentos Alvo */}
                <Card className="">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 font-sans">
                      <Users className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      Talentos Alvo ({selectedCampaignData.targets.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {selectedCampaignData.targets.map((target) => (
                        <div key={target.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                          <div className="flex items-center gap-3">
                            <Avatar className="w-10 h-10">
                              <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary font-medium text-sm">
                                {target.name.split(' ').map(n => n[0]).join('')}
                              </AvatarFallback>
                            </Avatar>

                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-lia-text-primary">
                                  {target.name}
                                </span>
                                <Badge className={`text-xs ${getPriorityColor(target.priority)}`}>
                                  {target.priority}
                                </Badge>
                              </div>
                              <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                                {target.role}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <div className="text-center">
                              {getContactStatusIcon(target.status)}
                              <div className="text-xs lia-text-base mt-1">
                                {target.status}
                              </div>
                            </div>

                            {target.response && (
                              <Badge variant="outline" className="text-xs">
                                {target.response}
                              </Badge>
                            )}

                            <div className="flex gap-1">
                              <Button variant="outline" size="sm" className="h-7 text-xs">
                                <Linkedin className="w-3 h-3 mr-1" />
                                LinkedIn
                              </Button>
                              <Button variant="outline" size="sm" className="h-7 text-xs">
                                <Mail className="w-3 h-3 mr-1" />
                                Contatar
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="p-6 text-center">
                <Target className="w-12 h-12 lia-text-base mx-auto mb-4" />
                <h3 className="text-lg font-medium font-sans text-lia-text-primary mb-2">
                  Selecione uma campanha
                </h3>
                <p className="text-lia-text-primary dark:text-lia-text-primary">
                  Escolha uma campanha para ver os detalhes e gerenciar a operação
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
