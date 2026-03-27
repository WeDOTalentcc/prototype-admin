"use client"

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

export function CandidateTabs({ tabs, activeTab, onTabChange }: CandidateTabsProps) {
  return (
    <div className="mb-0">
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex items-center space-x-6 nav-tabs" aria-label="Tabs" role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              role="tab"
              className={`group inline-flex items-center gap-2 py-2 px-1 border-b-2 tab-button ${
                activeTab === tab.id
                  ? 'border-gray-950 text-gray-950 dark:border-gray-50 dark:text-gray-50'
                  : 'border-transparent text-gray-800 hover:text-gray-950 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <span>{tab.label}</span>
              {tab.comingSoon && (
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  style={{ backgroundColor: 'var(--gray-100)', color: 'var(--gray-700)' }}
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
}
