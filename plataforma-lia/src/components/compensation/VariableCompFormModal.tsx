"use client"

import React from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import { COMP_KIND_OPTIONS, FREQUENCY_OPTIONS, type VariableCompRecord } from "./variable-comp-types"

interface VariableCompFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editing: VariableCompRecord | null
  setEditing: React.Dispatch<React.SetStateAction<VariableCompRecord | null>>
  isSaving: boolean
  onSave: (c: VariableCompRecord) => void
}

const selectClass =
  "h-10 w-full rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-3 text-sm text-lia-text-primary"
const numInput = "h-10 w-full rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-3 text-sm"

export function VariableCompFormModal({ open, onOpenChange, editing, setEditing, isSaving, onSave }: VariableCompFormModalProps) {
  if (!editing) return null
  const c = editing
  const set = (patch: Partial<VariableCompRecord>) => setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
  const setSpec = (patch: Record<string, unknown>) => set({ spec: { ...(c.spec || {}), ...patch } })
  const isPercent = (c.value_type || "percent") === "percent"
  const isCommission = c.kind === "commission"
  const isEquity = c.kind === "equity"

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{c.id ? "Editar verba variável" : "Nova verba variável"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs mb-1 block">Tipo *</Label>
              <select className={selectClass} value={c.kind} onChange={(e) => set({ kind: e.target.value })}>
                {COMP_KIND_OPTIONS.map((o) => (
                  <option key={o.id} value={o.id}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs mb-1 block">Frequência</Label>
              <select className={selectClass} value={c.frequency || ""} onChange={(e) => set({ frequency: e.target.value || null })}>
                <option value="">—</option>
                {FREQUENCY_OPTIONS.map((o) => (
                  <option key={o.id} value={o.id}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <Label className="text-xs mb-1 block">Nome *</Label>
            <Input value={c.name} onChange={(e) => set({ name: e.target.value })} placeholder="Ex: Bônus anual de performance" />
          </div>

          <div>
            <Label className="text-xs mb-1 block">Descrição</Label>
            <Textarea value={c.description || ""} onChange={(e) => set({ description: e.target.value })} rows={2} placeholder="Detalhe a regra desta verba..." />
          </div>

          {!isEquity && (
            <div>
              <Label className="text-xs mb-1 block">Unidade do valor</Label>
              <select className={selectClass} value={c.value_type || "percent"} onChange={(e) => set({ value_type: e.target.value })}>
                <option value="percent">% do salário</option>
                <option value="currency">R$ (valor)</option>
              </select>
            </div>
          )}

          {/* Faixa inicial / final (por unidade) */}
          {!isEquity && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs mb-1 block">Faixa inicial ({isPercent ? "%" : "R$"})</Label>
                <input
                  type="number"
                  className={numInput}
                  value={(isPercent ? c.min_pct : c.min_amount) ?? ""}
                  onChange={(e) => set(isPercent ? { min_pct: e.target.value ? Number(e.target.value) : null } : { min_amount: e.target.value ? Number(e.target.value) : null })}
                  placeholder="0"
                />
              </div>
              <div>
                <Label className="text-xs mb-1 block">Faixa final ({isPercent ? "%" : "R$"})</Label>
                <input
                  type="number"
                  className={numInput}
                  value={(isPercent ? c.max_pct : c.max_amount) ?? ""}
                  onChange={(e) => set(isPercent ? { max_pct: e.target.value ? Number(e.target.value) : null } : { max_amount: e.target.value ? Number(e.target.value) : null })}
                  placeholder="0"
                />
              </div>
            </div>
          )}

          {isCommission && (
            <div>
              <Label className="text-xs mb-1 block">% base sobre meta</Label>
              <input
                type="number"
                className={numInput}
                value={(c.spec as { base_pct?: number })?.base_pct ?? ""}
                onChange={(e) => setSpec({ base_pct: e.target.value ? Number(e.target.value) : undefined })}
                placeholder="5"
              />
            </div>
          )}

          {isEquity && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs mb-1 block">% equity (grant)</Label>
                <input
                  type="number"
                  className={numInput}
                  value={(c.spec as { equity_pct?: number })?.equity_pct ?? ""}
                  onChange={(e) => setSpec({ equity_pct: e.target.value ? Number(e.target.value) : undefined })}
                  placeholder="0.5"
                />
              </div>
              <div className="flex items-end">
                <p className="text-micro text-lia-text-tertiary">Vesting/strike detalhados na Fase 2.</p>
              </div>
            </div>
          )}

          <label className="flex items-center gap-2 text-xs text-lia-text-secondary cursor-pointer select-none">
            <input type="checkbox" className="h-3.5 w-3.5 accent-lia-btn-primary-bg" checked={!!c.is_highlighted} onChange={(e) => set({ is_highlighted: e.target.checked })} />
            Destacar esta verba
          </label>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>Cancelar</Button>
          <Button onClick={() => onSave(c)} disabled={isSaving || !c.name.trim()}>
            {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
            Salvar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
