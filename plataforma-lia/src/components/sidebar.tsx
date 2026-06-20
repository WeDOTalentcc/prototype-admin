"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState, useCallback, useEffect, useMemo, useRef } from "react"
import type { MenuItemType, JobFilterItemType, SidebarProps } from "@/lib/sidebar/sidebar.types"
import { useSidebarState } from "@/lib/sidebar/useSidebarState"
import { cn } from "@/lib/utils"
import {
  Users,
  Briefcase,
  Settings,
  ChevronLeft,
  ChevronRight,
  Lock,
  Crown,
  HelpCircle,
  PlayCircle,
  PauseCircle,
  CheckCircle,
  XCircle,
  Target,
  Filter,
  ChevronDown,
  ChevronUp,
  Brain,
  MessageCircle,
  User,
  X,
  Trash2,
  Search,
  Bot,
  GitBranch,
  Database,
  MoreHorizontal,
  KeyRound,
  LogOut,
  Bell,
  Eye,
  EyeOff,
  Check,
  Loader2,
  FolderKanban,
  Package,
  BarChart2,
  LineChart,
  FileText,
} from "lucide-react"
import type { RecentItem } from "@/hooks/shared/use-recent-items"
import { useFocusedJobStore } from "@/stores/focused-job-store"
import { useTargetDeployments } from "@/hooks/agents/use-target-deployments"
import { hasModuleAccess } from "@/utils/license-manager"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { LIATipsModal } from "@/components/lia-tips-modal"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { NotificationSystem } from "@/components/notification-system"
import { BetaBadge } from "@/components/ui/beta-badge"
import { AgentsQuotaBadge } from "@/components/pages-agent-studio/AgentsQuotaBadge"
import { HitlPendingBadge } from "@/components/hitl-pending-badge"
import { SetupProgressIcon } from "@/components/onboarding/SetupProgressIcon"
import { IASidebar } from "@/components/ia-sidebar/IASidebar"
import { useIASessionStore } from "@/stores/ia-session-store"
import { useIASessions } from "@/hooks/ia-sessions/useIASessions"
import { ProfileModal } from "@/components/modals/profile-modal"
import { useAuth } from "@/contexts/auth-context"
import { useAuthenticatedUserId } from "@/hooks/shared/use-authenticated-user-id"
import type { Notification as AppNotification } from "@/hooks/shared/use-notifications"
import Image from "next/image"
import { useTranslations } from 'next-intl'
import { useRouter } from "next/navigation"
import { useLocale } from "next-intl"
import { LanguageSwitcher } from "@/components/language-switcher"

const sectionLabelKeys: Record<string, string> = {
  "Operacional": "sections.operational",
  "Configuração": "sections.configuration",
}

const itemLabelKeys: Record<string, string> = {
  "Conversar": "items.conversar",
  "Recrutar": "items.recrutar",
  "Vagas": "items.jobs",
  "Projetos": "items.projects",
  "Funil de Talentos": "items.talentPipeline",
  "Agentes": "items.agentes",
  "Marketplace": "items.marketplace",
  "Decidir": "items.decidir",
  "Indicadores": "items.indicadores",
  "Relatórios": "items.relatorios",
}

const filterLabelKeys: Record<string, string> = {
  "Todas": "filters.all",
  "Ativas": "filters.active",
  "Paralisadas": "filters.paused",
  "Concluídas": "filters.completed",
  "Canceladas": "filters.cancelled",
  "Por Estágio": "filters.byStage",
}

const miscLabelKeys: Record<string, string> = {
  "Ver todos os bancos": "labels.seeAllPools",
  "Ver todos os agentes": "labels.seeAllAgents",
  "Ver todos": "labels.seeAll",
  "RECENTES": "labels.recent",
  "Limpar": "labels.clearRecent",
  "Remover dos recentes": "labels.removeFromRecent",
}

interface MenuSection {
  label: string
  items: MenuItemType[]
}

const BASE_MENU_SECTIONS: MenuSection[] = [
  {
    label: "",
    items: [
      { icon: MessageCircle, label: "Conversar", isCore: true },
      { icon: Brain, label: "Conversas", isCore: true, navKey: "__ia-sidebar__" },
    ],
  },
  {
    label: "",
    items: [
      {
        icon: BarChart2,
        label: "Decidir",
        isCore: true,
        navigateOnClick: true,
        alwaysExpanded: true,
        subItems: [
          { icon: LineChart, label: "Indicadores", isCore: true },
          { icon: FileText, label: "Relatórios", isCore: true },
        ],
      },
      {
        icon: GitBranch,
        label: "Recrutar",
        isCore: true,
        navigateOnClick: true,
        alwaysExpanded: true,
        subItems: [
          { icon: Briefcase, label: "Vagas", isCore: true },
          {
            icon: Users,
            label: "Funil de Talentos",
            isCore: true,
            navigateOnClick: true,
            maxVisibleSubItems: 3,
            seeAllLabel: "Ver todos os bancos",
            seeAllTarget: "Funil de Talentos",
          },
        ],
      },
      {
        icon: Bot,
        label: "Agentes",
        isCore: true,
        navigateOnClick: true,
        maxVisibleSubItems: 3,
        seeAllLabel: "Ver todos os agentes",
        seeAllTarget: "Agentes",
        isBeta: true,
        subItems: [
          { icon: Package, label: "Marketplace", isCore: true },
        ],
      },
      {
        icon: FolderKanban,
        label: "Projetos",
        isCore: true,
      },
    ],
  },
]

