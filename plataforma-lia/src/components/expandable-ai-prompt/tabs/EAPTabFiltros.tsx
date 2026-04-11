"use client"

import React from 'react'
import { type SearchFilters } from "@/components/search/advanced-filters-modal"
import { Filter, Search } from "lucide-react"
import { useExpandableAIPromptCore } from "../useExpandableAIPromptCore"

// NOTE: SearchFilters doesn't formally include 'locations' in its type definition,
// but the runtime data may contain it (pre-existing issue across the codebase).
// We use a local extended type to match the actual runtime shape.
type SearchFiltersExtended = SearchFilters & {
  locations?: { locations?: string[] }
}

type EAPTabFiltrosProps = Pick<
  ReturnType<typeof useExpandableAIPromptCore>,
  'advancedFilters' | 'setAdvancedFilters' | 'setShowAdvancedFiltersModal' | 'onCommand'
>

export const EAPTabFiltros = React.memo(function EAPTabFiltros(props: EAPTabFiltrosProps) {
  const { advancedFilters, setAdvancedFilters, setShowAdvancedFiltersModal, onCommand } = props

  const filtersExt = advancedFilters as SearchFiltersExtended

  const activeCount = [
    filtersExt.locations?.locations?.length || 0,
    advancedFilters.job?.titles?.length || 0,
    advancedFilters.job?.levels?.length || 0,
    advancedFilters.company?.companyItems?.length || 0,
    advancedFilters.skills?.skillItems?.length || 0,
    advancedFilters.education?.degrees?.length || 0,
    advancedFilters.languages?.languages?.length || 0,
    advancedFilters.general?.minExperience ? 1 : 0,
    advancedFilters.general?.maxExperience ? 1 : 0
  ].reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-3">
      <p className="text-xs lia-body">Configure filtros avançados para refinar sua busca</p>

      {/* Resumo de filtros ativos */}
      {activeCount > 0 && (
        <div className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-lia-text-secondary">
              {activeCount} filtro{activeCount > 1 ? 's' : ''} ativo{activeCount > 1 ? 's' : ''}
            </span>
            <button
              onClick={() => setAdvancedFilters({
                ppiOptions: {},
                general: {},
                job: {},
                company: {},
                skills: {},
                education: {},
                languages: {}
              } as SearchFilters)}
              className="text-xs text-lia-text-primary hover:text-status-error"
            >
              Limpar
            </button>
          </div>
        </div>
      )}

      {/* Botão para abrir modal completo */}
      <button
        className="w-full px-4 py-3 bg-lia-bg-primary border-2 border-dashed border-lia-border-subtle rounded-xl hover:border-lia-border-default hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
        onClick={() => setShowAdvancedFiltersModal(true)}
      >
        <Filter className="w-4 h-4 text-lia-text-primary" />
        <span className="text-xs text-lia-text-primary">Abrir Filtros Avançados</span>
      </button>

      {/* Botão de aplicar filtros */}
      <button
        className="w-full px-3 py-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active text-xs rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
        onClick={() => {
          onCommand(JSON.stringify(advancedFilters), 'apply_filters')
        }}
      >
        <Search className="w-3.5 h-3.5" />
        Buscar com Filtros
      </button>
    </div>
  )
})
EAPTabFiltros.displayName = 'EAPTabFiltros'
