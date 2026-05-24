"use client"

/**
 * BenefitFormModal — cadastro/edicao de beneficio da empresa.
 *
 * Refactor canonical 2026-05-24:
 * - DialogContent (era DraggableDialogContent: drag handle de 48px bloqueava clicks)
 * - useBenefitTaxonomy hook (era 3 arrays hardcoded: BENEFIT_CATEGORIES, VALUE_TYPES, WAITING_PERIODS)
 * - Tokens DS v4.2.2: rounded-md (era rounded-full), border-lia-border-subtle (substitui cores hardcoded fora do DS)
 * - Secoes reagrupadas: Basico → Quem recebe → Como funciona → Vigencia → Fornecedor → Historico
 * - 4 switches em lista vertical (era grid 2x2 confuso)
 * - <BenefitFormSection> extraido para DRY
 *
 * Aplica:
 * - canonical-fix: taxonomia 100% via hook canonical (single source of truth)
 * - production-quality (frontend): tokens DS, Rules of Hooks compliant
 * - design: hierarquia visual + agrupamento mental do recrutador
 */

import React from "react"
import { useTranslations } from "next-intl"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  DollarSign,
  Percent,
  Info,
  Repeat,
  Receipt,
  Shield,
  Loader2,
  Lock,
  X,
  Plus,
  type LucideIcon,
} from "lucide-react"
import {
  APPLICABLE_TO_OPTIONS,
  CONTRACT_TYPE_OPTIONS,
  SENIORITY_OPTIONS,
  type SubsidiaryEntry,
  type BenefitHistoryEntry,
  type BenefitTabRecord,
} from "./benefits-types"
import { useDepartmentsList } from "@/hooks/settings/useDepartmentsList"
import { useBenefitTaxonomy } from "@/hooks/settings/useBenefitTaxonomy"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// Canonical: alias para BenefitTabRecord — pattern matches BenefitItemCard.tsx:23.
// Removed local interface duplication (TS2322 fix: BenefitsTab.tsx:165/167).
type Benefit = BenefitTabRecord

interface BenefitFormModalProps {
  context?: "settings" | "job"
  open: boolean
  onOpenChange: (open: boolean) => void
  editingBenefit: Benefit | null
  setEditingBenefit: (b: Benefit | null) => void
  isSaving: boolean
  onSave: (benefit: Benefit) => void
  history?: BenefitHistoryEntry[]
  historyLoading?: boolean
}

// ---------------------------------------------------------------------------
// Mapping: lucide icon name (from canonical backend) → component
// ---------------------------------------------------------------------------

const VALUE_TYPE_ICON_MAP: Record<string, LucideIcon> = {
  DollarSign,
  Percent,
  Repeat,
  Receipt,
  Shield,
  Info,
}

function valueTypeIcon(iconName: string): LucideIcon {
  return VALUE_TYPE_ICON_MAP[iconName] ?? Info
}

// ---------------------------------------------------------------------------
// Section wrapper — usado pra cada bloco logico do form (DRY)
// ---------------------------------------------------------------------------