interface DynamicSubItem {
  id: string
  name: string
  status: string
}

function useSidebarDynamicItems() {
  const [agents, setAgents] = useState<DynamicSubItem[]>([])
  const [pools, setPools] = useState<DynamicSubItem[]>([])

  useEffect(() => {
    let cancelled = false

    async function loadAgents() {
      try {
        const res = await fetch("/api/backend-proxy/custom-agents?category=sourcing")
        if (!res.ok) return
        const data = await res.json()
        const mapped = (data?.agents || [])
          .filter((a: { status: string }) => a.status === "active" || a.status === "paused")
          .map((a: { id: string; name: string; status: string }) => ({
            id: a.id,
            name: a.name,
            status: a.status,
          }))
        if (!cancelled) setAgents(mapped)
      } catch { /* silent */ }
    }

    async function loadPools() {
      try {
        const res = await fetch("/api/backend-proxy/talent-pools?per_page=5")
        if (!res.ok) return
        const data = await res.json()
        const items = Array.isArray(data) ? data : (data?.talent_pools || data?.data || [])
        const mapped = items.slice(0, 5).map((p: { id: string; name?: string; attributes?: { name?: string } }) => ({
          id: p.id,
          name: (p as any).attributes?.name ?? p.name ?? "",
          status: "active",
        }))
        if (!cancelled) setPools(mapped)
      } catch { /* silent */ }
    }

    loadAgents()
    loadPools()
    return () => { cancelled = true }
  }, [])

  return { agents, pools }
}


const jobFilterItems: JobFilterItemType[] = [
  { icon: Filter, label: "Todas", value: "todas", count: 10 },
  { icon: PlayCircle, label: "Ativas", value: "ativas", count: 7 },
  { icon: PauseCircle, label: "Paralisadas", value: "paralisadas", count: 1 },
  { icon: CheckCircle, label: "Concluídas", value: "concluidas", count: 1 },
  { icon: XCircle, label: "Canceladas", value: "canceladas", count: 1 },
  { icon: Target, label: "Por Estágio", value: "por-estagio", count: 0 }
]


