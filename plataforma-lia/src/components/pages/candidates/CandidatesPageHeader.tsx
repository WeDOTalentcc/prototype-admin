"use client"

import { Button } from "@/components/ui/button"
import { Users, Plus, Search, Bookmark } from "lucide-react"
import { CandidateTabs } from "@/components/pages/candidates/CandidateTabs"

interface Tab {
  id: string
  label: string
  icon?: React.ComponentType<{ className?: string }>
  count?: number
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
    <div className="flex-shrink-0 px-4 pt-3 pb-0 bg-white dark:bg-lia-bg-primary">
      {/* Header Principal - Padrão Gestão de Vagas */}
      <div className="flex items-center justify-between mb-0.5">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
              <Users className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              Funil de Talentos
            </h1>
          </div>
        </div>
        <div className="flex gap-2">
          {/* Botão Novo Candidato - visível em todas as abas */}
          <Button
            className="gap-2 h-8 px-3 font-medium"
            onClick={onAddCandidate}
          >
            <Plus className="w-4 h-4" />
            Novo Candidato
          </Button>

          {/* Botões específicos por aba */}
          {activeTab === 'search' && showSearchResults && (
            <>
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={onNewSearch}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>

              {/* Botão para salvar busca atual */}
              {(searchTerm || quickFilters.size > 0 || getActiveAdvancedFiltersCount() > 0) && (
                <Button
                  variant="outline"
                  className="gap-2 h-8 px-3"
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
              className="gap-2 h-8 px-3"
              onClick={onNewSearch}
            >
              <Search className="w-4 h-4" />
              Nova Busca
            </Button>
          )}
        </div>
      </div>

      {/* Sistema de Abas - extraído para CandidateTabs (Sprint F5) */}
      <CandidateTabs
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={onTabChange}
      />
    </div>
  )
}
