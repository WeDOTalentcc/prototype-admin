"use client"

import React, { useCallback, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import {
  Plus,
  Gift,
  Loader2,
  Stethoscope,
  Utensils,
  Car,
  GraduationCap,
  HeartPulse,
  Wallet,
  Home,
  Baby,
  Clock,
  Shield,
  type LucideIcon,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { textStyles } from "@/lib/design-tokens"
import { BenefitFormModal } from "./BenefitFormModal"
import { BenefitItemCard } from "./BenefitItemCard"
import { invalidateBenefitsCache } from "@/hooks/company/useCompanyBenefits"
import {
  BENEFIT_CATEGORY_META,
  type BenefitCategory,
  type CompanyBenefit,
} from "@/types/benefits"
import { apiFetch } from "@/lib/api/api-fetch"

const CATEGORY_ICONS: Record<BenefitCategory, LucideIcon> = {
  health: Stethoscope,
  food: Utensils,
  transport: Car,
  education: GraduationCap,
  wellness: HeartPulse,
  financial: Wallet,
  quality_life: Home,
  family: Baby,
  flexibility: Clock,
  security: Shield,
  other: Gift,
}

const CATEGORY_ORDER: BenefitCategory[] = [
  "health",
  "food",
  "transport",
  "wellness",
  "financial",
  "education",
  "family",
  "quality_life",
  "flexibility",
  "security",
  "other",
]

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
  const t = useTranslations("settings.benefits")
  // company_id é resolvido pelo backend via JWT (REGRA 2 canonical).
  // companyId é mantido como guard rail (não chamar API antes de carregar) + para invalidar cache.
  const [showModal, setShowModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<CompanyBenefit | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadExtracting, setUploadExtracting] = useState(false)
  const [extractedBenefits, setExtractedBenefits] = useState<unknown[] | null>(null)

  const groups = useMemo(() => {
    const byCategory = new Map<BenefitCategory, LooseBenefit[]>()
    for (const b of benefits) {
      const category = (b.category as BenefitCategory) || "quality_life"
      const list = byCategory.get(category) || []
      list.push(b)
      byCategory.set(category, list)
    }
    for (const list of byCategory.values()) {
      list.sort((a, b) => {
        const aHighlight = a.is_highlighted ? 0 : 1
        const bHighlight = b.is_highlighted ? 0 : 1
        if (aHighlight !== bHighlight) return aHighlight - bHighlight
        return (a.name || "").localeCompare(b.name || "", "pt-BR")
      })
    }
    const ordered: { category: BenefitCategory; items: LooseBenefit[] }[] = []
    for (const cat of CATEGORY_ORDER) {
      const items = byCategory.get(cat)
      if (items && items.length) ordered.push({ category: cat, items })
    }
    for (const [cat, items] of byCategory.entries()) {
      if (!CATEGORY_ORDER.includes(cat)) ordered.push({ category: cat, items })
    }
    return ordered
  }, [benefits])

  const totalCount = benefits.length

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


  const handleBenefitUpload = async (file: File) => {
    setUploadExtracting(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await apiFetch("/api/backend-proxy/company/benefits/upload-extract", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error((data as { error?: string; detail?: string }).error || (data as { detail?: string }).detail || "Falha na extração")
      }

      const extracted = (data as { benefits?: unknown[]; extracted_count?: number }).benefits
      const count = (data as { extracted_count?: number }).extracted_count ?? (Array.isArray(extracted) ? extracted.length : 0)

      if (extracted && Array.isArray(extracted) && extracted.length > 0) {
        setExtractedBenefits(extracted)
        // TODO: modal de confirmação em lote — próxima iteração
        if (typeof window !== "undefined") {
          window.alert(`${count} benefício(s) extraído(s). Funcionalidade de confirmação em lote em desenvolvimento.`)
        }
      } else {
        if (typeof window !== "undefined") {
          window.alert("Nenhum benefício encontrado no documento. Verifique se é um manual de benefícios válido.")
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Tente novamente"
      setError(`Erro na extração: ${msg}`)
    } finally {
      setUploadExtracting(false)
    }
  }

  const handleSave = useCallback(
    async (benefit: CompanyBenefit) => {
      if (!companyId) {
        setError(t("companyNotIdentified"))
        return
      }
      if (!benefit.name?.trim()) {
        setError(t("benefitNameRequired"))
        return
      }
      setIsSaving(true)
      setError(null)
      try {
        const url = benefit.id
          ? `/api/backend-proxy/company/benefits/${benefit.id}`
          : `/api/backend-proxy/company/benefits/`
        // REGRA 2 canonical: strip company_id do body se presente — backend rejeita.
        const { company_id: _strip, ...benefitWithoutCompanyId } =
          benefit as CompanyBenefit & { company_id?: string }
        void _strip
        const res = await apiFetch(url, {
          method: benefit.id ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(benefitWithoutCompanyId),
        })
        if (!res.ok) {
          const text = await res.text().catch(() => "")
          throw new Error(text || t("saveFailed", { status: res.status }))
        }
        setShowModal(false)
        setEditingBenefit(null)
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : t("saveErrorGeneric"))
      } finally {
        setIsSaving(false)
      }
    },
    [companyId, refresh, t]
  )

  const handleDelete = useCallback(
    async (benefitId: string) => {
      if (!benefitId) return
      if (typeof window !== "undefined" && !window.confirm(t("removeBenefitConfirm"))) {
        return
      }
      setBusyId(benefitId)
      setError(null)
      try {
        const res = await apiFetch(`/api/backend-proxy/company/benefits/${benefitId}`,
          { method: "DELETE" }
        )
        if (!res.ok) {
          throw new Error(t("removeFailed", { status: res.status }))
        }
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : t("removeErrorGeneric"))
      } finally {
        setBusyId(null)
      }
    },
    [refresh, t]
  )

  const handleToggleStatus = useCallback(
    async (benefit: CompanyBenefit) => {
      if (!benefit.id || !companyId) return
      setBusyId(benefit.id)
      setError(null)
      try {
        const res = await apiFetch(`/api/backend-proxy/company/benefits/${benefit.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: !benefit.is_active }),
          }
        )
        if (!res.ok) throw new Error(t("updateStatusFailed", { status: res.status }))
        await refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : t("updateStatusErrorGeneric"))
      } finally {
        setBusyId(null)
      }
    },
    [companyId, refresh, t]
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className={textStyles.description}>
          {t("manageItemByItem")}
        </p>
        <div className="flex items-center gap-2">
          <label
            htmlFor="benefit-upload-input"
            className={[
              "inline-flex items-center gap-1.5 cursor-pointer px-3 py-1.5 rounded-md text-xs font-medium border border-lia-border-subtle bg-lia-bg-secondary text-lia-text-secondary hover:bg-lia-interactive-hover hover:text-lia-text-primary transition-colors",
              uploadExtracting ? "opacity-60 pointer-events-none" : "",
            ].join(" ")}
            title="Importar benefícios de documento PDF/Word"
          >
            {uploadExtracting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            )}
            {uploadExtracting ? "Extraindo..." : "Importar"}
          </label>
          <input
            id="benefit-upload-input"
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            className="sr-only"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) {
                handleBenefitUpload(file)
                e.target.value = ""
              }
            }}
          />
          <Button
            type="button"
            size="sm"
            onClick={openCreate}
            data-testid="add-benefit-cta"
            className="inline-flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            {t("addBenefitBtn")}
          </Button>
        </div>
      </div>

      {error && (
        <div className="px-3 py-2 rounded-lg text-xs bg-status-error/10 text-status-error border border-status-error/30">
          {error}
        </div>
      )}

      {totalCount === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-8 rounded-lg border border-dashed border-lia-border-subtle text-lia-text-secondary">
          <Gift className="w-6 h-6 text-lia-text-tertiary" />
          <p className={textStyles.description}>{t("noBenefitsYet")}</p>
          <Button type="button" size="sm" variant="outline" onClick={openCreate}>
            <Plus className="w-3.5 h-3.5 mr-1" />
            {t("addFirst")}
          </Button>
        </div>
      ) : (
        <div className="space-y-4" data-testid="benefits-list">
          {groups.map(({ category, items }) => {
            const meta = BENEFIT_CATEGORY_META[category]
            const Icon = CATEGORY_ICONS[category] || Gift
            return (
              <section
                key={category}
                aria-label={meta?.name || category}
                data-testid={`benefits-group-${category}`}
              >
                <div className="flex items-center gap-2 px-1 pb-2">
                  <Icon className="w-4 h-4 text-lia-text-secondary" aria-hidden="true" />
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-lia-text-secondary">
                    {meta?.name || category}
                  </h4>
                  <span
                    className="ml-1 inline-flex items-center justify-center min-w-[1.25rem] px-1.5 h-5 rounded-full bg-lia-bg-secondary text-[10px] font-medium text-lia-text-secondary"
                    data-testid={`benefits-group-count-${category}`}
                  >
                    {items.length}
                  </span>
                </div>
                <div
                  role="list"
                  className="rounded-lg border border-lia-border-subtle divide-y divide-lia-border-subtle overflow-hidden"
                >
                  {items.map((b) => (
                    <div
                      key={b.id || b.name}
                      role="listitem"
                      className={busyId === b.id ? "opacity-60 pointer-events-none" : ""}
                    >
                      <BenefitItemCard
                        benefit={{
                          id: b.id,
                          name: b.name || t("noNameDefault"),
                          description: b.description || "",
                          category: b.category || "quality_life",
                          icon: (b as { icon?: string }).icon,
                          value_type: b.value_type || "informative",
                          value: b.value,
                          percentage_value: b.percentage_value,
                          value_details: b.value_details,
                          applicable_to: (b as { applicable_to?: string[] }).applicable_to || ["all"],
                          seniority_levels: b.seniority_levels || ["all"],
                          contract_types: (b as { contract_types?: string[] }).contract_types || [],
                          departments: (b as { departments?: Record<string, unknown> }).departments || {},
                          waiting_period_days: b.waiting_period_days || 0,
                          is_mandatory: !!b.is_mandatory,
                          is_active: b.is_active !== false,
                          is_highlighted: !!b.is_highlighted,
                          is_discount: !!b.is_discount,
                          order: (b as { order?: number }).order || 0,
                          provider: b.provider,
                          provider_contact: (b as { provider_contact?: string }).provider_contact,
                        }}
                        isEditingBenefits={true}
                        onToggleStatus={(sel) => handleToggleStatus(sel as CompanyBenefit)}
                        onEdit={(sel) => openEdit(sel as CompanyBenefit)}
                        onDelete={handleDelete}
                      />
                    </div>
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      )}

      {isSaving && (
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
          {t("savingShort")}
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
