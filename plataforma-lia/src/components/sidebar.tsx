"use client"

import React, { useState, useCallback, useEffect } from "react"
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
  User,
  X,
  Trash2,
  Search
} from "lucide-react"
import type { RecentItem } from "@/hooks/use-recent-items"
import { hasModuleAccess } from "@/utils/license-manager"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { LIATipsModal } from "@/components/lia-tips-modal"
import Image from "next/image"

// Memoizar os dados estáticos para evitar recriações
// Menu principal - apenas páginas operacionais do dia-a-dia
const menuItems: MenuItemType[] = [
  { icon: Target, label: "Tarefas", isCore: true },
  { icon: Briefcase, label: "Vagas", isCore: true },
  { icon: Users, label: "Funil de Talentos", isCore: true },
]


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
  shouldShowContent
}: {
  item: MenuItemType
  currentPage: string
  onNavigate: (page: string) => void
  isCollapsed: boolean
  shouldShowContent: boolean
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const isLocked = item.moduleId && !hasModuleAccess(item.moduleId)
  const canAccess = item.isCore || (item.moduleId && hasModuleAccess(item.moduleId))
  const hasSubItems = item.subItems && item.subItems.length > 0

  // Auto-expand if current page is a subitem
  useEffect(() => {
    if (hasSubItems && item.subItems?.some(sub => sub.label === currentPage)) {
      setIsExpanded(true)
    }
  }, [currentPage, hasSubItems, item.subItems])

  const handleClick = useCallback(() => {
    if (hasSubItems) {
      setIsExpanded(prev => !prev)
    } else if (canAccess) {
      onNavigate(item.label)
    } else {
      onNavigate(`upgrade-${item.moduleId}`)
    }
  }, [hasSubItems, canAccess, onNavigate, item.label, item.moduleId])

  const isActive = currentPage === item.label || (hasSubItems && item.subItems?.some(sub => sub.label === currentPage))

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
 "w-full flex items-center gap-2 px-2 py-2 rounded-md text-left transition-colors duration-200 text-base-ui leading-tight min-h-10",
          isLocked
            ? "text-lia-text-primary cursor-default opacity-60"
            : "hover:bg-lia-interactive-hover",
          isActive && canAccess
            ? "bg-lia-bg-tertiary text-lia-text-primary font-semibold"
            : canAccess
            ? "text-lia-text-primary font-normal"
            : "text-lia-text-primary font-normal",
          isCollapsed && !shouldShowContent ? "justify-center px-1.5" : ""
        )}
        title={isCollapsed && !shouldShowContent ? item.label : undefined}
        disabled={isLocked || false}
      >
        <div className="flex items-center gap-1">
          <item.icon className="w-4 h-4 flex-shrink-0" />
          {isLocked && <Lock className="w-2 h-2" />}
        </div>
        {shouldShowContent && (
          <div className="flex items-center justify-between flex-1">
            <span className="text-base-ui">{item.label}</span>
            <div className="flex items-center gap-1">
              {item.isPremium && !isLocked && (
                <Crown className="w-2 h-2 text-lia-text-primary" />
              )}
              {isLocked && (
                <span className="text-xs bg-lia-interactive-active px-1.5 py-0.5 rounded-full">
                  Premium
                </span>
              )}
              {hasSubItems && (
                isExpanded ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />
              )}
            </div>
          </div>
        )}
      </button>

      {/* SubItems */}
      {hasSubItems && isExpanded && shouldShowContent && (
        <div className="ml-4 mt-1 space-y-1">
          {item.subItems?.map((subItem) => {
            const subIsLocked = subItem.moduleId && !hasModuleAccess(subItem.moduleId)
            const subCanAccess = subItem.isCore || (subItem.moduleId && hasModuleAccess(subItem.moduleId))

            return (
              <button
                key={subItem.label}
                onClick={() => {
                  if (subCanAccess) {
                    onNavigate(subItem.label)
                  } else {
                    onNavigate(`upgrade-${subItem.moduleId}`)
                  }
                }}
                className={cn(
 "w-full flex items-center gap-2 px-2 py-2 rounded-md text-left transition-colors duration-200 text-base-ui leading-tight min-h-10",
                  subIsLocked
                    ? "text-lia-text-primary cursor-default opacity-60"
                    : "hover:bg-lia-interactive-hover",
                  currentPage === subItem.label && subCanAccess
                    ? "bg-lia-bg-tertiary text-lia-text-primary font-semibold"
                    : subCanAccess
                    ? "text-lia-text-primary font-normal"
                    : "text-lia-text-primary font-normal"
                )}
                disabled={subIsLocked || false}
              >
                <div className="flex items-center gap-1.5">
                  <subItem.icon className="w-4 h-4 flex-shrink-0" />
                  {subIsLocked && <Lock className="w-2 h-2" />}
                </div>
                <div className="flex items-center justify-between flex-1">
                  <span className="text-base-ui">{subItem.label}</span>
                  {subItem.isPremium && !subIsLocked && (
                    <Crown className="w-2 h-2 text-lia-text-primary" />
                  )}
                  {subIsLocked && (
                    <span className="text-xs bg-lia-interactive-active px-1 py-0.5 rounded-full">
                      Premium
                    </span>
                  )}
                </div>
              </button>
            )
          })}
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
          ? "bg-lia-bg-tertiary text-lia-text-primary font-semibold"
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
            <span className="text-xs bg-lia-interactive-active px-1.5 py-0.5 rounded-full h-5 flex items-center">
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
  chat: { icon: Brain, color: 'text-wedo-cyan' },
  candidato: { icon: User, color: 'text-lia-text-secondary' },
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
  const config = RECENT_TYPE_CONFIG[item.type]
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
        title="Remover dos recentes"
      >
        <X className="w-3 h-3 text-lia-text-disabled" />
      </button>
    </div>
  )
})

