"use client"

/**
 * SalaryBandsSection — catalogo GRANULAR das faixas salariais por nivel (fonte unica).
 *
 * Multiplas faixas por nivel (escopo por departamento/contrato/filial). Agrupado por
 * nivel na exibicao. CRUD via SalaryBandFormModal. As verbas (%) derivam R$ da
 * faixa que casa o escopo; as vagas usam a faixa que casa nivel+departamento. React Query.
 */
import React, { useMemo, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { Plus, Loader2, Layers, Pencil, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSalaryBands, type SalaryBandRow } from "@/hooks/company/useSalaryBands"
import { CANONICAL_SENIORITY_LEVELS, seniorityLabel } from "@/lib/compensation/seniority-levels"
import { SalaryBandFormModal } from "@/components/compensation/SalaryBandFormModal"

const BASE = "/api/backend-proxy/company/salary-bands"

function scopeSummary(b: SalaryBandRow): string {
  const parts: string[] = []
  const deps = b.departments && typeof b.departments === "object"
    ? Object.keys(b.departments).filter((k) => (b.departments as Record<string, unknown>)[k])
    : []
  if (deps.length) parts.push(deps.join(", "))
  if (b.contract_types?.length) parts.push(b.contract_types.join(", "))
  if (b.subsidiaries?.length) parts.push(`${b.subsidiaries.length} filial(is)`)
  return parts.length ? parts.join(" · ") : "Todos"
}

function fmt(v?: number | null, currency = "BRL"): string {
  if (v == null) return "—"
  try { return v.toLocaleString("pt-BR", { style: "currency", currency, maximumFractionDigits: 0 }) }
  catch { return `R$ ${Math.round(v).toLocaleString("pt-BR")}` }
}

export function SalaryBandsSection() {
  const queryClient = useQueryClient()
  const { data: bands = [], isLoading } = useSalaryBands()
  const [editing, setEditing] = useState<SalaryBandRow | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const grouped = useMemo(() => {
    const byLevel = new Map<string, SalaryBandRow[]>()
    for (const b of bands) {
      const arr = byLevel.get(b.level) || []
      arr.push(b)
      byLevel.set(b.level, arr)
    }
    return CANONICAL_SENIORITY_LEVELS
      .filter((l) => byLevel.has(l.id))
      .map((l) => ({ level: l.id, label: l.label, items: byLevel.get(l.id)! }))
  }, [bands])

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["company-salary-bands"] }),
      queryClient.invalidateQueries({ queryKey: ["company-salary-band-map"] }),
    ])
  }

  async function handleSave(b: SalaryBandRow) {
    setIsSaving(true)
    try {
      const url = b.id ? `${BASE}/${b.id}` : `${BASE}/`
      const res = await fetch(url, {
        method: b.id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(b),
      })
      if (res.ok) { await invalidate(); setModalOpen(false); setEditing(null) }
    } finally { setIsSaving(false) }
  }

  async function handleDelete(id?: string) {
    if (!id) return
    const res = await fetch(`${BASE}/${id}`, { method: "DELETE" })
    if (res.ok) await invalidate()
  }

  function openCreate(level?: string) {
    setEditing({
      level: level || "junior",
      min: null, mid: null, max: null,
      currency: "BRL",
      contract_types: [],
      departments: {},
      subsidiaries: [],
    })
    setModalOpen(true)
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
            Min / mid / max por nível — granular por departamento, contrato e filial. Verbas (%) e vagas reutilizam.
          </p>
        </div>
        <Button size="sm" onClick={() => openCreate()} className="gap-1.5 text-xs">
          <Plus className="w-3.5 h-3.5" />Adicionar faixa
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 p-4 text-sm text-lia-text-secondary">
          <Loader2 className="w-4 h-4 animate-spin" />Carregando…
        </div>
      ) : bands.length === 0 ? (
        <div className="rounded-md border border-dashed border-lia-border-default p-6 text-center">
          <Layers className="w-5 h-5 mx-auto text-lia-text-muted mb-2" />
          <p className="text-sm text-lia-text-secondary mb-3">Nenhuma faixa salarial definida.</p>
          <Button size="sm" variant="outline" onClick={() => openCreate()} className="gap-1.5 text-xs">
            <Plus className="w-3.5 h-3.5" />Adicionar faixa
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {grouped.map((g) => (
            <div key={g.level}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-lia-text-secondary">{g.label}</span>
                <button
                  type="button"
                  onClick={() => openCreate(g.level)}
                  className="text-xs text-lia-btn-primary-bg hover:underline inline-flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />faixa neste nível
                </button>
              </div>
              <div className="rounded-md border border-lia-border-subtle divide-y divide-lia-border-subtle">
                {g.items.map((b) => (
                  <div key={b.id} className="flex items-center justify-between px-3 py-2">
                    <div className="min-w-0">
                      <div className="text-sm text-lia-text-primary tabular-nums">
                        {fmt(b.min, b.currency || "BRL")} – {fmt(b.max, b.currency || "BRL")}
                        {b.mid != null && (
                          <span className="text-lia-text-tertiary"> (mid {fmt(b.mid, b.currency || "BRL")})</span>
                        )}
                      </div>
                      <div className="text-xs text-lia-text-tertiary truncate">{scopeSummary(b)}</div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        type="button"
                        onClick={() => { setEditing(b); setModalOpen(true) }}
                        className="p-1 text-lia-text-secondary hover:text-lia-text-primary"
                        aria-label="Editar faixa"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(b.id)}
                        className="p-1 text-lia-text-secondary hover:text-status-error"
                        aria-label="Remover faixa"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <SalaryBandFormModal
        open={modalOpen}
        onOpenChange={(o) => { if (!o) { setModalOpen(false); setEditing(null) } }}
        editing={editing}
        setEditing={setEditing}
        isSaving={isSaving}
        onSave={handleSave}
      />
    </div>
  )
}

export default SalaryBandsSection
