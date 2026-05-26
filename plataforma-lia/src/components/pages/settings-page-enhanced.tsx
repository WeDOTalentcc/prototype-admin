"use client"

import React, { Suspense, useState, useMemo, useCallback, useEffect } from"react"
import { useSearchParams } from "next/navigation"
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
  ChevronDown, ChevronUp, Lock, Unlock, Circle, Plug, Shield, Webhook, Sparkles
} from"lucide-react"

const SECTION_ICON_COLORS: Record<string, string> = {
  'minha-empresa': 'text-wedo-cyan',
  'pipeline': 'text-emerald-500',
  'screening': 'text-amber-500',
  'templates-assinatura': 'text-violet-500',
  'comunicacao-alertas': 'text-rose-400',
  'usuarios-departamentos': 'text-sky-500',
  'integrations': 'text-emerald-500',
  'webhooks': 'text-wedo-cyan',
  'fairness-compliance': 'text-violet-400',
}


import dynamic from"next/dynamic"
import { useTranslations } from "next-intl"
import { LoadingFallback } from"@/components/ui/loading"
import { HubLoadingState } from"@/components/settings/_shared"
function I18nLoadingFallback({ tKey }: { tKey: string }) {
  const tLoad = useTranslations("settings.loading")
  return <LoadingFallback text={tLoad(tKey)} />
}

const MinhaEmpresaHub = dynamic(() => import("@/components/settings/MinhaEmpresaHub").then(m => ({ default: m.MinhaEmpresaHub })), { ssr: false, loading: () => <I18nLoadingFallback tKey="company" /> })
const AiCreditsPage = dynamic(() => import("@/components/pages/ai-credits-page").then(m => ({ default: m.AiCreditsPage })), { ssr: false, loading: () => <I18nLoadingFallback tKey="company" /> })
const RecruitmentPipelineTab = dynamic(() => import("@/components/settings/RecruitmentPipelineTab").then(m => ({ default: m.RecruitmentPipelineTab })), { ssr: false, loading: () => <I18nLoadingFallback tKey="pipeline" /> })
const AutomationsTab = dynamic(() => import("@/components/settings/recruitment/automations-tab").then(m => ({ default: m.AutomationsTab })), { ssr: false, loading: () => <I18nLoadingFallback tKey="automations" /> })
const RecruitmentScreeningTab = dynamic(() => import("@/components/settings/RecruitmentScreeningTab").then(m => ({ default: m.RecruitmentScreeningTab })), { ssr: false, loading: () => <I18nLoadingFallback tKey="screening" /> })
// P0.G (audit 2026-05-21): aggregated catalog managers for Pipeline Stages,
// Alert Rules, Integration Catalog, Webhook Event Types.
const CatalogsManagementSection = dynamic(() => import("@/components/settings/CatalogsManagementSection").then(m => ({ default: m.CatalogsManagementSection })), { ssr: false, loading: () => <I18nLoadingFallback tKey="screening" /> })
const CommunicationHub = dynamic(() => import("@/components/settings/CommunicationHub").then(m => ({ default: m.CommunicationHub })), { ssr: false, loading: () => <I18nLoadingFallback tKey="communication" /> })
const IntegrationsHub = dynamic(() => import("@/components/settings/IntegrationsHub").then(m => ({ default: m.IntegrationsHub })), { ssr: false, loading: () => <I18nLoadingFallback tKey="integrations" /> })
const UsuariosDepartamentosHub = dynamic(() => import("@/components/settings/UsuariosDepartamentosHub").then(m => ({ default: m.UsuariosDepartamentosHub })), { ssr: false, loading: () => <I18nLoadingFallback tKey="users" /> })
const FairnessComplianceHub = dynamic(() => import("@/components/settings/FairnessComplianceHub").then(m => ({ default: m.FairnessComplianceHub })), { ssr: false, loading: () => <I18nLoadingFallback tKey="compliance" /> })
const WebhooksManager = dynamic(() => import("@/components/settings/WebhooksManager").then(m => ({ default: m.WebhooksManager })), { ssr: false, loading: () => <I18nLoadingFallback tKey="webhooks" /> })
// PR 3 (2026-05-25): GovernancaHub removido — panels movidos para /wedo-admin/governanca/ (staff) e Consent/DSR/AuditSummary integrados em FairnessComplianceHub.

