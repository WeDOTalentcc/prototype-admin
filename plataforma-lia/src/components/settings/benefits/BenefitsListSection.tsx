"use client"

import React, { useCallback, useMemo, useState } from "react"
import { Plus, Gift, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { textStyles } from "@/lib/design-tokens"
import { BenefitFormModal } from "./BenefitFormModal"
import { BenefitItemCard } from "./BenefitItemCard"
import { invalidateBenefitsCache } from "@/hooks/company/useCompanyBenefits"
import type { CompanyBenefit } from "@/types/benefits"

type LooseBenefit = Partial<CompanyBenefit> & { id?: string; name?: string }

interface BenefitsListSectionProps {
  benefits: LooseBenefit[]
  companyId: string | null
  onChanged: () => Promise<void> | void
}

function emptyBenefit(): CompanyBenefit {
  return {
    name: "",
    description: "",
    category: "quality_life",
    value_type: "informative",
    seniority_levels: ["all"],
    waiting_period_days: 0,
    is_mandatory: false,
    is_active: true,
    is_highlighted: false,
    is_discount: false,
  }
}

function dispatchSettingsUpdate() {
  if (typeof window === "undefined") return
  const detail = {
    actionId: "configure_benefits",
    section: "benefits",
    source: "ui" as const,
    ts: Date.now(),
  }
  window.dispatchEvent(new CustomEvent("lia:settings-success", { detail }))
  window.dispatchEvent(new CustomEvent("lia:settings-updated", { detail }))
}

export function BenefitsListSection({
  benefits,
  companyId,
  onChanged,
}: BenefitsListSectionProps) {
  const [showModal, setShowModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<CompanyBenefit | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const sorted = useMemo(
    () =>
      [...benefits].sort((a, b) => {
        const aHighlight = a.is_highlighted ? 0 : 1
        const bHighlight = b.is_highlighted ? 0 : 1
        if (aHighlight !== bHighlight) return aHighlight - bHighlight
        return (a.name || "").localeCompare(b.name || "", "pt-BR")
      }),
    [benefits]
  )

  const refresh = useCallback(async () => {
    if (companyId) invalidateBenefitsCache(companyId)
    dispatchSettingsUpdate()
    await onChanged()
  }, [companyId, onChanged])

  const openCreate = useCallback(() => {
    setError(null)
    setEditingBenefit(emptyBenefit())
    setShowModal(true)
  }, [])

  const openEdit = useCallback((b: CompanyBenefit) => {
    setError(null)
    setEditingBenefit({ ...b })
    setShowModal(true)
  }, [])

  const handleSave = useCallback(
    async (benefit: CompanyBenefit) => {
      if (!companyId) {
        setError("Empresa não identificada. Recarregue a página.")
        return
      }
      if (!benefit.name?.trim()) {
        setError("Informe o nome do benefício.")
        return
      }
      setIsSaving(true)
      setError(null)
      try {
        const cid = encodeURIComponent(companyId)
        const url = benefit.id
          ? `/api/backend-proxy/company/benefits/${benefit.id}?company_id=${cid}`
          : `/api/backend-proxy/company/benefits/?company_id=${cid}`
        const res = await fetch(url, {
          method: benefit.id ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(benefit),
        })
        if (!res.ok) {
          const text = await res.text().catch(() => "")
          throw new Error(text || `Falha ao salvar benefício (${res.status})`)
        }
        setShowModal(false)
        setEditingBenefit(null)
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao salvar benefício.")
      } finally {
        setIsSaving(false)
      }
    },
    [companyId, refresh]
  )

  const handleDelete = useCallback(
    async (benefitId: string) => {
      if (!benefitId) return
      if (typeof window !== "undefined" && !window.confirm("Remover este benefício?")) {
        return
      }
      setBusyId(benefitId)
      setError(null)
      try {
        const res = await fetch(
          `/api/backend-proxy/company/benefits/${benefitId}`,
          { method: "DELETE" }
        )
        if (!res.ok) {
          throw new Error(`Falha ao remover (${res.status})`)
        }
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao remover benefício.")
      } finally {
        setBusyId(null)
      }
    },
    [refresh]
  )

  const handleToggleStatus = useCallback(
    async (benefit: CompanyBenefit) => {
      if (!benefit.id || !companyId) return
      setBusyId(benefit.id)
      setError(null)
      try {
        const res = await fetch(
          `/api/backend-proxy/company/benefits/${benefit.id}?company_id=${encodeURIComponent(companyId)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: !benefit.is_active }),
          }
        )
        if (!res.ok) throw new Error(`Falha ao atualizar status (${res.status})`)
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao atualizar benefício.")
      } finally {
        setBusyId(null)
      }
    },
    [companyId, refresh]
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className={textStyles.description}>
          Gerencie item a item o pacote de benefícios oferecido.
        </p>
        <Button
          type="button"
          size="sm"
          onClick={openCreate}
          data-testid="add-benefit-cta"
          className="inline-flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Adicionar benefício
        </Button>
      </div>

      {error && (
        <div className="px-3 py-2 rounded-lg text-xs bg-status-error/10 text-status-error border border-status-error/30">
          {error}
        </div>
      )}

      {sorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-8 rounded-lg border border-dashed border-lia-border-subtle text-lia-text-secondary">
          <Gift className="w-6 h-6 text-lia-text-tertiary" />
          <p className={textStyles.description}>Nenhum benefício cadastrado ainda.</p>
          <Button type="button" size="sm" variant="outline" onClick={openCreate}>
            <Plus className="w-3.5 h-3.5 mr-1" />
            Adicionar o primeiro
          </Button>
        </div>
      ) : (
        <div
          role="list"
          className="rounded-lg border border-lia-border-subtle divide-y divide-lia-border-subtle overflow-hidden"
          data-testid="benefits-list"
        >
          {sorted.map((b) => (
            <div
              key={b.id || b.name}
              role="listitem"
              className={busyId === b.id ? "opacity-60 pointer-events-none" : ""}
            >
              <BenefitItemCard
                benefit={{
                  id: b.id,
                  name: b.name || "Sem nome",
                  description: b.description || "",
                  category: b.category || "quality_life",
                  value_type: b.value_type || "informative",
                  value: b.value,
                  percentage_value: b.percentage_value,
                  value_details: b.value_details,
                  seniority_levels: b.seniority_levels || ["all"],
                  waiting_period_days: b.waiting_period_days || 0,
                  is_mandatory: !!b.is_mandatory,
                  is_active: b.is_active !== false,
                  is_highlighted: !!b.is_highlighted,
                  is_discount: !!b.is_discount,
                  provider: b.provider,
                }}
                isEditingBenefits={true}
                onToggleStatus={(sel) => handleToggleStatus(sel as CompanyBenefit)}
                onEdit={(sel) => openEdit(sel as CompanyBenefit)}
                onDelete={handleDelete}
              />
            </div>
          ))}
        </div>
      )}

      {isSaving && (
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
          Salvando...
        </div>
      )}

      <BenefitFormModal
        open={showModal}
        onOpenChange={(o) => {
          setShowModal(o)
          if (!o) setEditingBenefit(null)
        }}
        editingBenefit={editingBenefit as unknown as never}
        setEditingBenefit={(b) =>
          setEditingBenefit(b as unknown as CompanyBenefit | null)
        }
        isSaving={isSaving}
        onSave={(b) => handleSave(b as unknown as CompanyBenefit)}
      />
    </div>
  )
}
