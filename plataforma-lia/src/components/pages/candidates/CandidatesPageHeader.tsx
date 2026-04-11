"use client"

import { Button } from "@/components/ui/button"
import { Plus, Search, Bookmark } from "lucide-react"
import { PageTabNavigation } from "@/components/ui/page-tab-navigation"

interface Tab {
  id: string
  label: string
  icon?: React.ComponentType<{ className?: string }>
  count?: number
  comingSoon?: boolean
}

interface CandidatesPageHeaderProps {
  tabs: Tab[]
  activeTab: string
  showSearchResults: boolean
  searchTerm: string
  quickFilters: Set<string>
  getActiveAdvancedFiltersCount: () => number
  onTabChange: (tab: string) => void
  onAddCandidate: () => void
  onNewSearch: () => void
  onSaveCurrentSearch: () => void
}

export function CandidatesPageHeader({
  tabs,
  activeTab,
  showSearchResults,
  searchTerm,
  quickFilters,
  getActiveAdvancedFiltersCount,
  onTabChange,
  onAddCandidate,
  onNewSearch,
  onSaveCurrentSearch,
}: CandidatesPageHeaderProps) {
  return (
    <div data-testid="candidates-page-header" className="flex-shrink-0 px-4 pt-3 pb-0 bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-lg font-semibold text-lia-text-primary">
          Funil de Talentos
        </h1>
        <div className="flex gap-2">
          {/* Botão Novo Candidato - visível em todas as abas */}
          <Button
            data-testid="new-candidate-btn"
            className="gap-2 h-8 px-3 font-medium hover:bg-lia-interactive-hover transition-colors cursor-pointer"
            onClick={onAddCandidate}
          >
            <Plus className="w-4 h-4" />
            Novo Candidato
          </Button>

          {/* Botões específicos por aba */}
          {activeTab === 'search' && showSearchResults && (
            <>
              <Button
                data-testid="new-search-btn"
                variant="outline"
                className="gap-2 h-8 px-3 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={onNewSearch}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>

              {/* Botão para salvar busca atual */}
              {(searchTerm || quickFilters.size > 0 || getActiveAdvancedFiltersCount() > 0) && (
                <Button
                  data-testid="save-search-btn"
                  variant="outline"
                  className="gap-2 h-8 px-3 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                  onClick={onSaveCurrentSearch}
                  title="Salvar esta busca para reutilizar"
                >
                  <Bookmark className="w-4 h-4" />
                  Salvar Busca
                </Button>
              )}
            </>
          )}

          {(activeTab === 'favorites' || activeTab === 'history' || activeTab === 'saved-searches') && (
            <Button
              variant="outline"
              className="gap-2 h-8 px-3 hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              onClick={onNewSearch}
            >
              <Search className="w-4 h-4" />
              Nova Busca
            </Button>
          )}
        </div>
      </div>

      <PageTabNavigation
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={onTabChange}
      />
    </div>
  )
}
