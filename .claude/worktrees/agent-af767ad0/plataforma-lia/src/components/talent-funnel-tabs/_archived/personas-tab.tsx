"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ExpandableAIPrompt } from "@/components/expandable-ai-prompt"
import { LIAIcon } from "@/components/ui/lia-icon"
import { PersonaCreationModal } from "@/components/modals/persona-creation-modal"
import { callOrchestratedPipelineChat } from "@/lib/api/kanban-assistant"
import {
  Plus, Building, Users, Target, TrendingUp, AlertCircle, AlertTriangle,
  CheckCircle, Clock, Settings, ArrowDown, ArrowRight,
  Briefcase, MapPin, DollarSign, Calendar, Edit, Eye,
  BarChart3, PieChart, Zap, Brain, Search, Filter,
  ExternalLink, Star, ArrowUpDown, Linkedin, Globe
} from "lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

// Mock de personas com dados mais ricos e realistas
const mockPersonas = [
  {
    id: 'persona-1',
    name: 'Dev Frontend Sênior',
    description: 'Desenvolvedor React/Vue.js com foco em performance e UX',
    avatar: '👨‍💻',
    status: 'active',
    createdAt: '2024-01-10',
    basedOnJob: 'Frontend Engineer - E-commerce Platform',

    metrics: {
      candidatesInBase: 23,
      monthlyMatches: 8,
      hires: 4,
      hiresThisMonth: 2,
      hiresLastMonth: 1,
      avgTimeToHire: 14,
      successRate: 87,
      costPerHire: 12500,
      roi: 340
    },

    criticalStatus: {
      isCritical: false,
      reason: null,
      urgency: 'normal'
    },

    recentHires: [
      { name: 'Ana Costa', hiredAt: '2024-02-18', salary: 15000, timeToHire: 12, source: 'LinkedIn' },
      { name: 'João Silva', hiredAt: '2024-02-05', salary: 14000, timeToHire: 16, source: 'Referral' }
    ],

    criteria: {
      skills: {
        required: ['React', 'TypeScript', 'CSS'],
        preferred: ['Next.js', 'Tailwind CSS', 'GraphQL'],
        weight: 40
      },
      experience: { min: 5, max: 10, weight: 25 },
      education: { required: ['Superior Completo'], preferred: ['Ciência da Computação'], weight: 10 },
      location: { preferred: ['São Paulo', 'Rio de Janeiro', 'Remoto'], weight: 15 },
      salary: { min: 10000, max: 18000, weight: 10 }
    }
  },
  {
    id: 'persona-2',
    name: 'Designer UX Estratégico',
    description: 'UX Designer com foco em estratégia de produto e pesquisa',
    avatar: '🎨',
    status: 'active',
    createdAt: '2024-01-15',
    basedOnJob: 'Senior UX Designer - Fintech Product',

    metrics: {
      candidatesInBase: 12,
      monthlyMatches: 3,
      hires: 2,
      hiresThisMonth: 1,
      hiresLastMonth: 0,
      avgTimeToHire: 11,
      successRate: 92,
      costPerHire: 15000,
      roi: 280
    },

    criticalStatus: {
      isCritical: true,
      reason: 'Baixo volume de candidatos na base (12)',
      urgency: 'medium'
    },

    recentHires: [
      { name: 'Carlos Mendes', hiredAt: '2024-02-12', salary: 18000, timeToHire: 9, source: 'Headhunting' }
    ],

    criteria: {
      skills: {
        required: ['User Research', 'Figma', 'Prototyping'],
        preferred: ['Design Systems', 'Usability Testing', 'Analytics'],
        weight: 45
      },
      experience: { min: 4, max: 8, weight: 25 },
      education: { required: ['Superior Completo'], preferred: ['Design', 'Psicologia'], weight: 15 },
      location: { preferred: ['São Paulo', 'Híbrido'], weight: 10 },
      salary: { min: 12000, max: 20000, weight: 5 }
    }
  },
  {
    id: 'persona-3',
    name: 'Data Scientist ML',
    description: 'Cientista de dados especializado em Machine Learning e AI',
    avatar: '🤖',
    status: 'active',
    createdAt: '2024-02-20',
    basedOnJob: 'Senior Data Scientist - AI Platform',

    metrics: {
      candidatesInBase: 6,
      monthlyMatches: 1,
      hires: 0,
      hiresThisMonth: 0,
      hiresLastMonth: 0,
      avgTimeToHire: 0,
      successRate: 0,
      costPerHire: 0,
      roi: 0
    },

    criticalStatus: {
      isCritical: true,
      reason: 'Persona nova sem contratações + base crítica (6 candidatos)',
      urgency: 'high'
    },

    recentHires: [],

    criteria: {
      skills: {
        required: ['Python', 'Machine Learning', 'TensorFlow'],
        preferred: ['MLOps', 'AWS', 'Spark'],
        weight: 50
      },
      experience: { min: 3, max: 8, weight: 25 },
      education: { required: ['Superior Completo'], preferred: ['Estatística', 'Matemática', 'Computação'], weight: 15 },
      location: { preferred: ['São Paulo', 'Remoto'], weight: 5 },
      salary: { min: 15000, max: 25000, weight: 5 }
    }
  },
  {
    id: 'persona-4',
    name: 'Tech Lead Full Stack',
    description: 'Líder técnico com experiência em arquitetura e gestão',
    avatar: '🚀',
    status: 'paused',
    createdAt: '2024-02-01',
    basedOnJob: 'Technical Lead - Platform Architecture',

    metrics: {
      candidatesInBase: 5,
      monthlyMatches: 0,
      hires: 1,
      hiresThisMonth: 0,
      hiresLastMonth: 0,
      avgTimeToHire: 21,
      successRate: 100,
      costPerHire: 25000,
      roi: 450
    },

    criticalStatus: {
      isCritical: true,
      reason: 'Status pausado + base crítica (5 candidatos)',
      urgency: 'high'
    },

    recentHires: [
      { name: 'Pedro Costa', hiredAt: '2024-01-25', salary: 25000, timeToHire: 21, source: 'Headhunting' }
    ],

    criteria: {
      skills: {
        required: ['Liderança Técnica', 'Arquitetura', 'Node.js'],
        preferred: ['AWS', 'Kubernetes', 'Microservices'],
        weight: 35
      },
      experience: { min: 7, max: 15, weight: 30 },
      education: { required: ['Superior Completo'], preferred: ['Engenharia', 'Ciência da Computação'], weight: 10 },
      location: { preferred: ['São Paulo'], weight: 15 },
      salary: { min: 18000, max: 30000, weight: 10 }
    }
  }
]

