"use client"

import { X } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useTranslations } from 'next-intl'

interface ColumnDef {
  id: string
  label: string
  visible: boolean
  category?: string
}

interface ColumnView {
  id: string
  name: string
}

interface ColumnConfigPanelProps {
  open: boolean
  onClose: () => void
  columnConfig: ColumnDef[]
  visibleColumnIds: string[]
  savedColumnViews: ColumnView[]
  toggleColumn: (id: string) => void
  applyColumnView: (id: string) => void
  deleteColumnView: (id: string) => void
  saveColumnView: (name: string) => void
  resetColumnsToDefault: () => void
  onToast?: (message: string) => void
}

export function ColumnConfigPanel({
  open,
  onClose,
  columnConfig,
  visibleColumnIds,
  savedColumnViews,
  toggleColumn,
  applyColumnView,
  deleteColumnView,
  saveColumnView,
  resetColumnsToDefault,
  onToast,
}: ColumnConfigPanelProps) {
  const t = useTranslations('jobs.columnConfig')
  const categoryLabels: Record<string, string> = {
    principais: t('categories.principais'),
    informacoes: t('categories.informacoes'),
    prazos: t('categories.prazos'),
    responsaveis: t('categories.responsaveis'),
    localizacao: t('categories.localizacao'),
    remuneracao: t('categories.remuneracao'),
    divulgacao: t('categories.divulgacao'),
    requisitos: t('categories.requisitos'),
    targeting: t('categories.targeting'),
    metricas: t('categories.metricas'),
  }

  if (!open) return null

  const handleSaveView = () => {
    const name = prompt(t('viewNamePrompt'))
    if (name) {
      saveColumnView(name)
      onToast?.(t('viewSaved', { name }))
    }
  }

  const handleResetColumns = () => {
    resetColumnsToDefault()
    onToast?.(t('columnsReset'))
  }

  return (
    <div className="flex-shrink-0 w-80 transition-colors motion-reduce:transition-none duration-300" data-testid="column-config-panel">
      <Card className="h-full flex flex-col overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="flex-shrink-0 p-4 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-lia-text-primary">{t('title')}</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 hover:bg-lia-btn-primary-bg/10 dark:hover:bg-lia-bg-tertiary/10 rounded-full"
            >
              <X className="w-4 h-4 text-lia-text-primary" />
            </Button>
          </div>
          <p className="text-xs text-lia-text-primary mt-1">
            {t('description', { count: visibleColumnIds.length })}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {savedColumnViews.length > 0 && (
            <div className="mb-4 pb-3 dark:border-lia-border-subtle">
              <h4 className="text-xs font-semibold text-lia-text-primary mb-2">
                {t('savedViews')}
              </h4>
              <div className="space-y-1">
                {savedColumnViews.map(view => (
                  <div key={view.id} className="flex items-center justify-between p-2 hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover rounded-xl">
                    <button
                      onClick={() => applyColumnView(view.id)}
                      className="text-xs text-lia-text-primary hover:text-lia-text-primary"
                    >
                      {view.name}
                    </button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteColumnView(view.id)}
                      className="h-5 w-5 p-0"
                    >
                      <X className="w-3 h-3 text-lia-text-muted" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-3">
            {Object.keys(categoryLabels).map((categoryKey) => {
              const categoryColumns = columnConfig.filter(col => col.category === categoryKey)
              if (categoryColumns.length === 0) return null
              return (
                <div key={categoryKey}>
                  <h4 className="text-xs font-semibold text-lia-text-primary mb-2">
                    {categoryLabels[categoryKey]}
                  </h4>
                  <div className="space-y-1">
                    {categoryColumns.map(col => (
                      <label key={col.id} className="flex items-center gap-2 p-2 hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover rounded-xl cursor-pointer">
                        <input
                          type="checkbox"
                          className="w-3 h-3 accent-lia-btn-primary-bg"
                          checked={col.visible}
                          onChange={() => toggleColumn(col.id)}
                        />
                        <span className="text-xs">{col.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="flex-shrink-0 p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={handleSaveView}
            >
              {t('saveView')}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={handleResetColumns}
            >
              {t('resetDefault')}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
