"use client"

import React, { useMemo } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Loader2, Calculator } from "lucide-react"
import { COMP_KIND_OPTIONS, FREQUENCY_OPTIONS, type VariableCompRecord } from "./variable-comp-types"
import { EligibilityScopeEditor, VigenciaSubsidiariesEditor } from "@/components/settings/_shared"
import { useSalaryBands } from "@/hooks/company/useSalaryBands"
import { useDepartmentsList } from "@/hooks/settings/useDepartmentsList"
import { resolveForBand, bandMapFromList, fmtBRL } from "@/lib/compensation/resolve"
import { seniorityLabel } from "@/lib/compensation/seniority-levels"

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
const sectionTitle = "text-xs font-semibold uppercase tracking-wide text-lia-text-tertiary"

export function VariableCompFormModal({ open, onOpenChange, editing, setEditing, isSaving, onSave }: VariableCompFormModalProps) {
  // Hooks SEMPRE no topo (rules-of-hooks), antes de qualquer early return.
  const { data: bands = [] } = useSalaryBands()
  const { departments, loading: deptsLoading } = useDepartmentsList()
  const bandMap = useMemo(() => bandMapFromList(bands), [bands])

  if (!editing) return null
  const c = editing
  const set = (patch: Partial<VariableCompRecord>) => setEditing((prev) => (prev ? { ...prev, ...patch } : prev))
  const setSpec = (patch: Record<string, unknown>) => set({ spec: { ...(c.spec || {}), ...patch } })
  const isPercent = (c.value_type || "percent") === "percent"
  const isCommission = c.kind === "commission"
  const isEquity = c.kind === "equity"

  // Preview do R$ derivado (% x faixa do nivel) — fonte autoritativa e o backend.
  const allLevels = Object.keys(bandMap)
  const scopedLevels =
    c.seniority_levels && c.seniority_levels.length && !c.seniority_levels.includes("all")
      ? c.seniority_levels.filter((l) => bandMap[l])
      : allLevels
  const freqLabel = FREQUENCY_OPTIONS.find((f) => f.id === c.frequency)?.label
  const previewRows = (!isEquity ? scopedLevels : [])
    .map((level) => ({ level, r: resolveForBand(c, bandMap[level]) }))
    .filter((x) => x.r.basis !== "undefined" && (x.r.min !== null || x.r.max !== null))

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

          {/* Preview do R$ derivado da faixa salarial canonica (so % do salario) */}
          {!isEquity && isPercent && (
            <div className="rounded-md border border-lia-border-subtle bg-lia-bg-tertiary/50 p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Calculator className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className={sectionTitle}>Valor estimado (R$) por nível</span>
              </div>
              {allLevels.length === 0 ? (
                <p className="text-xs text-lia-text-tertiary">
                  Defina as <strong>Faixas Salariais por Nível</strong> em Configurações para ver o R$ estimado. A verba guarda apenas o %; o valor é derivado da faixa do nível.
                </p>
              ) : previewRows.length === 0 ? (
                <p className="text-xs text-lia-text-tertiary">Preencha a faixa (%) para estimar o valor.</p>
              ) : (
                <ul className="space-y-0.5">
                  {previewRows.map(({ level, r }) => (
                    <li key={level} className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-secondary">{seniorityLabel(level)}</span>
                      <span className="text-lia-text-primary tabular-nums">
                        {fmtBRL(r.min, r.currency)} – {fmtBRL(r.max, r.currency)}
                        {freqLabel ? <span className="text-lia-text-tertiary"> / {freqLabel.toLowerCase()}</span> : null}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
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

          {/* Elegibilidade (a quem a verba se aplica) — editor canonico compartilhado */}
          <div className="border-t border-lia-border-subtle pt-3 space-y-3">
            <p className={sectionTitle}>Elegibilidade</p>
            <p className="text-xs text-lia-text-tertiary -mt-1">
              A quem esta verba se aplica. Deixe vazio para aplicar a todos.
            </p>
            <EligibilityScopeEditor
              value={c}
              onChange={set}
              departments={departments}
              deptsLoading={deptsLoading}
            />
          </div>

          {/* Vigencia + Filiais — editor canonico compartilhado */}
          <div className="border-t border-lia-border-subtle pt-3 space-y-3">
            <p className={sectionTitle}>Vigência &amp; Filiais</p>
            <VigenciaSubsidiariesEditor value={c} onChange={set} />
          </div>

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