const personasAnalytics = {
  totalPersonas: 4,
  activePersonas: 3,
  criticalPersonas: 3,
  totalHires: 7,
  totalCandidatesInBase: 46,
  avgSuccessRate: 64.75,
  avgCostPerHire: 15625,
  totalROI: 267.5,
  monthlyTrends: {
    jan2024: { hires: 1, personas: 2, successRate: 95 },
    fev2024: { hires: 6, personas: 4, successRate: 89 }
  },
  criticalAlerts: [
    {
      type: 'low_base',
      personas: ['Designer UX Estratégico', 'Data Scientist ML', 'Tech Lead Full Stack'],
      message: '3 personas com base crítica (<15 candidatos)',
      urgency: 'high',
      action: 'expand_candidate_base'
    },
    {
      type: 'no_hires',
      personas: ['Data Scientist ML'],
      message: '1 persona sem contratações há 30+ dias',
      urgency: 'medium',
      action: 'review_criteria'
    },
    {
      type: 'paused_status',
      personas: ['Tech Lead Full Stack'],
      message: '1 persona pausada com demanda ativa',
      urgency: 'high',
      action: 'reactivate_persona'
    }
  ],
  opportunities: [
    {
      type: 'market_gap',
      message: 'Detectada alta demanda por DevOps Engineers (18 vagas sem persona)',
      impact: 'high',
      suggestedAction: 'Criar persona DevOps especializada',
      estimatedROI: '320%'
    },
    {
      type: 'salary_optimization',
      message: 'Persona Frontend pode reduzir custo por contratação em 15%',
      impact: 'medium',
      suggestedAction: 'Otimizar faixa salarial e critérios',
      estimatedSavings: 'R$ 2.500 por hire'
    }
  ],
  creationHistory: [
    {
      date: '2024-02-20',
      persona: 'Data Scientist ML',
      basedOnJob: 'Senior Data Scientist - AI Platform',
      reason: 'Nova linha de produto AI',
      creator: 'Ana Silva',
      initialCandidates: 6,
      performance: 'Abaixo do esperado - precisa ajustes'
    },
    {
      date: '2024-02-01',
      persona: 'Tech Lead Full Stack',
      basedOnJob: 'Technical Lead - Platform Architecture',
      reason: 'Expansão do time de arquitetura',
      creator: 'Carlos Mendes',
      initialCandidates: 8,
      performance: 'Boa taxa de conversão, mas pausada'
    },
    {
      date: '2024-01-15',
      persona: 'Designer UX Estratégico',
      basedOnJob: 'Senior UX Designer - Fintech Product',
      reason: 'Foco em experiência do usuário',
      creator: 'Maria Costa',
      initialCandidates: 15,
      performance: 'Excelente qualidade, baixo volume'
    },
    {
      date: '2024-01-10',
      persona: 'Dev Frontend Sênior',
      basedOnJob: 'Frontend Engineer - E-commerce Platform',
      reason: 'Demanda recorrente frontend',
      creator: 'Ana Silva',
      initialCandidates: 20,
      performance: 'Top performer - modelo de sucesso'
    }
  ],
  jobPersonaGaps: [
    {
      jobTitle: 'DevOps Engineer',
      openings: 18,
      hasPersona: false,
      urgency: 'high',
      estimatedTimeToCreate: '3 dias',
      potentialCandidates: 67
    },
    {
      jobTitle: 'Product Manager',
      openings: 12,
      hasPersona: false,
      urgency: 'medium',
      estimatedTimeToCreate: '5 dias',
      potentialCandidates: 34
    },
    {
      jobTitle: 'Mobile Developer',
      openings: 8,
      hasPersona: false,
      urgency: 'medium',
      estimatedTimeToCreate: '2 dias',
      potentialCandidates: 89
    },
    {
      jobTitle: 'QA Engineer',
      openings: 6,
      hasPersona: false,
      urgency: 'low',
      estimatedTimeToCreate: '4 dias',
      potentialCandidates: 23
    }
  ]
}

const marketAnalysis = {
  totalJobPostings: 156,
  jobsWithoutPersona: 44,
  recentJobs: [
    { title: 'DevOps Engineer AWS', company: 'Startup Fintech', postedAt: '2024-02-20', hasPersona: false, urgency: 'high' },
    { title: 'Mobile Developer React Native', company: 'E-commerce', postedAt: '2024-02-19', hasPersona: false, urgency: 'medium' },
    { title: 'Backend Engineer Go', company: 'SaaS Platform', postedAt: '2024-02-18', hasPersona: false, urgency: 'low' }
  ],
  trendingSkills: [
    { skill: 'Python', growth: '+15%', hasPersona: true },
    { skill: 'DevOps', growth: '+22%', hasPersona: false },
    { skill: 'React Native', growth: '+18%', hasPersona: false },
    { skill: 'Go', growth: '+12%', hasPersona: false }
  ]
}

