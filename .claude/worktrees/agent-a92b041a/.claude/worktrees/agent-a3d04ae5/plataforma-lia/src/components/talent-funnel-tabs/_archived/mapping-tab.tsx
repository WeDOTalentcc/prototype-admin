"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ExpandableAIPrompt } from "@/components/expandable-ai-prompt"
import { LIAIcon } from "@/components/ui/lia-icon"
import { callOrchestratedPipelineChat } from "@/lib/api/kanban-assistant"
import {
  Plus, Building, Users, Target, TrendingUp, AlertCircle,
  CheckCircle, Clock, Settings, ArrowDown, ArrowRight,
  Briefcase, MapPin, DollarSign, Calendar, Edit, Eye,
  BarChart3, PieChart, Zap, Brain, Search, Filter,
  ExternalLink, Star, ArrowUpDown, Linkedin, Globe, FileText
} from "lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

// Mock data para empresas mapeadas
const mappedCompanies = [
  {
    id: 'company-1',
    name: 'Nubank',
    industry: 'Fintech',
    size: '5000+',
    location: 'São Paulo, SP',
    website: 'nubank.com.br',
    linkedin: 'https://linkedin.com/company/nubank',
    mappedAt: '2024-02-15',
    lastUpdate: '2024-02-20',
    status: 'active',
    priority: 'high',
    departments: [
      {
        name: 'Tecnologia',
        headCount: 1200,
        avgSalary: 18000,
        topTalents: [
          { name: 'João Silva', role: 'Principal Engineer', linkedin: 'joao-silva', experience: '8 anos', skills: ['Scala', 'Kafka', 'AWS'] },
          { name: 'Maria Costa', role: 'Staff Engineer', linkedin: 'maria-costa', experience: '6 anos', skills: ['Python', 'ML', 'Data'] },
          { name: 'Pedro Santos', role: 'Tech Lead', linkedin: 'pedro-santos', experience: '7 anos', skills: ['React', 'Node.js', 'GraphQL'] }
        ],
        openings: [
          { role: 'Senior Backend Engineer', salary: '15-22k', posted: '5d', urgency: 'high' },
          { role: 'Data Scientist', salary: '18-25k', posted: '12d', urgency: 'medium' }
        ]
      },
      {
        name: 'Produto & Design',
        headCount: 300,
        avgSalary: 14000,
        topTalents: [
          { name: 'Ana Lima', role: 'Principal Designer', linkedin: 'ana-lima', experience: '9 anos', skills: ['Product Design', 'Figma', 'User Research'] },
          { name: 'Carlos Mendes', role: 'Senior PM', linkedin: 'carlos-mendes', experience: '5 anos', skills: ['Product Strategy', 'Analytics', 'A/B Testing'] }
        ],
        openings: [
          { role: 'Senior Product Designer', salary: '12-18k', posted: '8d', urgency: 'medium' }
        ]
      }
    ],
    intelligence: {
      culture: 'Autonomia, inovação, dados',
      benefits: 'PLR, equity, flexibilidade',
      techStack: ['Scala', 'Kotlin', 'React', 'Kafka', 'AWS'],
      hiringTrends: 'Foco em seniores, processo rigoroso',
      avgProcessTime: '25-30 dias',
      notes: 'Forte cultura de engenharia, salários competitivos, difícil de tirar talentos'
    }
  },
  {
    id: 'company-2',
    name: 'iFood',
    industry: 'Marketplace',
    size: '3000+',
    location: 'São Paulo, SP',
    website: 'ifood.com.br',
    linkedin: 'https://linkedin.com/company/ifood',
    mappedAt: '2024-01-20',
    lastUpdate: '2024-02-18',
    status: 'active',
    priority: 'medium',
    departments: [
      {
        name: 'Tecnologia',
        headCount: 800,
        avgSalary: 16000,
        topTalents: [
          { name: 'Lucas Oliveira', role: 'Engineering Manager', linkedin: 'lucas-oliveira', experience: '10 anos', skills: ['Java', 'Microservices', 'Leadership'] },
          { name: 'Fernanda Rocha', role: 'Principal Mobile', linkedin: 'fernanda-rocha', experience: '8 anos', skills: ['iOS', 'Android', 'React Native'] }
        ],
        openings: [
          { role: 'Mobile Engineer', salary: '12-18k', posted: '15d', urgency: 'high' },
          { role: 'DevOps Engineer', salary: '14-20k', posted: '7d', urgency: 'high' }
        ]
      }
    ],
    intelligence: {
      culture: 'Agilidade, impacto, colaboração',
      benefits: 'Vale-refeição, plano saúde, home office',
      techStack: ['Java', 'Kotlin', 'React Native', 'AWS', 'Kubernetes'],
      hiringTrends: 'Crescimento acelerado, contratação ágil',
      avgProcessTime: '15-20 dias',
      notes: 'Processo mais rápido, ambiente dinâmico, oportunidades de crescimento'
    }
  },
  {
    id: 'company-3',
    name: 'Stone',
    industry: 'Fintech',
    size: '2000+',
    location: 'São Paulo, SP',
    website: 'stone.com.br',
    linkedin: 'https://linkedin.com/company/stone',
    mappedAt: '2024-02-01',
    lastUpdate: '2024-02-19',
    status: 'monitoring',
    priority: 'low',
    departments: [
      {
        name: 'Tecnologia',
        headCount: 600,
        avgSalary: 15000,
        topTalents: [
          { name: 'Roberto Lima', role: 'Tech Lead', linkedin: 'roberto-lima', experience: '6 anos', skills: ['Go', 'Microservices', 'Cloud'] }
        ],
        openings: [
          { role: 'Backend Engineer', salary: '10-16k', posted: '20d', urgency: 'low' }
        ]
      }
    ],
    intelligence: {
      culture: 'Transparência, meritocracia, inovação',
      benefits: 'Equity, flexibilidade, desenvolvimento',
      techStack: ['Go', 'Python', 'React', 'AWS'],
      hiringTrends: 'Foco em qualidade, processo criterioso',
      avgProcessTime: '20-25 dias',
      notes: 'Empresa em crescimento, boa para pegar talentos plenos/seniors'
    }
  }
]

