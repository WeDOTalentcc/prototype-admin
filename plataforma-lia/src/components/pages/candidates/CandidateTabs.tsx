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
    <div data-testid="candidate-tabs" className="mb-0">
      <nav data-testid="candidate-tabs-nav" className="flex items-center gap-1 nav-tabs" aria-label="Tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            data-testid={`candidate-tab-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer font-['Open_Sans',sans-serif] ${
              activeTab === tab.id
                ? 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-btn-primary-hover'
                : 'text-lia-text-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover'
            }`}
          >
            {tab.label}
            {tab.comingSoon && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-lia-interactive-active text-lia-text-secondary dark:bg-lia-bg-secondary">
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
