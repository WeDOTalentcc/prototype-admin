"use client"

import { memo } from 'react'
import { tabStyles } from "@/lib/design-tokens"
import { useTranslations } from "next-intl"

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
  const t = useTranslations('candidates')
  return (
    <div data-testid="candidate-tabs" className="mb-0">
      <nav data-testid="candidate-tabs-nav" className="flex gap-1 p-1 bg-lia-bg-secondary rounded-lg w-fit" aria-label="Tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            data-testid={`candidate-tab-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
              activeTab === tab.id
                ? 'bg-lia-bg-primary text-lia-text-primary shadow-sm dark:bg-lia-bg-primary'
                : 'text-lia-text-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-tertiary'
            }`}
          >
            {tab.label}
            {tab.comingSoon && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-lia-interactive-active text-lia-text-secondary dark:bg-lia-bg-secondary">
                {t('tabs.comingSoon')}
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
