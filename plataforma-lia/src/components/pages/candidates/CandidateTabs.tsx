"use client"

import { memo } from 'react'

/**
 * CandidateTabs — barra de navegação de abas do Funil de Talentos.
 *
 * Sprint F5 — extração de componente de candidates-page.tsx.
 * Portabilidade Vue: props → defineProps; onTabChange → emit('tab-change', id).
 */

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
      <div className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
        <nav className="-mb-px flex items-center space-x-6 nav-tabs" aria-label="Tabs" role="tablist">
          {/* TODO Sprint 3: migrar para <Tabs> shadcn */}
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              role="tab"
              className={`group inline-flex items-center gap-2 py-2 px-1 border-b-2 tab-button ${
                activeTab === tab.id
                  ? 'border-gray-950 text-lia-text-primary dark:border-lia-border-medium dark:text-lia-text-primary'
                  : 'border-transparent text-lia-text-primary hover:text-lia-text-primary hover:border-lia-border-default dark:text-lia-text-tertiary dark:hover:text-lia-text-disabled'
              }`}
            >
              <span>{tab.label}</span>
              {tab.comingSoon && (
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  style={{backgroundColor: 'var(--gray-100)', color: 'var(--gray-700)'}}
                >
                  Em Breve
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>
    </div>
  )
})
CandidateTabs.displayName = 'CandidateTabs'

export { CandidateTabs }