// Componente de item de menu memoizado
const MenuItem = React.memo(({
  item,
  currentPage,
  onNavigate,
  isCollapsed,
  shouldShowContent,
  t,
}: {
  item: MenuItemType
  currentPage: string
  onNavigate: (page: string) => void
  isCollapsed: boolean
  shouldShowContent: boolean
  t: (key: string) => string
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const isLocked = item.moduleId && !hasModuleAccess(item.moduleId)
  const canAccess = item.isCore || (item.moduleId && hasModuleAccess(item.moduleId))
  const hasSubItems = item.subItems && item.subItems.length > 0
  const chevronRef = useRef<HTMLSpanElement>(null)

  // Auto-expand if current page is a subitem or if this navigateOnClick item is active
  useEffect(() => {
    if (hasSubItems && (
      item.subItems?.some(sub => sub.label === currentPage) ||
      (item.navigateOnClick && currentPage === item.label)
    )) {
      setIsExpanded(true)
    }
  }, [currentPage, hasSubItems, item.subItems, item.navigateOnClick, item.label])

  const handleClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    // Chevron is a visual zone inside the row: clicking it only toggles expand,
    // never navigates. The label/icon area navigates (and keeps submenu open).
    if (hasSubItems && chevronRef.current && chevronRef.current.contains(e.target as Node)) {
      setIsExpanded(prev => !prev)
      return
    }

    if (hasSubItems && item.navigateOnClick) {
      if (canAccess) onNavigate(item.navKey || item.label)
      setIsExpanded(true)
    } else if (hasSubItems) {
      setIsExpanded(prev => !prev)
    } else if (canAccess) {
      onNavigate(item.navKey || item.label)
    } else {
      onNavigate(`upgrade-${item.moduleId}`)
    }
  }, [hasSubItems, canAccess, onNavigate, item.label, item.navKey, item.moduleId, item.navigateOnClick])

  // When alwaysExpanded is set, sub-items stay visible regardless of the
  // collapse state — the chevron is hidden since there is nothing to toggle.
  const expanded = item.alwaysExpanded || isExpanded

  const isIASidebarTrigger = item.navKey === "__ia-sidebar__"
  const isActive = currentPage === item.label || (hasSubItems && item.subItems?.some(sub => sub.label === currentPage))

  return (
    <div>
      <button
        onClick={handleClick}
        aria-current={isActive && canAccess ? "page" : undefined}
        className={cn(
 "w-full flex items-center gap-2 px-2 py-2 rounded-md text-left transition-colors duration-200 text-base-ui leading-tight min-h-10",
          isIASidebarTrigger
            ? "bg-zinc-900 text-white hover:bg-zinc-800 font-medium"
            : isLocked
            ? "text-lia-text-primary cursor-default opacity-60"
            : "hover:bg-lia-interactive-hover",
          !isIASidebarTrigger && isActive && canAccess
            ? "bg-lia-interactive-active text-lia-text-primary font-semibold"
            : !isIASidebarTrigger && canAccess
            ? "text-lia-text-primary font-normal"
            : !isIASidebarTrigger
            ? "text-lia-text-primary font-normal"
            : "",
          isCollapsed && !shouldShowContent ? "justify-center px-1.5" : "",
          item.isFuturo ? "opacity-40 pointer-events-none" : ""
        )}
        title={isCollapsed && !shouldShowContent ? `${itemLabelKeys[item.label] ? t(itemLabelKeys[item.label]) : item.label}${item.isBeta ? ` (${t('labels.beta')})` : ""}` : undefined}
        disabled={isLocked || false}
      >
        <div className="flex items-center gap-1">
          <item.icon className={cn("w-4 h-4 flex-shrink-0", isIASidebarTrigger && "text-wedo-cyan")} />
          {isLocked && <Lock className="w-2 h-2" />}
        </div>
        {shouldShowContent && (
          <div className="flex items-center justify-between flex-1">
            <div className="flex items-center gap-1.5">
              <span className="text-base-ui">{itemLabelKeys[item.label] ? t(itemLabelKeys[item.label]) : item.label}</span>
              {item.isBeta && (
                <BetaBadge size="sm" label={t('labels.beta')} />
              )}
              {item.label === "Agentes" && (
                <AgentsQuotaBadge />
              )}
            </div>
            <div className="flex items-center gap-1">
              {item.isPremium && !isLocked && (
                <Crown className="w-2 h-2 text-lia-text-primary" />
              )}
              {isLocked && (
                <span className="text-micro bg-lia-interactive-active px-1.5 py-0.5 rounded-full">
                  {t('labels.premium')}
                </span>
              )}
              {hasSubItems && !item.alwaysExpanded && (
                <span
                  ref={chevronRef}
                  role="button"
                  aria-label={isExpanded ? t('labels.collapseSubmenu') : t('labels.expandSubmenu')}
                  aria-expanded={isExpanded}
                  className="inline-flex items-center justify-center p-1 -m-1 rounded hover:bg-lia-interactive-active cursor-pointer"
                >
                  {isExpanded ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />}
                </span>
              )}
            </div>
          </div>
        )}
      </button>

      {/* SubItems */}
      {hasSubItems && expanded && shouldShowContent && (
        <div className="ml-4 mt-1 space-y-0.5">
          {(item.maxVisibleSubItems
            ? item.subItems!.slice(0, item.maxVisibleSubItems)
            : item.subItems!
          ).map((subItem) => {
            const navKey = subItem.navKey || subItem.label
            const subHasRichFeatures = !!(subItem.subItems?.length || subItem.navigateOnClick || subItem.seeAllLabel)

            if (subHasRichFeatures) {
              return (
                <div key={navKey} className="ml-0">
                  <MenuItem
                    item={subItem}
                    currentPage={currentPage}
                    onNavigate={onNavigate}
                    isCollapsed={false}
                    shouldShowContent={true}
                    t={t}
                  />
                </div>
              )
            }

            const subIsLocked = subItem.moduleId && !hasModuleAccess(subItem.moduleId)
            const subCanAccess = subItem.isCore || (subItem.moduleId && hasModuleAccess(subItem.moduleId))

            return (
              <button
                key={navKey}
                onClick={() => {
                  if (subCanAccess) {
                    onNavigate(navKey)
                  } else {
                    onNavigate(`upgrade-${subItem.moduleId}`)
                  }
                }}
                className={cn(
 "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors duration-200 text-sm-ui leading-tight min-h-8",
                  subIsLocked
                    ? "text-lia-text-secondary cursor-default opacity-60"
                    : "hover:bg-lia-interactive-hover",
                  subItem.isFuturo ? "opacity-40 pointer-events-none" : "",
                  currentPage === subItem.label && subCanAccess
                    ? "bg-lia-interactive-active text-lia-text-primary font-semibold"
                    : subCanAccess
                    ? "text-lia-text-secondary font-normal"
                    : "text-lia-text-secondary font-normal"
                )}
                disabled={subIsLocked || false}
              >
                <div className="flex items-center gap-1.5">
                  <subItem.icon className="w-3.5 h-3.5 flex-shrink-0" />
                  {subIsLocked && <Lock className="w-2 h-2" />}
                </div>
                <div className="flex items-center justify-between flex-1 min-w-0">
                  <span className="text-sm-ui truncate">{itemLabelKeys[subItem.label] ? t(itemLabelKeys[subItem.label]) : subItem.label}</span>
                  {subItem.isPremium && !subIsLocked && (
                    <Crown className="w-2 h-2 text-lia-text-primary" />
                  )}
                  {subIsLocked && (
                    <span className="text-micro bg-lia-interactive-active px-1 py-0.5 rounded-full">
                      {t('labels.premium')}
                    </span>
                  )}
                </div>
              </button>
            )
          })}
          {item.maxVisibleSubItems && item.subItems!.length > item.maxVisibleSubItems && item.seeAllTarget && (
            <button
              onClick={() => onNavigate(item.seeAllTarget!)}
              className="w-full flex items-center gap-2 px-2 py-1 rounded-md text-left transition-colors duration-200 hover:bg-lia-interactive-hover min-h-7"
            >
              <MoreHorizontal className="w-3 h-3 flex-shrink-0 text-lia-text-muted" />
              <span className="text-xs text-lia-text-muted hover:text-lia-text-secondary">
                {item.seeAllLabel ? (miscLabelKeys[item.seeAllLabel] ? t(miscLabelKeys[item.seeAllLabel]) : item.seeAllLabel) : t("labels.seeAll")} ({item.subItems!.length})
              </span>
            </button>
          )}
        </div>
      )}
    </div>
  )
})

