"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Brain, Loader2, Plus, X, XCircle } from "lucide-react"

// ----------------------------------------------------------------
// Reusable array editor for responsibilities / tech skills / behavioural
// ----------------------------------------------------------------

export type ArrayEditorVariant = "list" | "tags"

interface AISuggestionTag {
  /** Display label */
  label: string
  /** Unique key for deduplication */
  key: string
}

interface JDArrayEditorProps {
  /** Section label shown above the editor */
  label: string
  /** Current items in the list */
  items: string[]
  /** Called with the updated array when the user adds / removes an item */
  onChange: (items: string[]) => void
  /** "list" = bullet list (responsibilities), "tags" = pill chips (skills / competencies) */
  variant?: ArrayEditorVariant
  /** Placeholder text for the add-item input */
  placeholder?: string
  /** field key — used as editingField discriminator passed down from parent */
  fieldKey: string
  /** Currently active editing field key (parent-owned) */
  editingField: string | null
  /** Controlled value of the transient new-item input */
  newItemValue: string
  /** Called when the user changes the transient input */
  onNewItemChange: (value: string) => void
  /** Called when user opens the inline input for THIS field */
  onStartEditing: (fieldKey: string) => void
  /** Called when user closes the inline input */
  onStopEditing: () => void
  /** AI suggestions (optional) */
  aiSuggestions?: AISuggestionTag[]
  /** Whether AI suggestions are loading */
  isLoadingAI?: boolean
  /** Called when the user triggers AI suggestion fetch */
  onFetchAI?: () => void
  /** Called when user accepts an AI suggestion (removes it from suggestions list) */
  onAcceptSuggestion?: (key: string) => void
}

export const JDArrayEditor = React.memo(function JDArrayEditor({
  label,
  items,
  onChange,
  variant = "list",
  placeholder = "Adicionar item...",
  fieldKey,
  editingField,
  newItemValue,
  onNewItemChange,
  onStartEditing,
  onStopEditing,
  aiSuggestions,
  isLoadingAI,
  onFetchAI,
  onAcceptSuggestion,
}: JDArrayEditorProps) {
  const isThisFieldEditing = editingField === fieldKey

  const handleAdd = () => {
    const trimmed = newItemValue.trim()
    if (trimmed) {
      onChange([...items, trimmed])
      onNewItemChange("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleAdd()
    }
  }

  const handleRemove = (idx: number) => {
    onChange(items.filter((_, i) => i !== idx))
  }

  return (
    <div>
      {/* Label row — with optional AI suggestion button */}
      <div className="flex items-center gap-2 mb-2">
        <label className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide">
          {label}
        </label>
        {onFetchAI && (
          <button
            onClick={onFetchAI}
            disabled={isLoadingAI}
            className="flex items-center gap-1 text-micro px-2 py-0.5 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/[.06] transition-colors motion-reduce:transition-none hover:opacity-80 disabled:opacity-50"
          >
            {isLoadingAI ? (
              <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <Brain className="h-3 w-3 text-wedo-cyan" />
            )}
            Sugerir com IA
          </button>
        )}
      </div>

      <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-3">
        {/* Items */}
        {variant === "list" && (
          <div className="space-y-0.5">
            {items.map((item, idx) => (
              <div
                key={`${fieldKey}-${idx}`}
                className="group flex items-start gap-2 py-1 px-1 rounded-md hover:bg-lia-interactive-hover"
              >
                <span className="text-xs text-lia-text-secondary mt-0.5 shrink-0">•</span>
                <span className="text-xs text-lia-text-secondary flex-1 leading-relaxed">
                  {item}
                </span>
                <button
                  onClick={() => handleRemove(idx)}
                  className="opacity-0 group-hover:opacity-100 text-lia-text-secondary hover:text-status-error shrink-0 transition-opacity motion-reduce:transition-none"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {variant === "tags" && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {/* Current items */}
            {items.map((item, idx) => (
              <span
                key={`${fieldKey}-tag-${idx}-${item}`}
                className="inline-flex items-center gap-1 text-micro px-2 py-0.5 bg-lia-bg-tertiary text-lia-text-secondary rounded-full border border-lia-border-subtle"
              >
                {item}
                <button
                  onClick={() => handleRemove(idx)}
                  className="lia-text-secondary hover:text-status-error"
                >
                  <XCircle className="h-3 w-3" />
                </button>
              </span>
            ))}

            {/* AI suggestion chips */}
            {aiSuggestions?.map((s) => (
              <button
                key={s.key}
                onClick={() => onAcceptSuggestion?.(s.key)}
                className="inline-flex items-center gap-1 text-micro px-2 py-0.5 rounded-full border transition-colors motion-reduce:transition-none hover:opacity-80 border-wedo-cyan/40 text-wedo-cyan-text bg-wedo-cyan/[0.08]"
              >
                <Plus className="h-3 w-3 text-lia-text-secondary" />
                {s.label}
              </button>
            ))}
          </div>
        )}

        {/* Inline add input */}
        {isThisFieldEditing ? (
          <div className="flex gap-1.5 mt-2">
            <input
              value={newItemValue}
              onChange={(e) => onNewItemChange(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 h-7 text-xs border border-lia-border-subtle rounded-md px-2.5 focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 bg-lia-bg-secondary"
              placeholder={placeholder}
              autoFocus
            />
            <button
              onClick={() => {
                handleAdd()
                onStopEditing()
              }}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary px-2"
            >
              OK
            </button>
          </div>
        ) : (
          <button
            onClick={() => {
              onNewItemChange("")
              onStartEditing(fieldKey)
            }}
            className="text-xs text-lia-text-secondary hover:text-lia-text-secondary flex items-center gap-1 mt-2"
          >
            <Plus className="h-3 w-3" /> Adicionar
          </button>
        )}
      </div>
    </div>
  )
})

export default JDArrayEditor
