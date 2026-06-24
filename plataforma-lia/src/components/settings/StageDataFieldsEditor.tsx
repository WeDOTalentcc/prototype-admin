"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { Database, X, Plus, ChevronDown, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { StageDataField } from "./recruitment-journey.types"

const CATEGORY_LABELS: Record<StageDataField["category"], string> = {
  basic: "Dados Básicos",
  document: "Documentos",
  financial: "Financeiro",
  admissional: "Admissional",
}

type CatalogItem = Omit<StageDataField, "required" | "auto_collect">

const FIELD_CATALOG: CatalogItem[] = [
  { id: "cpf",           displayName: "CPF",                   category: "basic" },
  { id: "full_name",     displayName: "Nome Completo",         category: "basic" },
  { id: "birth_date",    displayName: "Data de Nascimento",    category: "basic" },
  { id: "address",       displayName: "Endereço Completo",     category: "basic" },
  { id: "phone",         displayName: "Telefone",              category: "basic" },
  { id: "rg",            displayName: "RG",                    category: "document" },
  { id: "cnh",           displayName: "CNH",                   category: "document" },
  { id: "ctps",          displayName: "CTPS",                  category: "document" },
  { id: "diploma",       displayName: "Diploma",               category: "document" },
  { id: "certificates",  displayName: "Certificados",          category: "document" },
  { id: "bank_account",  displayName: "Conta Bancária",        category: "financial" },
  { id: "pis_pasep",     displayName: "PIS/PASEP",             category: "financial" },
  { id: "aso",           displayName: "ASO",                   category: "admissional" },
  { id: "signed_contract", displayName: "Contrato Assinado",  category: "admissional" },
  { id: "photo_3x4",     displayName: "Foto 3x4",              category: "admissional" },
]

const CATEGORY_ORDER: StageDataField["category"][] = [
  "basic", "document", "financial", "admissional",
]

interface StageDataFieldsEditorProps {
  stageId: string
  fields: StageDataField[]
  onSave: (stageId: string, fields: StageDataField[]) => Promise<void>
}

export function StageDataFieldsEditor({
  stageId,
  fields,
  onSave,
}: StageDataFieldsEditorProps) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [open])

  const save = useCallback(async (newFields: StageDataField[]) => {
    setSaving(true)
    try {
      await onSave(stageId, newFields)
    } finally {
      setSaving(false)
    }
  }, [stageId, onSave])

  const addField = useCallback((item: CatalogItem) => {
    if (fields.some(f => f.id === item.id)) return
    const newField: StageDataField = { ...item, required: false, auto_collect: false }
    setOpen(false)
    void save([...fields, newField])
  }, [fields, save])

  const removeField = useCallback((id: string) => {
    void save(fields.filter(f => f.id !== id))
  }, [fields, save])

  const toggleRequired = useCallback((id: string) => {
    void save(fields.map(f => f.id === id ? { ...f, required: !f.required } : f))
  }, [fields, save])

  const available = FIELD_CATALOG.filter(c => !fields.some(f => f.id === c.id))
  const grouped = CATEGORY_ORDER.reduce<Record<string, CatalogItem[]>>((acc, cat) => {
    const items = available.filter(f => f.category === cat)
    if (items.length) acc[cat] = items
    return acc
  }, {})

  return (
    <div className="mt-3 pt-3 border-t border-lia-border-subtle">
      <div className="flex items-center gap-1.5 mb-2">
        <Database className="w-3.5 h-3.5 text-lia-text-tertiary" />
        <span className="text-xs font-medium text-lia-text-secondary">Campos de Coleta</span>
        {saving && (
          <Loader2 className="w-3 h-3 text-lia-text-tertiary animate-spin ml-auto" />
        )}
      </div>

      {fields.length === 0 && (
        <p className="text-xs text-lia-text-tertiary mb-2">
          Nenhum campo configurado — candidatos nesta etapa não precisam enviar dados.
        </p>
      )}

      {fields.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {fields.map(f => (
            <div
              key={f.id}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle"
            >
              <button
                onClick={() => toggleRequired(f.id)}
                title={f.required ? "Obrigatório — clique para tornar opcional" : "Opcional — clique para tornar obrigatório"}
                className={cn(
                  "w-3.5 h-3.5 rounded-full text-[9px] font-bold flex items-center justify-center transition-colors shrink-0",
                  f.required
                    ? "bg-status-error text-white"
                    : "bg-transparent text-lia-text-tertiary border border-lia-border-subtle hover:border-status-warning/70"
                )}
              >
                {f.required ? "!" : "?"}
              </button>
              <span>{f.displayName}</span>
              <button
                onClick={() => removeField(f.id)}
                className="ml-0.5 text-lia-text-tertiary hover:text-status-error transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="relative" ref={dropdownRef}>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 gap-1 text-xs text-lia-text-tertiary hover:text-lia-text-primary px-2"
          onClick={() => setOpen(v => !v)}
        >
          <Plus className="w-3 h-3" />
          Adicionar Campo
          <ChevronDown className={cn("w-3 h-3 transition-transform", open && "rotate-180")} />
        </Button>

        {open && (
          <div className="absolute left-0 top-7 z-30 w-60 bg-lia-bg-primary border border-lia-border-subtle rounded-lg shadow-lg p-2 space-y-1.5 max-h-72 overflow-y-auto">
            {Object.keys(grouped).length === 0 ? (
              <p className="text-xs text-lia-text-tertiary px-2 py-1.5">
                Todos os campos já foram adicionados.
              </p>
            ) : (
              Object.entries(grouped).map(([cat, items]) => (
                <div key={cat}>
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-lia-text-tertiary px-2 mb-0.5">
                    {CATEGORY_LABELS[cat as StageDataField["category"]]}
                  </p>
                  {items.map(item => (
                    <button
                      key={item.id}
                      onClick={() => addField(item)}
                      className="w-full text-left text-xs px-2 py-1.5 rounded hover:bg-lia-bg-secondary text-lia-text-primary transition-colors"
                    >
                      {item.displayName}
                    </button>
                  ))}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
