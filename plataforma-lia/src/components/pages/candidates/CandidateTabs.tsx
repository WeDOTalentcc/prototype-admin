"use client"

import { memo } from 'react'
import { tabStyles } from "@/lib/design-tokens"

interface Tab {
  id: string
  label: string
  comingSoon?: boolean
}

interface CandidateTabsProps {
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
}

const CandidateTabs = memo(function CandidateTabs({ tabs, activeTab, onTabChange }: CandidateTabsProps) {
  return (
    <div className="mb-0">
      <nav className="flex items-center gap-1 nav-tabs" aria-label="Tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] ${
              activeTab === tab.id
                ? 'bg-gray-100 text-gray-900 dark:bg-gray-800'
                : 'text-lia-text-secondary hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {tab.label}
            {tab.comingSoon && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-200 text-gray-600 dark:bg-lia-bg-secondary">
                Em Breve
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  )
})
CandidateTabs.displayName = 'CandidateTabs'

export { CandidateTabs }
