"use client"

import { memo } from 'react'

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
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-full transition-colors tab-button ${
              activeTab === tab.id
                ? 'bg-gray-100 text-gray-900 dark:bg-lia-bg-elevated dark:text-lia-text-primary'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:text-lia-text-tertiary dark:hover:text-lia-text-secondary dark:hover:bg-lia-bg-secondary'
            }`}
          >
            <span>{tab.label}</span>
            {tab.comingSoon && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-200 text-gray-600 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary">
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
