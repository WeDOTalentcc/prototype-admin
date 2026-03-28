"use client"

import { X } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

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

const CATEGORY_CONFIG: Record<string, string> = {
  principais: 'Colunas Principais',
  informacoes: 'Informações da Vaga',
  prazos: 'Prazos',
  responsaveis: 'Responsáveis',
  localizacao: 'Localização e Modelo',
  remuneracao: 'Remuneração e Budget',
  divulgacao: 'Divulgação',
  requisitos: 'Requisitos',
  targeting: 'Segmentação',
  metricas: 'Métricas',
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
  if (!open) return null

  const handleSaveView = () => {
    const name = prompt("Nome da visualização:")
    if (name) {
      saveColumnView(name)
      onToast?.(`Visualização "${name}" salva!`)
    }
  }

  const handleResetColumns = () => {
    resetColumnsToDefault()
    onToast?.("Colunas resetadas para o padrão")
  }

  return (
    <div className="flex-shrink-0 w-80 transition-all duration-300">
      <Card className="h-full flex flex-col overflow-hidden bg-white dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700">
        <div className="flex-shrink-0 p-4 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-gray-950 dark:text-gray-50">Configurar Colunas</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 hover:bg-gray-900/10 dark:hover:bg-gray-100/10 rounded-full"
            >
              <X className="w-4 h-4 text-gray-950 dark:text-gray-50" />
            </Button>
          </div>
          <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">
            Selecione as colunas visíveis na tabela ({visibleColumnIds.length} ativas)
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {savedColumnViews.length > 0 && (
            <div className="mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
              <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                Visualizações Salvas
              </h4>
              <div className="space-y-1">
                {savedColumnViews.map(view => (
                  <div key={view.id} className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md">
                    <button
                      onClick={() => applyColumnView(view.id)}
                      className="text-xs text-gray-800 hover:text-gray-900"
                    >
                      {view.name}
                    </button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteColumnView(view.id)}
                      className="h-5 w-5 p-0"
                    >
                      <X className="w-3 h-3 text-gray-400" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-3">
            {Object.entries(CATEGORY_CONFIG).map(([categoryKey, categoryLabel]) => {
              const categoryColumns = columnConfig.filter(col => col.category === categoryKey)
              if (categoryColumns.length === 0) return null
              return (
                <div key={categoryKey}>
                  <h4 className="text-xs font-semibold text-gray-800 dark:text-gray-200 mb-2">
                    {categoryLabel}
                  </h4>
                  <div className="space-y-1">
                    {categoryColumns.map(col => (
                      <label key={col.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md cursor-pointer">
                        <input
                          type="checkbox"
                          className="w-3 h-3 accent-gray-900"
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

        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={handleSaveView}
            >
              Salvar Visualização
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs"
              onClick={handleResetColumns}
            >
              Resetar Padrão
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
