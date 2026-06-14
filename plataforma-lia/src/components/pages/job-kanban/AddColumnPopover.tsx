"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
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
  { nameKey: 'catalogTesteTecnico', behavior: 'evaluation', color: 'var(--lia-border-default)' },
  { nameKey: 'catalogTesteIngles', behavior: 'evaluation', color: 'var(--lia-border-default)' },
  { nameKey: 'catalogEntrevistaTecnica', behavior: 'scheduling', color: 'var(--status-warning)' },
  { nameKey: 'catalogEntrevistaGestor', behavior: 'scheduling', color: 'var(--status-success)' },
  { nameKey: 'catalogEntrevistaFinal', behavior: 'scheduling', color: 'var(--lia-border-subtle)' },
  { nameKey: 'catalogDinamicaGrupo', behavior: 'scheduling', color: 'var(--wedo-purple)' },
  { nameKey: 'catalogReferencias', behavior: 'verification', color: 'var(--lia-border-subtle)' },
  { nameKey: 'catalogCaseEstudo', behavior: 'evaluation', color: 'var(--lia-border-default)' },
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
  const t = useTranslations('kanban')
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
          color: 'var(--lia-text-tertiary)',
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
        color: 'var(--lia-text-tertiary)',
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
        color: 'var(--lia-text-tertiary)',
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
    const displayName = t(cat.nameKey)
    const stageName = toStageName(displayName).replace(/\//g, '')

    try {
      const response = await fetch('/api/backend-proxy/recruitment-stages/stages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: stageName,
          display_name: displayName,
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
        displayName: displayName,
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
        displayName: displayName,
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
    cat => !dynamicStages.some(ds => ds.displayName === t(cat.nameKey))
  )

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
      onClick={onClose}
    >
      <div
        className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl w-full max-w-[420px] max-h-[600px] overflow-y-auto p-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-lia-text-primary">{t('addColumnToPipeline')}</h3>
          <button onClick={onClose} className="p-1 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover">
            <X className="w-4 h-4 text-lia-text-muted" />
          </button>
        </div>

        <div className="space-y-3 mb-4">
          <label className="text-xs font-medium text-lia-text-secondary">{t('stageName')}</label>
          <input
            type="text"
            value={columnName}
            onChange={(e) => { setColumnName(e.target.value); setInferredBehavior(null) }}
            placeholder={t('stageNamePlaceholder')}
            className="w-full px-3 py-2 text-sm border border-lia-border-subtle dark:border-lia-border-subtle dark:bg-lia-bg-secondary rounded-xl focus:outline-none focus:ring-1 focus:ring-lia-border-medium focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
          />
          {columnName.length >= 3 && !inferredBehavior && (
            <button
              onClick={handleInferBehavior}
              className="text-xs px-3 py-2 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover text-lia-text-secondary transition-colors motion-reduce:transition-none"
            >
              {t('suggestActionType')}
            </button>
          )}
          {inferredBehavior && (
            <div className="flex items-center gap-2 p-2 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
              <span className="text-micro px-2 py-0.5 rounded-full font-medium bg-wedo-cyan/15 text-wedo-cyan-text">
                {inferredBehavior.suggested_behavior}
              </span>
              <span className="text-micro text-lia-text-muted">
                {t('confidenceLabel', { percent: Math.round(inferredBehavior.confidence * 100) })}
              </span>
            </div>
          )}
        </div>

        <button
          disabled={columnName.length < 2 || isAddingColumn}
          onClick={handleAddCustom}
          className={`w-full py-2.5 rounded-md text-sm font-medium text-white transition-opacity motion-reduce:transition-none disabled:opacity-40 disabled:cursor-not-allowed ${columnName.length >= 2 && !isAddingColumn ? 'bg-lia-btn-primary-bg' : 'bg-lia-text-tertiary'}`}
        >
          {isAddingColumn ? t('adding') : t('addColumnButton')}
        </button>

        {availableCatalog.length > 0 && (
          <div className="mt-4 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
            <label className="text-xs font-medium text-lia-text-tertiary mb-2 block">{t('orChooseFromCatalog')}</label>
            <div className="grid grid-cols-2 gap-2">
              {availableCatalog.map(cat => (
                <button
                  key={cat.nameKey}
                  disabled={isAddingColumn}
                  onClick={() => handleAddCatalog(cat)}
                  className="flex items-center gap-2 p-2 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{backgroundColor: cat.color}} />
                  <span className="text-xs text-lia-text-secondary font-medium">{t(cat.nameKey)}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
