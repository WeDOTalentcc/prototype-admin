"use client"

import { useTranslations } from "next-intl"
import { Filter, X, ArrowUpDown } from "lucide-react"
import { useKanbanStore } from "@/stores/kanban-store"
import { KANBAN_SORT_FIELDS, type KanbanSortField } from "./utils/kanbanHelpers"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { textStyles } from "@/lib/design-tokens"

const SORT_FIELD_KEYS: Array<{ value: KanbanSortField; key: string }> = [
  { value: 'score', key: 'sortFieldScore' },
  { value: 'name', key: 'sortFieldName' },
  { value: 'appliedDate', key: 'sortFieldAppliedDate' },
  { value: 'fitScore', key: 'sortFieldFitScore' },
  { value: 'notaLiaGeral', key: 'sortFieldNotaLiaGeral' },
] as const

const STATUS_KEYS = [
  { value: 'novo', key: 'statusNew' },
  { value: 'em_analise', key: 'statusInAnalysis' },
  { value: 'aguardando_aprovacao', key: 'statusAwaitingApproval' },
  { value: 'triado_aprovado', key: 'statusScreenedApproved' },
  { value: 'negociacao', key: 'statusNegotiation' },
] as const

const ORIGIN_KEYS = [
  { value: 'web', label: 'Web' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'sourcing', key: 'originActiveSourcing' },
  { value: 'ats', label: 'ATS' },
] as const

const WORK_MODEL_KEYS = [
  { value: 'remoto', key: 'workModelRemote' },
  { value: 'hibrido', key: 'workModelHybrid' },
  { value: 'presencial', key: 'workModelOnsite' },
] as const

interface KanbanFiltersPanelProps {
  open: boolean
  onClose: () => void
  scoreMin: number
  onScoreMinChange: (value: number) => void
  statusFilter: string[]
  onStatusFilterChange: (value: string[]) => void
  originFilter: string[]
  onOriginFilterChange: (value: string[]) => void
  workModelFilter: string[]
  onWorkModelFilterChange: (value: string[]) => void
}

