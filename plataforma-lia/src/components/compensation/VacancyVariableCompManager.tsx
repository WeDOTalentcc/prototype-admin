"use client"

/**
 * VacancyVariableCompManager — reflete o catalogo de Remuneracao Variavel
 * (Configuracoes) dentro da vaga. Reusa VariableCompList (mode="vacancy"):
 * lista agrupada por tipo, vincular/desvincular, compativeis (matches_vaga)
 * destacados, criar inline + promover ao catalogo. Strings PT hardcoded
 * (consistente com compensation-policies).
 */
import React, { useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Coins, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { VariableCompList } from "./VariableCompList"
import { VariableCompFormModal } from "./VariableCompFormModal"
import { defaultComponent, type VariableCompRecord } from "./variable-comp-types"

type VagaComp = {
  component_id?: string | null
  source: "catalog" | "inline"
  kind: string
  name: string
  [k: string]: unknown
}

interface VacancyVariableCompManagerProps {
  value: unknown[]
  onChange: (next: VagaComp[]) => void
  editable?: boolean
  seniorityLevel?: string
  department?: string
  contractType?: string
}

function coerceName(b: unknown): string {
  if (typeof b === "string") return b.trim()
  if (b && typeof b === "object") return String((b as { name?: string }).name || "").trim()
  return ""
}
function coerceId(b: unknown): string | null {
  if (b && typeof b === "object") {
    const o = b as { component_id?: string; id?: string }
    return o.component_id || o.id || null
  }
  return null
}
function toVagaComp(b: unknown): VagaComp {
  const cid = coerceId(b)
  const name = coerceName(b)
  const base = (b && typeof b === "object" ? (b as Record<string, unknown>) : {}) as Record<string, unknown>
  return {
    ...base,
    component_id: cid,
    name: name || "(sem nome)",
    kind: (base.kind as string) || "bonus",
    source: (base.source as "catalog" | "inline") || (cid ? "catalog" : "inline"),
  }
}
const INLINE_ID = (name: string) => `inline:${name.toLowerCase()}`

function recordFromCatalog(r: Record<string, unknown>): VariableCompRecord {
  return {
    id: String(r.id),
    kind: String(r.kind || "bonus"),
    name: String(r.name || ""),
    description: (r.description as string) || "",
    value_type: (r.value_type as string) || "percent",
    target_pct: (r.target_pct as number) ?? null,
    min_pct: (r.min_pct as number) ?? null,
    max_pct: (r.max_pct as number) ?? null,
    min_amount: (r.min_amount as number) ?? null,
    max_amount: (r.max_amount as number) ?? null,
    currency: (r.currency as string) ?? "BRL",
    frequency: (r.frequency as string) ?? null,
    trigger: (r.trigger as string) ?? null,
    spec: (r.spec as Record<string, unknown>) || {},
    is_active: r.is_active !== false,
    is_highlighted: !!r.is_highlighted,
    matches_vaga: (r.matches_vaga as boolean) ?? null,
  }
}
function recordFromInline(vc: VagaComp): VariableCompRecord {
  return {
    ...defaultComponent,
    id: INLINE_ID(vc.name),
    kind: vc.kind || "bonus",
    name: vc.name,
    description: (vc.description as string) || "",
    value_type: (vc.value_type as string) || "percent",
    min_pct: (vc.min_pct as number) ?? null,
    max_pct: (vc.max_pct as number) ?? null,
    min_amount: (vc.min_amount as number) ?? null,
    max_amount: (vc.max_amount as number) ?? null,
    spec: (vc.spec as Record<string, unknown>) || {},
    is_highlighted: !!vc.is_highlighted,
    matches_vaga: null,
  }
}

export function VacancyVariableCompManager({ value, onChange, editable = true, seniorityLevel, department, contractType }: VacancyVariableCompManagerProps) {
  const queryClient = useQueryClient()
  const linked = useMemo<VagaComp[]>(
    () => (value || []).map(toVagaComp).filter((c) => c.name && c.name !== "(sem nome)"),
    [value],
  )

  const { data: catalog = [], isLoading, error, refetch } = useQuery<Record<string, unknown>[]>({
    queryKey: ["vaga-comp-active", seniorityLevel || "", department || "", contractType || ""],
    queryFn: async () => {
      const qs = new URLSearchParams({ with_matches: "true" })
      if (seniorityLevel) qs.set("seniority_level", seniorityLevel)
      if (department) qs.set("department", department)
      if (contractType) qs.set("contract_type", contractType)
      const res = await fetch(`/api/backend-proxy/company/compensation-components/active?${qs.toString()}`, { signal: AbortSignal.timeout(12000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return Array.isArray(json) ? json : json?.data || []
    },
    staleTime: 30_000,
    retry: 1,
  })

  const linkedCatalogIds = useMemo(() => new Set(linked.filter((c) => c.component_id).map((c) => String(c.component_id))), [linked])
  const catalogIds = useMemo(() => new Set(catalog.map((r) => String(r.id))), [catalog])
  const inlineLinked = useMemo(() => linked.filter((c) => !c.component_id || !catalogIds.has(String(c.component_id))), [linked, catalogIds])

  const records: VariableCompRecord[] = useMemo(
    () => [...catalog.map(recordFromCatalog), ...inlineLinked.map(recordFromInline)],
    [catalog, inlineLinked],
  )
  const linkedIds = useMemo(() => {
    const ids = new Set<string>(linkedCatalogIds)
    inlineLinked.forEach((c) => ids.add(INLINE_ID(c.name)))
    return ids
  }, [linkedCatalogIds, inlineLinked])

  const [editing, setEditing] = useState<VariableCompRecord | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<"create" | "edit">("create")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [alsoSaveToCatalog, setAlsoSaveToCatalog] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  function snapshot(r: VariableCompRecord, source: "catalog" | "inline", cid?: string | null): VagaComp {
    return {
      component_id: cid ?? null,
      source,
      kind: r.kind,
      name: r.name,
      description: r.description,
      value_type: r.value_type,
      target_pct: r.target_pct,
      min_pct: r.min_pct,
      max_pct: r.max_pct,
      min_amount: r.min_amount,
      max_amount: r.max_amount,
      currency: r.currency,
      frequency: r.frequency,
      trigger: r.trigger,
      spec: r.spec,
      is_highlighted: r.is_highlighted,
      attached_at: new Date().toISOString(),
    }
  }

  function toggleLink(rec: VariableCompRecord) {
    const id = String(rec.id || "")
    if (id.startsWith("inline:")) {
      onChange(linked.filter((c) => INLINE_ID(c.name) !== id))
      return
    }
    if (linkedCatalogIds.has(id)) onChange(linked.filter((c) => String(c.component_id) !== id))
    else onChange([...linked, snapshot(rec, "catalog", id)])
  }

  function openCreate(kind?: string) {
    setModalMode("create"); setEditingId(null)
    setEditing({ ...defaultComponent, kind: kind || "bonus" }); setModalOpen(true)
  }
  function openEdit(rec: VariableCompRecord) {
    setModalMode("edit"); setEditingId(String(rec.id || ""))
    setEditing({ ...rec }); setModalOpen(true)
  }

  async function handleSave(r: VariableCompRecord) {
    setIsSaving(true)
    try {
      if (modalMode === "edit" && editingId) {
        const eidOf = (entry: VagaComp) => entry.component_id ? String(entry.component_id) : INLINE_ID(entry.name)
        if (linked.some((e) => eidOf(e) === editingId)) {
          onChange(linked.map((entry) => {
            if (eidOf(entry) !== editingId) return entry
            const merged = snapshot(r, entry.source, entry.component_id)
            if (entry.source === "catalog") merged.catalog_overrides = { ...r }
            return merged
          }))
        } else {
          // editar item ainda nao vinculado -> vincula com os valores editados
          const src = editingId.startsWith("inline:") ? "inline" : "catalog"
          const snap = snapshot(r, src, src === "catalog" ? editingId : null)
          if (src === "catalog") snap.catalog_overrides = { ...r }
          onChange([...linked, snap])
        }
      } else if (alsoSaveToCatalog) {
        const res = await fetch("/api/backend-proxy/company/compensation-components/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(r),
        })
        if (res.ok) {
          const created = await res.json().catch(() => ({}))
          const newId = created?.id || created?.data?.id || null
          onChange([...linked, snapshot(r, "catalog", newId)])
          await queryClient.invalidateQueries({ queryKey: ["vaga-comp-active"] })
        }
      } else {
        onChange([...linked, snapshot(r, "inline", null)])
      }
      setModalOpen(false); setEditing(null)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <div className="flex items-center gap-2 p-4 text-sm text-lia-text-secondary"><Loader2 className="w-4 h-4 animate-spin" />Carregando verbas variáveis…</div>
  }
  if (error) {
    return (
      <div className="flex items-center justify-between p-4 rounded-md border border-status-error/30 bg-status-error/5">
        <span className="flex items-center gap-2 text-sm text-status-error"><AlertCircle className="w-4 h-4" />Erro ao carregar verbas variáveis.</span>
        <Button size="sm" variant="outline" onClick={() => refetch()}>Tentar de novo</Button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wider">Remuneração Variável</h3>
          <p className="text-xs text-lia-text-tertiary">Vincule verbas do catálogo da empresa. Compatíveis com o nível e a área da vaga aparecem destacados.</p>
        </div>
        {editable && (
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-lia-text-secondary cursor-pointer select-none">
              <input type="checkbox" className="h-3.5 w-3.5 accent-lia-btn-primary-bg" checked={alsoSaveToCatalog} onChange={(e) => setAlsoSaveToCatalog(e.target.checked)} />
              Também salvar no catálogo
            </label>
            <Button size="sm" onClick={() => openCreate()} className="gap-1.5 text-xs"><Plus className="w-3.5 h-3.5" />Adicionar verba</Button>
          </div>
        )}
      </div>

      {records.length === 0 ? (
        <div className="rounded-md border border-dashed border-lia-border-default p-6 text-center">
          <Coins className="w-5 h-5 mx-auto text-lia-text-disabled mb-2" />
          <p className="text-sm text-lia-text-secondary">Nenhuma verba variável no catálogo da empresa ainda.</p>
          {editable && <Button size="sm" variant="outline" onClick={() => openCreate()} className="mt-3 gap-1.5 text-xs"><Plus className="w-3.5 h-3.5" />Adicionar verba</Button>}
        </div>
      ) : (
        <VariableCompList
          components={records}
          isEditing={editable}
          mode="vacancy"
          linkedIds={linkedIds}
          onToggle={toggleLink}
          onEdit={openEdit}
          onCreateInKind={(k) => openCreate(k)}
          onDelete={() => { /* vaga: toggle desvincula, nao deleta do catalogo */ }}
        />
      )}

      <VariableCompFormModal
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

export default VacancyVariableCompManager
