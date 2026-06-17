"use client"
import React from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Filter, X } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"

interface DynamicStageItem {
  id: string
  name: string
  displayName: string
  color?: string
}

export interface KanbanTableFiltersPanelProps {
  onShowTableFiltersPanelChange: (value: boolean) => void
  dynamicStages: DynamicStageItem[]
  tableStageFilter: string[]
  onTableStageFilterChange: (value: string[]) => void
}

export const KanbanTableFiltersPanel = React.memo(function KanbanTableFiltersPanel({
  onShowTableFiltersPanelChange,
  dynamicStages,
  tableStageFilter,
  onTableStageFilterChange,
}: KanbanTableFiltersPanelProps) {
  const t = useTranslations('kanban')
  return (
    <div className="flex-shrink-0 w-72 transition-colors motion-reduce:transition-none duration-300">
      <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
        {/* Header do Painel de Filtros */}
        <div className="flex-shrink-0 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-lia-text-secondary" />
              <h3 className={textStyles.title}>
                {t('advancedFilters')}
              </h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onShowTableFiltersPanelChange(false)}
              className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </Button>
          </div>
          <p className={`${textStyles.description} mt-1`}>
            {t('refineCandidates')}
          </p>
        </div>

        {/* Conteúdo dos Filtros - Scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Filtro por Etapa */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">
              {t('pipelineStage')}
            </label>
            <div className="space-y-1.5">
              {dynamicStages.map((stage) => (
                <label key={stage.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={tableStageFilter.includes(stage.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onTableStageFilterChange([...tableStageFilter, stage.id])
                      } else {
                        onTableStageFilterChange(tableStageFilter.filter(s => s !== stage.id))
                      }
                    }}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default text-lia-text-primary focus:ring-lia-btn-primary-bg/20"
                  />
                  <span className="text-xs text-lia-text-secondary">
                    {stage.displayName}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Filtro por Score */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">
              {t('minLIAScore')}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="100"
                defaultValue="0"
                className="flex-1 h-1.5 bg-lia-interactive-active rounded-md appearance-none cursor-pointer accent-lia-btn-primary-bg"
              />
              <span className="text-xs text-lia-text-secondary w-8 text-right">0%</span>
            </div>
          </div>

          {/* Filtro por Status */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">
              {t('statusLabel')}
            </label>
            <div className="space-y-1.5">
              {[t('statusNew'), t('statusInAnalysis'), t('statusAwaitingApproval'), t('statusScreenedApproved'), t('statusNegotiation')].map((status) => (
                <label key={status} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default text-lia-text-primary focus:ring-lia-btn-primary-bg/20"
                  />
                  <span className="text-xs text-lia-text-secondary">
                    {status}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Filtro por Modelo de Trabalho */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">
              {t('workModel')}
            </label>
            <div className="space-y-1.5">
              {[t('workModelRemote'), t('workModelHybrid'), t('workModelOnsite')].map((modelo) => (
                <label key={modelo} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default text-lia-text-primary focus:ring-lia-btn-primary-bg/20"
                  />
                  <span className="text-xs text-lia-text-secondary">
                    {modelo}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Footer com Ações */}
        <div className="flex-shrink-0 p-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex gap-2">
            <button
              onClick={() => {
                onTableStageFilterChange([])
              }}
              className="flex-1 px-3 py-2 text-xs font-medium text-lia-text-secondary bg-lia-bg-primary border border-lia-border-subtle rounded-xl hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            >
              {t('clear')}
            </button>
            <button
              onClick={() => onShowTableFiltersPanelChange(false)}
              className="flex-1 px-3 py-2 text-xs font-medium text-white rounded-md transition-colors motion-reduce:transition-none bg-lia-btn-primary-hover"
            >
              {t('applyFilters')}
            </button>
          </div>
        </div>
      </Card>
    </div>
  )
})
KanbanTableFiltersPanel.displayName = "KanbanTableFiltersPanel"
