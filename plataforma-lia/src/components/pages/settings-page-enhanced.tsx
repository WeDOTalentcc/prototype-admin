"use client"

import React, { useState, useMemo, useCallback, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
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
  ChevronDown, ChevronUp, Lock, Unlock, Circle, Plug, Shield
} from"lucide-react"

const SECTION_ICON_COLORS: Record<string, string> = {
  'minha-empresa': 'text-wedo-cyan',
  'pipeline': 'text-emerald-500',
  'screening': 'text-amber-500',
  'templates-assinatura': 'text-violet-500',
  'comunicacao-alertas': 'text-rose-400',
  'usuarios-departamentos': 'text-sky-500',
  'integrations': 'text-emerald-500',
  'lia-personalizacao': 'text-cyan-500',
  'fairness-compliance': 'text-violet-400',
  'consumo': 'text-teal-500',
}


import dynamic from"next/dynamic"
import { LoadingFallback } from"@/components/ui/loading"
const MinhaEmpresaHub = dynamic(() => import("@/components/settings/MinhaEmpresaHub").then(m => ({ default: m.MinhaEmpresaHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando empresa..." /> })
const RecruitmentPipelineTab = dynamic(() => import("@/components/settings/RecruitmentPipelineTab").then(m => ({ default: m.RecruitmentPipelineTab })), { ssr: false, loading: () => <LoadingFallback text="Carregando pipeline..." /> })
const RecruitmentScreeningTab = dynamic(() => import("@/components/settings/RecruitmentScreeningTab").then(m => ({ default: m.RecruitmentScreeningTab })), { ssr: false, loading: () => <LoadingFallback text="Carregando screening..." /> })
const CommunicationHub = dynamic(() => import("@/components/settings/CommunicationHub").then(m => ({ default: m.CommunicationHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando comunicação..." /> })
const IntegrationsHub = dynamic(() => import("@/components/settings/IntegrationsHub").then(m => ({ default: m.IntegrationsHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando integrações..." /> })
const UsuariosDepartamentosHub = dynamic(() => import("@/components/settings/UsuariosDepartamentosHub").then(m => ({ default: m.UsuariosDepartamentosHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando usuários..." /> })
const FairnessComplianceHub = dynamic(() => import("@/components/settings/FairnessComplianceHub").then(m => ({ default: m.FairnessComplianceHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando compliance..." /> })
const ConsumoHub = dynamic(() => import("@/components/settings/ConsumoHub").then(m => ({ default: m.ConsumoHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando consumo..." /> })
const LiaPersonalizacaoHub = dynamic(() => import("@/components/settings/LiaPersonalizacaoHub").then(m => ({ default: m.LiaPersonalizacaoHub })), { ssr: false, loading: () => <LoadingFallback text="Carregando LIA..." /> })

import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip"
import { useHoverDebounce } from '@/lib/sidebar/useHoverDebounce'
import { ErrorBoundarySection } from"@/components/ui/error-boundary-section"
import { useCompanyId } from"@/hooks/company/useCompanyId"
import { SETTINGS_SECTION_ALIASES } from "@/lib/settings/resolve-settings-target"

interface SettingsSubsection {
  id: string
  title: string
  description: string
  fields: string[]
}

type SettingsSectionGroup = "empresa" | "processo" | "lia" | "comunicacao" | "plataforma"

const SECTION_GROUPS: { id: SettingsSectionGroup; label: string; defaultExpanded: boolean }[] = [
  { id: "empresa", label: "Empresa", defaultExpanded: true },
  { id: "processo", label: "Processo", defaultExpanded: true },
  { id: "lia", label: "LIA & Personalização", defaultExpanded: true },
  { id: "comunicacao", label: "Comunicação", defaultExpanded: true },
  { id: "plataforma", label: "Plataforma", defaultExpanded: false },
]

interface SettingsSection {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  status: 'completed' | 'incomplete' | 'pending'
  priority: 'high' | 'medium' | 'low'
  category: 'basic' | 'advanced' | 'integrations'
  estimatedTime: number
  group: SettingsSectionGroup
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
    id: 'minha-empresa',
    title: 'Minha Empresa',
    description: 'Dados, cultura, benefícios e políticas',
    icon: Building,
    status: 'incomplete',
    priority: 'high',
    category: 'basic',
    estimatedTime: 15,
    group: 'empresa' as const,
  },
  {
    id: 'lia-personalizacao',
    title: 'LIA & Personalizacao',
    description: 'Persona da IA, instrucoes por campo e learning loops',
    icon: Brain,
    status: 'incomplete',
    priority: 'high',
    category: 'advanced',
    estimatedTime: 10,
    dependencies: ['minha-empresa'],
    group: 'lia' as const,
  },
  {
    id: 'pipeline',
    title: 'Pipeline',
    description: 'Etapas do processo seletivo',
    icon: Workflow,
    status: 'pending',
    priority: 'high',
    category: 'advanced',
    estimatedTime: 10,
    dependencies: ['minha-empresa'],
    group: 'processo' as const,
  },
  {
    id: 'screening',
    title: 'Screening',
    description: 'Perguntas de elegibilidade via WhatsApp',
    icon: MessageSquare,
    status: 'pending',
    priority: 'high',
    category: 'advanced',
    estimatedTime: 10,
    dependencies: ['minha-empresa'],
    group: 'processo' as const,
  },
  {
    id: 'templates-assinatura',
    title: 'Templates & Assinatura',
    description: 'Modelos de comunicação e assinatura de email',
    icon: FileText,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 10,
    group: 'comunicacao' as const,
  },
  {
    id: 'comunicacao-alertas',
    title: 'Comunicação & Alertas',
    description: 'Horários LGPD, alertas e notificações da LIA',
    icon: Bell,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 10,
    dependencies: ['minha-empresa'],
    group: 'comunicacao' as const,
  },
  {
    id: 'usuarios-departamentos',
    title: 'Usuários & Departamentos',
    description: 'Recrutadores, permissões e estrutura organizacional',
    icon: Users,
    status: 'incomplete',
    priority: 'medium',
    category: 'basic',
    estimatedTime: 10,
    group: 'plataforma' as const,
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
    group: 'plataforma' as const,
  },
  {
    id: 'fairness-compliance',
    title: 'Fairness & LGPD',
    description: 'Equidade da IA e pedidos LGPD de candidatos',
    icon: Shield,
    status: 'incomplete',
    priority: 'low',
    category: 'advanced',
    estimatedTime: 0,
    group: 'plataforma' as const,
    subsections: [
      { id: 'fairness', title: 'Fairness & Compliance', description: 'Eventos de equidade e auditoria da IA', fields: [] },
      { id: 'lgpd-candidatos', title: 'LGPD Candidatos', description: 'Pedidos Art. 20 de candidatos (prazo 15 dias úteis)', fields: [] },
      { id: 'studio', title: 'Agent Studio', description: 'Compliance do Agent Studio', fields: [] },
    ],
  },
  {
    id: 'consumo',
    title: 'Consumo',
    description: 'Créditos IA, Pearch, agentes e billing',
    icon: BarChart3,
    status: 'incomplete',
    priority: 'low',
    category: 'advanced',
    estimatedTime: 0,
    group: 'plataforma' as const,
  },
]

const settingsSections: SettingsSection[] = getDefaultSections()

const getCompletionBadgeColor = (percentage: number): string => {
  if (percentage >= 80) return ' dark:bg-status-success/30 dark:text-status-success'
  if (percentage >= 50) return ' dark:bg-status-warning/30 dark:text-status-warning'
  return ' dark:bg-status-error/30 dark:text-status-error'
}

export default function SettingsPageEnhanced() {
  const { companyId, tenantInfo, isLoading: isTenantLoading } = useCompanyId()
  const [activeSection, setActiveSection] = useState<string>('minha-empresa')
  const [activeSubsection, setActiveSubsection] = useState<string>('')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['minha-empresa']))

  // Init determinístico (igual no SSR e no primeiro render do cliente) para evitar
  // hydration mismatch. A preferência salva em localStorage é aplicada após a
  // montagem, no useEffect abaixo — nunca durante o primeiro render.
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    () => new Set(SECTION_GROUPS.filter(g => g.defaultExpanded).map(g => g.id))
  )

  useEffect(() => {
    try {
      const saved = localStorage.getItem('settings-groups-expanded')
      if (saved) setExpandedGroups(new Set(JSON.parse(saved) as string[]))
    } catch {}
  }, [])

  const toggleGroupExpanded = useCallback((groupId: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(groupId)) {
        next.delete(groupId)
      } else {
        next.add(groupId)
      }
      try { localStorage.setItem('settings-groups-expanded', JSON.stringify([...next])) } catch {}
      return next
    })
  }, [])

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail === 'alertas') {
        setActiveSection('comunicacao-alertas')
        setActiveSubsection('')
        setExpandedSections(new Set(['comunicacao-alertas']))
      }
    }
    window.addEventListener('settings-open-tab', handler)
    return () => window.removeEventListener('settings-open-tab', handler)
  }, [])

  // Task #1277 — reconecta o atalho do chat (`lia:settings-action`).
  // O hook `useUIAction` (settings_open_tab) dispara este CustomEvent com
  // `{ section, subsection, field }`. Aqui abrimos a aba correta entre os 10
  // hubs canônicos e, se houver `field`, rolamos até ele dentro do hub.
  // Sem este listener, o atalho fica quebrado (regressão da antiga Task #712).
  useEffect(() => {
    const actionHandler = (e: Event) => {
      const detail = ((e as CustomEvent).detail || {}) as {
        section?: string
        subsection?: string
        field?: string
      }
      const rawSection = detail.section
      if (typeof rawSection !== 'string' || !rawSection) return
      // Aplica os mesmos aliases do deep-link (`alertas → comunicacao-alertas`).
      const section = SETTINGS_SECTION_ALIASES[rawSection] ?? rawSection
      const known = settingsSections.find((s) => s.id === section)
      if (!known) return // section inválida → ignora sem trocar a aba
      setActiveSection(section)
      setActiveSubsection(
        typeof detail.subsection === 'string' ? detail.subsection : '',
      )
      setExpandedSections((prev) => new Set([...Array.from(prev), section]))
      setExpandedGroups((prev) => new Set(prev).add(known.group))

      const field = detail.field
      if (typeof field === 'string' && field && typeof window !== 'undefined') {
        // Espera o hub montar (next paint) antes de procurar o campo.
        window.requestAnimationFrame(() => {
          const el = (document.querySelector(`[data-field="${field}"]`) ||
            document.querySelector(`[n="${field}"]`)) as HTMLElement | null
          if (!el) return
          el.scrollIntoView({ behavior: 'smooth', block: 'center' })
          el.dataset.recentlyHighlighted = 'true'
          window.setTimeout(() => {
            delete el.dataset.recentlyHighlighted
          }, 3000)
        })
      }
    }
    window.addEventListener('lia:settings-action', actionHandler)
    return () => window.removeEventListener('lia:settings-action', actionHandler)
  }, [])

  // Deep-link: /configuracoes?section=<id> abre a secao diretamente.
  // Conserta os NAVIGATION_OVERRIDES (?section=pipeline, ?section=templates-assinatura,
  // ?section=consumo via redirect ai-credits) que antes caiam em minha-empresa.
  useEffect(() => {
    if (typeof window === "undefined") return
    const requested = new URLSearchParams(window.location.search).get("section")
    if (!requested) return
    const match = settingsSections.find((s) => s.id === requested)
    if (!match) return
    setActiveSection(match.id)
    setActiveSubsection("")
    setExpandedSections(new Set([match.id]))
    setExpandedGroups((prev) => new Set(prev).add(match.group))
  }, [])
  
  const [sectionCompletion, setSectionCompletion] = useState<Record<string, number>>({
    'minha-empresa': 0,
    'pipeline': 0,
    'screening': 0,
    'templates-assinatura': 0,
    'comunicacao-alertas': 0,
    'usuarios-departamentos': 0,
    'integrations': 0,
    'fairness-compliance': 0,
    'consumo': 0,
    'lia-personalizacao': 0,
  })

  const [subsectionCompletion, setSubsectionCompletion] = useState<Record<string, boolean>>({})

  const [overallProgress, setOverallProgress] = useState<number>(0)
  const [progressLoading, setProgressLoading] = useState<boolean>(true)
  
  const [isCollapsed, setIsCollapsed] = useState(true)
  // Init determinístico (igual no SSR e no primeiro render do cliente) para
  // evitar hydration mismatch. A preferência de "fixado" salva em localStorage
  // é aplicada após a montagem, no useEffect abaixo — nunca no primeiro render.
  const [isLocked, setIsLocked] = useState(false)

  useEffect(() => {
    try {
      const saved = localStorage.getItem('settings-sidebar-locked')
      if (saved === null) {
        // Primeira visita: abre a barra fixada para reduzir custo de descoberta.
        setIsLocked(true)
        setIsCollapsed(false)
      } else {
        setIsLocked(saved === 'true')
        // Restaura a última largura escolhida (recolhida vs expandida) por hover,
        // independente do lock — mesmo padrão de `settings-sidebar-locked`.
        const savedCollapsed = localStorage.getItem('settings-sidebar-collapsed')
        if (savedCollapsed !== null) {
          setIsCollapsed(savedCollapsed === 'true')
        }
      }
    } catch {}
  }, [])

  const toggleLocked = useCallback(() => {
    setIsLocked(prev => {
      const next = !prev
      try { localStorage.setItem('settings-sidebar-locked', String(next)) } catch {}
      return next
    })
  }, [])

  const expandSettings = useCallback(() => {
    setIsCollapsed(false)
    try { localStorage.setItem('settings-sidebar-collapsed', 'false') } catch {}
  }, [])
  const collapseSettings = useCallback(() => {
    setIsCollapsed(true)
    try { localStorage.setItem('settings-sidebar-collapsed', 'true') } catch {}
  }, [])

  const {
    handleMouseEnter: handleSettingsMouseEnter,
    handleMouseLeave: handleSettingsMouseLeave,
  } = useHoverDebounce({
    onExpand: expandSettings,
    onCollapse: collapseSettings,
    isEnabled: !isLocked,
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
          // P0-4: all 9 canonical sidebar section IDs mapped to backend keys
          'minha-empresa': data.sections['minha-empresa'] ?? prev['minha-empresa'],
          // pipeline/screening/templates share recrutamento-lia score (no dedicated backend key yet)
          'pipeline': data.sections['pipeline'] ?? data.sections['recrutamento-lia'] ?? prev['pipeline'],
          'screening': data.sections['screening'] ?? data.sections['recrutamento-lia'] ?? prev['screening'],
          'templates-assinatura': data.sections['templates-assinatura'] ?? data.sections['recrutamento-lia'] ?? prev['templates-assinatura'],
          'comunicacao-alertas': data.sections['comunicacao-alertas'] ?? prev['comunicacao-alertas'],
          'usuarios-departamentos': data.sections['usuarios-departamentos'] ?? prev['usuarios-departamentos'],
          'integrations': data.sections['integracoes'] ?? data.sections['integrations'] ?? prev['integrations'],
          'fairness-compliance': data.sections['fairness-compliance'] ?? prev['fairness-compliance'],
          'consumo': data.sections['ai-credits'] ?? data.sections['consumo'] ?? prev['consumo'],
          'lia-personalizacao': data.sections['lia-personalizacao'] ?? prev['lia-personalizacao'],
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


  const renderSectionContent = () => {
    switch (activeSection) {
      case 'minha-empresa':
        return (
          <ErrorBoundarySection>
            <MinhaEmpresaHub />
          </ErrorBoundarySection>
        )
      case 'lia-personalizacao':
        return (
          <ErrorBoundarySection>
            <LiaPersonalizacaoHub activeSubsection={activeSubsection} />
          </ErrorBoundarySection>
        )
      case 'pipeline':
        return (
          <ErrorBoundarySection>
            <RecruitmentPipelineTab />
          </ErrorBoundarySection>
        )
      case 'screening':
        return (
          <ErrorBoundarySection>
            <RecruitmentScreeningTab />
          </ErrorBoundarySection>
        )
      case 'templates-assinatura':
        return (
          <ErrorBoundarySection>
            <CommunicationHub visibleTabs={['templates', 'signature']} stacked />
          </ErrorBoundarySection>
        )
      case 'comunicacao-alertas':
        return (
          <ErrorBoundarySection>
            <CommunicationHub activeSubsection="alerts" visibleTabs={['alerts']} />
          </ErrorBoundarySection>
        )
      case 'usuarios-departamentos':
        return (
          <ErrorBoundarySection>
            <UsuariosDepartamentosHub />
          </ErrorBoundarySection>
        )
      case 'integrations':
        return (
          <ErrorBoundarySection>
            <IntegrationsHub activeSubsection={activeSubsection} />
          </ErrorBoundarySection>
        )
      case 'fairness-compliance':
        return (
          <ErrorBoundarySection>
            <FairnessComplianceHub activeSubsection={activeSubsection || 'fairness'} />
          </ErrorBoundarySection>
        )
      case 'consumo':
        return (
          <ErrorBoundarySection>
            <ConsumoHub />
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
          transition-[width,colors] duration-300 ease-in-out motion-reduce:transition-none
          flex-shrink-0
        `}
        onMouseEnter={handleSettingsMouseEnter}
        onMouseLeave={handleSettingsMouseLeave}
      >
        <Card className="h-full m-3 border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary backdrop-blur-sm rounded-xl overflow-hidden flex flex-col">
          <div className={`p-4 dark:border-lia-border-subtle ${isCollapsed && !isLocked ? 'px-2' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary rounded-lg flex items-center justify-center flex-shrink-0">
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
                  onClick={toggleLocked}
                  className="h-6 w-6 p-0 flex-shrink-0"
                  title={isLocked ?"Desbloquear menu" :"Bloquear menu expandido"}
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
            <TooltipProvider delayDuration={150}>
            <nav className="space-y-0" aria-label="Configurações">
              {(() => {
                const grouped = SECTION_GROUPS.map(g => ({
                  ...g,
                  sections: settingsSections.filter(s => s.group === g.id),
                })).filter(g => g.sections.length > 0)
                return grouped.map((grp, gi) => (
                  <div key={grp.id} data-group-id={grp.id}>
                    {shouldShowContent && (
                      <button
                        onClick={() => toggleGroupExpanded(grp.id)}
                        className={`w-full flex items-center justify-between px-1 pb-1 text-[10px] font-semibold uppercase tracking-widest text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors ${gi === 0 ? 'pt-1' : 'pt-4'}`}
                        aria-expanded={expandedGroups.has(grp.id)}
                        aria-controls={`group-${grp.id}`}
                      >
                        <span>{grp.label}</span>
                        {expandedGroups.has(grp.id)
                          ? <ChevronDown className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
                          : <ChevronRight className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
                        }
                      </button>
                    )}
                    {(!shouldShowContent || expandedGroups.has(grp.id)) && grp.sections.map((section) => {
                const IconComponent = section.icon
                const isExpanded = expandedSections.has(section.id)
                const isActive = activeSection === section.id

                const sectionButton = (
                    <button
                      data-testid={`settings-menu-${section.id}`}
                      data-active={isActive && !activeSubsection}
                      aria-label={section.title}
                      onClick={() => {
                        setActiveSection(section.id)
                        setActiveSubsection('')
                        if (section.subsections && section.subsections.length > 0) {
                          handleToggleSection(section.id)
                        }
                      }}
                      className={`w-full flex items-center gap-2 p-2.5 rounded-lg text-left transition-colors motion-reduce:transition-none ${
                        isActive && !activeSubsection
                          ? 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary'
                          : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50 text-lia-text-secondary'
                      } ${!shouldShowContent ? 'justify-center' : ''}`}
                    >
                      <IconComponent className={`w-4 h-4 flex-shrink-0 ${SECTION_ICON_COLORS[section.id] || ''}`} />
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
                            <Chip
                              variant="neutral"
                              className={`text-micro px-1.5 py-0.5 ${getCompletionBadgeColor(sectionCompletion[section.id] || 0)} border-0 rounded-full font-medium`}
                            >
                              {sectionCompletion[section.id] || 0}%
                            </Chip>
                          </div>
                        </>
                      )}
                    </button>
                )

                return (
                  <div key={section.id}>
                    {shouldShowContent ? sectionButton : (
                      <Tooltip>
                        <TooltipTrigger asChild>{sectionButton}</TooltipTrigger>
                        <TooltipContent side="right">{section.title}</TooltipContent>
                      </Tooltip>
                    )}

                    {shouldShowContent && isExpanded && section.subsections && (
                      <div className="ml-6 mt-1 space-y-1 border-l-2 border-lia-border-subtle dark:border-lia-border-subtle pl-2">
                        {section.subsections.map((subsection) => {
                          const isComplete = subsectionCompletion[subsection.id] ?? false
                          return (
                            <button
                              key={subsection.id}
                              onClick={() => handleSelectSubsection(section.id, subsection.id)}
                              className={`w-full text-left px-2 py-1.5 rounded-lg transition-colors motion-reduce:transition-none ${
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
                  </div>
                ))
              })()}
            </nav>
            </TooltipProvider>

          </div>
        </Card>
      </aside>

        <div className="flex-1 flex flex-col" data-testid="settings-content-area" data-active-section={activeSection}>
          <div className="p-6 dark:border-lia-border-subtle">
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
                        <Chip variant="neutral" muted className={badgeStyles.info}>
                          {tenantInfo.planId}
                        </Chip>
                      )}
                      {tenantInfo.status && (
                        <Chip variant="neutral" muted className={tenantInfo.status === 'active' ? badgeStyles.success : badgeStyles.warning}>
                          {tenantInfo.status === 'active' ? 'Ativo' : tenantInfo.status}
                        </Chip>
                      )}
                    </div>
                  </div>
                  <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg flex items-center justify-center">
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
