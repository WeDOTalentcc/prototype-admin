"use client"

import { useState } from "react"
import { X } from "lucide-react"

interface DynamicStage {
  id: string
  name: string
  displayName: string
  order: number
  color: string
  stageType: string
  isHired: boolean
  isRejection: boolean
  isFinal: boolean
}

interface InferredBehavior {
  suggested_behavior: string
  confidence: number
}

interface AddColumnPopoverProps {
  isOpen: boolean
  onClose: () => void
  dynamicStages: DynamicStage[]
  isAddingColumn: boolean
  onSetIsAddingColumn: (v: boolean) => void
  onAddStage: (stage: DynamicStage) => void
}

const CATALOG_STAGES = [
  { name: 'Teste Técnico', behavior: 'evaluation', color: 'var(--gray-300)' },
  { name: 'Teste de Inglês', behavior: 'evaluation', color: 'var(--gray-300)' },
  { name: 'Entrevista Técnica', behavior: 'scheduling', color: 'var(--status-warning)' },
  { name: 'Entrevista Gestor', behavior: 'scheduling', color: 'var(--status-success)' },
  { name: 'Entrevista Final', behavior: 'scheduling', color: 'var(--gray-200)' },
  { name: 'Dinâmica de Grupo', behavior: 'scheduling', color: 'var(--wedo-purple)' },
  { name: 'Referências', behavior: 'verification', color: 'var(--gray-200)' },
  { name: 'Case / Estudo', behavior: 'evaluation', color: 'var(--gray-300)' },
]

function toStageName(displayName: string) {
  return displayName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
}

export function AddColumnPopover({
  isOpen,
  onClose,
  dynamicStages,
  isAddingColumn,
  onSetIsAddingColumn,
  onAddStage,
}: AddColumnPopoverProps) {
  const [columnName, setColumnName] = useState('')
  const [inferredBehavior, setInferredBehavior] = useState<InferredBehavior | null>(null)

  if (!isOpen) return null

  const maxOrder = dynamicStages
    .filter(s => !s.isFinal && !s.isHired && !s.isRejection)
    .reduce((max, s) => Math.max(max, s.order), 0)

  const handleAddCustom = async () => {
    if (columnName.length < 2 || isAddingColumn) return
    onSetIsAddingColumn(true)
    const stageName = toStageName(columnName)

    try {
      const response = await fetch('/api/backend-proxy/recruitment-stages/stages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: stageName,
          display_name: columnName,
          stage_order: maxOrder + 1,
          action_behavior: inferredBehavior?.suggested_behavior || 'passive',
          color: 'var(--gray-400)',
          is_system: false,
        }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const result = await response.json()
      const newStage: DynamicStage = {
        id: result?.id || `custom_${Date.now()}`,
        name: stageName,
        displayName: columnName,
        order: maxOrder + 1,
        color: 'var(--gray-400)',
        stageType: 'active',
        isHired: false,
        isRejection: false,
        isFinal: false,
      }
      onAddStage(newStage)
    } catch {
      const newStage: DynamicStage = {
        id: `custom_${Date.now()}`,
        name: stageName,
        displayName: columnName,
        order: maxOrder + 1,
        color: 'var(--gray-400)',
        stageType: 'active',
        isHired: false,
        isRejection: false,
        isFinal: false,
      }
      onAddStage(newStage)
    } finally {
      onSetIsAddingColumn(false)
      setColumnName('')
      setInferredBehavior(null)
      onClose()
    }
  }

  const handleAddCatalog = async (cat: typeof CATALOG_STAGES[number]) => {
    if (isAddingColumn) return
    onSetIsAddingColumn(true)
    const stageName = toStageName(cat.name).replace(/\//g, '')

    try {
      const response = await fetch('/api/backend-proxy/recruitment-stages/stages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: stageName,
          display_name: cat.name,
          stage_order: maxOrder + 1,
          action_behavior: cat.behavior || 'passive',
          color: cat.color,
          is_system: false,
        }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const result = await response.json()
      const newStage: DynamicStage = {
        id: result?.id || `catalog_${Date.now()}_${stageName}`,
        name: stageName,
        displayName: cat.name,
        order: maxOrder + 1,
        color: cat.color,
        stageType: 'active',
        isHired: false,
        isRejection: false,
        isFinal: false,
      }
      onAddStage(newStage)
    } catch {
      const newStage: DynamicStage = {
        id: `catalog_${Date.now()}_${stageName}`,
        name: stageName,
        displayName: cat.name,
        order: maxOrder + 1,
        color: cat.color,
        stageType: 'active',
        isHired: false,
        isRejection: false,
        isFinal: false,
      }
      onAddStage(newStage)
    } finally {
      onSetIsAddingColumn(false)
      onClose()
    }
  }

  const handleInferBehavior = async () => {
    try {
      const res = await fetch('/api/backend-proxy/recruitment-stages/stages/infer-behavior', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage_name: columnName }),
      })
      if (res.ok) {
        const data = await res.json()
        setInferredBehavior(data)
      }
    } catch {}
  }

  const availableCatalog = CATALOG_STAGES.filter(
    cat => !dynamicStages.some(ds => ds.displayName === cat.name)
  )

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-900 rounded-md w-full max-w-[420px] max-h-[600px] overflow-y-auto p-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Adicionar Coluna ao Pipeline</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
            <X className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          </button>
        </div>

        <div className="space-y-3 mb-4">
          <label className="text-xs font-medium text-gray-600 dark:text-gray-400">Nome da Etapa</label>
          <input
            type="text"
            value={columnName}
            onChange={(e) => { setColumnName(e.target.value); setInferredBehavior(null) }}
            placeholder="Ex: Teste de Lógica, Entrevista Cultural..."
            className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 rounded focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-gray-400 transition-all"
          />
          {columnName.length >= 3 && !inferredBehavior && (
            <button
              onClick={handleInferBehavior}
              className="text-xs px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-all"
            >
              Sugerir tipo de ação
            </button>
          )}
          {inferredBehavior && (
            <div className="flex items-center gap-2 p-2 rounded bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
              <span className="text-micro px-2 py-0.5 rounded-full font-medium bg-wedo-cyan/15 text-wedo-cyan">
                {inferredBehavior.suggested_behavior}
              </span>
              <span className="text-micro text-gray-400">
                {Math.round(inferredBehavior.confidence * 100)}% confiança
              </span>
            </div>
          )}
        </div>

        <button
          disabled={columnName.length < 2 || isAddingColumn}
          onClick={handleAddCustom}
          className="w-full py-2.5 rounded text-sm font-medium text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ backgroundColor: columnName.length >= 2 && !isAddingColumn ? 'var(--gray-950)' : 'var(--gray-400)' }}
        >
          {isAddingColumn ? 'Adicionando...' : 'Adicionar Coluna'}
        </button>

        {availableCatalog.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 block">Ou escolha do catálogo:</label>
            <div className="grid grid-cols-2 gap-2">
              {availableCatalog.map(cat => (
                <button
                  key={cat.name}
                  disabled={isAddingColumn}
                  onClick={() => handleAddCatalog(cat)}
                  className="flex items-center gap-2 p-2 rounded-sm border border-gray-200 dark:border-gray-700 hover:border-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }} />
                  <span className="text-xs text-gray-700 dark:text-gray-300 font-medium">{cat.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
