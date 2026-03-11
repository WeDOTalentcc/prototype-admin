"use client"

import React, { useState, useMemo, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Settings, Building, Zap, Users, Database, GitBranch,
  ChevronRight, Plus, Edit, Trash2, Save, X, Check, AlertTriangle,
  Globe, Link, Upload, Download, FileText, Mail, Phone, MapPin, LayoutDashboard,
  Calendar, Target, BarChart3, TrendingUp, UserCheck, Award,
  Key, Eye, EyeOff, Brain, MessageSquare, Clock,
  Copy, PlayCircle, PauseCircle, ArrowRight, CheckCircle, AlertCircle,
  Timer, Workflow, Filter, Search, Heart, Star, Briefcase, GraduationCap,
  Network, DollarSign, Layers, Move, ArrowUp, ArrowDown, MoreHorizontal,
  Send, Bell, Palette, Lightbulb, TrendingDown, Activity, RotateCcw,
  ChevronLeft, FastForward, SkipForward, RefreshCw, Zap as Lightning,
  MousePointer, Compass, HelpCircle, Rocket,
  ChevronDown, ChevronUp, Lock, Unlock, Circle
} from "lucide-react"
import { ProgressDashboard } from "@/components/settings/progress-dashboard"
import { CompanyTeamHub } from "@/components/settings/CompanyTeamHub"
import { RecruitmentHub } from "@/components/settings/RecruitmentHub"
import { CommunicationHub } from "@/components/settings/CommunicationHub"
import { GoalsPlanningHub } from "@/components/settings/GoalsPlanningHub"
import { GlobalSearchHub } from "@/components/settings/GlobalSearchHub"
import { TasksPage } from "@/components/pages/tasks-page"

import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

interface SettingsSubsection {
  id: string
  title: string
  description: string
  fields: string[]
}

interface SettingsSection {
  id: string
  title: string
  description: string
  icon: any
  status: 'completed' | 'incomplete' | 'pending'
  priority: 'high' | 'medium' | 'low'
  category: 'basic' | 'advanced' | 'integrations'
  estimatedTime: number
  dependencies?: string[]
  subsections?: SettingsSubsection[]
}

interface ProgressMetrics {
  overall: number
  byCategory: {
    basic: number
    advanced: number
    integrations: number
  }
  sectionsCompleted: number
  totalSections: number
  estimatedTimeRemaining: number
  criticalSectionsCompleted: number
  totalCriticalSections: number
}

interface SectionProgress {
  completed: number
  total: number
  percentage: number
}