MenuItem.displayName = 'MenuItem'

// Componente de item de filtro de vagas memoizado
const JobFilterItem = React.memo(({
  item,
  isActive,
  onNavigate,
  isCollapsed,
  shouldShowContent
}: {
  item: JobFilterItemType
  isActive: boolean
  onNavigate: (filter: string) => void
  isCollapsed: boolean
  shouldShowContent: boolean
}) => {
  const handleClick = useCallback(() => {
    onNavigate(item.value)
  }, [onNavigate, item.value])

  return (
    <button
      onClick={handleClick}
      className={cn(
 "w-full flex items-center gap-2 px-2 py-1.5 rounded-full text-left transition-colors duration-200 text-xs leading-tight min-h-[36px]",
        "hover:bg-lia-interactive-hover",
        isActive
          ? "bg-lia-interactive-active text-lia-text-primary font-semibold"
          : "text-lia-text-primary font-normal",
        isCollapsed && !shouldShowContent ? "justify-center px-1.5" : ""
      )}
      title={isCollapsed && !shouldShowContent ? item.label : undefined}
    >
      <div className="flex items-center gap-1">
        <item.icon className="w-4 h-4 flex-shrink-0" />
      </div>
      {shouldShowContent && (
        <div className="flex items-center justify-between flex-1">
          <span className="text-base-ui">{item.label}</span>
          {item.count !== undefined && item.count > 0 && (
            <span className="text-micro bg-lia-interactive-active px-1.5 py-0.5 rounded-full h-5 flex items-center">
              {item.count}
            </span>
          )}
        </div>
      )}
    </button>
  )
})

JobFilterItem.displayName = 'JobFilterItem'

const RECENT_TYPE_CONFIG = {
  vaga: { icon: Briefcase, color: 'text-lia-text-secondary' },
  chat: { icon: Brain, color: 'text-lia-text-secondary' },
  candidato: { icon: User, color: 'text-lia-text-secondary' },
  banco: { icon: Database, color: 'text-lia-text-secondary' },
} as const

const RecentItemRow = React.memo(({
  item,
  onClick,
  onRemove,
}: {
  item: RecentItem
  onClick: (item: RecentItem) => void
  onRemove: (id: string, type: RecentItem['type']) => void
}) => {
  const t = useTranslations('sidebar')
  const config = RECENT_TYPE_CONFIG[item.type as keyof typeof RECENT_TYPE_CONFIG]
  const Icon = config.icon

  return (
    <div className="group relative flex items-center">
      <button
        onClick={() => onClick(item)}
        className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors motion-reduce:transition-none duration-200 text-sm-ui leading-tight min-h-8 hover:bg-lia-interactive-hover text-lia-text-secondary"
        title={item.title}
      >
        <Icon className={cn("w-3.5 h-3.5 flex-shrink-0", config.color)} />
        <span className="truncate flex-1">{item.title}</span>
      </button>
      <button
        onClick={(e) => {
          e.stopPropagation()
          onRemove(item.id, item.type)
        }}
        className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none duration-150 p-0.5 rounded-md hover:bg-lia-interactive-active"
        title={t("labels.removeFromRecent")}
      >
        <X className="w-3 h-3 text-lia-text-muted" />
      </button>
    </div>
  )
})

RecentItemRow.displayName = 'RecentItemRow'

