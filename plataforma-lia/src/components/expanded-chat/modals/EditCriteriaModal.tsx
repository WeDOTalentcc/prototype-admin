"use client"

/**
 * EditCriteriaModal — edição de critérios de calibração.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.3 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { X, Plus, FileText, Upload } from "lucide-react"
import { cn } from "@/lib/utils"

interface Criterion {
  id: string
  text: string
  source: 'technical' | 'behavioral'
}

interface EditCriteriaModalProps {
  open: boolean
  criteria: Criterion[]
  onClose: () => void
  onAddCriterion: (text: string) => void
  onRemoveCriterion: (id: string) => void
}

export function EditCriteriaModal({ open, criteria, onClose, onAddCriterion, onRemoveCriterion }: EditCriteriaModalProps) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl w-panel-xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800">
                Editar Critérios
              </h3>
              <button
                onClick={onClose}
                className="p-2 rounded-md hover:bg-gray-50 transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {criteria.map((criterion) => (
                <div
                  key={criterion.id}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded-md group"
                >
                  <div className="cursor-move text-gray-300 hover:text-gray-500">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M11 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-2-8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 4c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-gray-500 w-6">①</span>
                  <span className="flex-1 text-sm text-gray-800">{criterion.text}</span>
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded-md",
                    criterion.source === 'technical' ? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400' : 'bg-wedo-purple/10 text-wedo-purple'
                  )}>
                    {criterion.source === 'technical' ? 'Técnico' : 'Comportamental'}
                  </span>
                  <button
                    onClick={() => onRemoveCriterion(criterion.id)}
                    className="p-1.5 rounded-md text-gray-300 hover:text-status-error hover:bg-status-error/10 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            <div className="px-6 py-4 border-t border-gray-200 space-y-3">
              <div className="flex gap-2">
                <button className="flex items-center gap-2 px-4 py-2 text-sm text-gray-500 hover:text-gray-800 transition-colors">
                  <FileText className="w-4 h-4" />
                  Selecionar Preset
                </button>
                <button className="flex items-center gap-2 px-4 py-2 text-sm text-gray-500 hover:text-gray-800 transition-colors">
                  <Upload className="w-4 h-4" />
                  Salvar Preset
                </button>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    const text = prompt('Digite o novo critério:')
                    if (text) onAddCriterion(text)
                  }}
                  className="flex-1 py-2.5 px-4 border border-gray-200 rounded-md text-sm font-medium text-gray-500 hover:border-gray-900 dark:hover:border-gray-50 hover:text-gray-900 dark:hover:text-gray-50 transition-colors flex items-center justify-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Adicionar Critério
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 py-2.5 px-4 bg-gray-900 text-white rounded-md text-sm font-medium hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-colors"
                >
                  Atualizar ↗
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
