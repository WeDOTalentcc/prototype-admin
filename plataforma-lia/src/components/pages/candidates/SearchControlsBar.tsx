"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { ArrowUpDown, CheckCircle, Target, ChevronsLeftRight } from "lucide-react"
import type { TableColumn } from "./CandidateSearchResultsView.types"

export interface SearchControlsBarProps {
  selectedCandidatesForBatch: Set<string>
  searchSortBy: string
  sortedCandidatesLength: number
  selectAllCandidates: () => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (value: boolean) => void
  getActiveTableFiltersCount: () => number
  showColumnConfig: boolean
  onToggleColumnConfig: () => void
  tableColumns: TableColumn[]
}

export function SearchControlsBar({
  selectedCandidatesForBatch,
  searchSortBy,
  sortedCandidatesLength,
  selectAllCandidates,
  showTableFiltersPanel,
  setShowTableFiltersPanel,
  getActiveTableFiltersCount,
  showColumnConfig,
  onToggleColumnConfig,
  tableColumns,
}: SearchControlsBarProps) {
  return (
    <div className="flex items-center gap-3">
      {selectedCandidatesForBatch.size > 0 && (
        <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary border-0 text-xs font-medium">
          🎯 {selectedCandidatesForBatch.size}
        </Badge>
      )}

      {searchSortBy !== 'relevance' && (
        <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary border-0 text-xs font-medium gap-1">
          <ArrowUpDown className="w-3 h-3" />
          {searchSortBy === 'score_desc' ? 'Maior Score' :
           searchSortBy === 'score_asc' ? 'Menor Score' :
           searchSortBy === 'name_asc' ? 'Nome A-Z' :
           searchSortBy === 'name_desc' ? 'Nome Z-A' :
           searchSortBy === 'experience_desc' ? 'Maior Experiência' : 'Relevância'}
        </Badge>
      )}

      {selectedCandidatesForBatch.size === 0 && sortedCandidatesLength > 0 && (
        <button
          onClick={selectAllCandidates}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-lia-text-primary bg-lia-bg-primary border border-lia-border-subtle rounded-full hover:bg-gray-50 transition-colors motion-reduce:transition-none"
        >
          <CheckCircle className="w-4 h-4 text-lia-text-tertiary" />
          Selecionar Todos
        </button>
      )}

      <button
        onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
        className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none ${
          showTableFiltersPanel
            ? 'bg-gray-900 text-white hover:bg-gray-800'
            : 'text-lia-text-primary bg-lia-bg-primary border border-lia-border-subtle hover:bg-gray-50'
        }`}
      >
        <Target className="w-4 h-4" />
        Filtros
        {getActiveTableFiltersCount() > 0 && (
          <span className={`text-xs font-medium ${showTableFiltersPanel ? 'text-lia-text-disabled' : 'text-lia-text-tertiary'}`}>
            {getActiveTableFiltersCount()}
          </span>
        )}
      </button>

      <button
        onClick={onToggleColumnConfig}
        title="Configurar colunas da tabela"
        className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors motion-reduce:transition-none ${
          showColumnConfig
            ? 'bg-gray-900 text-white hover:bg-gray-800'
            : 'text-lia-text-primary bg-lia-bg-primary border border-lia-border-subtle hover:bg-gray-50'
        }`}
      >
        <ChevronsLeftRight className="w-4 h-4" />
        Colunas
        <span className={`text-xs font-medium ${showColumnConfig ? 'text-lia-text-disabled' : 'text-lia-text-tertiary'}`}>
          {tableColumns.filter(col => col.visible && col.id !== 'acoes').length}
        </span>
      </button>
    </div>
  )
}