export function PersonasTab() {
  const [personas] = useState(mockPersonas)
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'overview' | 'performance' | 'gaps'>('overview')
  const [showPersonaModal, setShowPersonaModal] = useState(false)
  const [selectedPersonaForModal, setSelectedPersonaForModal] = useState<any>(null)
  const [showCreationModal, setShowCreationModal] = useState(false)
  const [creationModalJob, setCreationModalJob] = useState<any>(null)
  const [liaMessages, setLiaMessages] = useState<any[]>([])
  const [isLiaLoading, setIsLiaLoading] = useState(false)
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([])

  const addLiaMessage = (content: string, type: 'response' | 'user' | 'error' = 'response') => {
    setLiaMessages(prev => [...prev, {
      id: `msg-${Date.now()}`,
      type,
      content,
      timestamp: Date.now()
    }])
  }

  // Mock persona details modal component
  const PersonaDetailsModal = ({ persona, isOpen, onClose }: any) => {
    if (!isOpen || !persona) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-900 rounded-md max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-4xl">{persona.avatar}</div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-950 dark:text-gray-50">{persona.name}</h2>
                  <p className="text-gray-800 dark:text-gray-200">{persona.description}</p>
                </div>
              </div>
              <Button variant="outline" onClick={onClose}>✕</Button>
            </div>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Performance Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle>📊 Performance Atual</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Taxa de Sucesso:</span>
                      <span className="font-semibold text-green-600">{persona.metrics.successRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Contratações:</span>
                      <span className="font-semibold">{persona.metrics.hires} total</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tempo Médio:</span>
                      <span className="font-semibold">{persona.metrics.avgTimeToHire} dias</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Custo por Hire:</span>
                      <span className="font-semibold">R$ {persona.metrics.costPerHire.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>ROI:</span>
                      <span className="font-semibold text-gray-700 dark:text-gray-300">{persona.metrics.roi}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent Hires */}
              <Card>
                <CardHeader>
                  <CardTitle>🎯 Últimas Contratações</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {persona.recentHires.map((hire: any, index: number) => (
                      <div key={index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                        <div className="font-medium">{hire.name}</div>
                        <div className="text-sm text-gray-800 dark:text-gray-200">
                          R$ {hire.salary.toLocaleString()} • {hire.timeToHire}d • {hire.source}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          {new Date(hire.hiredAt).toLocaleDateString('pt-BR')}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Skills Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>💡 Análise de Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Skills Obrigatórias:</label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {persona.criteria.skills.required.map((skill: string, index: number) => (
                          <Badge key={index} className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Skills Preferenciais:</label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {persona.criteria.skills.preferred.map((skill: string, index: number) => (
                          <Badge key={index} variant="outline">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Optimization Suggestions */}
              <Card>
                <CardHeader>
                  <CardTitle>🔧 Sugestões LIA</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                      <div className="font-medium text-gray-700 dark:text-gray-300">
                        💡 Otimização de Critérios
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        Expandir para incluir Vue.js aumentaria a base em 23%
                      </div>
                    </div>
                    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-md">
                      <div className="font-medium text-green-800 dark:text-green-300">
                        📈 Performance Insights
                      </div>
                      <div className="text-sm text-green-700 dark:text-green-200 mt-1">
                        Esta persona tem a melhor taxa de conversão (87%)
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="flex gap-3 mt-6 pt-6">
              <Button onClick={() => handleViewCandidates(persona.id)}>
                <Users className="w-4 h-4 mr-2" />
                Ver Candidatos ({persona.metrics.candidatesInBase})
              </Button>
              <Button variant="outline" onClick={() => handleEditPersona(persona.id)}>
                <Edit className="w-4 h-4 mr-2" />
                Editar Critérios
              </Button>
              <Button variant="outline">
                <BarChart3 className="w-4 h-4 mr-2" />
                Analytics Detalhados
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const handleUIAction = (action: string, params?: Record<string, unknown>) => {
    switch (action) {
      case 'view_persona':
        if (params?.persona_id) {
          handleViewDetails(params.persona_id as string)
        }
        break
      case 'view_candidates':
        if (params?.persona_id) {
          handleViewCandidates(params.persona_id as string)
        }
        break
      case 'edit_persona':
        if (params?.persona_id) {
          handleEditPersona(params.persona_id as string)
        }
        break
      case 'create_persona':
        setShowCreationModal(true)
        break
      default:
        console.log('UI action not implemented:', action, params)
    }
  }

  const handleAICommand = async (command: string) => {
    setIsLiaLoading(true)
    
    addLiaMessage(command, 'user')
    
    try {
      const response = await callOrchestratedPipelineChat({
        message: command,
        mode: 'persona',
        context: {
          personas: personas.map(p => ({
            id: p.id,
            name: p.name,
            description: p.description,
            avatar: p.avatar,
            status: p.status,
            basedOnJob: p.basedOnJob,
            metrics: p.metrics,
            criticalStatus: p.criticalStatus,
            recentHires: p.recentHires,
            criteria: p.criteria
          })),
          selectedPersona: selectedPersona,
          totalPersonas: personas.length,
          activePersonas: personas.filter(p => p.status === 'active').length,
          criticalPersonas: personas.filter(p => p.criticalStatus.isCritical).length,
          totalCandidates: personas.reduce((acc, p) => acc + p.metrics.candidatesInBase, 0),
          totalHires: personas.reduce((acc, p) => acc + p.metrics.hires, 0),
          analytics: personasAnalytics,
          jobPersonaGaps: personasAnalytics.jobPersonaGaps
        }
      })
      
      addLiaMessage(response.content)
      
      if (response.ui_action) {
        handleUIAction(response.ui_action, response.ui_action_params)
      }
      
      if (response.suggested_prompts?.length > 0) {
        setSuggestedPrompts(response.suggested_prompts)
      }
    } catch (error) {
      console.error('Error calling persona chat:', error)
      addLiaMessage('Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.', 'error')
    } finally {
      setIsLiaLoading(false)
    }
  }

  const handleLIAInsights = () => {
    alert(`🧠 Análise LIA - Personas\n\n` +
          `📊 Insights Detectados:\n\n` +
          `🏆 Top Performer: "Dev Frontend Sênior"\n` +
          `• 87% taxa de sucesso (melhor performance)\n` +
          `• R$ 12.500 custo médio (otimizado)\n` +
          `• Critérios bem calibrados\n\n` +
          `⚠️ Atenção Necessária: "Data Scientist ML"\n` +
          `• 0% conversão (sem contratações)\n` +
          `• Base muito restrita (6 candidatos)\n` +
          `• Critérios podem estar muito específicos\n\n` +
          `💡 Oportunidades:\n` +
          `• Replicar estratégia do Frontend para outras personas\n` +
          `• Criar persona DevOps (18 vagas descobertas)\n` +
          `• Expandir base de UX Designer (+20 candidatos)\n\n` +
          `🎯 Ação Recomendada: Otimizar personas críticas primeiro`)
  }

  // ✨ Enhanced handlers for persona actions
  const handleViewDetails = (personaId: string) => {
    const persona = personas.find(p => p.id === personaId)
    if (persona) {
      setSelectedPersonaForModal(persona)
      setShowPersonaModal(true)
    }
  }

  const handleViewCandidates = (personaId: string) => {
    const persona = personas.find(p => p.id === personaId)
    if (persona) {
      // Simulate filtering candidates by persona
      const filterData = {
        type: 'persona_filter',
        personaId: personaId,
        personaName: persona.name,
        expectedCount: persona.metrics.candidatesInBase
      }

      sessionStorage.setItem('candidateFilter', JSON.stringify(filterData))

      alert(`🎯 Filtro Aplicado\n\n` +
            `📋 Persona: ${persona.name}\n` +
            `👥 Candidatos: ${persona.metrics.candidatesInBase}\n` +
            `🔍 Critérios:\n` +
            `• Skills: ${persona.criteria.skills.required.join(', ')}\n` +
            `• Experiência: ${persona.criteria.experience.min}-${persona.criteria.experience.max} anos\n` +
            `• Localização: ${persona.criteria.location.preferred.join(', ')}\n\n` +
            `➡️ Navegando para aba Candidatos...`)

      // Simulate navigation to candidates tab
      setTimeout(() => {
        const candidatesTab = document.querySelector('[role="tab"][aria-label*="Candidatos"]') as HTMLElement
        if (candidatesTab) {
          candidatesTab.click()
        }
      }, 1000)
    }
  }

  const handleEditPersona = (personaId: string) => {
    const persona = personas.find(p => p.id === personaId)
    if (persona) {
      alert(`✏️ Editando Persona: ${persona.name}\n\n` +
            `🔧 Funcionalidades Disponíveis:\n\n` +
            `📋 Critérios Básicos:\n` +
            `• Skills obrigatórias e preferenciais\n` +
            `• Faixa de experiência\n` +
            `• Range salarial\n` +
            `• Localização preferencial\n\n` +
            `🎯 Configurações Avançadas:\n` +
            `• Peso de cada critério\n` +
            `• Sourcing automático\n` +
            `• Alertas inteligentes\n` +
            `• Threshold de matching\n\n` +
            `🧠 LIA Suggestions:\n` +
            `• Otimizações baseadas em performance\n` +
            `• Ajustes de mercado em tempo real\n` +
            `• Comparação com personas similares\n\n` +
            `💡 Esta funcionalidade abriria um formulário completo de edição`)
    }
  }

  const handleFixCriticalPersona = (personaId: string) => {
    const persona = personas.find(p => p.id === personaId)
    if (!persona) return

    alert(`🛠️ LIA Fix Automático\n\n` +
          `🎯 Persona: ${persona.name}\n` +
          `❌ Problemas Identificados:\n` +
          `${persona.criticalStatus.reason}\n\n` +
          `🔧 Correções Aplicadas:\n\n` +
          `📊 Ajuste de Critérios:\n` +
          `• Expandir skills preferenciais (+3 tecnologias)\n` +
          `• Flexibilizar experiência (±1 ano)\n` +
          `• Ajustar range salarial baseado no mercado\n\n` +
          `🔍 Sourcing Intensivo:\n` +
          `• Busca ativa no LinkedIn (+50 candidatos)\n` +
          `• Cross-referência com outras plataformas\n` +
          `• Sourcing de candidatos passivos\n\n` +
          `📧 Alertas Configurados:\n` +
          `• Notificação diária de novos matches\n` +
          `• Alert se base cair abaixo de 15 candidatos\n\n` +
          `⏱️ Timeline: 5-7 dias para normalização\n` +
          `🎯 Meta: 25+ candidatos na base`)

    // Simulate fixing the persona
    setTimeout(() => {
      alert(`✅ Persona "${persona.name}" otimizada!\n\n` +
            `📈 Resultados Preliminares:\n` +
            `• +12 candidatos identificados\n` +
            `• Base expandida para 18 candidatos\n` +
            `• Sourcing automático ativo\n\n` +
            `🔄 Acompanhe o progresso nos próximos dias`)
    }, 2000)
  }

  // ✨ Handlers para ações dos insights de personas
  const handlePersonaInsightAction = (actionType: string, personaId?: string) => {
    switch (actionType) {
      case 'expand_candidate_base':
        alert(`🎯 Expansão Automática da Base\n\n` +
              `📊 Análise: 3 personas com base crítica detectadas\n\n` +
              `🔍 Estratégias LIA Ativadas:\n\n` +
              `1️⃣ Sourcing Inteligente:\n` +
              `• Busca semântica expandida (+40% termos)\n` +
              `• Sourcing ativo LinkedIn Sales Navigator\n` +
              `• GitHub contributors analysis\n` +
              `• Stack Overflow profiles mining\n\n` +
              `2️⃣ Cross-Referência:\n` +
              `• Análise de candidatos similares\n` +
              `• Mapping de skills adjacentes\n` +
              `• Identificação de talent pools\n\n` +
              `3️⃣ Automação:\n` +
              `• Alerts automáticos para novos matches\n` +
              `• Scoring dinâmico atualizado\n` +
              `• Pipeline de sourcing contínuo\n\n` +
              `🎯 Meta: 30+ candidatos por persona em 7 dias\n` +
              `💰 Investimento: R$ 3.500 (sourcing premium)\n` +
              `📈 ROI estimado: 285%\n\n` +
              `🚀 Iniciando expansão em 3... 2... 1...`)

        setTimeout(() => {
          alert(`⚡ Expansão Iniciada!\n\n` +
                `🔍 Sourcing Ativo:\n` +
                `• 847 perfis LinkedIn identificados\n` +
                `• 234 GitHub profiles analisados\n` +
                `• 89 Stack Overflow contributors\n\n` +
                `📊 Primeiros Resultados:\n` +
                `• +23 candidatos qualificados\n` +
                `• Score médio: 94.2%\n` +
                `• 12 candidatos premium identificados\n\n` +
                `⏱️ Processo continuará por 72h`)
        }, 2000)
        break

      case 'optimize_frontend_persona':
        alert(`✨ Replicação de Success Pattern\n\n` +
              `🏆 Persona "Dev Frontend Sênior" Analysis:\n\n` +
              `📊 Success Metrics:\n` +
              `• 87% taxa de sucesso (melhor da empresa)\n` +
              `• R$ 12.500 custo por hire (25% abaixo da média)\n` +
              `• 14 dias time-to-hire (30% mais rápido)\n` +
              `• 340% ROI (excepcional)\n\n` +
              `🧬 DNA de Sucesso Identificado:\n\n` +
              `1️⃣ Critérios Otimizados:\n` +
              `• Skills ratio: 70% técnicas, 30% comportamentais\n` +
              `• Experience range: sweet spot 4-8 anos\n` +
              `• Salary positioning: 15% above market\n\n` +
              `2️⃣ Sourcing Strategy:\n` +
              `• Focus em passive candidates (80%)\n` +
              `• GitHub activity weightning\n` +
              `• Cultural fit pre-screening\n\n` +
              `🔄 Aplicando Pattern em:\n` +
              `• "Designer UX Estratégico" → +35% conversão esperada\n` +
              `• "Data Scientist ML" → +50% base expansion\n` +
              `• "Tech Lead Full Stack" → reativação otimizada\n\n` +
              `🎯 Impacto Total Estimado:\n` +
              `• +45% conversão geral\n` +
              `• -20% custo médio por hire\n` +
              `• -25% time-to-hire\n\n` +
              `🚀 Aplicar otimizações automaticamente?`)

        setTimeout(() => {
          if (confirm('Confirma aplicação das otimizações baseadas no success pattern?')) {
            alert(`🎉 Success Pattern Aplicado!\n\n` +
                  `✅ Personas Otimizadas:\n` +
                  `• Designer UX: critérios ajustados\n` +
                  `• Data Scientist: sourcing expandido\n` +
                  `• Tech Lead: reativado com novos parâmetros\n\n` +
                  `📈 Monitoring Ativo:\n` +
                  `• A/B testing automático\n` +
                  `• Performance tracking\n` +
                  `• Continuous optimization\n\n` +
                  `⏱️ Primeiros resultados em 48-72h`)
          }
        }, 1000)
        break

      case 'create_devops_persona':
        const devopsData = {
          title: 'DevOps Engineer Specialist',
          openings: 18,
          estimatedCandidates: 67,
          urgency: 'high',
          marketDemand: '+22%',
          avgSalary: 'R$ 16.000',
          timeToCreate: '3 dias'
        }

        alert(`🆕 Criação Automática: DevOps Specialist\n\n` +
              `📊 Market Intelligence:\n\n` +
              `🔥 Alta Demanda Detectada:\n` +
              `• ${devopsData.openings} vagas abertas sem persona\n` +
              `• ${devopsData.marketDemand} crescimento no trimestre\n` +
              `• ${devopsData.estimatedCandidates} candidatos identificados\n` +
              `• Urgência: ${devopsData.urgency}\n\n` +
              `🎯 Auto-Generated Criteria:\n\n` +
              `💡 Core Skills (LIA Analysis):\n` +
              `• AWS/Azure (obrigatório)\n` +
              `• Docker + Kubernetes (obrigatório)\n` +
              `• Terraform/Ansible (obrigatório)\n` +
              `• CI/CD pipelines (obrigatório)\n\n` +
              `⭐ Preferred Skills:\n` +
              `• Python/Go scripting\n` +
              `• Monitoring (Prometheus/Grafana)\n` +
              `• Security practices\n` +
              `• Cloud architecture\n\n` +
              `📋 Profile Parameters:\n` +
              `• Experiência: 3-8 anos\n` +
              `• Salário: R$ 12-20k (média: ${devopsData.avgSalary})\n` +
              `• Localização: São Paulo, Remoto\n` +
              `• Cultural fit: startup mindset\n\n` +
              `⏱️ Setup Timeline: ${devopsData.timeToCreate}\n` +
              `📈 ROI Estimado: 280% (baseado em similares)\n` +
              `🚀 Sourcing Automático: Ativo\n\n` +
              `✅ Confirma criação da persona?`)

        setTimeout(() => {
          if (confirm('Criar persona DevOps automaticamente?')) {
            alert(`⚡ Criando Persona DevOps...\n\n` +
                  `🔄 Processo Automático:\n` +
                  `• Analisando job descriptions... ✅\n` +
                  `• Calibrando critérios... ✅\n` +
                  `• Sourcing inicial... ⏳\n\n` +
                  `⏱️ Finalização em 30 segundos...`)

            setTimeout(() => {
              alert(`🎉 Persona "DevOps Engineer Specialist" Criada!\n\n` +
                    `📊 Setup Completo:\n\n` +
                    `✅ Critérios Calibrados:\n` +
                    `• 67 candidatos na base inicial\n` +
                    `• Score médio: 89.4%\n` +
                    `• 23 high-potential identificados\n\n` +
                    `🔍 Sourcing Ativo:\n` +
                    `• LinkedIn automation: ON\n` +
                    `• GitHub monitoring: ON\n` +
                    `• Stack Overflow tracking: ON\n\n` +
                    `📧 Alerts Configurados:\n` +
                    `• Novos matches diários\n` +
                    `• Performance tracking semanal\n` +
                    `• Market trends monitoring\n\n` +
                    `🎯 Primeira contratação estimada: 12-16 dias`)

              setCreationModalJob({
                title: 'DevOps Engineer Specialist',
                company: 'Auto-Generated',
                description: 'Persona criada automaticamente baseada em demanda detectada',
                requirements: ['AWS', 'Docker', 'Kubernetes', 'Terraform']
              })
              setShowCreationModal(true)
            }, 3000)
          }
        }, 1000)
        break

      case 'fix_critical_personas':
        alert(`🛠️ LIA Emergency Fix - Personas Críticas\n\n` +
              `🚨 Situação Crítica Detectada:\n\n` +
              `❌ Data Scientist ML:\n` +
              `• 0 contratações em 30 dias\n` +
              `• Apenas 6 candidatos na base\n` +
              `• Critérios muito restritivos\n` +
              `• Status: Crítico 🔴\n\n` +
              `⏸️ Tech Lead Full Stack:\n` +
              `• Status pausado incorretamente\n` +
              `• 5 candidatos high-quality\n` +
              `• Demanda ativa detectada\n` +
              `• Status: Reativação urgente 🟡\n\n` +
              `📉 UX Designer Estratégico:\n` +
              `• Base muito pequena (12 candidatos)\n` +
              `• Taxa de conversão alta (92%)\n` +
              `• Potencial de expansão\n` +
              `• Status: Expandir 🟠\n\n` +
              `🔧 Plano de Correção Automática:\n\n` +
              `1️⃣ Data Scientist ML:\n` +
              `• Flexibilizar experiência: 2-8 anos (era 3-8)\n` +
              `• Expandir skills: +MLOps, +Data Engineering\n` +
              `• Aumentar salary range: +15%\n` +
              `• Sourcing intensivo: GitHub + Kaggle\n\n` +
              `2️⃣ Tech Lead Full Stack:\n` +
              `• Reativar imediatamente\n` +
              `• Prioridade alta para sourcing\n` +
              `• Alert para novas oportunidades\n` +
              `• Review de critérios vs. demanda\n\n` +
              `3️⃣ UX Designer Estratégico:\n` +
              `• Sourcing premium: Behance + Dribbble\n` +
              `• Expandir localização: +Híbrido\n` +
              `• Cross-reference com Product Designers\n\n` +
              `⏱️ Timeline de Correção:\n` +
              `• Ajustes: Imediato\n` +
              `• Sourcing: 24-48h\n` +
              `• Resultados: 5-7 dias\n\n` +
              `🎯 Meta Final:\n` +
              `• Todas personas com 15+ candidatos\n` +
              `• Performance normalizada\n` +
              `• Monitoring ativo\n\n` +
              `🚀 Aplicar correções automaticamente?`)

        setTimeout(() => {
          if (confirm('Aplicar plano de correção automática?')) {
            alert(`⚡ Aplicando Correções...\n\n` +
                  `🔄 Processo em Andamento:\n\n` +
                  `✅ Data Scientist ML:\n` +
                  `• Critérios ajustados\n` +
                  `• Sourcing GitHub iniciado\n` +
                  `• +8 candidatos identificados\n\n` +
                  `✅ Tech Lead Full Stack:\n` +
                  `• Persona reativada\n` +
                  `• Prioridade alta configurada\n` +
                  `• Alert de demanda ativo\n\n` +
                  `✅ UX Designer:\n` +
                  `• Sourcing premium iniciado\n` +
                  `• +6 candidatos em análise\n` +
                  `• Behance/Dribbble connected\n\n` +
                  `📊 Progress Tracking:\n` +
                  `• Real-time monitoring ativo\n` +
                  `• Daily reports configurados\n` +
                  `• Auto-adjustment enabled\n\n` +
                  `⏱️ Update completo em 48-72h`)
          }
        }, 1000)
        break

      default:
        console.log('Ação de persona não implementada:', actionType)
    }
  }

  // ✨ Função para criar persona baseada em vaga
  const createPersonaFromJob = (jobGap: any) => {
    const personaData = {
      jobTitle: jobGap.jobTitle,
      openings: jobGap.openings,
      estimatedCandidates: jobGap.potentialCandidates,
      urgency: jobGap.urgency,
      timeToCreate: jobGap.estimatedTimeToCreate
    }

    alert(`🎯 LIA Smart Creation: ${personaData.jobTitle}\n\n` +
          `📊 Market Intelligence Analysis:\n\n` +
          `🔍 Demanda Detectada:\n` +
          `• ${personaData.openings} vagas abertas\n` +
          `• ${personaData.estimatedCandidates} candidatos potenciais\n` +
          `• Urgência: ${personaData.urgency}\n` +
          `• Timeline: ${personaData.timeToCreate}\n\n` +
          `🧠 LIA Pre-Analysis:\n\n` +
          `📋 Auto-Generated Profile:\n` +
          `• Skills extraídas de job descriptions\n` +
          `• Salary range baseado em market data\n` +
          `• Experience level otimizado\n` +
          `• Location preferences mapeadas\n\n` +
          `🎯 Smart Sourcing Strategy:\n` +
          `• Platform prioritization\n` +
          `• Search terms optimization\n` +
          `• Passive candidate identification\n` +
          `• Cultural fit assessment\n\n` +
          `⚡ Quick vs Custom Creation:\n\n` +
          `🚀 Quick (Auto): 5 min\n` +
          `• LIA creates persona automatically\n` +
          `• Based on job pattern analysis\n` +
          `• 85% accuracy rate\n\n` +
          `🔧 Custom (Manual): 15-30 min\n` +
          `• Full customization control\n` +
          `• Manual criteria adjustment\n` +
          `• 95% accuracy rate\n\n` +
          `Escolha: [Q]uick ou [C]ustom?`)

    // Simulate creation choice
    setTimeout(() => {
      setCreationModalJob({
        title: personaData.jobTitle,
        company: 'Market Analysis',
        description: `Persona baseada em análise de ${personaData.openings} vagas similares`,
        requirements: ['Skill Auto-Detected', 'Experience Auto-Calibrated']
      })
      setShowCreationModal(true)
    }, 1000)
  }

  return (
    <div className="space-y-4">
      {/* LIA Prompt - AI First */}
      <div className="flex flex-col lg:flex-row gap-2 mb-4">
        <div className="flex-1">
          <ExpandableAIPrompt
            selectedCandidates={[]}
            onCommand={handleAICommand}
            filteredCount={personas.length}
            totalCount={personas.length}
            candidateContext={null}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2 text-xs h-8 px-3 bg-green-50 hover:bg-green-100 border-green-200"
            onClick={handleLIAInsights}
            title="LIA analisa personas e sugere otimizações"
          >
            <LIAIcon size="sm" />
            LIA Insights
          </Button>
        </div>
      </div>

      {/* LIA Messages Display */}
      {liaMessages.length > 0 && (
        <Card className="bg-gradient-to-r from-purple-50 to-gray-100 dark:to-gray-800 dark:from-purple-900/20 dark:to-gray-100 dark:to-gray-800 border-purple-200 dark:border-purple-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <LIAIcon size="sm" />
                <span className="font-medium text-gray-950 dark:text-gray-50">Respostas da LIA</span>
                <Badge variant="outline" className="text-xs">{liaMessages.length}</Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={() => setLiaMessages([])}
              >
                Limpar
              </Button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {liaMessages.slice().reverse().map((msg) => (
                <div
                  key={msg.id}
                  className="bg-white dark:bg-gray-800 rounded-md p-3 border border-purple-100 dark:border-purple-800"
                >
                  <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                    {msg.content.split('**').map((part: string, i: number) => 
                      i % 2 === 1 ? <strong key={i}>{part}</strong> : part
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString('pt-BR')}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ✨ Insights Estratégicos da LIA - Movido para o topo */}
      <Card className="bg-gray-100 dark:bg-gray-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-gray-700 dark:bg-gray-300 rounded-md flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-gray-950 dark:text-gray-50">
                🎯 Insights Estratégicos de Personas
              </h3>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Análise inteligente de performance e oportunidades
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Performance Líder
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                Persona Frontend: 87% taxa de sucesso - replicar estratégia
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Aplicar critérios em outras personas
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handlePersonaInsightAction('optimize_frontend_persona')}
                >
                  <Zap className="w-3 h-3 mr-1" />
                  Otimizar
                </Button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Situação Crítica
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                3 personas com base crítica (&lt;15 candidatos) precisam atenção
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Expandir base e ajustar critérios
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handlePersonaInsightAction('fix_critical_personas')}
                >
                  <Target className="w-3 h-3 mr-1" />
                  Corrigir
                </Button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <Plus className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Gap Detectado
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                DevOps: 18 vagas abertas sem persona - alta demanda
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Criar persona especializada
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handlePersonaInsightAction('create_devops_persona')}
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Criar
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ✨ Dashboard Estratégico Expandido */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-gray-700 dark:text-gray-300" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Personas Ativas</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {personasAnalytics.activePersonas}/{personasAnalytics.totalPersonas}
                </p>
                <p className="text-xs text-gray-700 dark:text-gray-300">
                  {personasAnalytics.criticalPersonas} críticas
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-green-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Base Total</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {personasAnalytics.totalCandidatesInBase}
                </p>
                <p className="text-xs text-green-600">candidatos</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-purple-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Contratações</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {personasAnalytics.totalHires}
                </p>
                <p className="text-xs text-purple-600">este mês</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-orange-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Taxa Média</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {personasAnalytics.avgSuccessRate.toFixed(0)}%
                </p>
                <p className="text-xs text-orange-600">conversão</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-red-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Custo Médio</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  R$ {(personasAnalytics.avgCostPerHire / 1000).toFixed(0)}k
                </p>
                <p className="text-xs text-red-600">por hire</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ✨ Alertas Críticos */}
      {personasAnalytics.criticalAlerts.length > 0 && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-red-800 dark:text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              🚨 Alertas Críticos ({personasAnalytics.criticalAlerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {personasAnalytics.criticalAlerts.map((alert, index) => (
                <div key={index} className="bg-white dark:bg-gray-800 rounded-md p-3 border border-red-200">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-red-800 dark:text-red-300">
                      {alert.message}
                    </h4>
                    <Badge className={`text-xs ${
                      alert.urgency === 'high' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {alert.urgency === 'high' ? 'Alta' : 'Média'} Prioridade
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-800 dark:text-gray-200">
                      Personas afetadas: {alert.personas.join(', ')}
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-6 text-xs"
                      onClick={() => handlePersonaInsightAction(alert.action)}
                    >
                      <Zap className="w-3 h-3 mr-1" />
                      Resolver
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ✨ Gaps de Vagas vs Personas */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-orange-600" />
              🎯 Gaps: Vagas sem Personas ({personasAnalytics.jobPersonaGaps.length})
            </CardTitle>
            <Badge className="bg-orange-100 text-orange-800">
              {marketAnalysis.jobsWithoutPersona} vagas descobertas
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {personasAnalytics.jobPersonaGaps.map((gap, index) => (
              <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-950 dark:text-gray-50">
                    {gap.jobTitle}
                  </h4>
                  <Badge className={`text-xs ${
                    gap.urgency === 'high' ? 'bg-red-100 text-red-700' :
                    gap.urgency === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {gap.urgency === 'high' ? 'Urgente' :
                     gap.urgency === 'medium' ? 'Médio' : 'Baixo'}
                  </Badge>
                </div>

                <div className="space-y-2 text-sm text-gray-800 dark:text-gray-200">
                  <div className="flex justify-between">
                    <span>Vagas abertas:</span>
                    <span className="font-medium">{gap.openings}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Candidatos estimados:</span>
                    <span className="font-medium">{gap.potentialCandidates}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tempo de criação:</span>
                    <span className="font-medium">{gap.estimatedTimeToCreate}</span>
                  </div>
                </div>

                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 text-xs h-7"
                    onClick={() => createPersonaFromJob(gap)}
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    Criar Persona
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="text-xs h-7"
                    onClick={() => {
                      alert(`📊 Candidatos encontrados para ${gap.jobTitle}:\n\n• ${gap.potentialCandidates} candidatos identificados\n• Navegando para busca...`)
                    }}
                  >
                    <Eye className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ✨ Histórico de Criação de Personas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-700 dark:text-gray-300" />
            📅 Histórico de Criação de Personas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {personasAnalytics.creationHistory.map((history, index) => (
              <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-gray-950 dark:text-gray-50">
                      {history.persona}
                    </h4>
                    <Badge variant="outline" className="text-xs">
                      {new Date(history.date).toLocaleDateString('pt-BR')}
                    </Badge>
                  </div>

                  <p className="text-sm text-gray-800 dark:text-gray-200 mb-1">
                    Baseada em: {history.basedOnJob}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span>Por: {history.creator}</span>
                    <span>•</span>
                    <span>Base inicial: {history.initialCandidates} candidatos</span>
                    <span>•</span>
                    <span>Motivo: {history.reason}</span>
                  </div>

                  <div className="mt-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      history.performance.includes('Top performer') ? 'bg-green-100 text-green-700' :
                      history.performance.includes('Excelente') ? 'bg-blue-100 text-blue-700' :
                      history.performance.includes('Boa') ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      📊 {history.performance}
                    </span>
                  </div>
                </div>

                <div className="flex gap-1">
                  <Button variant="outline" size="sm" className="h-7 text-xs">
                    <Eye className="w-3 h-3 mr-1" />
                    Ver
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ✨ Oportunidades Estratégicas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            💡 Oportunidades Estratégicas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {personasAnalytics.opportunities.map((opportunity, index) => (
              <div key={index} className="bg-green-50 dark:bg-green-900/20 rounded-md p-4 border border-green-200">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-green-800 dark:text-green-300">
                    {opportunity.message}
                  </h4>
                  <Badge className="bg-green-100 text-green-800 text-xs">
                    {opportunity.impact} impacto
                  </Badge>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-sm text-green-700 dark:text-green-300">
                    💡 {opportunity.suggestedAction} • ROI: {opportunity.estimatedROI || opportunity.estimatedSavings}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-6 text-xs border-green-300 text-green-700 hover:bg-green-100"
                    onClick={() => {
                      alert(`🚀 Implementando: ${opportunity.suggestedAction}\n\nImpacto esperado: ${opportunity.estimatedROI || opportunity.estimatedSavings}`)
                    }}
                  >
                    <Zap className="w-3 h-3 mr-1" />
                    Implementar
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Controles */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
            Personas de Talentos ({personas.length})
          </h2>
          <p className="text-sm text-gray-800 dark:text-gray-200">
            Perfis ideais baseados em padrões de contratação bem-sucedidos
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Configurar
          </Button>

          <Button size="sm" onClick={() => setShowCreationModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Nova Persona
          </Button>
        </div>
      </div>

      {/* Lista de Personas */}
      <div className="space-y-4">
        {personas.map((persona) => (
          <Card key={persona.id} className="border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{persona.avatar}</div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <CardTitle className="text-lg">{persona.name}</CardTitle>
                      <Badge className={`text-xs px-2 py-1 ${
                        persona.status === 'active' ? 'bg-green-100 text-green-700' :
                        persona.status === 'paused' ? 'bg-gray-100 text-gray-800 dark:text-gray-200' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {persona.status === 'active' ? 'Ativa' :
                         persona.status === 'paused' ? 'Pausada' : 'Rascunho'}
                      </Badge>
                      {persona.criticalStatus.isCritical && (
                        <Badge className="text-xs bg-red-100 text-red-700 border-red-200">
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          Crítica
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-800 dark:text-gray-200">
                      {persona.description}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      Baseada em: {persona.basedOnJob}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-lg font-semibold text-green-600">
                    {persona.metrics.successRate}% conversão
                  </div>
                  <div className="text-xs text-gray-600">
                    {persona.metrics.candidatesInBase} candidatos na base
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">{persona.metrics.candidatesInBase}</p>
                  <p className="text-xs text-gray-600">Candidatos</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-green-600">{persona.metrics.hires}</p>
                  <p className="text-xs text-gray-600">Contratações</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-purple-600">{persona.metrics.avgTimeToHire}d</p>
                  <p className="text-xs text-gray-600">Tempo Médio</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold text-orange-600">R$ {(persona.metrics.costPerHire/1000).toFixed(0)}k</p>
                  <p className="text-xs text-gray-600">Custo/Hire</p>
                </div>
              </div>

              {persona.recentHires.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-2">
                    🎯 Últimas Contratações ({persona.recentHires.length})
                  </h4>
                  <div className="space-y-2">
                    {persona.recentHires.map((hire, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
                        <div>
                          <span className="text-sm font-medium">{hire.name}</span>
                          <span className="text-xs text-gray-600 ml-2">
                            • R$ {hire.salary.toLocaleString()} • {hire.timeToHire}d • {hire.source}
                          </span>
                        </div>
                        <span className="text-xs text-gray-600">
                          {new Date(hire.hiredAt).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50">Critérios da Persona:</h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">Skills Obrigatórias:</p>
                    <div className="flex flex-wrap gap-1">
                      {persona.criteria.skills.required.map((skill, index) => (
                        <Badge key={index} className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-1">Skills Preferenciais:</p>
                    <div className="flex flex-wrap gap-1">
                      {persona.criteria.skills.preferred.slice(0, 3).map((skill, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {persona.criteria.skills.preferred.length > 3 && (
                        <Badge variant="secondary" className="text-xs text-gray-600">
                          +{persona.criteria.skills.preferred.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex justify-between text-xs text-gray-800 dark:text-gray-200">
                  <span>Experiência: {persona.criteria.experience.min}-{persona.criteria.experience.max} anos</span>
                  <span>Salário: R$ {persona.criteria.salary.min.toLocaleString()}-{persona.criteria.salary.max.toLocaleString()}</span>
                </div>
              </div>

              {/* Ações - Enhanced with real functionality */}
              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleViewDetails(persona.id)}
                >
                  <Eye className="w-3 h-3 mr-2" />
                  Ver Detalhes
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleViewCandidates(persona.id)}
                >
                  <Users className="w-3 h-3 mr-2" />
                  Ver Candidatos ({persona.metrics.candidatesInBase})
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEditPersona(persona.id)}
                >
                  <Edit className="w-3 h-3 mr-2" />
                  Editar
                </Button>
                {persona.criticalStatus.isCritical && (
                  <Button
                    size="sm"
                    className="bg-red-600 hover:bg-red-700"
                    onClick={() => handleFixCriticalPersona(persona.id)}
                  >
                    <Zap className="w-3 h-3 mr-2" />
                    Corrigir
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Modals */}
      <PersonaDetailsModal
        persona={selectedPersonaForModal}
        isOpen={showPersonaModal}
        onClose={() => {
          setShowPersonaModal(false)
          setSelectedPersonaForModal(null)
        }}
      />

      <PersonaCreationModal
        isOpen={showCreationModal}
        onClose={() => {
          setShowCreationModal(false)
          setCreationModalJob(null)
        }}
        baseJob={creationModalJob}
        suggestedCandidates={creationModalJob?.estimatedCandidates}
      />

      {/* Empty State */}
      {personas.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Target className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
              Nenhuma persona criada
            </h3>
            <p className="text-gray-800 dark:text-gray-200 mb-4">
              Crie sua primeira persona para otimizar o recrutamento
            </p>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Criar Primeira Persona
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