function BenefitFormSection({
  title,
  children,
  isFirst = false,
}: {
  title: string
  children: React.ReactNode
  isFirst?: boolean
}) {
  return (
    <div
      className={
        isFirst
          ? "space-y-3"
          : "border-t border-lia-border-subtle pt-4 mt-4 space-y-3"
      }
    >
      <h4
        className={`${textStyles.label} uppercase tracking-wider text-lia-text-tertiary`}
      >
        {title}
      </h4>
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// ChipMultiSelect — chips toggleaveis para arrays
// ---------------------------------------------------------------------------

function ChipMultiSelect({
  options,
  selected,
  onChange,
  ariaLabel,
}: {
  options: readonly { id: string; label: string }[]
  selected: string[]
  onChange: (next: string[]) => void
  ariaLabel: string
}) {
  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id))
    } else {
      if (id === "all") {
        onChange(["all"])
      } else {
        onChange([...selected.filter((s) => s !== "all"), id])
      }
    }
  }
  return (
    <div className="flex flex-wrap gap-1.5 mt-1" role="group" aria-label={ariaLabel}>
      {options.map((opt) => {
        const isSel = selected.includes(opt.id)
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => toggle(opt.id)}
            className={[
              "px-2.5 py-1 rounded-full text-xs border transition-colors motion-reduce:transition-none",
              isSel
                ? "bg-lia-bg-tertiary border-lia-btn-primary-bg text-lia-text-primary"
                : "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover hover:text-lia-text-primary",
            ].join(" ")}
            aria-pressed={isSel}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// SwitchRow — toggle horizontal (substitui grid 2x2 do legado)
// ---------------------------------------------------------------------------

function SwitchRow({
  label,
  description,
  checked,
  onCheckedChange,
}: {
  label: string
  description: string
  checked: boolean
  onCheckedChange: (b: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between p-3 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
      <div className="flex-1 pr-3">
        <Label className={textStyles.label}>{label}</Label>
        <p className="text-xs text-lia-text-tertiary mt-0.5">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function BenefitFormModal({
  open,
  onOpenChange,
  editingBenefit,
  setEditingBenefit,
  isSaving,
  onSave,
  history,
  historyLoading,
}: BenefitFormModalProps) {
  const t = useTranslations("settings.benefits")
  const { departments: companyDepartments, loading: deptsLoading } = useDepartmentsList()
  const {
    categories: BENEFIT_CATEGORIES,
    valueTypes: VALUE_TYPES,
    waitingPeriods: WAITING_PERIODS,
    isLoading: taxonomyLoading,
  } = useBenefitTaxonomy()

  // Normaliza selectedDepartmentIds — `departments` pode ser dict legado, array novo ou null.
  const selectedDepartmentIds: string[] = (() => {
    const v = editingBenefit?.departments
    if (!v) return []
    if (Array.isArray(v)) return v.filter((x): x is string => typeof x === "string")
    if (typeof v === "object") return Object.keys(v as Record<string, unknown>)
    return []
  })()

  const toggleDepartment = (deptId: string) => {
    if (!editingBenefit) return
    const next = selectedDepartmentIds.includes(deptId)
      ? selectedDepartmentIds.filter((id) => id !== deptId)
      : [...selectedDepartmentIds, deptId]
    setEditingBenefit({ ...editingBenefit, departments: next })
  }

  // Validacao condicional por value_type (espelha backend Pydantic)
  const validationError: string | null = (() => {
    if (!editingBenefit) return null
    if (!editingBenefit.name?.trim()) return null
    const vt = (editingBenefit.value_type || "informative").toLowerCase()
    if (
      vt === "monetary" &&
      (editingBenefit.value === undefined || editingBenefit.value === null)
    ) {
      return "Valor monetário é obrigatório quando o tipo é Monetário."
    }
    if (
      vt === "percentage" &&
      (editingBenefit.percentage_value === undefined ||
        editingBenefit.percentage_value === null)
    ) {
      return "Percentual é obrigatório quando o tipo é Percentual."
    }
    if (
      (vt === "match" || vt === "reimbursement" || vt === "coverage") &&
      !editingBenefit.value_details?.trim()
    ) {
      return "Detalhes do valor são obrigatórios para este tipo."
    }
    if (
      vt === "informative" &&
      !editingBenefit.value_details?.trim() &&
      !editingBenefit.description?.trim()
    ) {
      return "Detalhes (ou descrição) são obrigatórios quando o tipo é Informativo."
    }
    return null
  })()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[720px] max-h-[90vh] overflow-y-auto"
        data-testid="benefit-form-modal"
      >
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            {editingBenefit?.id ? t("formTitleEdit") : t("formTitleNew")}
          </DialogTitle>
          <DialogDescription className={textStyles.description}>
            {t("formDescription")}
          </DialogDescription>
        </DialogHeader>

        {editingBenefit && (
          <div className="py-2">
            {/* ===================================================== */}
            {/* SECAO 1 — BASICO                                       */}
            {/* ===================================================== */}
            <BenefitFormSection title="Identificação básica" isFirst>
              <div>
                <Label htmlFor="name" className={textStyles.label}>
                  {t("benefitName")} <span className="text-status-error">*</span>
                </Label>
                <Input
                  id="name"
                  value={editingBenefit.name}
                  onChange={(e) =>
                    setEditingBenefit({ ...editingBenefit, name: e.target.value })
                  }
                  placeholder={t("benefitNamePlaceholder")}
                  className="mt-1 rounded-md text-sm"
                />
              </div>

              <div>
                <Label htmlFor="description" className={textStyles.label}>
                  {t("descriptionLabel")}
                </Label>
                <Textarea
                  id="description"
                  value={editingBenefit.description}
                  onChange={(e) =>
                    setEditingBenefit({ ...editingBenefit, description: e.target.value })
                  }
                  placeholder={t("descriptionPlaceholder")}
                  className="mt-1 rounded-md text-sm"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>
                    {t("categoryLabel")} <span className="text-status-error">*</span>
                  </Label>
                  <Select
                    value={editingBenefit.category}
                    onValueChange={(value) =>
                      setEditingBenefit({ ...editingBenefit, category: value })
                    }
                    disabled={taxonomyLoading}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-sm">
                      <SelectValue
                        placeholder={taxonomyLoading ? "Carregando..." : "Selecione"}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {BENEFIT_CATEGORIES.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id} className="text-sm">
                          <div className="flex items-center gap-2">
                            <span aria-hidden>{cat.icon}</span>
                            <span>{cat.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className={textStyles.label}>Ícone (emoji ou nome)</Label>
                  <Input
                    value={editingBenefit.icon || ""}
                    onChange={(e) =>
                      setEditingBenefit({ ...editingBenefit, icon: e.target.value })
                    }
                    placeholder="🏥 ou stethoscope"
                    className="mt-1 rounded-md text-sm"
                  />
                </div>
              </div>
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 2 — QUEM RECEBE                                  */}
            {/* ===================================================== */}
            <BenefitFormSection title="Quem recebe">
              <div>
                <Label className={textStyles.label}>Senioridade aplicável</Label>
                <ChipMultiSelect
                  options={SENIORITY_OPTIONS}
                  selected={editingBenefit.seniority_levels || []}
                  onChange={(next) =>
                    setEditingBenefit({ ...editingBenefit, seniority_levels: next })
                  }
                  ariaLabel="Senioridade aplicável"
                />
              </div>
              <div>
                <Label className={textStyles.label}>Aplicável a</Label>
                <ChipMultiSelect
                  options={APPLICABLE_TO_OPTIONS}
                  selected={editingBenefit.applicable_to || []}
                  onChange={(next) =>
                    setEditingBenefit({ ...editingBenefit, applicable_to: next })
                  }
                  ariaLabel="Aplicável a"
                />
              </div>
              <div>
                <Label className={textStyles.label}>Tipos de contrato</Label>
                <ChipMultiSelect
                  options={CONTRACT_TYPE_OPTIONS}
                  selected={editingBenefit.contract_types || []}
                  onChange={(next) =>
                    setEditingBenefit({ ...editingBenefit, contract_types: next })
                  }
                  ariaLabel="Tipos de contrato"
                />
              </div>
              <div>
                <Label className={textStyles.label}>
                  Departamentos específicos (opcional)
                </Label>
                <p className="text-xs text-lia-text-secondary mb-2">
                  {selectedDepartmentIds.length === 0
                    ? "Nenhum departamento selecionado (aplica a todos)"
                    : `${selectedDepartmentIds.length} selecionado(s)`}
                </p>
                {deptsLoading ? (
                  <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                    <Loader2
                      size={14}
                      className="animate-spin motion-reduce:animate-none"
                    />
                    Carregando departamentos...
                  </div>
                ) : companyDepartments.length === 0 ? (
                  <p className="text-xs text-lia-text-tertiary italic">
                    Nenhum departamento cadastrado. Cadastre em Configurações →
                    Departamentos primeiro.
                  </p>
                ) : (
                  <div
                    className="flex flex-wrap gap-1.5"
                    role="group"
                    aria-label="Departamentos específicos"
                  >
                    {companyDepartments.map((dept) => {
                      const isSel = selectedDepartmentIds.includes(dept.id)
                      return (
                        <button
                          key={dept.id}
                          type="button"
                          onClick={() => toggleDepartment(dept.id)}
                          aria-pressed={isSel}
                          className={[
                            "px-2.5 py-1 rounded-full text-xs border transition-colors motion-reduce:transition-none",
                            isSel
                              ? "bg-lia-bg-tertiary border-lia-btn-primary-bg text-lia-text-primary"
                              : "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover hover:text-lia-text-primary",
                          ].join(" ")}
                        >
                          {dept.name}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 3 — COMO FUNCIONA (valor + carencia)             */}
            {/* ===================================================== */}
            <BenefitFormSection title="Como funciona">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>
                    {t("valueType")} <span className="text-status-error">*</span>
                  </Label>
                  <Select
                    value={editingBenefit.value_type}
                    onValueChange={(value) =>
                      setEditingBenefit({ ...editingBenefit, value_type: value })
                    }
                    disabled={taxonomyLoading}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-sm">
                      <SelectValue
                        placeholder={taxonomyLoading ? "Carregando..." : "Selecione"}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {VALUE_TYPES.map((type) => {
                        const Icon = valueTypeIcon(type.icon)
                        return (
                          <SelectItem key={type.id} value={type.id} className="text-sm">
                            <div className="flex items-center gap-2">
                              <Icon className="w-3.5 h-3.5" />
                              <span>{type.name}</span>
                            </div>
                          </SelectItem>
                        )
                      })}
                    </SelectContent>
                  </Select>
                </div>

                {editingBenefit.value_type === "monetary" && (
                  <div>
                    <Label className={textStyles.label}>
                      {t("valueCurrency", { currency: CURRENCY_SYMBOL })}
                    </Label>
                    <Input
                      type="number"
                      value={editingBenefit.value ?? ""}
                      onChange={(e) =>
                        setEditingBenefit({
                          ...editingBenefit,
                          value:
                            e.target.value === ""
                              ? undefined
                              : parseFloat(e.target.value),
                        })
                      }
                      placeholder="0,00"
                      className="mt-1 rounded-md text-sm"
                    />
                  </div>
                )}

                {editingBenefit.value_type === "percentage" && (
                  <div>
                    <Label className={textStyles.label}>{t("percentageLabel")}</Label>
                    <Input
                      type="number"
                      value={editingBenefit.percentage_value ?? ""}
                      onChange={(e) =>
                        setEditingBenefit({
                          ...editingBenefit,
                          percentage_value:
                            e.target.value === ""
                              ? undefined
                              : parseFloat(e.target.value),
                        })
                      }
                      placeholder="0"
                      className="mt-1 rounded-md text-sm"
                    />
                  </div>
                )}

                {(editingBenefit.value_type === "informative" ||
                  editingBenefit.value_type === "match" ||
                  editingBenefit.value_type === "reimbursement" ||
                  editingBenefit.value_type === "coverage") && (
                  <div>
                    <Label className={textStyles.label}>
                      {t("valueDetails")}
                      {editingBenefit.value_type !== "informative" && (
                        <span className="text-status-error"> *</span>
                      )}
                    </Label>
                    <Input
                      value={editingBenefit.value_details || ""}
                      onChange={(e) =>
                        setEditingBenefit({
                          ...editingBenefit,
                          value_details: e.target.value,
                        })
                      }
                      placeholder={
                        editingBenefit.value_type === "match"
                          ? "Ex: empresa iguala até 5% do salário"
                          : editingBenefit.value_type === "reimbursement"
                            ? "Ex: até R$ 500/mês mediante nota fiscal"
                            : editingBenefit.value_type === "coverage"
                              ? "Ex: cobertura com 30% de coparticipação"
                              : t("valueDetailsPlaceholder")
                      }
                      className="mt-1 rounded-md text-sm"
                    />
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>{t("waitingPeriod")}</Label>
                  <Select
                    value={String(editingBenefit.waiting_period_days)}
                    onValueChange={(value) =>
                      setEditingBenefit({
                        ...editingBenefit,
                        waiting_period_days: parseInt(value),
                      })
                    }
                    disabled={taxonomyLoading}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-sm">
                      <SelectValue
                        placeholder={taxonomyLoading ? "Carregando..." : "Selecione"}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {WAITING_PERIODS.map((period) => (
                        <SelectItem
                          key={period.id}
                          value={String(period.id)}
                          className="text-sm"
                        >
                          {period.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className={textStyles.label}>Ordem (apresentação)</Label>
                  <Input
                    type="number"
                    value={editingBenefit.order ?? 0}
                    onChange={(e) =>
                      setEditingBenefit({
                        ...editingBenefit,
                        order:
                          e.target.value === ""
                            ? 0
                            : parseInt(e.target.value, 10) || 0,
                      })
                    }
                    placeholder="0"
                    className="mt-1 rounded-md text-sm"
                  />
                </div>
              </div>

              {validationError && (
                <p
                  className="text-xs text-status-warning mt-1"
                  role="alert"
                  data-testid="validation-error"
                >
                  {validationError}
                </p>
              )}

              <div className="space-y-2 pt-1">
                <SwitchRow
                  label={t("activeLabel")}
                  description={t("activeDesc")}
                  checked={editingBenefit.is_active}
                  onCheckedChange={(checked) =>
                    setEditingBenefit({ ...editingBenefit, is_active: checked })
                  }
                />
                <SwitchRow
                  label={t("highlight")}
                  description={t("highlightDesc")}
                  checked={editingBenefit.is_highlighted}
                  onCheckedChange={(checked) =>
                    setEditingBenefit({ ...editingBenefit, is_highlighted: checked })
                  }
                />
                <SwitchRow
                  label={t("mandatoryLabel")}
                  description={t("mandatoryDesc")}
                  checked={editingBenefit.is_mandatory}
                  onCheckedChange={(checked) =>
                    setEditingBenefit({ ...editingBenefit, is_mandatory: checked })
                  }
                />
                <SwitchRow
                  label={t("payrollDeduction")}
                  description={t("payrollDeductionDesc")}
                  checked={editingBenefit.is_discount}
                  onCheckedChange={(checked) =>
                    setEditingBenefit({ ...editingBenefit, is_discount: checked })
                  }
                />
              </div>
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 4 — VIGENCIA & COBERTURA                         */}
            {/* ===================================================== */}
            <BenefitFormSection title="Vigência e cobertura">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>Início do contrato</Label>
                  <Input
                    type="date"
                    value={editingBenefit.valid_from || ""}
                    onChange={(e) =>
                      setEditingBenefit({
                        ...editingBenefit,
                        valid_from: e.target.value || null,
                      })
                    }
                    className="mt-1 rounded-md text-sm"
                  />
                </div>
                <div>
                  <Label className={textStyles.label}>Fim do contrato</Label>
                  <Input
                    type="date"
                    value={editingBenefit.valid_until || ""}
                    onChange={(e) =>
                      setEditingBenefit({
                        ...editingBenefit,
                        valid_until: e.target.value || null,
                      })
                    }
                    className="mt-1 rounded-md text-sm"
                  />
                </div>
              </div>

              <div>
                <Label className={textStyles.label}>Filiais aplicáveis</Label>
                <p className="text-xs text-lia-text-tertiary mb-2">
                  Deixe em branco para aplicar a todas as entidades da empresa
                </p>
                <div className="space-y-2">
                  {(editingBenefit.subsidiaries || []).map((sub, idx) => (
                    <div key={idx} className="flex gap-2 items-center">
                      <Input
                        value={sub.name}
                        onChange={(e) => {
                          const next = [...(editingBenefit.subsidiaries || [])]
                          next[idx] = { ...next[idx], name: e.target.value }
                          setEditingBenefit({ ...editingBenefit, subsidiaries: next })
                        }}
                        placeholder="Nome da filial"
                        className="flex-1 rounded-md text-sm"
                      />
                      <Input
                        value={sub.cnpj || ""}
                        onChange={(e) => {
                          const next = [...(editingBenefit.subsidiaries || [])]
                          next[idx] = { ...next[idx], cnpj: e.target.value || null }
                          setEditingBenefit({ ...editingBenefit, subsidiaries: next })
                        }}
                        placeholder="CNPJ"
                        maxLength={18}
                        className="w-40 rounded-md text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const next = (editingBenefit.subsidiaries || []).filter(
                            (_, i) => i !== idx,
                          )
                          setEditingBenefit({ ...editingBenefit, subsidiaries: next })
                        }}
                        className="text-lia-text-tertiary hover:text-status-error transition-colors"
                        aria-label="Remover filial"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const next = [
                        ...(editingBenefit.subsidiaries || []),
                        { name: "", cnpj: null },
                      ]
                      setEditingBenefit({ ...editingBenefit, subsidiaries: next })
                    }}
                  >
                    <Plus size={14} className="mr-1" /> Adicionar filial
                  </Button>
                </div>
              </div>
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 5 — FORNECEDOR (PII em provider_contact)         */}
            {/* ===================================================== */}
            <BenefitFormSection title="Fornecedor">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>{t("provider")}</Label>
                  <Input
                    value={editingBenefit.provider || ""}
                    onChange={(e) =>
                      setEditingBenefit({ ...editingBenefit, provider: e.target.value })
                    }
                    placeholder={t("providerPlaceholder")}
                    className="mt-1 rounded-md text-sm"
                  />
                </div>
                <div>
                  <Label className={`${textStyles.label} flex items-center gap-1`}>
                    <Lock className="w-3 h-3 text-lia-text-tertiary" />
                    Contato do fornecedor (interno)
                  </Label>
                  <Input
                    value={editingBenefit.provider_contact || ""}
                    onChange={(e) =>
                      setEditingBenefit({
                        ...editingBenefit,
                        provider_contact: e.target.value,
                      })
                    }
                    placeholder="email ou telefone"
                    className="mt-1 rounded-md text-sm"
                  />
                  <p className="text-[10px] text-lia-text-tertiary mt-0.5">
                    Informação interna — não é exibida para candidatos.
                  </p>
                </div>
              </div>
              <div>
                <Label className={textStyles.label}>CNPJ do fornecedor</Label>
                <Input
                  value={editingBenefit.provider_cnpj || ""}
                  onChange={(e) =>
                    setEditingBenefit({
                      ...editingBenefit,
                      provider_cnpj: e.target.value,
                    })
                  }
                  placeholder="XX.XXX.XXX/XXXX-XX"
                  maxLength={18}
                  className="mt-1 rounded-md text-sm"
                />
              </div>
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 6 — HISTORICO (apenas em edicao)                 */}
            {/* ===================================================== */}
            {editingBenefit.id && (
              <BenefitFormSection title="Histórico de alterações">
                {historyLoading ? (
                  <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
                    <Loader2 size={14} className="animate-spin" /> Carregando...
                  </div>
                ) : !history || history.length === 0 ? (
                  <p className="text-xs text-lia-text-tertiary italic">
                    Nenhuma alteração registrada ainda.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {history.map((entry) => (
                      <div
                        key={entry.id}
                        className="flex gap-3 text-xs border-l-2 border-lia-border-subtle pl-3 py-1"
                      >
                        <div className="flex-1">
                          <span className="font-medium text-lia-text-primary">
                            {entry.change_type === "created"
                              ? "Criado"
                              : entry.change_type === "updated"
                                ? "Atualizado"
                                : entry.change_type === "deactivated"
                                  ? "Desativado"
                                  : entry.change_type}
                          </span>
                          {entry.changed_by && (
                            <span className="text-lia-text-secondary ml-1">
                              por {entry.changed_by}
                            </span>
                          )}
                          {entry.change_notes && (
                            <p className="text-lia-text-secondary mt-0.5">
                              {entry.change_notes}
                            </p>
                          )}
                        </div>
                        <span className="text-lia-text-tertiary shrink-0">
                          {new Date(entry.changed_at).toLocaleDateString("pt-BR", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </BenefitFormSection>
            )}
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false)
              setEditingBenefit(null)
            }}
            className="rounded-md text-sm"
          >
            {t("cancel")}
          </Button>
          <Button
            onClick={() => editingBenefit && onSave(editingBenefit)}
            disabled={
              isSaving ||
              !editingBenefit?.name?.trim() ||
              validationError !== null
            }
            className="rounded-md text-sm bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
            title={validationError || undefined}
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                {t("savingBtn")}
              </>
            ) : editingBenefit?.id ? (
              t("saveChanges")
            ) : (
              t("createBenefit")
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