interface LiaMessage {
  id: string
  type: 'response' | 'user' | 'error' | 'info'
  content: string
  timestamp: number
}

export function MappingTab() {
  const [companies] = useState(mappedCompanies)
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [showCompanyModal, setShowCompanyModal] = useState(false)
  const [selectedCompanyForModal, setSelectedCompanyForModal] = useState<any>(null)
  const [expandedCompanies, setExpandedCompanies] = useState<Set<string>>(new Set(['company-1']))
  const [liaMessages, setLiaMessages] = useState<LiaMessage[]>([])
  const [isLiaLoading, setIsLiaLoading] = useState(false)
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([])

  // Mock company intelligence modal
  const CompanyIntelligenceModal = ({ company, isOpen, onClose }: any) => {
    if (!isOpen || !company) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-900 rounded-md max-w-5xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                  <Building className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-950 dark:text-gray-50">{company.name}</h2>
                  <p className="text-gray-800 dark:text-gray-200">{company.industry} • {company.size} funcionários</p>
                </div>
              </div>
              <Button variant="outline" onClick={onClose}>✕</Button>
            </div>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Company Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>🏢 Visão Geral</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Indústria:</span>
                      <span className="font-medium">{company.industry}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tamanho:</span>
                      <span className="font-medium">{company.size} funcionários</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Localização:</span>
                      <span className="font-medium">{company.location}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Última atualização:</span>
                      <span className="font-medium">{new Date(company.lastUpdate).toLocaleDateString('pt-BR')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Prioridade:</span>
                      <Badge className={company.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}>
                        {company.priority === 'high' ? 'Alta' : 'Média'}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Intelligence Data */}
              <Card>
                <CardHeader>
                  <CardTitle>🧠 Intelligence</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Cultura:</label>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{company.intelligence.culture}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Benefícios:</label>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{company.intelligence.benefits}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Tech Stack:</label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {company.intelligence.techStack.map((tech: string, index: number) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Tempo de Processo:</label>
                      <p className="text-sm text-gray-800 dark:text-gray-200">{company.intelligence.avgProcessTime}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Departments */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>🏛️ Departamentos ({company.departments.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {company.departments.map((dept: any, index: number) => (
                      <div key={index} className="bg-white dark:bg-gray-800 rounded-md p-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium text-gray-950 dark:text-gray-50">{dept.name}</h4>
                          <div className="flex items-center gap-4 text-sm text-gray-800 dark:text-gray-200">
                            <span>{dept.headCount} pessoas</span>
                            <span>R$ {dept.avgSalary.toLocaleString()} média</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                              🎯 Top Talentos ({dept.topTalents.length})
                            </h5>
                            <div className="space-y-2">
                              {dept.topTalents.map((talent: any, idx: number) => (
                                <div key={idx} className="p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                  <div className="font-medium text-sm">{talent.name}</div>
                                  <div className="text-xs text-gray-800 dark:text-gray-200">
                                    {talent.role} • {talent.experience}
                                  </div>
                                  <div className="flex flex-wrap gap-1 mt-1">
                                    {talent.skills.slice(0, 3).map((skill: string, skillIdx: number) => (
                                      <Badge key={skillIdx} variant="outline" className="text-xs">
                                        {skill}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div>
                            <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                              📢 Vagas Abertas ({dept.openings.length})
                            </h5>
                            <div className="space-y-2">
                              {dept.openings.map((opening: any, idx: number) => (
                                <div key={idx} className="p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                  <div className="font-medium text-sm">{opening.role}</div>
                                  <div className="text-xs text-gray-800 dark:text-gray-200">
                                    R$ {opening.salary} • {opening.posted} atrás
                                  </div>
                                  <Badge className={`text-xs mt-1 ${
                                    opening.urgency === 'high' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                                  }`}>
                                    {opening.urgency === 'high' ? 'Urgente' : 'Normal'}
                                  </Badge>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Intelligence Notes */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>📝 Notas de Intelligence</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-4">
                    <p className="text-sm text-gray-700 dark:text-gray-300">{company.intelligence.notes}</p>
                  </div>
                  <div className="mt-4">
                    <h5 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Tendências de Contratação:</h5>
                    <p className="text-sm text-gray-800 dark:text-gray-200">{company.intelligence.hiringTrends}</p>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="flex gap-3 mt-6 pt-6">
              <Button onClick={() => handleViewCandidatesByCompany(company.id, company.name)}>
                <Users className="w-4 h-4 mr-2" />
                Ver Candidatos desta Empresa
              </Button>
              <Button variant="outline" onClick={() => handleEditCompanyMapping(company.id)}>
                <Edit className="w-4 h-4 mr-2" />
                Editar Mapeamento
              </Button>
              <Button variant="outline" onClick={() => handleExportIntelligence(company.id)}>
                <FileText className="w-4 h-4 mr-2" />
                Exportar Intelligence
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const addLiaMessage = (content: string, type: 'response' | 'user' | 'error' = 'response') => {
    const newMessage: LiaMessage = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      content,
      timestamp: Date.now()
    }
    setLiaMessages(prev => [...prev, newMessage])
  }

  const handleUIAction = (action: string, params?: Record<string, unknown>) => {
    switch (action) {
      case 'view_company':
        if (params?.company_id) {
          handleViewCompanyIntelligence(params.company_id as string)
        }
        break
      case 'view_candidates':
        if (params?.company_id && params?.company_name) {
          handleViewCandidatesByCompany(params.company_id as string, params.company_name as string)
        }
        break
      case 'view_talents':
        if (params?.company_id) {
          const company = companies.find(c => c.id === params.company_id)
          if (company) {
            handleViewCompanyIntelligence(company.id)
          }
        }
        break
      case 'add_company':
        handleAddCompany()
        break
      default:
        console.log('UI action not implemented:', action, params)
    }
  }

  const handleAICommand = async (command: string, _action?: string) => {
    setIsLiaLoading(true)
    
    addLiaMessage(command, 'user')
    
    try {
      let totalTalents = 0
      let totalOpenings = 0
      let totalHeadcount = 0
      companies.forEach(company => {
        company.departments.forEach(dept => {
          totalTalents += dept.topTalents.length
          totalOpenings += dept.openings.length
          totalHeadcount += dept.headCount
        })
      })

      const response = await callOrchestratedPipelineChat({
        message: command,
        mode: 'mapping',
        context: {
          companies: companies.map(c => ({
            id: c.id,
            name: c.name,
            industry: c.industry,
            location: c.location,
            size: c.size,
            status: c.status,
            priority: c.priority,
            departments: c.departments.map(d => ({
              name: d.name,
              headCount: d.headCount,
              topTalentsCount: d.topTalents.length,
              openingsCount: d.openings.length,
              avgSalary: d.avgSalary
            })),
            intelligence: c.intelligence,
            lastUpdate: c.lastUpdate,
            mappedAt: c.mappedAt
          })),
          selectedCompany: selectedCompany,
          expandedCompanies: Array.from(expandedCompanies),
          totalCompanies: companies.length,
          highPriorityCompanies: companies.filter(c => c.priority === 'high').length,
          totalTalents,
          totalOpenings,
          totalHeadcount,
          industries: [...new Set(companies.map(c => c.industry))],
          locations: [...new Set(companies.map(c => c.location))]
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
      console.error('Error calling mapping chat:', error)
      addLiaMessage('Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente.', 'error')
    } finally {
      setIsLiaLoading(false)
    }
  }

  const handleLIAInsights = () => {
    alert(`🧠 Análise LIA - Mapeamento\n\n` +
          `📊 Intelligence Detectada:\n\n` +
          `🎯 Empresas Prioritárias:\n` +
          `• Nubank: 23 candidatos potenciais identificados\n` +
          `• iFood: 18 vagas abertas, alta urgência\n` +
          `• Stone: Expansão de 40% no time tech\n\n` +
          `🔍 Gaps de Mercado:\n` +
          `• DevOps: 67% das empresas contratando\n` +
          `• Data Science: Salários 15% acima da média\n` +
          `• Mobile: React Native em alta demanda\n\n` +
          `💡 Oportunidades:\n` +
          `• 156 candidatos de target companies identificados\n` +
          `• 23 movimentações recentes detectadas\n` +
          `• 12 empresas com processo de contratação lento\n\n` +
          `🎯 Ação Recomendada: Focar em sourcing ativo da Nubank`)
  }

  // Enhanced handlers for mapping actions
  const handleViewCandidatesByCompany = (companyId: string, companyName: string) => {
    // Simulate filtering candidates by company
    const filterData = {
      type: 'company_filter',
      companyId: companyId,
      companyName: companyName,
      expectedCount: Math.floor(Math.random() * 50) + 10 // Mock count
    }

    sessionStorage.setItem('candidateFilter', JSON.stringify(filterData))

    alert(`🎯 Filtro de Empresa Aplicado\n\n` +
          `🏢 Empresa: ${companyName}\n` +
          `👥 Candidatos encontrados: ${filterData.expectedCount}\n\n` +
          `🔍 Critérios de Busca:\n` +
          `• Candidatos atuais ou ex-funcionários\n` +
          `• Skills alinhadas com tech stack\n` +
          `• Localização compatível\n` +
          `• Nível sênior similar\n\n` +
          `📊 Breakdown:\n` +
          `• Atuais funcionários: ${Math.floor(filterData.expectedCount * 0.3)}\n` +
          `• Ex-funcionários: ${Math.floor(filterData.expectedCount * 0.7)}\n` +
          `• Candidatos passivos: ${Math.floor(filterData.expectedCount * 0.6)}\n` +
          `• Candidatos ativos: ${Math.floor(filterData.expectedCount * 0.4)}\n\n` +
          `➡️ Navegando para aba Candidatos...`)

    // Navigate to candidates tab
    setTimeout(() => {
      const candidatesTab = document.querySelector('[role="tab"][aria-label*="Candidatos"]') as HTMLElement
      if (candidatesTab) {
        candidatesTab.click()
      }
    }, 1500)
  }

  const handleAnalyzeCompany = (companyId: string) => {
    const company = companies.find(c => c.id === companyId)
    if (company) {
      setSelectedCompanyForModal(company)
      setShowCompanyModal(true)
    }
  }

  const handleEditCompanyMapping = (companyId: string) => {
    const company = companies.find(c => c.id === companyId)
    if (company) {
      alert(`✏️ Editando Mapeamento: ${company.name}\n\n` +
            `🔧 Funcionalidades Disponíveis:\n\n` +
            `🏢 Dados da Empresa:\n` +
            `• Informações básicas (size, industry, location)\n` +
            `• Links e contatos\n` +
            `• Status e prioridade\n\n` +
            `🏛️ Departamentos:\n` +
            `• Adicionar/editar departamentos\n` +
            `• Headcount e salary ranges\n` +
            `• Estrutura organizacional\n\n` +
            `👥 Talentos Mapeados:\n` +
            `• Adicionar key people\n` +
            `• Skills e experiência\n` +
            `• Links LinkedIn\n` +
            `• Notas de relacionamento\n\n` +
            `📢 Vagas Abertas:\n` +
            `• Tracking de job postings\n` +
            `• Salary ranges\n` +
            `• Urgência e timeline\n\n` +
            `🧠 Intelligence:\n` +
            `• Cultura e valores\n` +
            `• Tech stack\n` +
            `• Processo de hiring\n` +
            `• Competitividade salarial\n\n` +
            `💡 Esta funcionalidade abriria um formulário completo de edição`)
    }
  }

  const handleExportIntelligence = (companyId: string) => {
    const company = companies.find(c => c.id === companyId)
    if (company) {
      alert(`📊 Exportando Intelligence: ${company.name}\n\n` +
            `📋 Relatório Completo Gerado:\n\n` +
            `📈 Executive Summary:\n` +
            `• ${company.departments.length} departamentos mapeados\n` +
            `• ${company.departments.reduce((acc: number, dept: any) => acc + dept.topTalents.length, 0)} talentos identificados\n` +
            `• ${company.departments.reduce((acc: number, dept: any) => acc + dept.openings.length, 0)} vagas ativas\n` +
            `• Salary range: R$ ${Math.min(...company.departments.map((d: any) => d.avgSalary))}k - R$ ${Math.max(...company.departments.map((d: any) => d.avgSalary))}k\n\n` +
            `📊 Formatos Disponíveis:\n` +
            `• PDF Executive Report\n` +
            `• Excel Talent Database\n` +
            `• PowerPoint Presentation\n` +
            `• JSON Data Export\n\n` +
            `🎯 Includes:\n` +
            `• Org chart visual\n` +
            `• Talent heat map\n` +
            `• Competitive analysis\n` +
            `• Sourcing recommendations\n\n` +
            `💾 Relatório salvo em: Downloads/intelligence_${company.name.toLowerCase()}_${new Date().toISOString().split('T')[0]}.pdf`)
    }
  }

  const handleAddNewCompany = () => {
    alert(`🏢 Adicionar Nova Empresa\n\n` +
          `🔍 Métodos de Adição:\n\n` +
          `🌐 Busca Automática:\n` +
          `• Digite o nome da empresa\n` +
          `• LIA busca dados automaticamente\n` +
          `• LinkedIn, website, job boards\n` +
          `• Crunchbase integration\n\n` +
          `📋 Manual Input:\n` +
          `• Formulário completo\n` +
          `• Dados básicos obrigatórios\n` +
          `• Intelligence opcional\n\n` +
          `🤖 LIA Suggestions:\n` +
          `• Empresas similares aos seus targets\n` +
          `• Baseado em hiring patterns\n` +
          `• Market intelligence\n\n` +
          `📊 Bulk Import:\n` +
          `• Upload CSV/Excel\n` +
          `• Template disponível\n` +
          `• Validation automática\n\n` +
          `💡 Escolha: [A]utomática, [M]anual ou [B]ulk?`)
  }

  // Handlers for insight actions
  const handleMappingInsightAction = (actionType: string, data?: any) => {
    switch (actionType) {
      case 'expand_mapping':
        alert(`🚀 Expansão de Mapeamento Automática\n\n` +
              `📊 Análise de Mercado LIA:\n\n` +
              `🎯 Targets Identificados:\n` +
              `• 47 empresas similares aos seus targets\n` +
              `• 23 competitors diretos\n` +
              `• 15 empresas emergentes (high-growth)\n\n` +
              `🔍 Critérios de Seleção:\n` +
              `• Industry overlap: Fintech, SaaS, E-commerce\n` +
              `• Size range: 500-5000 funcionários\n` +
              `• Tech stack compatibility\n` +
              `• Geographic location match\n\n` +
              `🤖 Auto-Mapping Process:\n` +
              `• LinkedIn Company scraping\n` +
              `• Job postings analysis\n` +
              `• Salary benchmarking\n` +
              `• Tech stack identification\n\n` +
              `⏱️ Timeline: 24-48h para completion\n` +
              `💰 Investment: R$ 2.500 (data sources)\n` +
              `📈 ROI Estimado: 340% (baseado em sourcing efficiency)\n\n` +
              `🚀 Iniciar auto-mapping?`)
        break

      case 'competitive_analysis':
        alert(`🏆 Análise Competitiva Automática\n\n` +
              `📊 LIA Competitive Intelligence:\n\n` +
              `💰 Salary Benchmarking:\n` +
              `• Nubank: +15% above market average\n` +
              `• iFood: Market aligned, strong benefits\n` +
              `• Stone: Equity heavy, lower base\n` +
              `• Seu perfil: Competitive em seniors\n\n` +
              `🎯 Hiring Patterns:\n` +
              `• Nubank: Slow but thorough (30d avg)\n` +
              `• iFood: Fast hiring (15d avg)\n` +
              `• Stone: Selective, high bar\n` +
              `• Opportunity: Speed advantage\n\n` +
              `🧬 Tech Stack Overlap:\n` +
              `• React/Node.js: 89% overlap\n` +
              `• AWS/Cloud: 76% overlap\n` +
              `• Data/ML: 45% overlap\n` +
              `• Mobile: 34% overlap\n\n` +
              `🎪 Culture Differentiation:\n` +
              `• Autonomy: Your advantage\n` +
              `• Innovation: Competitive\n` +
              `• Work-life balance: Strong position\n\n` +
              `💡 Strategic Recommendations:\n` +
              `• Target Nubank's slow hiring process\n` +
              `• Emphasize speed and flexibility\n` +
              `• Leverage work-life balance\n` +
              `• Focus on mid-senior levels`)
        break

      case 'sourcing_opportunities':
        alert(`🎯 Oportunidades de Sourcing Identificadas\n\n` +
              `📈 LIA Market Analysis:\n\n` +
              `🔥 Hot Opportunities:\n\n` +
              `1️⃣ iFood Mobile Team:\n` +
              `• 12 eng. mobile sêniors\n` +
              `• Stack: React Native + native\n` +
              `• Salary gap: -20% vs. mercado\n` +
              `• Opportunity score: 9.2/10\n\n` +
              `2️⃣ Nubank Data Scientists:\n` +
              `• 18 data scientists\n` +
              `• Stack: Python, Scala, Spark\n` +
              `• Process muito longo (45d)\n` +
              `• Opportunity score: 8.7/10\n\n` +
              `3️⃣ Stone DevOps Team:\n` +
              `• 8 devops engineers\n` +
              `• Stack: AWS, Kubernetes\n` +
              `• Workload: Overworked\n` +
              `• Opportunity score: 8.9/10\n\n` +
              `🎪 Sourcing Strategy:\n` +
              `• Timing: Post-bonus season (Q1)\n` +
              `• Approach: Passive sourcing\n` +
              `• Value prop: Better work-life balance\n` +
              `• Channel: LinkedIn + referrals\n\n` +
              `🚀 Expected Results:\n` +
              `• 67 qualified candidates\n` +
              `• 23% response rate\n` +
              `• 15 interview-ready\n\n` +
              `💰 Investment: R$ 4.500\n` +
              `📊 ROI: 280% (based on hire cost)\n\n` +
              `🎯 Iniciar sourcing campaign?`)
        break

      default:
        console.log('Mapping insight action not implemented:', actionType)
    }
  }

  // Calcular totais
  const totals = companies.reduce((acc, company) => {
    const companyTalents = company.departments.reduce((sum, dept) => sum + dept.topTalents.length, 0)
    const companyOpenings = company.departments.reduce((sum, dept) => sum + dept.openings.length, 0)
    return {
      totalTalents: acc.totalTalents + companyTalents,
      totalOpenings: acc.totalOpenings + companyOpenings,
      avgSalary: acc.avgSalary + (company.departments.reduce((sum, dept) => sum + dept.avgSalary, 0) / company.departments.length)
    }
  }, { totalTalents: 0, totalOpenings: 0, avgSalary: 0 })

  const avgMarketSalary = Math.round(totals.avgSalary / companies.length)

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-700 border-green-200'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700 border-green-200'
      case 'monitoring': return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
      case 'paused': return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    }
  }

  const toggleCompany = (companyId: string) => {
    setExpandedCompanies(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(companyId)) {
        newExpanded.delete(companyId)
      } else {
        newExpanded.add(companyId)
      }
      return newExpanded
    })
  }

  return (
    <div className="space-y-4">
      {/* LIA Prompt - AI First */}
      <div className="flex flex-col lg:flex-row gap-2 mb-4">
        <div className="flex-1">
          <ExpandableAIPrompt
            selectedCandidates={[]}
            onCommand={handleAICommand}
            filteredCount={companies.length}
            totalCount={companies.length}
            candidateContext={null}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2 text-xs h-8 px-3 bg-green-50 hover:bg-green-100 border-green-200"
            onClick={handleLIAInsights}
            title="LIA analisa mapeamento e sugere ações"
          >
            <LIAIcon size="sm" />
            LIA Insights
          </Button>
        </div>
      </div>

      {/* LIA Messages Display */}
      {liaMessages.length > 0 && (
        <Card className="bg-gradient-to-r from-gray-100 dark:from-gray-800 to-green-50 dark:from-gray-100 dark:from-gray-800 dark:to-green-900/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <LIAIcon size="sm" />
                <h3 className="font-medium text-gray-950 dark:text-gray-50">
                  Respostas da LIA
                </h3>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-gray-500 hover:text-gray-800 dark:text-gray-200"
                onClick={() => setLiaMessages([])}
              >
                Limpar
              </Button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {liaMessages.map((msg) => (
                <div
                  key={msg.id}
                  className="bg-white dark:bg-gray-800 rounded-md p-3"
                >
                  <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
                    {msg.content.split('\n').map((line: string, idx: number) => {
                      const formattedLine = line
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      return (
                        <p
                          key={idx}
                          className={line.startsWith('•') || line.startsWith('   •') ? 'ml-2' : ''}
                          dangerouslySetInnerHTML={{ __html: formattedLine }}
                        />
                      )
                    })}
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString('pt-BR')}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ✨ Insights Estratégicos da LIA - At the top */}
      <Card className="bg-gray-100 dark:bg-gray-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-gray-700 dark:bg-gray-300 rounded-md flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-gray-950 dark:text-gray-50">
                🗺️ Intelligence de Mercado
              </h3>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Análise competitiva e oportunidades de sourcing
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Expansion Ready
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                47 empresas similares identificadas para mapping
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Auto-mapping disponível
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handleMappingInsightAction('expand_mapping')}
                >
                  <Zap className="w-3 h-3 mr-1" />
                  Expandir
                </Button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Competitive Intel
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                Análise salarial: você está 12% competitivo vs. targets
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Benchmarking atualizado
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handleMappingInsightAction('competitive_analysis')}
                >
                  <BarChart3 className="w-3 h-3 mr-1" />
                  Analisar
                </Button>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-md p-3">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-orange-600" />
                <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                  Hot Sourcing
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200 mb-2">
                67 candidatos high-potential identificados
              </p>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                💡 Campaign ready
              </p>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-6 text-xs flex-1"
                  onClick={() => handleMappingInsightAction('sourcing_opportunities')}
                >
                  <Target className="w-3 h-3 mr-1" />
                  Executar
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dashboard com Métricas do Mercado */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-gray-700 dark:text-gray-300" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Empresas Mapeadas</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {companies.length}
                </p>
                <p className="text-xs text-gray-700 dark:text-gray-300">+2 este mês</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-green-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Talentos Mapeados</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {totals.totalTalents}
                </p>
                <p className="text-xs text-green-600">Para abordagem direta</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-purple-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Vagas Competitor</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  {totals.totalOpenings}
                </p>
                <p className="text-xs text-purple-600">Gaps de mercado</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-orange-600" />
              <div>
                <p className="text-sm text-gray-800 dark:text-gray-200">Salário Médio</p>
                <p className="text-xl font-semibold text-gray-950 dark:text-gray-50">
                  R$ {avgMarketSalary.toLocaleString()}
                </p>
                <p className="text-xs text-orange-600">Benchmark mercado</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Company Cards */}
      <div className="space-y-4">
        {companies.map((company) => (
          <Card key={company.id} className="border-l-4 border-l-gray-400 dark:border-l-gray-600">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => toggleCompany(company.id)}
                    className="text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    {expandedCompanies.has(company.id) ? (
                      <ArrowDown className="w-4 h-4" />
                    ) : (
                      <ArrowRight className="w-4 h-4" />
                    )}
                  </button>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <CardTitle className="text-lg">{company.name}</CardTitle>
                      <Badge className={`text-xs px-2 py-1 ${getPriorityColor(company.priority)}`}>
                        {company.priority === 'high' ? 'Alta Prioridade' :
                         company.priority === 'medium' ? 'Média Prioridade' : 'Baixa Prioridade'}
                      </Badge>
                      <Badge className={`text-xs px-2 py-1 ${getStatusColor(company.status)}`}>
                        {company.status === 'active' ? 'Monitoramento Ativo' :
                         company.status === 'monitoring' ? 'Observação' : 'Pausado'}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-800 dark:text-gray-200">
                      {company.industry} • {company.size} funcionários • {company.location}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-6 text-xs"
                        onClick={() => handleViewCandidatesByCompany(company.id, company.name)}
                        title={`Ver candidatos que trabalham/trabalharam na ${company.name}`}
                      >
                        <Users className="w-3 h-3 mr-1" />
                        Ver Candidatos
                      </Button>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <a
                        href={`https://${company.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-700 dark:text-gray-300 hover:text-gray-600 dark:hover:text-gray-400 transition-colors text-xs flex items-center gap-1"
                      >
                        <Globe className="w-3 h-3" />
                        {company.website}
                      </a>
                      <a
                        href={company.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-700 dark:text-gray-300 hover:text-gray-600 dark:hover:text-gray-400 transition-colors text-xs flex items-center gap-1"
                      >
                        <Linkedin className="w-3 h-3" />
                        LinkedIn
                      </a>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-lg font-semibold text-green-600">
                    {company.departments.reduce((sum, dept) => sum + dept.topTalents.length, 0)} talentos
                  </div>
                  <div className="text-xs text-gray-600">
                    Mapeado em {new Date(company.mappedAt).toLocaleDateString('pt-BR')}
                  </div>
                </div>
              </div>
            </CardHeader>

            {expandedCompanies.has(company.id) && (
              <CardContent>
                {/* Departamentos */}
                <div className="space-y-4">
                  {company.departments.map((dept, index) => (
                    <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-md p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-950 dark:text-gray-50">
                            {dept.name}
                          </h4>
                          <p className="text-xs text-gray-800 dark:text-gray-200">
                            {dept.headCount} funcionários • Salário médio: R$ {dept.avgSalary.toLocaleString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                            {dept.topTalents.length} talentos mapeados
                          </Badge>
                          <Badge className="bg-orange-100 text-orange-800">
                            {dept.openings.length} vagas abertas
                          </Badge>
                        </div>
                      </div>

                      {/* Top Talentos */}
                      {dept.topTalents.length > 0 && (
                        <div className="mb-4">
                          <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">
                            🎯 Talentos Prioritários:
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                            {dept.topTalents.map((talent, idx) => (
                              <div key={idx} className="bg-white dark:bg-gray-900 rounded p-3 border border-gray-200 dark:border-gray-600">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-medium text-sm">{talent.name}</span>
                                  <a
                                    href={`https://linkedin.com/in/${talent.linkedin}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-gray-700 dark:text-gray-300 hover:text-gray-600 dark:hover:text-gray-400"
                                  >
                                    <Linkedin className="w-3 h-3" />
                                  </a>
                                </div>
                                <p className="text-xs text-gray-600 mb-2">{talent.role}</p>
                                <p className="text-xs text-gray-600 mb-2">{talent.experience}</p>
                                <div className="flex flex-wrap gap-1">
                                  {talent.skills.slice(0, 3).map((skill, skillIdx) => (
                                    <Badge key={skillIdx} variant="outline" className="text-xs">
                                      {skill}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Vagas Abertas */}
                      {dept.openings.length > 0 && (
                        <div>
                          <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">
                            📋 Vagas Abertas ({dept.openings.length}):
                          </h5>
                          <div className="space-y-2">
                            {dept.openings.map((opening, idx) => (
                              <div key={idx} className="flex items-center justify-between p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                                <div>
                                  <span className="font-medium">{opening.role}</span>
                                  <span className="text-gray-600 ml-2">• {opening.salary}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline">{opening.posted}</Badge>
                                  <Badge className={`${
                                    opening.urgency === 'high' ? 'bg-red-100 text-red-700' :
                                    opening.urgency === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                    'bg-green-100 text-green-700'
                                  }`}>
                                    {opening.urgency === 'high' ? 'Urgente' :
                                     opening.urgency === 'medium' ? 'Médio' : 'Normal'}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Inteligência da Empresa */}
                <div className="mt-4 bg-gray-100 dark:bg-gray-800 rounded-md p-4">
                  <h4 className="font-medium text-gray-600 dark:text-gray-400 mb-3">
                    🧠 Inteligência da Empresa
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-700 dark:text-gray-300 font-medium">Cultura:</p>
                      <p className="text-gray-600 dark:text-gray-400">{company.intelligence.culture}</p>
                    </div>
                    <div>
                      <p className="text-gray-700 dark:text-gray-300 font-medium">Benefícios:</p>
                      <p className="text-gray-600 dark:text-gray-400">{company.intelligence.benefits}</p>
                    </div>
                    <div>
                      <p className="text-gray-700 dark:text-gray-300 font-medium">Stack Técnico:</p>
                      <p className="text-gray-600 dark:text-gray-400">{company.intelligence.techStack.join(', ')}</p>
                    </div>
                    <div>
                      <p className="text-gray-700 dark:text-gray-300 font-medium">Processo:</p>
                      <p className="text-gray-600 dark:text-gray-400">{company.intelligence.avgProcessTime}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-gray-700 dark:text-gray-300 font-medium">Observações:</p>
                      <p className="text-gray-600 dark:text-gray-400">{company.intelligence.notes}</p>
                    </div>
                  </div>
                </div>

                {/* Enhanced Actions */}
                <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewCandidatesByCompany(company.id, company.name)}
                  >
                    <Users className="w-3 h-3 mr-2" />
                    Ver Candidatos
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAnalyzeCompany(company.id)}
                  >
                    <Eye className="w-3 h-3 mr-2" />
                    Analisar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditCompanyMapping(company.id)}
                  >
                    <Edit className="w-3 h-3 mr-2" />
                    Editar
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(company.linkedin, '_blank')}
                  >
                    <ExternalLink className="w-3 h-3 mr-2" />
                    LinkedIn
                  </Button>
                </div>
              </CardContent>
            )}
          </Card>
        ))}
      </div>

      {/* Enhanced Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
            Empresas Mapeadas ({companies.length})
          </h2>
          <p className="text-sm text-gray-800 dark:text-gray-200">
            Intelligence competitiva e sourcing de talentos
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Configurar
          </Button>

          <Button size="sm" onClick={handleAddNewCompany}>
            <Plus className="w-4 h-4 mr-2" />
            Nova Empresa
          </Button>
        </div>
      </div>

      {/* Company Intelligence Modal */}
      <CompanyIntelligenceModal
        company={selectedCompanyForModal}
        isOpen={showCompanyModal}
        onClose={() => {
          setShowCompanyModal(false)
          setSelectedCompanyForModal(null)
        }}
      />

      {/* Empty State */}
      {companies.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Building className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
              Nenhuma empresa mapeada
            </h3>
            <p className="text-gray-800 dark:text-gray-200 mb-4">
              Comece mapeando empresas target para identificar talentos e oportunidades
            </p>
            <Button onClick={handleAddNewCompany}>
              <Plus className="w-4 h-4 mr-2" />
              Mapear Primeira Empresa
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
