"use client"

import React, { useState, useMemo, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Settings, Building, Zap, Users, Database, GitBranch,
  ChevronRight, Plus, Edit, Trash2, Save, X, Check, AlertTriangle,
  Globe, Link, Upload, Download, FileText, Mail, Phone, MapPin,
  Calendar, Target, BarChart3, TrendingUp, UserCheck, Award,
  Key, Eye, EyeOff, Brain, MessageSquare, Clock,
  Copy, PlayCircle, PauseCircle, CheckCircle, AlertCircle,
  Timer, Workflow, Filter, Search, Heart, Star, Briefcase, GraduationCap,
  Network, DollarSign, Layers, Move, ArrowUp, ArrowDown, MoreHorizontal,
  Send, Bell, Palette, Lightbulb, TrendingDown, Activity, RotateCcw,
  ChevronLeft, FastForward, SkipForward, RefreshCw, Zap as Lightning,
  MousePointer, Compass, HelpCircle, Rocket,
  ChevronDown, ChevronUp, Lock, Unlock, Circle, Plug
} from "lucide-react"
import dynamic from "next/dynamic"
import { LoadingFallback } from "@/components/ui/loading"
const CompanyTeamHub = dynamic(() => import("@/components/settings/CompanyTeamHub").then(m => ({ default: m.CompanyTeamHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando empresa..." /> })
const RecruitmentHub = dynamic(() => import("@/components/settings/RecruitmentHub").then(m => ({ default: m.RecruitmentHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando recrutamento..." /> })
const CommunicationHub = dynamic(() => import("@/components/settings/CommunicationHub").then(m => ({ default: m.CommunicationHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando comunicação..." /> })
const GoalsPlanningHub = dynamic(() => import("@/components/settings/GoalsPlanningHub").then(m => ({ default: m.GoalsPlanningHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando metas..." /> })
const GlobalSearchHub = dynamic(() => import("@/components/settings/GlobalSearchHub").then(m => ({ default: m.GlobalSearchHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando busca..." /> })
const IntegrationsHub = dynamic(() => import("@/components/settings/IntegrationsHub").then(m => ({ default: m.IntegrationsHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando integrações..." /> })

import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { useCompanyId } from "@/hooks/useCompanyId"

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
  icon: React.ComponentType<{ className?: string }>
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
    id: 'integrations',
    title: 'Integrações',
    description: 'Conecte serviços externos à plataforma',
    icon: Plug,
    status: 'incomplete',
    priority: 'medium',
    category: 'integrations',
    estimatedTime: 10,
    subsections: [
      { id: 'ai-models', title: 'Modelos de IA', description: 'Provedores de IA (Gemini, Claude, OpenAI)', fields: ['ai_providers'] },
      { id: 'ats', title: 'ATS / Applicant Tracking', description: 'Gupy, Pandapé, Merge.dev', fields: ['ats_connections'] },
      { id: 'calendar', title: 'Calendário & Agendamento', description: 'Google Calendar, Microsoft Calendar', fields: ['calendar_integrations'] },
      { id: 'communication', title: 'Comunicação', description: 'Teams, WhatsApp, Email/SMTP', fields: ['communication_integrations'] },
      { id: 'crm-hris', title: 'CRM & HRIS', description: 'Salesforce, SAP, Workday', fields: ['crm_hris_integrations'] },
      { id: 'mcps-apis', title: 'MCPs & APIs', description: 'Webhooks e API REST', fields: ['api_integrations'] },
    ]
  },
]

const settingsSections: SettingsSection[] = getDefaultSections()

const getCompletionBadgeColor = (percentage: number): string => {
  if (percentage >= 80) return 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success'
  if (percentage >= 50) return 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning'
  return 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error'
}

export default function SettingsPageEnhanced() {
  const { companyId, tenantInfo, isLoading: isTenantLoading } = useCompanyId()
  const [activeSection, setActiveSection] = useState<string>('company-team')
  const [activeSubsection, setActiveSubsection] = useState<string>('')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['company-team']))
  const [users, setUsers] = useState<Array<{ id: string; name?: string; [key: string]: unknown }>>([])
  const [goals, setGoals] = useState<Record<string, unknown[]>>({})
  
  const [sectionCompletion, setSectionCompletion] = useState<Record<string, number>>({
    'company-team': 0,
    'recruitment': 0,
    'communication': 0,
    'goals-planning': 0,
    'global-search': 0,
    'integrations': 0,
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
    'ai-models': false,
    'ats': false,
    'calendar': false,
    'communication': false,
    'crm-hris': false,
    'mcps-apis': false,
  })

  const [overallProgress, setOverallProgress] = useState<number>(0)
  const [progressLoading, setProgressLoading] = useState<boolean>(true)
  
  const [isCollapsed, setIsCollapsed] = useState(true)
  const [isLocked, setIsLocked] = useState(false)


  const [showTemplateSelector, setShowTemplateSelector] = useState(false)

  const [formData, setFormData] = useState<Record<string, string>>({
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
          'integrations': data.sections['integrations'] ?? prev['integrations'],
        }))
      }
      
      if (data.subsections) {
        setSubsectionCompletion(prev => ({
          ...prev,
          ...data.subsections
        }))
      }
    } catch (error) {
    } finally {
      setProgressLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProgress()
  // eslint-disable-next-line react-hooks/exhaustive-deps
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


  const handleUserUpdate = (user: { id: string; [key: string]: unknown }) => {
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

  const handleGoalUpdate = (userId: string, userGoals: unknown[]) => {
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
          <ErrorBoundarySection>
          <CompanyTeamHub
            activeSubsection={activeSubsection}
            onUserUpdate={handleUserUpdate as any}
            onGoalUpdate={handleGoalUpdate as any}
          />
          </ErrorBoundarySection>
        )
      case 'recruitment':
        return (
          <ErrorBoundarySection>
          <RecruitmentHub
            activeSubsection={activeSubsection}
          />
          </ErrorBoundarySection>
        )
      case 'communication':
        return (
          <ErrorBoundarySection>
          <CommunicationHub
            activeSubsection={activeSubsection}
          />
          </ErrorBoundarySection>
        )
      case 'goals-planning':
        return (
          <ErrorBoundarySection>
          <GoalsPlanningHub
            users={users}
            onGoalUpdate={handleGoalUpdate as any}
            activeSubsection={activeSubsection}
          />
          </ErrorBoundarySection>
        )
      case 'global-search':
        return (
          <ErrorBoundarySection>
          <GlobalSearchHub
            activeSubsection={activeSubsection}
          />
          </ErrorBoundarySection>
        )
      case 'integrations':
        return (
          <ErrorBoundarySection>
            <IntegrationsHub activeSubsection={activeSubsection} />
          </ErrorBoundarySection>
        )
      default:
        return (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center mx-auto mb-4">
              <Settings className="w-8 h-8 text-lia-text-primary" />
            </div>
            <h3 className={`${textStyles.subtitle} mb-2`}>
              Selecione uma seção
            </h3>
            <p className={`${textStyles.description}`}>
              Escolha uma das opções no menu lateral
            </p>
          </div>
        )
    }
  }

  const shouldShowContent = !isCollapsed || isLocked

  return (
    <>
    <div className="flex h-screen bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      <aside 
        className={`
          ${isCollapsed && !isLocked ? 'w-16' : 'w-64'}
          transition-colors duration-200
          flex-shrink-0
        `}
        onMouseEnter={() => !isLocked && setIsCollapsed(false)}
        onMouseLeave={() => !isLocked && setIsCollapsed(true)}
      >
        <Card className="h-full m-3 border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary backdrop-blur-sm rounded-md overflow-hidden flex flex-col">
          <div className={`p-4 border-b border-lia-border-subtle dark:border-lia-border-subtle ${isCollapsed && !isLocked ? 'px-2' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary rounded-md flex items-center justify-center flex-shrink-0">
                <Settings className="w-5 h-5" />
              </div>
              {shouldShowContent && (
                <div className="flex-1 min-w-0">
                  <h1 className={`${textStyles.sidebarTitle} leading-tight`}>
                    Configurações
                  </h1>
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
                  </div>
                </div>
                <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5 mb-3">
                  <div
                    className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary h-1.5 rounded-full transition-[width,height] duration-500"
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
                      className={`w-full flex items-center gap-2 p-2.5 rounded-md text-left transition-colors motion-reduce:transition-none ${
                        isActive && !activeSubsection
                          ? 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary'
                          : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50 text-lia-text-secondary'
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
                              className={`text-micro px-1.5 py-0.5 ${getCompletionBadgeColor(sectionCompletion[section.id] || 0)} border-0 rounded-full font-medium`}
                            >
                              {sectionCompletion[section.id] || 0}%
                            </Badge>
                          </div>
                        </>
                      )}
                    </button>

                    {shouldShowContent && isExpanded && section.subsections && (
                      <div className="ml-6 mt-1 space-y-1 border-l-2 border-lia-border-subtle dark:border-lia-border-subtle pl-2">
                        {section.subsections.map((subsection) => {
                          const isComplete = subsectionCompletion[subsection.id] ?? false
                          return (
                            <button
                              key={subsection.id}
                              onClick={() => handleSelectSubsection(section.id, subsection.id)}
                              className={`w-full text-left px-2 py-1.5 rounded-md transition-colors motion-reduce:transition-none ${
                                activeSubsection === subsection.id
                                  ? 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated'
                                  : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50'
                              }`}
                            >
                              <div className="flex items-center gap-1.5">
                                {isComplete ? (
                                  <Check className="w-3 h-3 text-status-success dark:text-status-success flex-shrink-0" />
                                ) : (
                                  <Circle className="w-2.5 h-2.5 fill-amber-500 text-status-warning flex-shrink-0" />
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
          <div className="p-6 border-b border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex items-center justify-between">
              <div>
                <h2 className={`${textStyles.h3} mb-1`}>
                  {settingsSections.find(s => s.id === activeSection)?.title}
                  {activeSubsection && settingsSections.find(s => s.id === activeSection)?.subsections?.find(sub => sub.id === activeSubsection) && (
                    <span className="text-lia-text-secondary font-normal"> / {settingsSections.find(s => s.id === activeSection)?.subsections?.find(sub => sub.id === activeSubsection)?.title}</span>
                  )}
                </h2>
                <p className={textStyles.description}>
                  {activeSubsection
                    ? settingsSections.find(s => s.id === activeSection)?.subsections?.find(sub => sub.id === activeSubsection)?.description
                    : settingsSections.find(s => s.id === activeSection)?.description
                  }
                </p>
              </div>
              {tenantInfo && (
                <div className="flex items-center gap-3 text-right">
                  <div>
                    <p className={`${textStyles.labelSmall} text-lia-text-secondary`}>
                      {tenantInfo.companyName || 'Empresa'}
                    </p>
                    <div className="flex items-center gap-2 justify-end mt-0.5">
                      {tenantInfo.companyId && (
                        <span className={`${textStyles.description} font-mono text-[10px]`}>
                          ID: {tenantInfo.companyId.substring(0, 8)}...
                        </span>
                      )}
                      {tenantInfo.planId && (
                        <Badge className={badgeStyles.info}>
                          {tenantInfo.planId}
                        </Badge>
                      )}
                      {tenantInfo.status && (
                        <Badge className={tenantInfo.status === 'active' ? badgeStyles.success : badgeStyles.warning}>
                          {tenantInfo.status === 'active' ? 'Ativo' : tenantInfo.status}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-md flex items-center justify-center">
                    <Building className="w-4 h-4 text-lia-text-secondary" />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {renderSectionContent()}
          </div>
        </div>
      </div>


    </>
  )
}
