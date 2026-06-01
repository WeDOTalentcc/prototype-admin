"use client"

import React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import { EligibilityScopeEditor, VigenciaSubsidiariesEditor } from "@/components/settings/_shared"
import { useDepartmentsList } from "@/hooks/settings/useDepartmentsList"
import { CANONICAL_SENIORITY_LEVELS } from "@/lib/compensation/seniority-levels"
import type { SalaryBandRow } from "@/hooks/company/useSalaryBands"

interface SalaryBandFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editing: SalaryBandRow | null
  setEditing: React.Dispatch<React.SetStateAction<SalaryBandRow | null>>
  isSaving: boolean
  onSave: (b: SalaryBandRow) => void
}

const selectClass =
  "h-10 w-full rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-3 text-sm text-lia-text-primary"
const numInput = "h-10 w-full rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-3 text-sm tabular-nums"
const sectionTitle = "text-xs font-semibold uppercase tracking-wide text-lia-text-tertiary"

export function SalaryBandFormModal({ open, onOpenChange, editing, setEditing, isSaving, onSave }: SalaryBandFormModalProps) {
  const { departments, loading: deptsLoading } = useDepartmentsList()

  if (!editing) return null
  const b = editing
  const set = (patch: Partial<SalaryBandRow>) => setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
  const numOrNull = (v: string) => (v ? Number(v) : null)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{b.id ? "Editar faixa salarial" : "Nova faixa salarial"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs mb-1 block">Nível *</Label>
              <select className={selectClass} value={b.level} onChange={(e) => set({ level: e.target.value })}>
                {CANONICAL_SENIORITY_LEVELS.map((l) => (
                  <option key={l.id} value={l.id}>{l.label}</option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs mb-1 block">Moeda</Label>
              <select className={selectClass} value={b.currency || "BRL"} onChange={(e) => set({ currency: e.target.value })}>
                <option value="BRL">BRL — Real</option>
                <option value="USD">USD — Dólar</option>
                <option value="EUR">EUR — Euro</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <Label className="text-xs mb-1 block">Mín</Label>
              <input type="number" className={numInput} value={b.min ?? ""} placeholder="0"
                onChange={(e) => set({ min: numOrNull(e.target.value) })} />
            </div>
            <div>
              <Label className="text-xs mb-1 block">Mid</Label>
              <input type="number" className={numInput} value={b.mid ?? ""} placeholder="0"
                onChange={(e) => set({ mid: numOrNull(e.target.value) })} />
            </div>
            <div>
              <Label className="text-xs mb-1 block">Máx</Label>
              <input type="number" className={numInput} value={b.max ?? ""} placeholder="0"
                onChange={(e) => set({ max: numOrNull(e.target.value) })} />
            </div>
          </div>

          <div className="border-t border-lia-border-subtle pt-3 space-y-3">
            <p className={sectionTitle}>Escopo (a quem esta faixa se aplica)</p>
            <p className="text-xs text-lia-text-tertiary -mt-1">
              Faixas diferentes por departamento/área/filial são permitidas no mesmo nível. Vazio = aplica a todos.
            </p>
            <EligibilityScopeEditor
              value={b}
              onChange={set}
              departments={departments}
              deptsLoading={deptsLoading}
              showSeniority={false}
            />
          </div>

          <div className="border-t border-lia-border-subtle pt-3 space-y-3">
            <p className={sectionTitle}>Vigência &amp; Filiais</p>
            <VigenciaSubsidiariesEditor value={b} onChange={set} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>Cancelar</Button>
          <Button onClick={() => onSave(b)} disabled={isSaving || !b.level}>
            {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
            Salvar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
