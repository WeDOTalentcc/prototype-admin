"use client"

import { useState, useEffect } from "react"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"

export type FieldType = "text" | "email" | "tel" | "url" | "number" | "date" | "textarea"

export interface FieldDef {
  name: string
  label: string
  type?: FieldType
  required?: boolean
  placeholder?: string
}

interface EditArrayItemModalProps<T extends Record<string, unknown>> {
  open: boolean
  onClose: () => void
  /** Initial values (null = "add new item"). */
  initialItem: T | null
  fields: FieldDef[]
  /** Modal title (e.g. "Editar experiência" / "Adicionar formação"). */
  title: string
  /** Description shown under title. */
  description?: string
  /** Save callback. Returns success boolean. */
  onSave: (item: T) => Promise<{ success: boolean; error?: string }>
}

/**
 * Generic modal for editing or adding an item of a candidate array
 * (experience, education, language, certification, etc).
 *
 * Used by F5 Phase B2 — arrays canonical editing pattern. Multi-tenant
 * via parent's useCandidateArrayUpdate hook (which uses JWT).
 *
 * Use editable=false on parent + omit "Editar"/"Adicionar" buttons to
 * keep Surface 1 (drawer) read-only.
 */
export function EditArrayItemModal<T extends Record<string, unknown>>({
  open,
  onClose,
  initialItem,
  fields,
  title,
  description,
  onSave,
}: EditArrayItemModalProps<T>) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const next: Record<string, string> = {}
    for (const f of fields) {
      const raw = initialItem?.[f.name]
      next[f.name] = raw == null ? "" : String(raw)
    }
    setValues(next)
    setError(null)
    setSaving(false)
  }, [initialItem, fields, open])

  const handleChange = (name: string, value: string) =>
    setValues((prev) => ({ ...prev, [name]: value }))

  const handleSave = async () => {
    for (const f of fields) {
      if (f.required && !values[f.name]?.trim()) {
        setError(`Campo "${f.label}" é obrigatório`)
        return
      }
    }
    setSaving(true)
    setError(null)
    const item = { ...values } as unknown as T
    const result = await onSave(item)
    setSaving(false)
    if (result.success) {
      onClose()
    } else {
      setError(result.error ?? "Erro ao salvar")
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        <div className="space-y-3 py-2">
          {fields.map((f) => (
            <div key={f.name} className="space-y-1">
              <Label htmlFor={`field-${f.name}`} className="text-xs">
                {f.label}
                {f.required && <span className="text-status-error ml-0.5">*</span>}
              </Label>
              {f.type === "textarea" ? (
                <Textarea
                  id={`field-${f.name}`}
                  value={values[f.name] ?? ""}
                  onChange={(e) => handleChange(f.name, e.target.value)}
                  placeholder={f.placeholder}
                  rows={3}
                  className="text-sm"
                  disabled={saving}
                />
              ) : (
                <Input
                  id={`field-${f.name}`}
                  type={f.type ?? "text"}
                  value={values[f.name] ?? ""}
                  onChange={(e) => handleChange(f.name, e.target.value)}
                  placeholder={f.placeholder}
                  className="text-sm h-9"
                  disabled={saving}
                />
              )}
            </div>
          ))}

          {error && (
            <p className="text-xs text-status-error" role="alert">
              {error}
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                Salvando...
              </>
            ) : (
              "Salvar"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