const getDefaultSections = (): SettingsSection[] => [
  {
    id: 'company-team',
    title: 'Empresa & Equipe',
    description: 'Dados da empresa, usuários e permissões',
    icon: Building,
    status: 'incomplete',
    priority: 'high',
    category: 'basic',
    estimatedTime: 15,
    subsections: [
      { id: 'company-data', title: 'Dados da Empresa', description: 'Nome, logo, site', fields: ['company_name', 'cnpj', 'website', 'email', 'phone', 'logo'] },
      { id: 'departments', title: 'Departamentos', description: 'Estrutura organizacional', fields: ['departments', 'hierarchy'] },
      { id: 'tech-stack', title: 'Tech Stack', description: 'Stack tecnológico por categoria', fields: ['tech_stack', 'engineering_culture'] },
      { id: 'benefits', title: 'Benefícios', description: 'Pacote de benefícios da empresa', fields: ['benefits', 'eligibility'] },
      { id: 'users', title: 'Usuários', description: 'Recrutadores e permissões', fields: ['users', 'roles', 'permissions'] }
    ]
  },
  {
    id: 'recruitment',
    title: 'Recrutamento',
    description: 'Pipeline e elegibilidade',
    icon: Workflow,
    status: 'pending',
    priority: 'high',
    category: 'advanced',
    estimatedTime: 20,
    dependencies: ['company-team'],
    subsections: [
      { id: 'pipeline', title: 'Pipeline', description: 'Etapas do processo (configurado pelo CS)', fields: ['stages', 'flow'] },
      { id: 'screening', title: 'Perguntas de Elegibilidade', description: 'Perguntas iniciais via WhatsApp', fields: ['screening_questions'] },
      { id: 'hiring-policies', title: 'Políticas de Recrutamento', description: 'Regras de pipeline, agendamento e autonomia da LIA', fields: ['hiring_policy'] }
    ]
  },
  {
    id: 'communication',
    title: 'Comunicação & Alertas',
    description: 'Templates de email, alertas e preferências',
    icon: Mail,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 15,
    dependencies: ['company-team'],
    subsections: [
      { id: 'templates', title: 'Templates', description: 'Modelos de email', fields: ['email_templates'] },
      { id: 'signature', title: 'Assinatura', description: 'Assinatura padrão', fields: ['signature'] },
      { id: 'schedule', title: 'Horários LGPD', description: 'Janela de envio (8h-20h)', fields: ['sending_hours'] },
      { id: 'alerts', title: 'Alertas', description: 'Notificações e briefings da LIA', fields: ['alerts', 'notifications'] }
    ]
  },
  {
    id: 'goals-planning',
    title: 'Planejamento',
    description: 'Planejamento de contratações',
    icon: Target,
    status: 'completed',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 25,
    dependencies: ['recruitment'],
    subsections: [
      { id: 'workforce', title: 'Planejamento de Contratações', description: 'Planejamento anual', fields: ['workforce_plan'] }
    ]
  },
  {
    id: 'global-search',
    title: 'Busca Global',
    description: 'Configurações da Busca Global',
    icon: Globe,
    status: 'completed',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 5,
    subsections: [
      { id: 'limits', title: 'Limites', description: 'Limite de candidatos por busca', fields: ['search_limit'] },
      { id: 'options', title: 'Opções', description: 'Configurações de busca', fields: ['search_options'] },
      { id: 'costs', title: 'Custos', description: 'Tabela de custos da Busca Global', fields: ['credit_costs'] }
    ]
  },
  {
    id: 'control-panel',
    title: 'Painel de Controle',
    description: 'Tarefas, alertas e histórico de atividades',
    icon: LayoutDashboard,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 0,
    subsections: [
      { id: 'tasks', title: 'Tarefas', description: 'Gerenciar tarefas e alertas', fields: ['tasks'] },
      { id: 'activities', title: 'Histórico', description: 'Histórico de atividades', fields: ['activities'] }
    ]
  },
]

const settingsSections: SettingsSection[] = getDefaultSections()

const getCompletionBadgeColor = (percentage: number): string => {
  if (percentage >= 80) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
  if (percentage >= 50) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
  return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
}