const FocusedJobSection = React.memo(({
  job,
  onClear,
  shouldShowContent,
}: {
  job: { id: string; title: string; candidateCount: number; todayInterviewCount: number }
  onClear: () => void
  shouldShowContent: boolean
}) => {
  const t = useTranslations('sidebar')
  const router = useRouter()
  const locale = useLocale()
  const { data: deploymentsData } = useTargetDeployments({
    targetType: "job",
    targetId: job.id,
  })
  const activeAgentCount = (deploymentsData?.deployments ?? []).filter(
    (d: { is_active?: boolean }) => d.is_active !== false
  ).length

  if (!shouldShowContent) return null

  const jobUrl = `/${locale}/jobs/${job.id}`

  return (
    <div className="mb-1 px-1">
      <div className="rounded-lg bg-wedo-cyan/10 border border-wedo-cyan/20 p-2">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-semibold text-lia-text-tertiary tracking-[0.18em] uppercase opacity-70">
            {t('focusedJob.label')}
          </span>
          <button
            onClick={onClear}
            className="p-0.5 rounded hover:bg-wedo-cyan/15 text-lia-text-muted hover:text-lia-text-secondary"
            title={t('focusedJob.dismiss')}
            aria-label={t('focusedJob.dismiss')}
          >
            <X className="w-3 h-3" />
          </button>
        </div>
        <div className="flex items-center gap-1.5 px-1 mb-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-wedo-cyan flex-shrink-0" aria-hidden="true" />
          <span className="text-xs font-medium text-lia-text-primary line-clamp-1">{job.title}</span>
        </div>
        <div className="space-y-0.5">
          <button
            onClick={() => router.push(jobUrl)}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors duration-200 hover:bg-wedo-cyan/15 text-lia-text-secondary min-h-8"
          >
            <Users className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="text-sm-ui flex-1">{t('focusedJob.candidates')}</span>
            {job.candidateCount > 0 && (
              <span className="text-micro bg-wedo-cyan/20 text-wedo-cyan px-1.5 py-0.5 rounded-full">
                {job.candidateCount}
              </span>
            )}
          </button>
          {job.todayInterviewCount > 0 && (
            <button
              onClick={() => router.push(jobUrl)}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors duration-200 hover:bg-wedo-cyan/15 text-lia-text-secondary min-h-8"
            >
              <Eye className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="text-sm-ui flex-1">{t('focusedJob.interviews')}</span>
              <span className="text-micro bg-wedo-cyan/20 text-wedo-cyan px-1.5 py-0.5 rounded-full">
                {job.todayInterviewCount} {t('focusedJob.today')}
              </span>
            </button>
          )}
          <button
            onClick={() => router.push(`${jobUrl}?tab=agents`)}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors duration-200 hover:bg-wedo-cyan/15 text-lia-text-secondary min-h-8"
          >
            <Bot className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="text-sm-ui flex-1">{t('focusedJob.agents')}</span>
            {activeAgentCount > 0 && (
              <span className="text-micro bg-wedo-cyan/20 text-wedo-cyan px-1.5 py-0.5 rounded-full">
                {activeAgentCount}
              </span>
            )}
          </button>
          <button
            onClick={() => router.push(`${jobUrl}?tab=edit&section=configuracoes`)}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-left transition-colors duration-200 hover:bg-wedo-cyan/15 text-lia-text-secondary min-h-8"
          >
            <Settings className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="text-sm-ui">{t('focusedJob.configure')}</span>
          </button>
        </div>
      </div>
    </div>
  )
})

FocusedJobSection.displayName = 'FocusedJobSection'

