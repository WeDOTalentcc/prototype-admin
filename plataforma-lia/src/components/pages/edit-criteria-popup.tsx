'use client'

import React, { useState, useEffect } from 'react'
import { X, XIcon, GripVertical, Plus, ChevronRight, Bookmark } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIPreferencesStore } from '@/stores/ui-preferences-store'
import { Criterion, Preset, DEFAULT_PRESETS } from './candidate-review-modal-types'

interface EditCriteriaPopupProps {
  isOpen: boolean
  onClose: () => void
  criteria: Criterion[]
  onUpdate: (criteria: Criterion[]) => void
}

export const EditCriteriaPopup: React.FC<EditCriteriaPopupProps> = ({ isOpen, onClose, criteria, onUpdate }) => {
  const [localCriteria, setLocalCriteria] = useState<Criterion[]>(criteria)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [showPresets, setShowPresets] = useState(false)
  const [presetName, setPresetName] = useState('')
  const [showSavePreset, setShowSavePreset] = useState(false)
  const [savedPresets, setSavedPresets] = useState<Preset[]>([])

  useEffect(() => {
    setLocalCriteria(criteria)
  }, [criteria])

  const storedPresets = useUIPreferencesStore((s) => s.criteriaPresets)

  useEffect(() => {
    if (storedPresets.length > 0) {
      setSavedPresets(storedPresets.map(p => ({
        id: p.id,
        name: p.name,
        criteria: p.criteria.map(c => ({ id: c.id, text: c.text, isPinned: c.isPinned }))
      })))
    }
  }, [storedPresets])

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return

    const newCriteria = [...localCriteria]
    const draggedItem = newCriteria[draggedIndex]
    newCriteria.splice(draggedIndex, 1)
    newCriteria.splice(index, 0, draggedItem)
    setLocalCriteria(newCriteria)
    setDraggedIndex(index)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
  }

  const handleRemove = (id: string) => {
    setLocalCriteria(localCriteria.filter(c => c.id !== id))
  }

  const handleAdd = () => {
    const newCriterion: Criterion = {
      id: `criterion_${Date.now()}`,
      text: 'New criterion...',
      isPinned: false
    }
    setLocalCriteria([...localCriteria, newCriterion])
  }

  const handleUpdate = () => {
    onUpdate(localCriteria)
    onClose()
  }

  const handleSelectPreset = (preset: Preset) => {
    const newCriteria = preset.criteria.map((c, idx) => ({
      ...c,
      id: `preset_${Date.now()}_${idx}`
    }))
    setLocalCriteria(newCriteria)
    setShowPresets(false)
  }

  const handleSavePreset = () => {
    if (!presetName.trim()) return
    
    const newPreset: Preset = {
      id: `user_preset_${Date.now()}`,
      name: presetName,
      criteria: localCriteria
    }
    
    const updatedPresets = [...savedPresets, newPreset]
    setSavedPresets(updatedPresets)
    useUIPreferencesStore.getState().setCriteriaPresets(updatedPresets.map(p => ({
      id: p.id,
      name: p.name,
      criteria: p.criteria.map(c => ({ id: c.id, text: c.text, isPinned: !!c.isPinned }))
    })))
    setPresetName('')
    setShowSavePreset(false)
  }

  const allPresets = [...DEFAULT_PRESETS, ...savedPresets]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-overlay flex items-center justify-center">
      <div className="absolute inset-0 bg-lia-overlay" onClick={onClose} />
      <div 
        className="relative bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl w-full max-w-lg p-6 z-10"
       
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-lia-text-primary">
            Edit Criteria
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
          >
            <X className="w-5 h-5 text-lia-text-secondary" />
          </button>
        </div>

        <div className="space-y-2 mb-6 max-h-content-md overflow-y-auto">
          {localCriteria.map((criterion, index) => (
            <div
              key={criterion.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={`flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-md border transition-colors motion-reduce:transition-none ${
                draggedIndex === index ? 'border-lia-btn-primary-bg dark:border-lia-border-medium bg-lia-bg-secondary dark:bg-lia-bg-secondary/50' : 'border-lia-border-subtle'
              }`}
            >
              <span className="text-sm font-medium text-lia-text-secondary w-6">{index + 1}</span>
              <GripVertical className="w-4 h-4 text-lia-text-secondary cursor-grab" />
              <input
                type="text"
                value={criterion.text}
                onChange={(e) => {
                  const newCriteria = [...localCriteria]
                  newCriteria[index].text = e.target.value
                  setLocalCriteria(newCriteria)
                }}
                className="flex-1 bg-transparent border-none outline-none text-sm text-lia-text-primary"
              />
              <button
                onClick={() => handleRemove(criterion.id)}
                className="p-1 rounded-md hover:bg-status-error/10 transition-colors motion-reduce:transition-none"
              >
                <XIcon className="w-4 h-4 text-status-error" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-lia-border-subtle">
          <div className="flex items-center gap-4 relative">
            <button 
              onClick={() => setShowPresets(!showPresets)}
              className="text-sm font-medium text-lia-text-secondary hover:underline hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
            >
              Select Preset
            </button>
            <button 
              onClick={() => setShowSavePreset(!showSavePreset)}
              className="text-sm font-medium text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
            >
              <Bookmark className="w-4 h-4" />
              Save Preset
            </button>

            {showPresets && (
              <div className="absolute left-0 bottom-full mb-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle py-2 min-w-sidebar-content z-20">
                <p className="px-3 py-1 text-xs text-lia-text-secondary uppercase tracking-wide">Select a preset</p>
                {allPresets.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handleSelectPreset(preset)}
                    className="w-full px-3 py-2 text-left text-sm text-lia-text-primary hover:bg-lia-bg-secondary flex items-center justify-between"
                  >
                    <span>{preset.name}</span>
                    <span className="text-xs text-lia-text-secondary">{preset.criteria.length} criteria</span>
                  </button>
                ))}
              </div>
            )}

            {showSavePreset && (
              <div className="absolute left-0 bottom-full mb-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-3 min-w-[250px] z-20">
                <p className="text-xs font-medium text-lia-text-primary mb-2">Save as preset</p>
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="Preset name..."
                  className="w-full px-3 py-2 text-sm border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl focus:outline-none focus:border-lia-border-medium dark:focus:border-lia-border-medium mb-2 bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary"
                />
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowSavePreset(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSavePreset}
                    disabled={!presetName.trim()}
                    className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover"
                  >
                    Save
                  </Button>
                </div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleAdd}
              className="text-sm"
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Criterion
            </Button>
            <Button
              onClick={handleUpdate}
              className="text-sm bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover"
            >
              Update
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
