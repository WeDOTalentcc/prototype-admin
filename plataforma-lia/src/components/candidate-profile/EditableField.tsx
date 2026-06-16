"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Pencil, Check, X, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

export type EditableFieldType = "text" | "email" | "tel" | "url" | "number" | "textarea"

interface EditableFieldProps {
  /** Current value (read-only outside edit mode). */
  value: string | number | null | undefined
  /** Callback when user confirms with Enter/Save. Should return success/failure. */
  onSave: (newValue: string) => Promise<{ success: boolean; error?: string }>
  /** Optional client-side validator. Return null if valid, error message otherwise. */
  validate?: (value: string) => string | null
  /** Input type. Default 'text'. */
  type?: EditableFieldType
  /** Placeholder text when value is empty. */
  placeholder?: string
  /** Accessible label (used in aria-label and as visible hint). */
  label?: string
  /** Whether the field is currently editable. Defaults to true. Pass false to render read-only. */
  editable?: boolean
  /** External saving flag (e.g. from hook). */
  saving?: boolean
  /** Show the pencil icon even when value is empty. */
  showPencilWhenEmpty?: boolean
  /** Display string when value is empty/null. Default: 'Não informado'. */
  emptyDisplay?: string
  className?: string
}

/**
 * Canonical inline edit primitive — pencil icon next to value; click to edit.
 *
 * Enter saves, Esc cancels. Optimistic UI: shows new value immediately;
 * onSave returns failure → rolls back to prior value + shows error inline.
 *
 * Used by Surface 2/3 (page/route) for profile field edits. Surface 1
 * (drawer) passes editable={false} (read-only by design).
 *
 * LGPD: never use for race/gender/marital/religion/health/etc. Sensor
 * check_editable_fields_not_lgpd_sensitive.py blocks those at build.
 */
export function EditableField({
  value,
  onSave,
  validate,
  type = "text",
  placeholder,
  label,
  editable = true,
  saving = false,
  showPencilWhenEmpty = true,
  emptyDisplay = "Não informado",
  className,
}: EditableFieldProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<string>(value == null ? "" : String(value))
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(null)

  useEffect(() => {
    if (!editing) {
      setDraft(value == null ? "" : String(value))
      setError(null)
    }
  }, [value, editing])

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
      if ("select" in inputRef.current) {
        inputRef.current.select()
      }
    }
  }, [editing])

  const startEdit = useCallback(() => {
    if (!editable) return
    setEditing(true)
    setError(null)
  }, [editable])

  const cancelEdit = useCallback(() => {
    setEditing(false)
    setDraft(value == null ? "" : String(value))
    setError(null)
  }, [value])

  const saveEdit = useCallback(async () => {
    if (validate) {
      const validationErr = validate(draft)
      if (validationErr) {
        setError(validationErr)
        return
      }
    }
    const result = await onSave(draft)
    if (result.success) {
      setEditing(false)
      setError(null)
    } else {
      setError(result.error ?? "Erro ao salvar")
    }
  }, [draft, onSave, validate])

  const handleKey = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      if (e.key === "Enter" && type !== "textarea") {
        e.preventDefault()
        void saveEdit()
      } else if (e.key === "Escape") {
        e.preventDefault()
        cancelEdit()
      }
    },
    [saveEdit, cancelEdit, type]
  )

  const displayValue = value == null || value === "" ? emptyDisplay : String(value)
  const showPencil = editable && (showPencilWhenEmpty || (value != null && value !== ""))

  if (editing) {
    return (
      <div className={cn("inline-flex items-start gap-1.5", className)}>
        <div className="flex-1 min-w-0">
          {type === "textarea" ? (
            <Textarea
              ref={inputRef as React.RefObject<HTMLTextAreaElement>}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKey}
              placeholder={placeholder}
              aria-label={label}
              aria-invalid={Boolean(error)}
              className="text-sm"
              disabled={saving}
              rows={3}
            />
          ) : (
            <Input
              ref={inputRef as React.RefObject<HTMLInputElement>}
              type={type}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKey}
              placeholder={placeholder}
              aria-label={label}
              aria-invalid={Boolean(error)}
              className="text-sm h-8"
              disabled={saving}
            />
          )}
          {error && (
            <p className="text-xs text-status-error mt-1" role="alert">
              {error}
            </p>
          )}
        </div>
        <div className="flex gap-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => void saveEdit()}
            disabled={saving}
            aria-label={`Salvar ${label ?? "campo"}`}
          >
            {saving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            ) : (
              <Check className="w-3.5 h-3.5 text-status-success" aria-hidden="true" />
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={cancelEdit}
            disabled={saving}
            aria-label={`Cancelar edição de ${label ?? "campo"}`}
          >
            <X className="w-3.5 h-3.5 text-lia-text-tertiary" aria-hidden="true" />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <span className={cn("inline-flex items-center gap-1.5 group", className)}>
      <span className={cn("text-sm", (value == null || value === "") && "text-lia-text-tertiary italic")}>
        {displayValue}
      </span>
      {showPencil && (
        <button
          type="button"
          onClick={startEdit}
          aria-label={`Editar ${label ?? "campo"}`}
          className="opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity motion-reduce:transition-none p-0.5 rounded hover:bg-lia-bg-tertiary"
        >
          <Pencil className="w-3 h-3 text-lia-text-secondary" aria-hidden="true" />
        </button>
      )}
    </span>
  )
}