export default function SettingsPageEnhanced() {
  const [activeSection, setActiveSection] = useState<string>('company-team')
  const [activeSubsection, setActiveSubsection] = useState<string>('')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['company-team']))
  const [users, setUsers] = useState<any[]>([])
  const [goals, setGoals] = useState<any[]>([])
  
  const [sectionCompletion, setSectionCompletion] = useState<Record<string, number>>({
    'company-team': 0,
    'recruitment': 0,
    'communication': 0,
    'goals-planning': 0,
    'global-search': 0,
    'control-panel': 0
  })

  const [subsectionCompletion, setSubsectionCompletion] = useState<Record<string, boolean>>({
    'company-data': false,
    'departments': false,
    'benefits': false,
    'users': false,
    'pipeline': false,
    'screening': false,
    'templates': false,
    'signature': false,
    'schedule': false,
    'alerts': false,
    'hiring-policies': false,
    'workforce': false,
    'limits': false,
    'options': false,
    'costs': false,
    'tasks': false,
    'activities': false
  })

  const [overallProgress, setOverallProgress] = useState<number>(0)
  const [progressLoading, setProgressLoading] = useState<boolean>(true)
  
  const [isCollapsed, setIsCollapsed] = useState(true)
  const [isLocked, setIsLocked] = useState(false)


  const [showTemplateSelector, setShowTemplateSelector] = useState(false)

  const [showProgressDashboard, setShowProgressDashboard] = useState(false)

  const [formData, setFormData] = useState<{[key: string]: any}>({
    company_name: 'WedoTalent Enterprise',
    cnpj: '12.345.678/0001-90',
    website: 'https://www.wedotalent.com',
    email: 'contato@wedotalent.com',
    mission: 'Revolucionar o recrutamento através da inteligência artificial.',
    vision: 'Ser a plataforma líder em recrutamento inteligente no Brasil.'
  })

  const fetchProgress = useCallback(async () => {
    try {
      setProgressLoading(true)
      const response = await fetch('/api/backend-proxy/settings/progress/')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.overall !== undefined) {
        setOverallProgress(data.overall)
      }
      
      if (data.sections) {
        setSectionCompletion(prev => ({
          ...prev,
          'company-team': data.sections['company-team'] ?? prev['company-team'],
          'recruitment': data.sections['recruitment'] ?? prev['recruitment'],
          'communication': data.sections['communication'] ?? prev['communication'],
          'hiring-policies': data.sections['hiring-policies'] ?? prev['hiring-policies'],
          'goals-planning': data.sections['goals-planning'] ?? prev['goals-planning'],
          'global-search': data.sections['global-search'] ?? prev['global-search'],
          'control-panel': data.sections['control-panel'] ?? prev['control-panel']
        }))
      }
      
      if (data.subsections) {
        setSubsectionCompletion(prev => ({
          ...prev,
          ...data.subsections
        }))
      }
    } catch (error) {
      console.error('Failed to fetch progress from backend:', error)
    } finally {
      setProgressLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProgress()
  }, [])

  const handleSectionCompletionUpdate = useCallback((sectionId: string, completion: number) => {
    setSectionCompletion(prev => ({ ...prev, [sectionId]: completion }))
  }, [])

  const progressMetrics = useMemo<ProgressMetrics>(() => {
    const completedSections = settingsSections.filter(s => s.status === 'completed')
    const basicSections = settingsSections.filter(s => s.category === 'basic')
    const advancedSections = settingsSections.filter(s => s.category === 'advanced')
    const integrationSections = settingsSections.filter(s => s.category === 'integrations')

    const basicCompleted = basicSections.filter(s => s.status === 'completed').length
    const advancedCompleted = advancedSections.filter(s => s.status === 'completed').length
    const integrationsCompleted = integrationSections.filter(s => s.status === 'completed').length

    const criticalSections = settingsSections.filter(s => s.priority === 'high')
    const criticalCompleted = criticalSections.filter(s => s.status === 'completed')

    const estimatedTimeRemaining = settingsSections
      .filter(s => s.status !== 'completed')
      .reduce((acc, section) => acc + section.estimatedTime, 0)

    return {
      overall: overallProgress,
      byCategory: {
        basic: basicSections.length > 0 ? (basicCompleted / basicSections.length) * 100 : 0,
        advanced: advancedSections.length > 0 ? (advancedCompleted / advancedSections.length) * 100 : 0,
        integrations: integrationSections.length > 0 ? (integrationsCompleted / integrationSections.length) * 100 : 0
      },
      sectionsCompleted: completedSections.length,
      totalSections: settingsSections.length,
      estimatedTimeRemaining,
      criticalSectionsCompleted: criticalCompleted.length,
      totalCriticalSections: criticalSections.length
    }
  }, [overallProgress])

  const statusColors = {
    completed: badgeStyles.success,
    incomplete: badgeStyles.error,
    pending: badgeStyles.warning
  }

  const statusLabels = {
    completed: 'Configurado',
    incomplete: 'Incompleto',
    pending: 'Pendente'
  }

  const priorityIcons = {
    high: AlertTriangle,
    medium: Clock,
    low: CheckCircle
  }

  const handleToggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  const handleSelectSubsection = (sectionId: string, subsectionId: string) => {
    setActiveSection(sectionId)
    setActiveSubsection(subsectionId)
  }


  const handleUserUpdate = (user: any) => {
    setUsers(prev => {
      const existingIndex = prev.findIndex(u => u.id === user.id)
      if (existingIndex >= 0) {
        const newUsers = [...prev]
        newUsers[existingIndex] = user
        return newUsers
      } else {
        return [...prev, user]
      }
    })
  }

  const handleGoalUpdate = (userId: string, userGoals: any) => {
    setGoals(prev => ({
      ...prev,
      [userId]: userGoals
    }))
    setUsers(prev => prev.map(user =>
      user.id === userId ? { ...user, goals: userGoals } : user
    ))
  }

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'company-team':
        return (
          <CompanyTeamHub
            activeSubsection={activeSubsection}
            onUserUpdate={handleUserUpdate}
            onGoalUpdate={handleGoalUpdate}
          />
        )
      case 'recruitment':
        return (
          <RecruitmentHub
            activeSubsection={activeSubsection}
          />
        )
      case 'communication':
        return (
          <CommunicationHub
            activeSubsection={activeSubsection}
          />
        )
      case 'goals-planning':
        return (
          <GoalsPlanningHub
            users={users}
            onGoalUpdate={handleGoalUpdate}
            activeSubsection={activeSubsection}
          />
        )
      case 'global-search':
        return (
          <GlobalSearchHub
            activeSubsection={activeSubsection}
          />
        )
      case 'control-panel':
        return <TasksPage />
      default:
        return (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Settings className="w-8 h-8 text-gray-800" />
            </div>
            <h3 className={`${textStyles.subtitle} dark:text-gray-50 mb-2`}>
              Selecione uma seção
            </h3>
            <p className={`${textStyles.description} dark:text-gray-500`}>
              Escolha uma das opções no menu lateral
            </p>
          </div>
        )
    }
  }

  const shouldShowContent = !isCollapsed || isLocked

  return (
    <>
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
      <aside 
        className={`
          ${isCollapsed && !isLocked ? 'w-16' : 'w-64'}
          transition-all duration-200
          flex-shrink-0
        `}
        onMouseEnter={() => !isLocked && setIsCollapsed(false)}
        onMouseLeave={() => !isLocked && setIsCollapsed(true)}
      >
        <Card className="h-full m-3 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 backdrop-blur-sm rounded-md overflow-hidden flex flex-col">
          <div className={`p-4 border-b border-gray-200 dark:border-gray-700 ${isCollapsed && !isLocked ? 'px-2' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md flex items-center justify-center flex-shrink-0">
                <Settings className="w-5 h-5" />
              </div>
              {shouldShowContent && (
                <div className="flex-1 min-w-0">
                  <h1 className={`${textStyles.sidebarTitle} leading-tight`}>
                    Configurações
                  </h1>
                  <p className={`${textStyles.sidebarItem} leading-tight`}>
                    Admin WedoTalent
                  </p>
                </div>
              )}
              {shouldShowContent && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsLocked(!isLocked)}
                  className="h-6 w-6 p-0 flex-shrink-0"
                  title={isLocked ? "Desbloquear menu" : "Bloquear menu expandido"}
                >
                  {isLocked ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                </Button>
              )}
            </div>

            {shouldShowContent && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`${textStyles.labelSmall} tracking-tight uppercase`}>
                    Progresso do Setup
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={textStyles.metricSmall}>
                      {Math.round(progressMetrics.overall)}%
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowProgressDashboard(true)}
                      className="h-5 w-5 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      title="Ver Dashboard Detalhado"
                    >
                      <BarChart3 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-3 cursor-pointer"
                     onClick={() => setShowProgressDashboard(true)}
                     title="Clique para ver detalhes">
                  <div
                    className="bg-gray-900 dark:bg-gray-50 h-1.5 rounded-full transition-all duration-500"
                    style={{width: `${progressMetrics.overall}%`}}
                  />
                </div>

              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-3">
            <nav className="space-y-2">
              {settingsSections.map((section) => {
                const IconComponent = section.icon
                const PriorityIcon = priorityIcons[section.priority]
                const isExpanded = expandedSections.has(section.id)
                const isActive = activeSection === section.id

                return (
                  <div key={section.id}>
                    <button
                      onClick={() => {
                        setActiveSection(section.id)
                        setActiveSubsection('')
                        if (section.subsections && section.subsections.length > 0) {
                          handleToggleSection(section.id)
                        }
                      }}
                      className={`w-full flex items-center gap-2 p-2.5 rounded-md text-left transition-colors ${
                        isActive && !activeSubsection
                          ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-50'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-700/50 text-gray-700 dark:text-gray-300'
                      } ${isCollapsed && !isLocked ? 'justify-center' : ''}`}
                      title={isCollapsed && !isLocked ? section.title : ''}
                    >
                      <IconComponent className="w-4 h-4 flex-shrink-0" />
                      {shouldShowContent && (
                        <>
                          <div className="flex-1 min-w-0">
                            <div className={`${textStyles.sidebarItem} leading-tight`}>
                              {section.title}
                            </div>
                            <div className={`${textStyles.description} truncate leading-tight`}>
                              {section.description}
                            </div>
                          </div>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <Badge
                              variant="outline"
                              className={`text-[10px] px-1.5 py-0.5 ${getCompletionBadgeColor(sectionCompletion[section.id] || 0)} border-0 rounded-full font-medium`}
                            >
                              {sectionCompletion[section.id] || 0}%
                            </Badge>
                          </div>
                        </>
                      )}
                    </button>

                    {shouldShowContent && isExpanded && section.subsections && (
                      <div className="ml-6 mt-1 space-y-1 border-l-2 border-gray-200 dark:border-gray-700 pl-2">
                        {section.subsections.map((subsection) => {
                          const isComplete = subsectionCompletion[subsection.id] ?? false
                          return (
                            <button
                              key={subsection.id}
                              onClick={() => handleSelectSubsection(section.id, subsection.id)}
                              className={`w-full text-left px-2 py-1.5 rounded-md transition-colors ${
                                activeSubsection === subsection.id
                                  ? 'bg-gray-100 dark:bg-gray-700'
                                  : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                              }`}
                            >
                              <div className="flex items-center gap-1.5">
                                {isComplete ? (
                                  <Check className="w-3 h-3 text-green-600 dark:text-green-400 flex-shrink-0" />
                                ) : (
                                  <Circle className="w-2.5 h-2.5 fill-amber-500 text-amber-500 flex-shrink-0" />
                                )}
                                <span className={activeSubsection === subsection.id ? textStyles.sidebarItemActive : textStyles.sidebarItem}>
                                  {subsection.title}
                                </span>
                              </div>
                              <div className={`${textStyles.description} truncate leading-tight ml-4`}>{subsection.description}</div>
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </nav>
          </div>
        </Card>
      </aside>

        <div className="flex-1 flex flex-col">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h2 className={`${textStyles.h3} mb-1`}>
                  {settingsSections.find(s => s.id === activeSection)?.title}
                  {activeSubsection && settingsSections.find(s => s.id === activeSection)?.subsections?.find(sub => sub.id === activeSubsection) && (
                    <span className="text-gray-600 dark:text-gray-400 font-normal"> / {settingsSections.find(s => s.id === activeSection)?.subsections?.find(sub => sub.id === activeSubsection)?.title}</span>
                  )}
                </h2>
                <p className={textStyles.description}>
                  {activeSubsection
                    ? settingsSections.find(s => s.id === activeSection)?.subsections?.find(sub => sub.id === activeSubsection)?.description
                    : settingsSections.find(s => s.id === activeSection)?.description
                  }
                </p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {renderSectionContent()}
          </div>
        </div>
      </div>


      {showProgressDashboard && (
        <ProgressDashboard
          sections={settingsSections}
          onClose={() => setShowProgressDashboard(false)}
          onSectionSelect={(sectionId) => {
            setActiveSection(sectionId)
            setShowProgressDashboard(false)
          }}
        />
      )}
    </>
  )
}
