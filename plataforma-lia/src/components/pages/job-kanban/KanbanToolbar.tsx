"use client"

import React from "react"
import { useTranslations } from "next-intl"
import {
  Layers3, ListChecks, Search,
  Target, X, ChevronsLeftRight, CheckCircle, XCircle
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { ViewToggle } from "@/components/ui/view-toggle"
import { ToolbarButton } from "@/components/ui/toolbar-button"

interface KanbanToolbarProps {
  searchQuery: string
  setSearchQuery: (v: string) => void
  viewMode: string
  setViewMode: (v: string) => void
  showKanbanFiltersPanel: boolean
  setShowKanbanFiltersPanel: (v: boolean) => void
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: (v: boolean) => void
  showColumnConfig: boolean
  setShowColumnConfig: (v: boolean) => void
  tableColumns: Array<{ visible: boolean }>
  selectedCandidates: Set<string>
  setSelectedCandidates: (v: Set<string>) => void
  allTableCandidates: Array<Record<string, unknown>>
  candidatesData: Record<string, Array<Record<string, unknown>>>
  tableStageFilter: string[]
  kanbanScoreMin: number
  kanbanStatusFilter: string[]
  kanbanWorkModelFilter: string[]
  kanbanOriginFilter: string[]
}

export function KanbanToolbar({
  searchQuery,
  setSearchQuery,
  viewMode,
  setViewMode,
  showKanbanFiltersPanel,
  setShowKanbanFiltersPanel,
  showTableFiltersPanel,
  setShowTableFiltersPanel,
  showColumnConfig,
  setShowColumnConfig,
  tableColumns,
  selectedCandidates,
  setSelectedCandidates,
  allTableCandidates,
  candidatesData,
  tableStageFilter,
  kanbanScoreMin,
  kanbanStatusFilter,
  kanbanWorkModelFilter,
  kanbanOriginFilter,
}: KanbanToolbarProps) {
  const t = useTranslations('kanban')
  const getVisibleCandidates = () => {
    let visibleCandidates = allTableCandidates
    if (viewMode === "kanban") {
      visibleCandidates = allTableCandidates.filter(candidate => {
        if (searchQuery) {
          const query = searchQuery.toLowerCase()
          const matchesSearch =
            ((candidate.name as string | undefined)?.toLowerCase() ?? '').includes(query) ||
            (candidate.role as string | undefined)?.toLowerCase().includes(query) ||
            (candidate.company as string | undefined)?.toLowerCase().includes(query) ||
            (candidate.location as string | undefined)?.toLowerCase().includes(query) ||
            (candidate.current_company as string | undefined)?.toLowerCase().includes(query)
          if (!matchesSearch) return false
        }
        if (kanbanScoreMin > 0 && candidate.score && (candidate.score as number) < kanbanScoreMin) return false
        if (kanbanStatusFilter.length > 0 && candidate.status) {
          const candidateStatus = ((candidate.status as string | undefined)?.toLowerCase() ?? '').replace(/ /g, '_')
          if (!kanbanStatusFilter.includes(candidateStatus)) return false
        }
        if (kanbanWorkModelFilter.length > 0 && candidate.workModel) {
          const workModel = (candidate.workModel as string | undefined)?.toLowerCase() ?? ''
          if (!kanbanWorkModelFilter.includes(workModel)) return false
        }
        if (kanbanOriginFilter.length > 0) {
          const candidateOrigin = ((candidate.origin as string | undefined) || '').toLowerCase()
          if (!candidateOrigin || !kanbanOriginFilter.includes(candidateOrigin)) return false
        }
        return true
      })
    } else {
      visibleCandidates = allTableCandidates.filter(c => {
        if (tableStageFilter.length > 0) {
          const stage =
            candidatesData.sourcing?.includes(c) ? 'sourcing' :
            candidatesData.screening?.includes(c) ? 'screening' :
            candidatesData.interview_hr?.includes(c) ? 'interview_hr' :
            candidatesData.interview_technical?.includes(c) ? 'interview_technical' :
            candidatesData.interview_manager?.includes(c) ? 'interview_manager' :
            candidatesData.offer?.includes(c) ? 'offer' :
            candidatesData.hired?.includes(c) ? 'hired' :
            candidatesData.rejected?.includes(c) ? 'rejected' :
            candidatesData.offer_declined?.includes(c) ? 'offer_declined' : ''
          if (!tableStageFilter.includes(stage)) return false
        }
        return true
      })
    }
    return visibleCandidates
  }

  const handleSelectAll = () => {
    const visibleCandidates = getVisibleCandidates()
    if (selectedCandidates.size === visibleCandidates.length && visibleCandidates.length > 0) {
      setSelectedCandidates(new Set())
    } else {
      setSelectedCandidates(new Set(visibleCandidates.map(c => c.id as string)))
    }
  }

  const visibleCandidates = getVisibleCandidates()
  const allSelected = selectedCandidates.size === visibleCandidates.length && visibleCandidates.length > 0

  return (
    <div className="flex-shrink-0 bg-lia-bg-primary dark:bg-lia-bg-secondary px-4 py-2">
      <div className="w-full px-4 flex items-center justify-end gap-2">
        {/* Ações do lado direito */}
        <div className="flex items-center gap-2">
          {/* Barra de Busca */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
            <Input
              type="text"
              placeholder={t('searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-sm w-48"
              aria-label={t('searchCandidatesAria')}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-lia-bg-tertiary rounded-xl"
                aria-label={t('clearSearchAria')}
              >
                <X className="w-3 h-3 text-lia-text-primary" aria-hidden="true" />
              </button>
            )}
          </div>

          {/* Botões de Alternância de Visualização */}
          <ViewToggle
            value={viewMode}
            onChange={(v) => setViewMode(v)}
            ariaLabel="Alternar visualização"
            size="md"
            options={[
              { value: 'kanban', label: t('kanbanView'), icon: Layers3 },
              { value: 'table', label: t('tableView'), icon: ListChecks },
            ]}
          />

          {/* Botão Selecionar Todos */}
          <ToolbarButton
            size="md"
            onClick={handleSelectAll}
            icon={
              allSelected ? (
                <XCircle className="text-lia-text-tertiary" />
              ) : (
                <CheckCircle className="text-lia-text-tertiary" />
              )
            }
          >
            {allSelected ? t('deselectAll') : t('selectAllCount', { count: visibleCandidates.length })}
          </ToolbarButton>

          {/* Botão Filtros */}
          <ToolbarButton
            size="md"
            active={viewMode === "kanban" ? showKanbanFiltersPanel : showTableFiltersPanel}
            onClick={() => {
              if (viewMode === "kanban") {
                setShowKanbanFiltersPanel(!showKanbanFiltersPanel)
              } else {
                setShowTableFiltersPanel(!showTableFiltersPanel)
              }
            }}
            icon={<Target />}
          >
            {t('filters')}
          </ToolbarButton>

          {viewMode === "table" && (
            <ToolbarButton
              size="md"
              active={showColumnConfig}
              onClick={() => setShowColumnConfig(!showColumnConfig)}
              title={t('configureTableColumns')}
              icon={<ChevronsLeftRight />}
              trailing={
                <span
                  className={`text-xs font-medium ${showColumnConfig ? 'text-lia-text-tertiary' : 'text-lia-text-tertiary'}`}
                  aria-live="polite"
                  aria-atomic="true"
                >
                  {tableColumns.filter(col => col.visible).length}
                </span>
              }
            >
              {t('columns')}
            </ToolbarButton>
          )}
        </div>
      </div>
    </div>
  )
}
