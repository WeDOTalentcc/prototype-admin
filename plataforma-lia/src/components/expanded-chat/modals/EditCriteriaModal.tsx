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
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-lia-overlay">
          <div className="bg-lia-bg-primary rounded-xl w-panel-xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle">
              <h3 className="text-lg font-semibold text-lia-text-primary">
                Editar Critérios
              </h3>
              <button
                onClick={onClose}
                className="p-2 rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              >
                <X className="w-5 h-5 lia-text-secondary" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {criteria.map((criterion) => (
                <div
                  key={criterion.id}
                  className="flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-md group"
                >
                  <div className="cursor-move lia-text-muted hover:lia-text-secondary">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M11 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-2-8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 4c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                    </svg>
                  </div>
                  <span className="text-sm font-medium lia-text-secondary w-6">①</span>
                  <span className="flex-1 text-sm text-lia-text-primary">{criterion.text}</span>
                  <span className={cn(
 "text-xs px-2 py-0.5 rounded-md",
                    criterion.source === 'technical' ? 'bg-lia-bg-tertiary text-lia-text-secondary' : 'bg-wedo-purple/10 text-wedo-purple'
                  )}>
                    {criterion.source === 'technical' ? 'Técnico' : 'Comportamental'}
                  </span>
                  <button
                    onClick={() => onRemoveCriterion(criterion.id)}
                    className="p-1.5 rounded-md lia-text-muted hover:text-status-error hover:bg-status-error/10 transition-colors motion-reduce:transition-none opacity-0 group-hover:opacity-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            <div className="px-6 py-4 border-t border-lia-border-subtle space-y-3">
              <div className="flex gap-2">
                <button className="flex items-center gap-2 px-4 py-2 text-sm lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                  <FileText className="w-4 h-4" />
                  Selecionar Preset
                </button>
                <button className="flex items-center gap-2 px-4 py-2 text-sm lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
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
                  className="flex-1 py-2.5 px-4 border border-lia-border-subtle rounded-md text-sm font-medium lia-text-secondary hover:border-lia-btn-primary-bg hover:text-lia-text-primary transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Adicionar Critério
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 py-2.5 px-4 bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-md text-sm font-medium hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
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
