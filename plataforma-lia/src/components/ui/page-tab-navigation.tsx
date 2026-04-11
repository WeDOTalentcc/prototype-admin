"use client"

import { memo } from "react"
import { cn } from "@/lib/utils"

interface PageTab {
  id: string
  label: string
  icon?: React.ComponentType<{ className?: string }>
  count?: number | null
  comingSoon?: boolean
}

interface PageTabNavigationProps {
  tabs: PageTab[]
  activeTab: string
  onTabChange: (tabId: string) => void
  isLoading?: boolean
  className?: string
}

const PageTabNavigation = memo(function PageTabNavigation({
  tabs,
  activeTab,
  onTabChange,
  isLoading = false,
  className,
}: PageTabNavigationProps) {
  return (
    <div className={cn("mb-0", className)}>
      <nav
        className="flex gap-1 p-1 bg-lia-bg-secondary rounded-lg w-fit"
        role="tablist"
        aria-label="Tabs"
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              role="tab"
              aria-selected={isActive}
              className={cn(
                "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer",
                isActive
                  ? "bg-lia-bg-primary text-lia-text-primary shadow-sm"
                  : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
              )}
            >
              {tab.icon && <tab.icon className="w-3.5 h-3.5" />}
              {tab.label}
              {tab.count !== undefined && tab.count !== null && tab.count > 0 && (
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded-full text-[10px] font-bold",
                    isActive
                      ? "bg-lia-interactive-active text-lia-text-primary"
                      : "bg-lia-bg-tertiary text-lia-text-disabled"
                  )}
                >
                  {isLoading ? (
                    <span className="inline-block w-4 h-3 bg-lia-interactive-active rounded animate-pulse motion-reduce:animate-none" />
                  ) : (
                    tab.count
                  )}
                </span>
              )}
              {tab.comingSoon && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-lia-interactive-active text-lia-text-secondary">
                  Em Breve
                </span>
              )}
            </button>
          )
        })}
      </nav>
    </div>
  )
})
PageTabNavigation.displayName = "PageTabNavigation"

export { PageTabNavigation }
export type { PageTab, PageTabNavigationProps }
