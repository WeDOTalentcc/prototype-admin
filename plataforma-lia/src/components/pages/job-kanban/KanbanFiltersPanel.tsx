"use client"

import { Filter, X } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { textStyles } from "@/lib/design-tokens"

const STATUS_OPTIONS = [
  { value: 'novo', label: 'Novo' },
  { value: 'em_analise', label: 'Em análise' },
  { value: 'aguardando_aprovacao', label: 'Aguardando aprovação' },
  { value: 'triado_aprovado', label: 'Triado aprovado' },
  { value: 'negociacao', label: 'Negociação' },
]

const ORIGIN_OPTIONS = [
  { value: 'web', label: 'Web' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'sourcing', label: 'Busca Ativa' },
  { value: 'ats', label: 'ATS' },
]

const WORK_MODEL_OPTIONS = [
  { value: 'remoto', label: 'Remoto' },
  { value: 'hibrido', label: 'Híbrido' },
  { value: 'presencial', label: 'Presencial' },
]

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
  if (!open) return null

  const handleClear = () => {
    onScoreMinChange(0)
    onStatusFilterChange([])
    onWorkModelFilterChange([])
    onOriginFilterChange([])
  }

  const toggleItem = (list: string[], value: string, setter: (v: string[]) => void) => {
    setter(list.includes(value) ? list.filter(i => i !== value) : [...list, value])
  }

  return (
    <div className="flex-shrink-0 w-72 transition-colors motion-reduce:transition-none duration-300">
      <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle rounded-md">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-lia-text-secondary" />
              <h3 className={textStyles.title}>Filtros Avançados</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-7 w-7 p-0 hover:bg-gray-100"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </Button>
          </div>
          <p className={`${textStyles.description} mt-1`}>Refine os candidatos exibidos</p>
        </div>

        {/* Filtros - Scrollable */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Score LIA */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">
              Score LIA Mínimo
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="100"
                value={scoreMin}
                onChange={(e) => onScoreMinChange(Number(e.target.value))}
                className="flex-1 h-1.5 bg-gray-200 rounded-md appearance-none cursor-pointer accent-gray-900"
              />
              <span className="text-xs text-lia-text-secondary w-12 text-right">{scoreMin}%</span>
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Status</label>
            <div className="space-y-1.5">
              {STATUS_OPTIONS.map(({ value, label }) => (
                <label key={value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={statusFilter.includes(value)}
                    onChange={() => toggleItem(statusFilter, value, onStatusFilterChange)}
                    className="w-3.5 h-3.5 rounded-md border-lia-border-default text-lia-text-primary focus:ring-gray-900/20"
                  />
                  <span className="text-xs text-lia-text-secondary">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Origem */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Origem</label>
            <div className="space-y-1.5">
              {ORIGIN_OPTIONS.map(({ value, label }) => (
                <label key={value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={originFilter.includes(value)}
                    onChange={() => toggleItem(originFilter, value, onOriginFilterChange)}
                    className="w-3.5 h-3.5 rounded-md border-lia-border-default text-lia-text-primary focus:ring-gray-900/20"
                  />
                  <span className="text-xs text-lia-text-secondary">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Modelo de Trabalho */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">Modelo de Trabalho</label>
            <div className="space-y-1.5">
              {WORK_MODEL_OPTIONS.map(({ value, label }) => (
                <label key={value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={workModelFilter.includes(value)}
                    onChange={() => toggleItem(workModelFilter, value, onWorkModelFilterChange)}
                    className="w-3.5 h-3.5 rounded-md border-lia-border-default text-lia-text-primary focus:ring-gray-900/20"
                  />
                  <span className="text-xs text-lia-text-secondary">{label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-4 border-t border-lia-border-subtle bg-gray-50">
          <div className="flex gap-2">
            <button
              onClick={handleClear}
              className="flex-1 px-3 py-2 text-xs font-medium text-lia-text-secondary bg-lia-bg-primary border border-lia-border-subtle rounded-md hover:bg-gray-50 transition-colors motion-reduce:transition-none"
            >
              Limpar
            </button>
            <button
              onClick={onClose}
              className="flex-1 px-3 py-2 text-xs font-medium text-white rounded-md transition-colors motion-reduce:transition-none bg-gray-900 hover:bg-gray-800"
            >
              Aplicar
            </button>
          </div>
        </div>
      </Card>
    </div>
  )
}