export function Sidebar({ currentPage, onNavigate, recentItems, onRecentItemClick, onRecentItemRemove, onRecentItemsClear, onShowSearch, notificationOpen, onNotificationToggle }: SidebarProps) {

  const t = useTranslations('sidebar')
  const { agents, pools } = useSidebarDynamicItems()
  const { focusedJob, clearFocusedJob } = useFocusedJobStore()
  const { isIASidebarOpen, toggleIASidebar } = useIASessionStore()
  const { data: iaSessions = [] } = useIASessions()
  const totalUnread = iaSessions.reduce((sum, s) => sum + (s.unread_count ?? 0), 0)
  const { user: authUser, refreshUser } = useAuth()
  const { userId: authenticatedUserId, isReady: isAuthReady } = useAuthenticatedUserId()

  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking("sidebar-password", showPasswordModal)

  const handleNotificationClick = useCallback((notification: AppNotification) => {
    // talent_pool_insight: navigate to Indicadores for pool-level metrics
    if ((notification as { type?: string }).type === "talent_pool_insight") {
      onNavigate("Decidir")
      return
    }
    // digest notifications are now handled by WeeklyDigestChatProvider
  }, [onNavigate])

  const roleLabels: Record<string, string> = {
    admin: t("user.admin"),
    recruiter: t("user.recruiter"),
    viewer: t("user.viewer"),
  }

  const isSSOUser = !!(authUser && "sso_provider" in authUser && authUser.sso_provider)

  const currentUser = {
    name: authUser?.name || t("user.defaultName"),
    email: authUser?.email || t("user.defaultEmail"),
    role: authUser?.role ? (roleLabels[authUser.role] ?? authUser.role) : t("user.recruiter"),
    company: authUser?.company || "",
    avatar_url: (authUser && "avatar_url" in authUser ? authUser.avatar_url : undefined) as string | undefined,
    sso_provider: (authUser && "sso_provider" in authUser ? authUser.sso_provider : null) as string | null,
  }

  const handleOpenPasswordModal = () => {
    setCurrentPassword("")
    setNewPassword("")
    setConfirmPassword("")
    setPasswordError("")
    setPasswordSuccess(false)
    setIsChangingPassword(false)
    setShowPasswordModal(true)
  }

  const handleClosePasswordModal = () => {
    setShowPasswordModal(false)
    setCurrentPassword("")
    setNewPassword("")
    setConfirmPassword("")
    setPasswordError("")
    setPasswordSuccess(false)
    setIsChangingPassword(false)
  }

  const handlePasswordChange = async () => {
    setPasswordError("")
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError(t("password.errorFillAll"))
      return
    }
    if (newPassword.length < 8) {
      setPasswordError(t("password.errorMinLength"))
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError(t("password.errorMismatch"))
      return
    }
    setIsChangingPassword(true)
    try {
      const res = await fetch("/api/backend-proxy/auth/change-password", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error || t("password.errorGeneric"))
      }
      setPasswordSuccess(true)
      setTimeout(() => { handleClosePasswordModal() }, 2000)
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : t("password.errorGeneric"))
    } finally {
      setIsChangingPassword(false)
    }
  }

  const handleNavigateToNotifications = () => {
    onNavigate("Configurações")
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent("settings-open-tab", { detail: "alertas" }))
    }, 300)
  }

  const menuSections = useMemo(() => {
    const injectDynamic = (item: MenuItemType): MenuItemType => {
      if (item.label === "Agentes" && agents.length > 0) {
        return {
          ...item,
          subItems: [
            ...(item.subItems || []),
            ...agents.map(a => ({
              icon: Bot,
              label: a.name,
              isCore: true,
              navKey: `agent:${a.id}`,
            })),
          ],
        }
      }
      if (item.label === "Funil de Talentos" && pools.length > 0) {
        return {
          ...item,
          subItems: [
            ...(item.subItems || []),
            ...pools.map(p => ({
              icon: Database,
              label: p.name,
              isCore: true,
              navKey: `pool:${p.id}`,
            })),
          ],
        }
      }
      if (item.subItems && item.subItems.length > 0) {
        return {
          ...item,
          subItems: item.subItems.map(sub => injectDynamic(sub)),
        }
      }
      return item
    }
    return BASE_MENU_SECTIONS.map(section => ({
      ...section,
      items: section.items.map(item => injectDynamic(item)),
    }))
  }, [agents, pools])

  const handleDynamicNavigate = useCallback((page: string) => {
    if (page === "__ia-sidebar__") {
      toggleIASidebar()
      return
    }
    if (page.startsWith("agent:")) {
      onNavigate("Agentes")
      return
    }
    if (page.startsWith("pool:")) {
      onNavigate("Funil de Talentos")
      return
    }
    onNavigate(page)
  }, [onNavigate, toggleIASidebar])

  const {
    isMounted,
    showTipsModal,
    isCollapsed,
    isTemporaryExpanded,
    sidebarWidth,
    isResizing,
    reducedMotion,
    shouldShowContent,
    dynamicWidth,
    toggleCollapse,
    handleMouseEnter,
    handleMouseLeave,
    handleShowTipsModal,
    handleCloseTipsModal,
    startResize,
  } = useSidebarState()

  const handleNavigateFromTips = useCallback((page: string) => {
    onNavigate(page)
    handleCloseTipsModal()
  }, [onNavigate, handleCloseTipsModal])

  useEffect(() => {
    useFocusedJobStore.persist.rehydrate()
  }, [])

  return (
    <nav
      data-sidebar="true"
      aria-label={t("labels.mainMenu")}
      className={cn(
 "bg-lia-bg-primary min-h-screen flex flex-col border-r border-lia-border-subtle relative font-sans",
        isTemporaryExpanded && "z-50"
      )}
      style={{
        width: dynamicWidth,
        transition: isResizing || reducedMotion
          ? 'none'
          : 'width 250ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Logo and Toggle */}
      <div className={cn(
 "flex items-center justify-between",
        shouldShowContent ? "p-4" : "p-2 flex-col gap-2"
      )}>
        <div className="flex items-center justify-center">
          {shouldShowContent ? (
            <Image
              src="/logos/wedo-logo.png"
              alt={t('labels.logoAlt')}
              width={120}
              height={40}
              className="dark:invert w-auto h-auto"
              priority
            />
          ) : (
            <Image
              src="/logos/we-logo.png"
              alt={t('labels.logoSmallAlt')}
              width={40}
              height={40}
              className="dark:invert w-auto h-auto"
              priority
            />
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleCollapse}
          className="h-7 w-7 p-0 text-lia-text-primary hover:bg-lia-interactive-hover"
          title={isCollapsed ? t("labels.expandMenu") : t("labels.collapseMenu")}
        >
          {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </Button>
      </div>

      {/* Search + Bell — topo do sidebar (expanded) */}
      {shouldShowContent && (
        <div className="flex items-center gap-1.5 px-4 pb-3">
          <button
            type="button"
            onClick={() => onShowSearch?.()}
            className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-lia-bg-secondary dark:bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors text-xs"
          >
            <Search className="w-3 h-3 flex-shrink-0" />
            <span className="flex-1 text-left">Pesquisar...</span>
            <kbd className="text-[10px] text-lia-text-muted font-mono bg-lia-bg-primary dark:bg-lia-bg-secondary px-1.5 py-0.5 rounded border border-lia-border-subtle">⌘K</kbd>
          </button>
          {onNotificationToggle && isAuthReady && authenticatedUserId ? (
            <NotificationSystem
              userId={authenticatedUserId}
              onNotificationClick={handleNotificationClick}
              panelPosition="sidebar"
              externalIsOpen={notificationOpen}
              onExternalToggle={onNotificationToggle}
            />
          ) : null}

        </div>
      )}
      {/* Bell only — collapsed sidebar */}
      {!shouldShowContent && onNotificationToggle && isAuthReady && authenticatedUserId && (
        <div className="flex justify-center pb-2">
          <NotificationSystem
            userId={authenticatedUserId}
            onNotificationClick={handleNotificationClick}
            panelPosition="sidebar"
            externalIsOpen={notificationOpen}
            onExternalToggle={onNotificationToggle}
          />
        </div>
      )}



      {/* Menu and Workspace - Scrollable */}
      <div className={`py-4 flex-1 overflow-y-auto ${shouldShowContent ? 'px-4' : 'px-2'}`}>
        <nav className="space-y-1">
          {menuSections.map((section, sectionIdx) => (
            <React.Fragment key={section.label || String(sectionIdx)}>
              <div>
                {shouldShowContent && section.label && (
                  <h3 className="text-[10px] font-semibold text-lia-text-tertiary mb-1.5 tracking-[0.18em] uppercase px-2 opacity-70">
                    {sectionLabelKeys[section.label] ? t(sectionLabelKeys[section.label]) : section.label}
                  </h3>
                )}
                {!shouldShowContent && sectionIdx > 0 && section.label && (
                  <div className="border-t border-lia-border-subtle my-1.5" />
                )}
                <div className="space-y-1">
                  {section.items.map((item) => (
                    <MenuItem
                      key={item.label}
                      item={item}
                      currentPage={currentPage}
                      onNavigate={handleDynamicNavigate}
                      isCollapsed={isCollapsed}
                      shouldShowContent={shouldShowContent}
                      t={t}
                    />
                  ))}
                </div>
              </div>
              {sectionIdx === 0 && isMounted && focusedJob && (
                <FocusedJobSection
                  job={focusedJob}
                  onClear={clearFocusedJob}
                  shouldShowContent={shouldShowContent}
                />
              )}
            </React.Fragment>
          ))}
        </nav>

        {shouldShowContent && recentItems && recentItems.length > 0 && onRecentItemClick && onRecentItemRemove && (
          <div className="mt-5">
            <h3 className="text-xs font-semibold text-lia-text-primary mb-2 tracking-[0.2em] uppercase">
              {t("labels.recent")}
            </h3>
            <div className="space-y-0.5 max-h-[280px] overflow-y-auto">
              {recentItems.map((item) => (
                <RecentItemRow
                  key={`${item.type}-${item.id}`}
                  item={item}
                  onClick={onRecentItemClick}
                  onRemove={onRecentItemRemove}
                />
              ))}
            </div>
            {recentItems.length >= 2 && onRecentItemsClear && (
              <button
                onClick={onRecentItemsClear}
                className="flex items-center gap-1.5 mt-2 px-2 py-1 text-xs text-lia-text-muted hover:text-lia-text-secondary transition-colors motion-reduce:transition-none duration-200"
              >
                <Trash2 className="w-3 h-3" />
                {t("labels.clearRecentItems")}
              </button>
            )}
          </div>
        )}

      </div>

      {/* Tools & User Section - Fixed at Bottom — linha única unificada */}
      <div className="px-3 py-2 border-t border-lia-border-subtle bg-lia-bg-primary">
        <div className={cn(
          "flex items-center gap-1",
          isCollapsed && !isTemporaryExpanded ? "flex-col gap-0.5" : "justify-center"
        )}>

          {/* 1. Avatar — acesso mais frequente */}
          {isMounted ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="h-7 w-7 p-0 rounded-full hover:bg-lia-interactive-hover"
                title={currentUser.name}
              >
                <Avatar className="h-6 w-6">
                  <AvatarImage src={currentUser.avatar_url} alt={currentUser.name} />
                  <AvatarFallback className="text-[10px] bg-lia-bg-inverse text-lia-text-on-inverse">
                    {currentUser.name.split(" ").map(n => n[0]).join("")}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="start"
              side="top"
              sideOffset={8}
              className="w-64"
            >
              <div className="p-3 pb-4">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={currentUser.avatar_url} alt={currentUser.name} />
                    <AvatarFallback className="text-sm bg-lia-bg-inverse text-lia-text-on-inverse">
                      {currentUser.name.split(" ").map(n => n[0]).join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-lia-text-primary truncate">
                      {currentUser.name}
                    </div>
                    <div className="text-xs text-lia-text-tertiary truncate">
                      {currentUser.email}
                    </div>
                    <div className="text-xs text-lia-text-tertiary mt-0.5">
                      {currentUser.role}
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-1">
                <DropdownMenuItem
                  className="cursor-pointer text-xs"
                  onClick={() => setShowProfileModal(true)}
                >
                  <User className="w-3.5 h-3.5 mr-2" />
                  {t("user.myProfile")}
                </DropdownMenuItem>
                {!isSSOUser && (
                  <DropdownMenuItem
                    className="cursor-pointer text-xs"
                    onClick={handleOpenPasswordModal}
                  >
                    <KeyRound className="w-3.5 h-3.5 mr-2" />
                    {t("user.changePassword")}
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem
                  className="cursor-pointer text-xs"
                  onClick={handleNavigateToNotifications}
                >
                  <Bell className="w-3.5 h-3.5 mr-2" />
                  {t("labels.notificationPreferences")}
                </DropdownMenuItem>
              </div>

              <DropdownMenuSeparator />

              <div className="p-1">
                <DropdownMenuItem
                  className="cursor-pointer text-xs text-status-error dark:text-status-error"
                  onClick={() => onNavigate("Sair")}
                >
                  <LogOut className="w-3.5 h-3.5 mr-2" />
                  {t("user.logout")}
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
          ) : (
            <span className="h-7 w-7 inline-flex items-center justify-center rounded-full" aria-hidden="true">
              <Avatar className="h-6 w-6">
                <AvatarFallback className="text-[10px] bg-lia-bg-inverse text-lia-text-on-inverse">
                  {currentUser.name.split(" ").map(n => n[0]).join("")}
                </AvatarFallback>
              </Avatar>
            </span>
          )}

          {/* 4. Config, Idioma, Ajuda, HITL — inline ao lado do avatar */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onNavigate("Configurações")}
            className="h-6 w-6 p-0 text-lia-text-muted hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
            title={t("labels.settings")}
          >
            <Settings className="w-3 h-3" />
          </Button>

          <LanguageSwitcher collapsed={true} />

          <Button
            variant="ghost"
            size="sm"
            onClick={handleShowTipsModal}
            className="h-6 w-6 p-0 text-lia-text-muted hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
            title={t("labels.helpTips")}
          >
            <HelpCircle className="w-3 h-3" />
          </Button>

          {isMounted && <SetupProgressIcon />}
          {isMounted && <HitlPendingBadge />}

        </div>
      </div>

      {/* IASidebar — Apollo-style: opens adjacent to sidebar */}
      <IASidebar sidebarOffset={isCollapsed && !isTemporaryExpanded ? 64 : sidebarWidth} />

      {/* Resize Handle */}
      {shouldShowContent && !isTemporaryExpanded && (
        <div
          className={cn(
 "absolute top-0 right-0 w-1 h-full cursor-col-resize group z-10",
            "hover:w-1.5 transition-colors motion-reduce:transition-none duration-200",
            isResizing ? "bg-lia-border-medium w-1.5" : "bg-transparent hover:bg-lia-border-medium"
          )}
          onMouseDown={startResize}
          title={t("labels.resizeSidebar")}
        >
          {/* Indicador visual mais sutil */}
          <div className="absolute inset-y-0 right-0 w-px bg-lia-interactive-active group-hover:bg-lia-border-medium transition-colors motion-reduce:transition-none duration-200" />

          {/* Área de hover expandida para facilitar o clique */}
          <div className="absolute top-0 -right-2 w-4 h-full" />
        </div>
      )}

      {/* Indicador visual de atalho */}
      {isCollapsed && !isTemporaryExpanded && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-lia-bg-inverse text-lia-text-inverse text-xs px-2 py-1 rounded-xl opacity-0 hover:opacity-100 transition-opacity motion-reduce:transition-none duration-200 pointer-events-none">
          Ctrl+B
        </div>
      )}

      {/* Indicador de largura durante redimensionamento */}
      {isResizing && (
        <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-lia-text-primary text-lia-text-inverse text-sm px-3 py-2 rounded-md z-50 pointer-events-none">
          {sidebarWidth}px
        </div>
      )}

      {/* LIA Tips Modal */}
      <LIATipsModal
        isOpen={showTipsModal}
        onClose={handleCloseTipsModal}
        currentPage={currentPage}
        onNavigateToLibrary={() => handleNavigateFromTips("Biblioteca LIA")}
      />

      <ProfileModal
        open={showProfileModal}
        onOpenChange={setShowProfileModal}
        user={currentUser}
        onNavigateToSettings={handleNavigateToNotifications}
        onProfileUpdated={() => { refreshUser() }}
      />

      <Dialog open={showPasswordModal} onOpenChange={(open) => { if (!open) handleClosePasswordModal(); else setShowPasswordModal(true) }}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-lia-text-secondary" />
              {t("password.title")}
            </DialogTitle>
            <DialogDescription>
              {t("password.description")}
            </DialogDescription>
          </DialogHeader>

          {passwordSuccess ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="w-16 h-16 rounded-full bg-status-success/15 flex items-center justify-center mb-4">
                <Check className="w-8 h-8 text-status-success" />
              </div>
              <p className="text-lg font-medium text-status-success">{t("password.success")}</p>
            </div>
          ) : (
            <>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password-sb">{t("password.currentPassword")}</Label>
                  <div className="relative">
                    <Input
                      id="current-password-sb"
                      type={showCurrentPassword ? "text" : "password"}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder={t("password.currentPlaceholder")}
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    >
                      {showCurrentPassword ? (
                        <EyeOff className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Eye className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-password-sb">{t("password.newPassword")}</Label>
                  <div className="relative">
                    <Input
                      id="new-password-sb"
                      type={showNewPassword ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder={t("password.newPlaceholder")}
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                    >
                      {showNewPassword ? (
                        <EyeOff className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Eye className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password-sb">{t("password.confirmPassword")}</Label>
                  <div className="relative">
                    <Input
                      id="confirm-password-sb"
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder={t("password.confirmPlaceholder")}
                      className="pr-10"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-4 h-4 text-lia-text-secondary" />
                      ) : (
                        <Eye className="w-4 h-4 text-lia-text-secondary" />
                      )}
                    </Button>
                  </div>
                </div>

                {passwordError && (
                  <div className="flex items-center gap-2 text-status-error text-sm">
                    <X className="w-4 h-4" />
                    {passwordError}
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={handleClosePasswordModal}>
                  {t("password.cancel")}
                </Button>
                <Button
                  onClick={handlePasswordChange}
                  disabled={isChangingPassword}
                  className="text-lia-btn-primary-text hover:opacity-90 bg-lia-btn-primary-bg"
                >
                  {isChangingPassword && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  {t("password.change")}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </nav>
  )
}
