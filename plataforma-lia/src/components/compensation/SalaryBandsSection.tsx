"use client"

/**
 * SalaryBandsSection — FONTE UNICA das faixas salariais por nivel (SalaryBand).
 *
 * Define-se UMA vez aqui (Configuracoes -> Minha Empresa). As verbas variaveis (%)
 * derivam o R\$ desta faixa (sem redigitar) e a vaga usa como default do salary_range
 * do nivel. React Query key ["company-salary-bands"]. Strings PT.
 */
import React, { useEffect, useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Loader2, Trash2, Layers, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSalaryBands, type SalaryBandRow } from "@/hooks/company/useSalaryBands"
import { CANONICAL_SENIORITY_LEVELS, seniorityLabel } from "@/lib/compensation/seniority-levels"

const BASE = "/api/backend-proxy/company/salary-bands"
const numInput =
  "h-9 w-full rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-2 text-sm tabular-nums"
const selectClass =
  "h-9 w-full rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-2 text-sm text-lia-text-primary"

export function SalaryBandsSection() {
  const queryClient = useQueryClient()
  const { data: serverBands = [], isLoading } = useSalaryBands()

  const [rows, setRows] = useState<SalaryBandRow[]>([])
  const [dirty, setDirty] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [savedAt, setSavedAt] = useState<number | null>(null)

  // Sincroniza buffer local com o servidor enquanto nao houver edicao pendente.
  useEffect(() => {
    if (!dirty) setRows(serverBands)
  }, [serverBands, dirty])

  const usedLevels = useMemo(() => new Set(rows.map((r) => r.level)), [rows])
  const nextFreeLevel = useMemo(
    () => CANONICAL_SENIORITY_LEVELS.find((l) => !usedLevels.has(l.id))?.id || "",
    [usedLevels],
  )

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["company-salary-bands"] })
  }

  const patchRow = (idx: number, patch: Partial<SalaryBandRow>) => {
    setDirty(true)
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)))
  }
  const removeRow = (idx: number) => {
    setDirty(true)
    setRows((prev) => prev.filter((_, i) => i !== idx))
  }
  const addRow = () => {
    if (!nextFreeLevel) return
    setDirty(true)
    setRows((prev) => [...prev, { level: nextFreeLevel, min: null, mid: null, max: null, currency: "BRL" }])
  }

  const numOrNull = (v: string) => (v ? Number(v) : null)

  async function save() {
    setIsSaving(true)
    try {
      const bands = rows
        .filter((r) => r.level)
        .map((r, i) => ({
          level: r.level,
          label: seniorityLabel(r.level),
          min: r.min ?? null,
          mid: r.mid ?? null,
          max: r.max ?? null,
          currency: r.currency || "BRL",
          order: i,
        }))
      const res = await fetch(`${BASE}/`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bands }),
      })
      if (res.ok) {
        setDirty(false)
        await invalidate()
        setSavedAt(Date.now())
        setTimeout(() => setSavedAt(null), 2500)
      }
    } finally {
      setIsSaving(false)
    }
  }

  async function seedDefaults() {
    setIsSaving(true)
    try {
      const res = await fetch(`${BASE}/seed-defaults`, { method: "POST" })
      if (res.ok) {
        setDirty(false)
        await invalidate()
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-lia-text-secondary" />
            Faixas Salariais por Nível
          </h3>
          <p className="text-xs text-lia-text-tertiary">
            Defina min / mid / max por nível uma vez. As verbas variáveis (%) e as vagas reutilizam — sem redigitar.
          </p>
        </div>
        {dirty && (
          <Button size="sm" onClick={save} disabled={isSaving} className="gap-1.5 text-xs">
            {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            Salvar faixas
          </Button>
        )}
        {!dirty && savedAt && <span className="text-xs text-status-success">Salvo ✓</span>}
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 p-4 text-sm text-lia-text-secondary">
          <Loader2 className="w-4 h-4 animate-spin" />Carregando…
        </div>
      ) : rows.length === 0 ? (
        <div className="rounded-md border border-dashed border-lia-border-default p-6 text-center">
          <Layers className="w-5 h-5 mx-auto text-lia-text-disabled mb-2" />
          <p className="text-sm text-lia-text-secondary">Nenhuma faixa salarial definida.</p>
          <div className="flex items-center justify-center gap-2 mt-3">
            <Button size="sm" variant="outline" onClick={seedDefaults} disabled={isSaving} className="gap-1.5 text-xs">
              <Sparkles className="w-3.5 h-3.5" />Usar padrão BR
            </Button>
            <Button size="sm" variant="outline" onClick={addRow} className="gap-1.5 text-xs">
              <Plus className="w-3.5 h-3.5" />Adicionar nível
            </Button>
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-lia-border-subtle overflow-hidden">
          <div className="grid grid-cols-[1.4fr_1fr_1fr_1fr_auto] gap-2 px-3 py-2 bg-lia-bg-tertiary/50 text-micro uppercase tracking-wide text-lia-text-tertiary">
            <span>Nível</span><span>Mín (R$)</span><span>Mid (R$)</span><span>Máx (R$)</span><span />
          </div>
          <div className="divide-y divide-lia-border-subtle">
            {rows.map((r, idx) => (
              <div key={idx} className="grid grid-cols-[1.4fr_1fr_1fr_1fr_auto] gap-2 px-3 py-2 items-center">
                <select className={selectClass} value={r.level} onChange={(e) => patchRow(idx, { level: e.target.value })}>
                  {CANONICAL_SENIORITY_LEVELS.map((l) => (
                    <option key={l.id} value={l.id} disabled={l.id !== r.level && usedLevels.has(l.id)}>
                      {l.label}
                    </option>
                  ))}
                </select>
                <input type="number" className={numInput} value={r.min ?? ""} placeholder="0"
                  onChange={(e) => patchRow(idx, { min: numOrNull(e.target.value) })} />
                <input type="number" className={numInput} value={r.mid ?? ""} placeholder="0"
                  onChange={(e) => patchRow(idx, { mid: numOrNull(e.target.value) })} />
                <input type="number" className={numInput} value={r.max ?? ""} placeholder="0"
                  onChange={(e) => patchRow(idx, { max: numOrNull(e.target.value) })} />
                <button type="button" onClick={() => removeRow(idx)} aria-label={`Remover faixa ${seniorityLabel(r.level)}`}
                  className="text-lia-text-tertiary hover:text-status-error transition-colors">
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
          <div className="px-3 py-2 border-t border-lia-border-subtle">
            <button type="button" onClick={addRow} disabled={!nextFreeLevel}
              className="text-xs text-lia-btn-primary-bg hover:underline disabled:opacity-50 disabled:no-underline inline-flex items-center gap-1">
              <Plus className="w-3.5 h-3.5" />Adicionar nível
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default SalaryBandsSection
