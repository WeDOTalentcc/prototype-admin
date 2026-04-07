"use client"
import React from "react"
import { Filter, Check, Lightbulb } from "lucide-react"
import { Button } from "@/components/ui/button"

interface TabFiltrosProps {
  activeSearchFilters: Record<string, Record<string, unknown>>
  setActiveSearchFilters: (v: Record<string, Record<string, unknown>>) => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (v: boolean) => void
}

export const TabFiltros = React.memo(function TabFiltros({
  activeSearchFilters,
  setActiveSearchFilters,
  showTableFiltersPanel,
  setShowTableFiltersPanel,
}: TabFiltrosProps) {
  const hasActiveFilters = Object.values(activeSearchFilters).some(category =>
    Object.values(category as Record<string, unknown>).some(v => v === true || (typeof v === 'string' && v.length > 0))
  )

  return (
    <div data-testid="tab-filtros" className="space-y-4 overflow-y-auto flex-1 p-4">
      <div className="p-2.5 rounded-md bg-white border border-lia-border-subtle">
        <div className="flex items-start gap-2">
          <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
          <p className="text-xs text-lia-text-secondary">
            <strong>Dica:</strong> Use os filtros avan\u00e7ados para refinar sua busca por localiza\u00e7\u00e3o, experi\u00eancia, skills, idiomas e muito mais.
          </p>
        </div>
      </div>
      {hasActiveFilters && (
        <div className="p-3 rounded-md border bg-status-success/5 border-status-success/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-status-success" />
              <span className="text-xs font-medium text-status-success">Filtros ativos</span>
            </div>
            <button
              onClick={() => setActiveSearchFilters({
                ppiOptions: {}, general: {}, locations: {}, job: {},
                company: {}, skills: {}, education: {}, languages: {}
              })}
              className="text-xs text-lia-text-primary hover:text-status-error transition-colors motion-reduce:transition-none"
            >
              Limpar todos
            </button>
          </div>
        </div>
      )}
      <Button
        className={`w-full h-12 !text-sm font-semibold text-lia-bg-secondary ${showTableFiltersPanel ? 'bg-lia-text-primary' : 'bg-lia-text-secondary'}`}
        onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
      >
        <Filter className="w-4 h-4 mr-2" />
        {showTableFiltersPanel ? 'Fechar Filtros' : 'Abrir Filtros Avan\u00e7ados'}
      </Button>
      {!showTableFiltersPanel && (
        <p className="text-xs text-lia-text-primary text-center mt-2" aria-live="polite" aria-atomic="true">
          Os filtros aparecer\u00e3o ao lado da tabela de candidatos
        </p>
      )}
    </div>
  )
})

TabFiltros.displayName = "TabFiltros"