RecentItemRow.displayName = 'RecentItemRow'

export function Sidebar({ currentPage, onNavigate, recentItems, onRecentItemClick, onRecentItemRemove, onRecentItemsClear, onShowSearch }: SidebarProps) {
  // State, persistence, resize, keyboard shortcut and computed values
  // extracted to useSidebarState (src/lib/sidebar/useSidebarState.ts).
  // Vue 3 migration: replace with the equivalent composable — same return shape.
  const {
    isMounted,
    showTipsModal,
    isCollapsed,
    isTemporaryExpanded,
    sidebarWidth,
    isResizing,
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

  return (
    <div
      data-sidebar="true"
      className={cn(
 "bg-lia-bg-primary min-h-screen flex flex-col border-r border-lia-border-subtle relative font-sans",
        isTemporaryExpanded && "z-50"
      )}
      style={{width: dynamicWidth}}
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
              alt="WeDo Talent"
              width={120}
              height={40}
              className="dark:invert"
              style={{width: 'auto', height: 'auto'}}
              priority
            />
          ) : (
            <Image
              src="/logos/we-logo.png"
              alt="we"
              width={40}
              height={40}
              className="dark:invert"
              style={{width: 'auto', height: 'auto'}}
              priority
            />
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleCollapse}
          className="h-7 w-7 p-0 text-lia-text-primary hover:bg-lia-interactive-hover"
          title={`${isCollapsed ? "Expandir" : "Retrair"} menu (Ctrl+B)`}
        >
          {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </Button>
      </div>

      {/* Menu and Workspace - Scrollable */}
      <div className={`py-4 flex-1 overflow-y-auto ${shouldShowContent ? 'px-4' : 'px-2'}`}>
        <div className="mb-4">
          {shouldShowContent && (
            <h3 className="text-xs font-semibold text-lia-text-primary mb-2 tracking-[0.2em] uppercase">
              MENU
            </h3>
          )}
        </div>

        <nav className="space-y-1">
          {menuItems.map((item) => (
            <MenuItem
              key={item.label}
              item={item}
              currentPage={currentPage}
              onNavigate={onNavigate}
              isCollapsed={isCollapsed}
              shouldShowContent={shouldShowContent}
            />
          ))}
        </nav>

        {shouldShowContent && recentItems && recentItems.length > 0 && onRecentItemClick && onRecentItemRemove && (
          <div className="mt-5">
            <h3 className="text-xs font-semibold text-lia-text-primary mb-2 tracking-[0.2em] uppercase">
              RECENTES
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
                className="flex items-center gap-1.5 mt-2 px-2 py-1 text-xs text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none duration-200"
              >
                <Trash2 className="w-3 h-3" />
                Limpar recentes
              </button>
            )}
          </div>
        )}

      </div>

      {/* Tools Section - Fixed at Bottom */}
      <div className="px-3 py-2 border-t border-lia-border-subtle bg-lia-bg-primary">
        <div className={cn(
 "flex items-center gap-1",
          isCollapsed && !isTemporaryExpanded ? "flex-col gap-0.5" : "justify-center"
        )}>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onShowSearch?.()}
            className="h-6 w-6 p-0 text-lia-text-primary hover:bg-lia-interactive-hover"
            title="Busca Global"
          >
            <Search className="w-3 h-3" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onNavigate("Configurações")}
            className="h-6 w-6 p-0 text-lia-text-primary hover:bg-lia-interactive-hover"
            title="Configurações"
          >
            <Settings className="w-3 h-3" />
          </Button>

          <div className="flex items-center">
            <ThemeToggle />
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleShowTipsModal}
            className="h-6 w-6 p-0 text-lia-text-primary hover:bg-lia-interactive-hover"
            title="Ajuda e Dicas LIA"
          >
            <HelpCircle className="w-3 h-3" />
          </Button>
        </div>
      </div>

      {/* Resize Handle */}
      {shouldShowContent && !isTemporaryExpanded && (
        <div
          className={cn(
 "absolute top-0 right-0 w-1 h-full cursor-col-resize group z-10",
            "hover:w-1.5 transition-colors motion-reduce:transition-none duration-200",
            isResizing ? "bg-lia-border-medium w-1.5" : "bg-transparent hover:bg-lia-border-medium"
          )}
          onMouseDown={startResize}
          title="Arrastar para redimensionar sidebar"
        >
          {/* Indicador visual mais sutil */}
          <div className="absolute inset-y-0 right-0 w-px bg-lia-interactive-active group-hover:bg-lia-border-medium transition-colors motion-reduce:transition-none duration-200" />

          {/* Área de hover expandida para facilitar o clique */}
          <div className="absolute top-0 -right-2 w-4 h-full" />
        </div>
      )}

      {/* Indicador visual de atalho */}
      {isCollapsed && !isTemporaryExpanded && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-lia-bg-inverse text-lia-text-inverse text-xs px-2 py-1 rounded-md opacity-0 hover:opacity-100 transition-opacity motion-reduce:transition-none duration-200 pointer-events-none">
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
    </div>
  )
}
