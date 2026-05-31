"use client"

/**
 * VacancyBenefitsManager — reflete o catalogo de Beneficios (Configuracoes)
 * dentro da vaga (2026-05-31). Reusa o MESMO BenefitsList agrupado por
 * categoria (mode="vacancy"): linhas empilhadas, toggle = vincular/desvincular,
 * compativeis (matches_vaga) destacados. Permite criar beneficio inline e
 * (opcional) promover ao catalogo da empresa para reuso.
 *
 * Fonte de verdade do vinculo: a prop `benefits` (formData.benefits). O item
 * armazenado segue o contrato canonical VagaBenefit (snapshot + benefit_id).
 */
import React, { useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { Gift, Plus } from "lucide-react"
import { BenefitsList } from "@/components/settings/benefits/BenefitsList"
import { BenefitFormModal } from "@/components/settings/benefits/BenefitFormModal"
import { defaultBenefit } from "@/components/settings/benefits/benefits-types"
import type { BenefitTabRecord } from "@/components/settings/benefits/benefits-types"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { Button } from "@/components/ui/button"

type VagaBenefit = {
  benefit_id?: string | null
  source: "catalog" | "inline"
  name: string
  description?: string
  category?: string
  icon?: string
  value_type?: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels?: string[]
  contract_types?: string[]
  departments?: Record<string, unknown> | string[]
  is_highlighted?: boolean
  is_mandatory?: boolean
  attached_at?: string
  catalog_overrides?: Record<string, unknown> | null
}

interface VacancyBenefitsManagerProps {
  /** formData.benefits — aceita shape legado (string | {id,name}) e VagaBenefit. */
  benefits: unknown[]
  onChange: (next: VagaBenefit[]) => void
  seniorityLevel?: string
  department?: string
  contractType?: string
}

function coerceName(b: unknown): string {
  if (typeof b === "string") return b.trim()
  if (b && typeof b === "object") return String((b as { name?: string }).name || "").trim()
  return ""
}

function coerceBenefitId(b: unknown): string | null {
  if (b && typeof b === "object") {
    const o = b as { benefit_id?: string; id?: string }
    return o.benefit_id || o.id || null
  }
  return null
}

function toVagaBenefit(b: unknown): VagaBenefit {
  const bid = coerceBenefitId(b)
  const name = coerceName(b)
  const base = (b && typeof b === "object" ? (b as Record<string, unknown>) : {}) as Record<string, unknown>
  return {
    ...base,
    benefit_id: bid,
    name: name || "(sem nome)",
    source: (base.source as "catalog" | "inline") || (bid ? "catalog" : "inline"),
  }
}

function INLINE_ID(name: string): string {
  return `inline:${name.toLowerCase()}`
}

function recordFromCatalog(r: Record<string, unknown>): BenefitTabRecord {
  return {
    id: String(r.id),
    name: String(r.name || ""),
    description: String(r.description || ""),
    category: String(r.category || "other"),
    icon: (r.icon as string) || undefined,
    value_type: String(r.value_type || "informative"),
    value: r.value as number | undefined,
    percentage_value: r.percentage_value as number | undefined,
    value_details: (r.value_details as string) || "",
    applicable_to: (r.applicable_to as string[]) || [],
    seniority_levels: (r.seniority_levels as string[]) || [],
    contract_types: (r.contract_types as string[]) || [],
    departments: (r.departments as Record<string, unknown>) || {},
    waiting_period_days: (r.waiting_period_days as number) ?? 0,
    is_mandatory: !!r.is_mandatory,
    is_active: r.is_active !== false,
    is_highlighted: !!r.is_highlighted,
    is_discount: !!r.is_discount,
    order: (r.order as number) ?? 0,
    provider: (r.provider as string) || undefined,
    matches_vaga: (r.matches_vaga as boolean) ?? null,
  }
}

function recordFromInline(vb: VagaBenefit): BenefitTabRecord {
  return {
    ...defaultBenefit,
    id: INLINE_ID(vb.name),
    name: vb.name,
    description: vb.description || "",
    category: vb.category || "other",
    value_type: vb.value_type || "informative",
    value_details: vb.value_details || "",
    is_highlighted: !!vb.is_highlighted,
    is_mandatory: !!vb.is_mandatory,
    matches_vaga: null,
  }
}

export function VacancyBenefitsManager({
  benefits,
  onChange,
  seniorityLevel,
  department,
  contractType,
}: VacancyBenefitsManagerProps) {
  const t = useTranslations("settings.benefits")
  const tv = useTranslations("jobs.vacancyBenefits")
  const queryClient = useQueryClient()

  const linked = useMemo<VagaBenefit[]>(
    () => (benefits || []).map(toVagaBenefit).filter((b) => b.name && b.name !== "(sem nome)"),
    [benefits],
  )

  const { data: catalog = [], isLoading, error, refetch } = useQuery<Record<string, unknown>[]>({
    queryKey: ["vaga-benefits-active", seniorityLevel || "", department || "", contractType || ""],
    queryFn: async () => {
      const qs = new URLSearchParams({ with_matches: "true" })
      if (seniorityLevel) qs.set("seniority_level", seniorityLevel)
      if (department) qs.set("department", department)
      if (contractType) qs.set("contract_type", contractType)
      const res = await fetch(`/api/backend-proxy/company/benefits/active?${qs.toString()}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return Array.isArray(json) ? json : json?.data || []
    },
    staleTime: 30_000,
  })

  // ids de catalogo vinculados + nomes inline vinculados
  const linkedCatalogIds = useMemo(
    () => new Set(linked.filter((b) => b.benefit_id).map((b) => String(b.benefit_id))),
    [linked],
  )
  const catalogIds = useMemo(() => new Set(catalog.map((r) => String(r.id))), [catalog])
  const inlineLinked = useMemo(
    () => linked.filter((b) => !b.benefit_id || !catalogIds.has(String(b.benefit_id))),
    [linked, catalogIds],
  )

  const records: BenefitTabRecord[] = useMemo(() => {
    const cat = catalog.map(recordFromCatalog)
    const inline = inlineLinked.map(recordFromInline)
    return [...cat, ...inline]
  }, [catalog, inlineLinked])

  const linkedIds = useMemo(() => {
    const ids = new Set<string>(linkedCatalogIds)
    inlineLinked.forEach((b) => ids.add(INLINE_ID(b.name)))
    return ids
  }, [linkedCatalogIds, inlineLinked])

  // --- modal de criar/editar inline + promote-back -------------------------
  const [editingBenefit, setEditingBenefit] = useState<BenefitTabRecord | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<"create" | "edit">("create")
  const [editingId, setEditingId] = useState<string | null>(null)
  const [alsoSaveToCatalog, setAlsoSaveToCatalog] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  function snapshotFromRecord(r: BenefitTabRecord, source: "catalog" | "inline", benefitId?: string | null): VagaBenefit {
    return {
      benefit_id: benefitId ?? null,
      source,
      name: r.name,
      description: r.description,
      category: r.category,
      icon: r.icon,
      value_type: r.value_type,
      value: r.value,
      percentage_value: r.percentage_value,
      value_details: r.value_details,
      seniority_levels: r.seniority_levels,
      contract_types: r.contract_types,
      departments: r.departments,
      is_highlighted: r.is_highlighted,
      is_mandatory: r.is_mandatory,
      attached_at: new Date().toISOString(),
    }
  }

  function toggleLink(benefit: BenefitTabRecord) {
    const id = String(benefit.id || "")
    if (id.startsWith("inline:")) {
      // inline: toggle off remove pelo nome
      onChange(linked.filter((b) => INLINE_ID(b.name) !== id))
      return
    }
    if (linkedCatalogIds.has(id)) {
      onChange(linked.filter((b) => String(b.benefit_id) !== id))
    } else {
      onChange([...linked, snapshotFromRecord(benefit, "catalog", id)])
    }
  }

  function openCreate() {
    setModalMode("create")
    setEditingId(null)
    setEditingBenefit({ ...defaultBenefit })
    setModalOpen(true)
  }

  function openEdit(benefit: BenefitTabRecord) {
    const id = String(benefit.id || "")
    setModalMode("edit")
    setEditingId(id)
    setEditingBenefit({ ...benefit })
    setModalOpen(true)
  }

  async function handleModalSave(b: BenefitTabRecord) {
    setIsSaving(true)
    try {
      if (modalMode === "edit" && editingId) {
        // edita o item vinculado (override do snapshot; nao altera o catalogo)
        const next = linked.map((entry) => {
          const entryId = entry.benefit_id ? String(entry.benefit_id) : INLINE_ID(entry.name)
          if (entryId !== editingId) return entry
          const merged = snapshotFromRecord(b, entry.source, entry.benefit_id)
          if (entry.source === "catalog") merged.catalog_overrides = { ...b }
          return merged
        })
        onChange(next)
      } else if (alsoSaveToCatalog) {
        // promote-back: salva no catalogo (dedup case-insensitive no backend) e vincula
        const res = await fetch("/api/backend-proxy/company/benefits/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(b),
        })
        if (res.ok) {
          const created = await res.json()
          const newId = created?.id || created?.data?.id || null
          onChange([...linked, snapshotFromRecord(b, "catalog", newId)])
          await queryClient.invalidateQueries({ queryKey: ["vaga-benefits-active"] })
        }
      } else {
        // somente nesta vaga (inline)
        onChange([...linked, snapshotFromRecord(b, "inline", null)])
      }
      setModalOpen(false)
      setEditingBenefit(null)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={() => refetch()} />

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary">{tv("title")}</h3>
          <p className="text-xs text-lia-text-tertiary">{tv("subtitle")}</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-lia-text-secondary cursor-pointer select-none">
            <input
              type="checkbox"
              className="h-3.5 w-3.5 rounded border-lia-border-default accent-lia-btn-primary-bg"
              checked={alsoSaveToCatalog}
              onChange={(e) => setAlsoSaveToCatalog(e.target.checked)}
            />
            {tv("alsoSaveToCatalog")}
          </label>
          <Button size="sm" onClick={openCreate} className="gap-1.5 text-xs">
            <Plus className="w-3.5 h-3.5" />
            {tv("addBenefit")}
          </Button>
        </div>
      </div>

      {records.length === 0 ? (
        <div className="rounded-md border border-dashed border-lia-border-default p-6 text-center">
          <Gift className="w-5 h-5 mx-auto text-lia-text-disabled mb-2" />
          <p className="text-sm text-lia-text-secondary">{tv("emptyCatalog")}</p>
          <Button size="sm" variant="outline" onClick={openCreate} className="mt-3 gap-1.5 text-xs">
            <Plus className="w-3.5 h-3.5" />
            {tv("addBenefit")}
          </Button>
        </div>
      ) : (
        <BenefitsList
          benefits={records}
          isEditingBenefits={true}
          mode="vacancy"
          linkedIds={linkedIds}
          onToggleStatus={toggleLink}
          onEditBenefit={openEdit}
          onCreateBenefitInCategory={(categoryId) => {
            setModalMode("create")
            setEditingId(null)
            setEditingBenefit({ ...defaultBenefit, category: categoryId })
            setModalOpen(true)
          }}
          onDelete={() => { /* vaga: nao deleta do catalogo; toggle desvincula */ }}
        />
      )}

      <BenefitFormModal
        open={modalOpen}
        onOpenChange={(o: boolean) => { if (!o) { setModalOpen(false); setEditingBenefit(null) } }}
        editingBenefit={editingBenefit}
        setEditingBenefit={setEditingBenefit}
        isSaving={isSaving}
        onSave={handleModalSave}
        context="job"
      />
    </div>
  )
}

export default VacancyBenefitsManager