import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { useHoverDebounce } from '@/lib/sidebar/useHoverDebounce'
import { ErrorBoundarySection } from"@/components/ui/error-boundary-section"
import { useCompanyId } from"@/hooks/company/useCompanyId"
import { resolveSettingsTarget } from "@/lib/settings/resolve-settings-target"
import { apiFetch } from "@/lib/api/api-fetch"

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
    id: 'minha-empresa',
    title: 'Minha Empresa',
    description: 'Dados, cultura, benefícios e políticas',
    icon: Building,
    status: 'incomplete',
    priority: 'high',
    category: 'basic',
    estimatedTime: 15,
    // P1-4 (2026-05-26): 'learning-loops' movido para hub 'lia-personalizacao' (config LIA juntada).
    // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md + audit §9 (taxonomia 2026-05-26).
  },
  // P1-4 (2026-05-26): hub novo "LIA & Personalização" desentrelaça config LIA
  // (instrucoes-lia + learning-loops + ai-persona) do hub operacional Recrutamento.
  // Audit ref: ~/Documents/wedotalent_audit_2026-05-26/CONFIGURACOES_MENU_COHERENCE_AUDIT.md §9.
  {
    id: 'lia-personalizacao',
    title: 'LIA & Personalização',
    description: 'Persona, campos visíveis e learning loops da LIA',
    icon: Brain,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 10,
    dependencies: ['minha-empresa'],
    subsections: [
      { id: 'instrucoes-lia', title: 'Instruções LIA & Persona', description: 'Configure toggles, instruções por campo (34 canonical) e persona da LIA', fields: [] },
      { id: 'learning-loops', title: 'Learning Loops', description: 'Aprendizado contínuo: Big5 cultura, JD similar, WSI effectiveness (Sprint B Phase 2)', fields: [] },
    ],
  },
  // Consolidações P1 (2026-05-25): hub 'pipeline' absorvido em 'recrutamento-lia' como subsection.
  {
    id: 'recrutamento-lia',
    title: 'Recrutamento & LIA',
    description: 'Pipeline, screening e automações — políticas operacionais',
    icon: Workflow,
    status: 'pending',
    priority: 'high',
    category: 'advanced',
    estimatedTime: 20,
    dependencies: ['minha-empresa'],
    // Consolidações P1 (2026-05-25): hub NOVO absorve pipeline + screening (ex-standalone)
    // + instrucoes-lia (ex-subsection de minha-empresa, contém AiPersonaPanel + LiaFieldsConfigPanel).
    // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
    // P1-4 (2026-05-26): 'instrucoes-lia' movido para hub 'lia-personalizacao' (config LIA).
    subsections: [
      { id: 'pipeline', title: 'Pipeline', description: 'Etapas do processo seletivo (kanban, SLA, automation)', fields: [] },
      { id: 'screening', title: 'Screening', description: 'Perguntas de elegibilidade via WhatsApp', fields: [] },
      { id: 'automacoes', title: 'Automações', description: 'Regras de disparo automático no pipeline', fields: [] },
    ],
  },
  // Consolidações P1 (2026-05-25): hub 'templates-assinatura' absorvido em 'comunicacao-alertas' (renomeado 'Comunicação').
  {
    id: 'comunicacao-alertas',
    title: 'Comunicação',
    description: 'Templates, assinatura, horários LGPD, alertas e notificações da LIA',
    icon: Bell,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 15,
    dependencies: ['minha-empresa'],
    // Consolidações P1 (2026-05-25): renamed (era "Comunicação & Alertas") + absorveu templates-assinatura.
    // CommunicationHub agora expõe TODAS as tabs canonicas (templates/signature/schedule/alerts/abtesting).
    subsections: [
      { id: 'templates', title: 'Templates', description: 'Modelos de mensagens para candidatos', fields: [] },
      { id: 'signature', title: 'Assinatura', description: 'Assinatura padrão dos emails', fields: [] },
      { id: 'schedule', title: 'Horários', description: 'Janelas de envio e LGPD compliance', fields: [] },
      { id: 'alerts', title: 'Alertas', description: 'Alertas operacionais e SLA', fields: [] },
    ],
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
  },
  {
    id: 'ai-credits',
    title: 'AI Credits',
    description: 'Saldo + consumo de creditos LIA por modelo (BYOK + plataforma)',
    icon: Sparkles,
    status: 'incomplete',
    priority: 'medium',
    category: 'advanced',
    estimatedTime: 5,
  },
  // Webhooks DEFER (2026-05-25): hub removido do menu cliente — audit recomendou Wave 1+
  // (0 clientes usando, 0 deliveries lifetime, 0 dispatcher call sites no produto).
  // WebhooksManager.tsx preservado pra reativação futura quando 1º cliente pedir integração.
  // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
  {
    id: 'fairness-compliance',
    title: 'Compliance & LGPD',
    description: 'LGPD, consent, audit log e compliance da IA',
    icon: Shield,
    status: 'incomplete',
    priority: 'low',
    category: 'advanced',
    estimatedTime: 0,
    subsections: [
      // PR 2 (2026-05-25): 'fairness' removida — dashboard movido para /wedo-admin/fairness/ (staff).
      // PR 3 (2026-05-25): 'ai-transparency' removida — movido para /wedo-admin/governanca/ai-transparency/ (staff).
      // PR 3 (2026-05-25): 'consent' + 'audit-summary' adicionados — vindos de Governança dissolvida.
      // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
      { id: 'lgpd-candidatos', title: 'LGPD Candidatos', description: 'Pedidos Art. 20 de candidatos (prazo 15 dias úteis)', fields: [] },
      { id: 'consent', title: 'Consent', description: 'Tipos de consentimento e revogação (LGPD Art. 8)', fields: [] },
      { id: 'audit-summary', title: 'Audit Summary', description: 'Resumo de eventos LGPD dos últimos 30 dias (read-only)', fields: [] },
      { id: 'studio', title: 'Agent Studio', description: 'Compliance do Agent Studio', fields: [] },
    ],
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
  const searchParams = useSearchParams()
  const [activeSection, setActiveSection] = useState<string>('minha-empresa')
  const [activeSubsection, setActiveSubsection] = useState<string>('')
  // P2-1 (audit 2026-05-26): progressive disclosure — toggle pra esconder
  // hubs advanced/integrations. Default ON (mostra tudo, sem regressao
  // pra power users). Persistencia localStorage pra preferencia stick.
  const [showAdvanced, setShowAdvanced] = useState<boolean>(() => {
    if (typeof window === "undefined") return true
    const stored = window.localStorage.getItem("lia-settings-show-advanced")
    return stored === null ? true : stored === "true"
  })

  const handleToggleAdvanced = useCallback(() => {
    setShowAdvanced((prev) => {
      const next = !prev
      if (typeof window !== "undefined") {
        window.localStorage.setItem("lia-settings-show-advanced", String(next))
      }
      return next
    })
  }, [])
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['minha-empresa']))

  // Task #894 — quando a página é aberta via deep-link com `?section=…`
  // (ex.: CTA do job-publish-modal ou cards do chat-workflow-reels), abre
  // direto a tab solicitada em vez de cair na default `minha-empresa`.
  // O parâmetro `?field=…` continua funcionando para scroll-into-view
  // (compatibilidade com Task #712), mesmo sem `?section=`, desde que
  // a tab atual contenha o campo.
  useEffect(() => {
    const target = resolveSettingsTarget(searchParams)
    if (target.section) {
      setActiveSection(target.section)
      setActiveSubsection(target.subsection)
      setExpandedSections((prev) => new Set([...Array.from(prev), target.section as string]))
    }
    if (target.field && typeof window !== 'undefined') {
      window.requestAnimationFrame(() => {
        const el = document.querySelector(`[data-field="${target.field}"]`) as HTMLElement | null
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' })
          el.dataset.recentlyHighlighted = 'true'
          window.setTimeout(() => {
            if (el) delete el.dataset.recentlyHighlighted
          }, 3000)
        }
      })
    }
  }, [searchParams])

  useEffect(() => {
    const openTabHandler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (typeof detail !== 'string') return
      if (detail === 'alertas') {
        setActiveSection('comunicacao-alertas')
        setActiveSubsection('')
        setExpandedSections(new Set(['comunicacao-alertas']))
        return
      }
      const known = settingsSections.find((s) => s.id === detail)
      if (known) {
        setActiveSection(detail)
        setActiveSubsection('')
        setExpandedSections((prev) => new Set([...Array.from(prev), detail]))
      }
    }

    // Task #712 — bridge bidirecional chat<>configurações para as 7 actions
    // de company_settings. Quando a LIA executa uma action via chat, ela
    // dispara este evento e a tab correspondente abre destacando o campo.
    const actionHandler = (e: Event) => {
      const detail = (e as CustomEvent).detail || {}
      const section = detail.section || 'minha-empresa'
      const known = settingsSections.find((s) => s.id === section)
      if (!known) return
      setActiveSection(section)
      setActiveSubsection('')
      setExpandedSections((prev) => new Set([...Array.from(prev), section]))
      if (detail.field && typeof window !== 'undefined') {
        window.requestAnimationFrame(() => {
          const el = document.querySelector(`[data-field="${detail.field}"]`) as HTMLElement | null
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            el.dataset.recentlyHighlighted = 'true'
            window.setTimeout(() => {
              if (el) delete el.dataset.recentlyHighlighted
            }, 3000)
          }
        })
      }
    }

    window.addEventListener('settings-open-tab', openTabHandler)
    window.addEventListener('lia:settings-action', actionHandler)
    return () => {
      window.removeEventListener('settings-open-tab', openTabHandler)
      window.removeEventListener('lia:settings-action', actionHandler)
    }
  }, [])
  
  const [sectionCompletion, setSectionCompletion] = useState<Record<string, number>>({
    'minha-empresa': 0,
    'pipeline': 0,
    'screening': 0,
    'templates-assinatura': 0,
    'comunicacao-alertas': 0,
    'usuarios-departamentos': 0,
    'integrations': 0,
    'webhooks': 0,
    'fairness-compliance': 0,
  })

  const [subsectionCompletion, setSubsectionCompletion] = useState<Record<string, boolean>>({})

  const [overallProgress, setOverallProgress] = useState<number>(0)
  const [progressLoading, setProgressLoading] = useState<boolean>(true)
  
  const [isCollapsed, setIsCollapsed] = useState(true)
  const [isLocked, setIsLocked] = useState(false)

  const expandSettings = useCallback(() => setIsCollapsed(false), [])
  const collapseSettings = useCallback(() => setIsCollapsed(true), [])

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
      const response = await apiFetch('/api/backend-proxy/settings/progress/')
      
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
          // Canonical sidebar IDs (matching backend settings_progress.py P0-4 fix 2026-05-26).
          // Backend ADICIONOU 7 chaves canonical; aqui consumimos exatamente os 7 hubs do getDefaultSections().
          // Legacy IDs (pipeline, screening, templates-assinatura, webhooks) removidos — nao existem mais como hubs top-level.
          'minha-empresa': data.sections['minha-empresa'] ?? prev['minha-empresa'] ?? 0,
          'lia-personalizacao': data.sections['lia-personalizacao'] ?? prev['lia-personalizacao'] ?? 0,
          'recrutamento-lia': data.sections['recrutamento-lia'] ?? prev['recrutamento-lia'] ?? 0,
          'comunicacao-alertas': data.sections['comunicacao-alertas'] ?? prev['comunicacao-alertas'] ?? 0,
          'usuarios-departamentos': data.sections['usuarios-departamentos'] ?? prev['usuarios-departamentos'] ?? 0,
          'integrations': data.sections['integrations'] ?? prev['integrations'] ?? 0,
          'ai-credits': data.sections['ai-credits'] ?? prev['ai-credits'] ?? 0,
          'fairness-compliance': data.sections['fairness-compliance'] ?? prev['fairness-compliance'] ?? 0,
        }))
      }
      
      if (data.subsections) {
        setSubsectionCompletion(prev => ({
          ...prev,
          ...data.subsections
        }))
      }
    } catch (error) {
      // P0-4 (2026-05-26): nao silenciar — logar para observability
      console.error("[fetchProgress] failed to load settings progress", error)
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
            <Suspense fallback={<HubLoadingState />}>
              <MinhaEmpresaHub activeSubsection={activeSubsection} />
            </Suspense>
          </ErrorBoundarySection>
        )
      case 'ai-credits':
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <AiCreditsPage />
            </Suspense>
          </ErrorBoundarySection>
        )
      // Consolidações P1 (2026-05-25): cases pipeline/screening/templates-assinatura removidos.
      // Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
      case 'lia-personalizacao':
        // P1-4 (2026-05-26): hub novo agrupa instrucoes-lia + learning-loops.
        // Renderiza via MinhaEmpresaHub (componente canonical) com activeSubsection.
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <MinhaEmpresaHub activeSubsection={activeSubsection || 'instrucoes-lia'} />
            </Suspense>
          </ErrorBoundarySection>
        )
      case 'recrutamento-lia':
        // 3 subsections (operacional): pipeline (default) | screening | automacoes
        // P1-4: instrucoes-lia migrou para hub lia-personalizacao.
        if (activeSubsection === 'screening') {
          return (
            <ErrorBoundarySection>
              <Suspense fallback={<HubLoadingState />}>
                <RecruitmentScreeningTab />
              </Suspense>
            </ErrorBoundarySection>
          )
        }
        if (activeSubsection === 'automacoes') {
          return (
            <ErrorBoundarySection>
              <Suspense fallback={<HubLoadingState />}>
                <AutomationsTab onSettingsChange={() => {}} />
              </Suspense>
            </ErrorBoundarySection>
          )
        }
        // default → pipeline (mais comum)
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <RecruitmentPipelineTab />
            </Suspense>
          </ErrorBoundarySection>
        )
      case 'comunicacao-alertas':
        // Consolidações P1: agora exibe TODAS as 5 tabs (templates+signature+schedule+alerts+abtesting).
        // Default subsection = 'alerts' (matching comportamento histórico).
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <CommunicationHub
                activeSubsection={activeSubsection || 'alerts'}
                visibleTabs={['templates', 'signature', 'schedule', 'alerts', 'abtesting']}
              />
            </Suspense>
          </ErrorBoundarySection>
        )
      case 'usuarios-departamentos':
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <UsuariosDepartamentosHub />
            </Suspense>
          </ErrorBoundarySection>
        )
      case 'integrations':
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <IntegrationsHub activeSubsection={activeSubsection} />
            </Suspense>
          </ErrorBoundarySection>
        )
      // Webhooks DEFER (2026-05-25): case removido — hub não está mais no menu cliente.
      // WebhooksManager.tsx ainda existe — reativação futura.
      case 'fairness-compliance':
        return (
          <ErrorBoundarySection>
            <Suspense fallback={<HubLoadingState />}>
              <FairnessComplianceHub activeSubsection={activeSubsection || 'lgpd-candidatos'} />
            </Suspense>
          </ErrorBoundarySection>
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
                  onClick={() => setIsLocked(!isLocked)}
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
            {/* P2-1 (audit 2026-05-26): progressive disclosure toggle.
                Default ON; persist em localStorage. */}
            {shouldShowContent && (
              <button
                onClick={handleToggleAdvanced}
                data-testid="toggle-show-advanced"
                aria-pressed={showAdvanced}
                className="w-full text-left text-xs text-lia-text-secondary hover:text-lia-text-primary py-1.5 px-1 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              >
                {showAdvanced ? "Modo simples (essenciais)" : "Mostrar todas as configurações"}
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-3">
            <nav className="space-y-2" role="navigation" aria-label="Configurações">
              {settingsSections.filter((section) => {
                // P2-1 progressive disclosure: quando OFF, mostra apenas hubs essenciais
                // (basic categoryOR priority=high). Mantem operacional (Recrutamento & LIA)
                // visivel para evitar quebrar fluxo do recrutador.
                if (showAdvanced) return true
                return section.category === "basic" || section.priority === "high"
              }).map((section) => {
                const IconComponent = section.icon
                const PriorityIcon = priorityIcons[section.priority]
                const isExpanded = expandedSections.has(section.id)
                const isActive = activeSection === section.id

                return (
                  <div key={section.id}>
                    <button
                      data-testid={`settings-menu-${section.id}`}
                      data-active={isActive && !activeSubsection}
                      aria-label={section.title}
                      aria-current={isActive && !activeSubsection ? 'page' : undefined}
                      onClick={() => {
                        setActiveSection(section.id)
                        setActiveSubsection('')
                        if (section.subsections && section.subsections.length > 0) {
                          handleToggleSection(section.id)
                        }
                      }}
                      className={`w-full flex items-center gap-2 p-2.5 rounded-lg text-left transition-colors motion-reduce:transition-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-wedo-cyan ${
                        isActive && !activeSubsection
                          ? 'bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary'
                          : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50 text-lia-text-secondary'
                      } ${isCollapsed && !isLocked ? 'justify-center' : ''}`}
                      title={isCollapsed && !isLocked ? section.title : ''}
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
            </nav>

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
