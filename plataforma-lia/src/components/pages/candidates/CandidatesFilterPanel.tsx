"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { X, Search } from "lucide-react"
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
  onReSearchWithFilters,
}: CandidatesFilterPanelProps) {
  const t = useTranslations('candidates.filters')

  return (
    <div data-testid="candidates-filter-panel" className="flex-shrink-0 w-80 transition-colors motion-reduce:transition-none duration-300">
      <div className="bg-lia-bg-primary rounded-xl h-[calc(100vh-9rem)] overflow-hidden">
        <div className="p-4 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-lia-text-primary">
              {t('refineResults')}
            </h3>
            <p className="text-xs mt-0.5 text-lia-text-primary">
              {activeFiltersCount > 0
                ? (activeFiltersCount > 1
                    ? t('activeFiltersPlural', { count: activeFiltersCount })
                    : t('activeFiltersSingular', { count: activeFiltersCount }))
                : t('filterHint')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none text-lia-text-primary hover:text-lia-text-primary hover:bg-lia-bg-tertiary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan"
            aria-label={t('closePanel')}
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
        {onReSearchWithFilters && activeFiltersCount > 0 && (
          <div className="p-4 border-t border-lia-border-subtle">
            <button
              type="button"
              data-testid="re-search-with-filters-btn"
              onClick={onReSearchWithFilters}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
            >
              <Search className="w-4 h-4" aria-hidden="true" />
              {t('reSearchWithFilters')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
