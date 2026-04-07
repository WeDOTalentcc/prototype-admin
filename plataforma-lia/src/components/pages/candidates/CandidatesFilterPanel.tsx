"use client"

import React from "react"
import { X } from "lucide-react"
import { FilterSectionsBasic } from "./FilterSectionsBasic"
import { FilterSectionsProfile } from "./FilterSectionsProfile"
import { FilterSectionsAdvanced } from "./FilterSectionsAdvanced"
import type { CandidatesFilterPanelProps } from "./types"

export function CandidatesFilterPanel({
  tableFilters,
  setTableFilters,
  searchSortBy,
  onSortChange,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  activeFiltersCount,
  onToggleFilter,
  onClearAll,
  onClose,
}: CandidatesFilterPanelProps) {
  return (
    <div data-testid="candidates-filter-panel" className="flex-shrink-0 w-80 transition-colors motion-reduce:transition-none duration-300">
      <div className="bg-lia-bg-primary rounded-md h-[calc(100vh-9rem)] overflow-hidden">
        <div className="p-4 flex items-center justify-between border-b border-lia-border-subtle">
          <div>
            <h3 className="text-sm font-semibold text-lia-text-primary">
              Refinar Resultados
            </h3>
            <p className="text-xs mt-0.5 text-lia-text-primary">
              {activeFiltersCount > 0
                ? `${activeFiltersCount} filtro${activeFiltersCount > 1 ? "s" : ""} ativo${activeFiltersCount > 1 ? "s" : ""}`
                : "Filtre os resultados exibidos"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none text-lia-text-primary hover:text-lia-text-primary hover:bg-lia-bg-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan"
            aria-label="Fechar painel de filtros"
            data-dismiss="true"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto max-h-[calc(100vh-14rem)]">
          <FilterSectionsBasic
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            searchSortBy={searchSortBy}
            onSortChange={onSortChange}
            onToggleFilter={onToggleFilter}
          />

          <FilterSectionsProfile
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            onToggleFilter={onToggleFilter}
          />

          <FilterSectionsAdvanced
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            newSoftSkillFilter={newSoftSkillFilter}
            setNewSoftSkillFilter={setNewSoftSkillFilter}
            newCertificationFilter={newCertificationFilter}
            setNewCertificationFilter={setNewCertificationFilter}
            onClearAll={onClearAll}
          />
        </div>
      </div>
    </div>
  )
}