export function KanbanFiltersPanel({
  open,
  onClose,
  scoreMin,
  onScoreMinChange,
  statusFilter,
  onStatusFilterChange,
  originFilter,
  onOriginFilterChange,
  workModelFilter,
  onWorkModelFilterChange,
}: KanbanFiltersPanelProps) {
  const t = useTranslations('kanban')
  const kanbanSortBy = useKanbanStore((s) => s.kanbanSortBy)
  const kanbanSortOrder = useKanbanStore((s) => s.kanbanSortOrder)
  const setKanbanSortBy = useKanbanStore((s) => s.setKanbanSortBy)
  const setKanbanSortOrder = useKanbanStore((s) => s.setKanbanSortOrder)
  if (!open) return null

  const handleClear = () => {
    onScoreMinChange(0)
    onStatusFilterChange([])
    onWorkModelFilterChange([])
    onOriginFilterChange([])
    setKanbanSortBy('score')
    setKanbanSortOrder('desc')
  }

  const toggleItem = (list: string[], value: string, setter: (v: string[]) => void) => {
    setter(list.includes(value) ? list.filter(i => i !== value) : [...list, value])
  }

  return (
    <div data-testid="filters-panel" className="flex-shrink-0 w-72 transition-colors motion-reduce:transition-none duration-300">
      <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
        {/* Header */}
        <div className="flex-shrink-0 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-lia-text-secondary" />
              <h3 className={textStyles.title}>{t('advancedFilters')}</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 hover:bg-lia-bg-tertiary"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </Button>
          </div>
          <p className={`${textStyles.description} mt-1`}>{t('refineCandidates')}</p>
        </div>

        {/* Filtros - Scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Sort — GAP-03-006 */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary flex items-center gap-1.5">
              <ArrowUpDown className="w-3.5 h-3.5" />
              {t('sortLabel')}
            </label>
            <select
              data-testid="kanban-sort-field"
              value={kanbanSortBy}
              onChange={(e) => setKanbanSortBy(e.target.value as KanbanSortField)}
              className="w-full px-2 py-1.5 text-xs rounded-md border border-lia-border-default bg-lia-bg-primary text-lia-text-primary focus:ring-1 focus:ring-lia-btn-primary-bg/20"
            >
              {SORT_FIELD_KEYS.map(({ value, key }) => (
                <option key={value} value={value}>{t(key)}</option>
              ))}
            </select>
            <div className="flex gap-1.5">
              <button
                data-testid="kanban-sort-asc"
                onClick={() => setKanbanSortOrder('asc')}
                className={`flex-1 px-2 py-1 text-xs rounded-md border transition-colors motion-reduce:transition-none ${
                  kanbanSortOrder === 'asc'
                    ? 'bg-lia-btn-primary-bg text-white border-lia-btn-primary-bg'
                    : 'bg-lia-bg-primary text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-secondary'
                }`}
              >
                {t('sortOrderAsc')}
              </button>
              <button
                data-testid="kanban-sort-desc"
                onClick={() => setKanbanSortOrder('desc')}
                className={`flex-1 px-2 py-1 text-xs rounded-md border transition-colors motion-reduce:transition-none ${
                  kanbanSortOrder === 'desc'
                    ? 'bg-lia-btn-primary-bg text-white border-lia-btn-primary-bg'
                    : 'bg-lia-bg-primary text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-secondary'
                }`}
              >
                {t('sortOrderDesc')}
              </button>
            </div>
          </div>

          {/* Score */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">
              {t('minLIAScore')}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="100"
                value={scoreMin}
                onChange={(e) => onScoreMinChange(Number(e.target.value))}
                className="flex-1 h-1.5 bg-lia-interactive-active rounded-md appearance-none cursor-pointer accent-lia-btn-primary-bg"
              />
              <span className="text-xs text-lia-text-secondary w-12 text-right">{scoreMin}%</span>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">{t('statusLabel')}</label>
            <div className="space-y-1.5">
              {STATUS_KEYS.map(({ value, key }) => (
                <label key={value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={statusFilter.includes(value)}
                    onChange={() => toggleItem(statusFilter, value, onStatusFilterChange)}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default text-lia-text-primary focus:ring-lia-btn-primary-bg/20"
                  />
                  <span className="text-xs text-lia-text-secondary">{t(key)}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Origem */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">{t('originLabel')}</label>
            <div className="space-y-1.5">
              {ORIGIN_KEYS.map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={originFilter.includes(opt.value)}
                    onChange={() => toggleItem(originFilter, opt.value, onOriginFilterChange)}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default text-lia-text-primary focus:ring-lia-btn-primary-bg/20"
                  />
                  <span className="text-xs text-lia-text-secondary">{'key' in opt ? t(opt.key) : opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Modelo de Trabalho */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary">{t('workModel')}</label>
            <div className="space-y-1.5">
              {WORK_MODEL_KEYS.map(({ value, key }) => (
                <label key={value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={workModelFilter.includes(value)}
                    onChange={() => toggleItem(workModelFilter, value, onWorkModelFilterChange)}
                    className="w-3.5 h-3.5 rounded-xl border-lia-border-default text-lia-text-primary focus:ring-lia-btn-primary-bg/20"
                  />
                  <span className="text-xs text-lia-text-secondary">{t(key)}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex gap-2">
            <button
              onClick={handleClear}
              className="flex-1 px-3 py-2 text-xs font-medium text-lia-text-secondary bg-lia-bg-primary border border-lia-border-subtle rounded-xl hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            >
              {t('clear')}
            </button>
            <button
              onClick={onClose}
              className="flex-1 px-3 py-2 text-xs font-medium text-white rounded-md transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
            >
              {t('applyFilters')}
            </button>
          </div>
        </div>
      </Card>
    </div>
  )
}
