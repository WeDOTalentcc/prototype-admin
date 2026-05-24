"use client"


import { CURRENCY_SYMBOL } from "@/lib/pricing"
import React from "react"
import { useTranslations } from "next-intl"
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DraggableDialogContent,
} from "@/components/ui/dialog"
import {
  DollarSign,
  Percent,
  Info,
  Loader2,
  Stethoscope,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Shield,
  Clock,
  Gift,
  Lock,
  X,
  Plus,
} from "lucide-react"
import {
  APPLICABLE_TO_OPTIONS,
  CONTRACT_TYPE_OPTIONS,
  SENIORITY_OPTIONS,
  type SubsidiaryEntry,
  type BenefitHistoryEntry,
} from "./benefits-types"
import { useDepartmentsList } from "@/hooks/settings/useDepartmentsList"

interface Benefit {
  id?: string
  name: string
  description: string
  category: string
  icon?: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  applicable_to: string[]
  seniority_levels: string[]
  contract_types: string[]
  departments: Record<string, unknown> | string[] | null
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  order: number
  provider?: string
  provider_contact?: string
  subsidiaries?: SubsidiaryEntry[]
  valid_from?: string | null
  valid_until?: string | null
  review_frequency_months?: number | null
  next_review_date?: string | null
  provider_cnpj?: string | null
}

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

/**
 * Multi-select de chips toggleaveis.
 * Substitui o single-Select para arrays (seniority_levels, applicable_to, contract_types).
 */
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
      // 'all' mutually exclusive: marca all -> limpa demais; marca outro -> tira all
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

  // Normaliza selectedDepartmentIds — `departments` pode ser dict legado, array novo ou null.
  // Backend aceita dict | list | None (CompanyBenefitCreate.departments).
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

  const BENEFIT_CATEGORIES = [
    { id: "health", name: t("categoryHealth"), icon: Stethoscope, color: "text-status-error" },
    { id: "food", name: t("categoryFood"), icon: Utensils, color: "text-wedo-orange" },
    { id: "transport", name: t("categoryTransport"), icon: Car, color: "text-lia-text-primary" },
    { id: "education", name: t("categoryEducation"), icon: GraduationCap, color: "text-wedo-purple" },
    { id: "wellness", name: t("categoryHealth"), icon: Stethoscope, color: "text-wedo-cyan" },
    { id: "financial", name: t("categoryFinancial"), icon: Wallet, color: "text-status-success" },
    { id: "quality_life", name: t("categoryQualityLife"), icon: Home, color: "text-lia-text-secondary" },
    { id: "family", name: t("categoryFamily"), icon: Baby, color: "text-wedo-magenta" },
    { id: "flexibility", name: t("categoryQualityLife"), icon: Clock, color: "text-wedo-purple" },
    { id: "security", name: t("categorySecurity"), icon: Shield, color: "text-lia-text-primary" },
    { id: "other", name: t("noDescription"), icon: Gift, color: "text-lia-text-secondary" },
  ]

  const VALUE_TYPES = [
    { id: "monetary", name: t("valueMonetary"), icon: DollarSign, description: t("valueMonetaryDesc", { currency: CURRENCY_SYMBOL }) },
    { id: "percentage", name: t("valuePercentage"), icon: Percent, description: t("valuePercentageDesc") },
    { id: "informative", name: t("valueInformative"), icon: Info, description: t("valueInformativeDesc") },
  ]

  const WAITING_PERIODS = [
    { id: 0, name: t("waitingImmediate") },
    { id: 30, name: t("waiting30") },
    { id: 60, name: t("waiting60") },
    { id: 90, name: t("waiting90") },
    { id: 180, name: t("waiting180") },
    { id: 365, name: t("waiting365") },
  ]

  // Validacao condicional por value_type (espelha backend Pydantic)
  const validationError: string | null = (() => {
    if (!editingBenefit) return null
    if (!editingBenefit.name?.trim()) return null // exigido pelo backend, sinalizado pelo disabled
    const vt = (editingBenefit.value_type || "informative").toLowerCase()
    if (vt === "monetary" && (editingBenefit.value === undefined || editingBenefit.value === null)) {
      return "Valor monetário é obrigatório quando o tipo é Monetário."
    }
    if (vt === "percentage" && (editingBenefit.percentage_value === undefined || editingBenefit.percentage_value === null)) {
      return "Percentual é obrigatório quando o tipo é Percentual."
    }
    if (vt === "informative" && !editingBenefit.value_details?.trim() && !editingBenefit.description?.trim()) {
      return "Detalhes (ou descrição) são obrigatórios quando o tipo é Informativo."
    }
    return null
  })()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DraggableDialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            {editingBenefit?.id ? t("formTitleEdit") : t("formTitleNew")}
          </DialogTitle>
          <DialogDescription className={textStyles.description}>
            {t("formDescription")}
          </DialogDescription>
        </DialogHeader>

        {editingBenefit && (
          <div className="space-y-3 py-1.5">
            {/* ============ Identificacao ============ */}
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <Label htmlFor="name" className={textStyles.label}>{t("benefitName")}</Label>
                <Input
                  id="name"
                  value={editingBenefit.name}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, name: e.target.value })}
                  placeholder={t("benefitNamePlaceholder")}
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                />
              </div>

              <div className="col-span-2">
                <Label htmlFor="description" className={textStyles.label}>{t("descriptionLabel")}</Label>
                <Textarea
                  id="description"
                  value={editingBenefit.description}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, description: e.target.value })}
                  placeholder={t("descriptionPlaceholder")}
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                  rows={2}
                />
              </div>

              <div>
                <Label className={textStyles.label}>{t("categoryLabel")}</Label>
                <Select
                  value={editingBenefit.category}
                  onValueChange={(value) => setEditingBenefit({ ...editingBenefit, category: value })}
                >
                  <SelectTrigger className="mt-1 rounded-md text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BENEFIT_CATEGORIES.map((cat) => {
                      const Icon = cat.icon
                      return (
                        <SelectItem key={cat.id} value={cat.id} className="text-xs">
                          <div className="flex items-center gap-2">
                            <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                            <span>{cat.name}</span>
                          </div>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label className={textStyles.label}>Ícone (emoji ou nome)</Label>
                <Input
                  value={editingBenefit.icon || ""}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, icon: e.target.value })}
                  placeholder="🏥 ou stethoscope"
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                />
              </div>
            </div>

            {/* ============ Valor (3 modos) ============ */}
            <div className="border-t border-lia-border-subtle dark:border-lia-border-strong pt-3 space-y-2">
              <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>Valor</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>{t("valueType")}</Label>
                  <Select
                    value={editingBenefit.value_type}
                    onValueChange={(value) => setEditingBenefit({ ...editingBenefit, value_type: value })}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {VALUE_TYPES.map((type) => {
                        const Icon = type.icon
                        return (
                          <SelectItem key={type.id} value={type.id} className="text-xs">
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
                    <Label className={textStyles.label}>{t("valueCurrency", { currency: CURRENCY_SYMBOL })}</Label>
                    <Input
                      type="number"
                      value={editingBenefit.value ?? ""}
                      onChange={(e) =>
                        setEditingBenefit({
                          ...editingBenefit,
                          value: e.target.value === "" ? undefined : parseFloat(e.target.value),
                        })
                      }
                      placeholder="0,00"
                      className="mt-1 rounded-full text-xs py-1.5 px-2"
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
                          percentage_value: e.target.value === "" ? undefined : parseFloat(e.target.value),
                        })
                      }
                      placeholder="0"
                      className="mt-1 rounded-full text-xs py-1.5 px-2"
                    />
                  </div>
                )}

                {editingBenefit.value_type === "informative" && (
                  <div className="col-span-1">
                    <Label className={textStyles.label}>{t("valueDetails")}</Label>
                    <Input
                      value={editingBenefit.value_details || ""}
                      onChange={(e) => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })}
                      placeholder={t("valueDetailsPlaceholder")}
                      className="mt-1 rounded-full text-xs py-1.5 px-2"
                    />
                  </div>
                )}
              </div>
              {validationError && (
                <p className="text-xs text-amber-600 mt-1" role="alert">
                  {validationError}
                </p>
              )}
            </div>

            {/* ============ Elegibilidade ============ */}
            <div className="border-t border-lia-border-subtle dark:border-lia-border-strong pt-3 space-y-2">
              <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>Elegibilidade</h4>

              <div>
                <Label className={textStyles.label}>Senioridade aplicável</Label>
                <ChipMultiSelect
                  options={SENIORITY_OPTIONS}
                  selected={editingBenefit.seniority_levels || []}
                  onChange={(next) => setEditingBenefit({ ...editingBenefit, seniority_levels: next })}
                  ariaLabel="Senioridade aplicável"
                />
              </div>

              <div>
                <Label className={textStyles.label}>Aplicável a</Label>
                <ChipMultiSelect
                  options={APPLICABLE_TO_OPTIONS}
                  selected={editingBenefit.applicable_to || []}
                  onChange={(next) => setEditingBenefit({ ...editingBenefit, applicable_to: next })}
                  ariaLabel="Aplicável a"
                />
              </div>

              <div>
                <Label className={textStyles.label}>Tipos de contrato</Label>
                <ChipMultiSelect
                  options={CONTRACT_TYPE_OPTIONS}
                  selected={editingBenefit.contract_types || []}
                  onChange={(next) => setEditingBenefit({ ...editingBenefit, contract_types: next })}
                  ariaLabel="Tipos de contrato"
                />
              </div>

              <div>
                <Label className={textStyles.label}>Departamentos específicos (opcional)</Label>
                <p className="text-xs text-lia-text-secondary mb-2">
                  {selectedDepartmentIds.length === 0
                    ? "Nenhum departamento selecionado (aplica a todos)"
                    : `${selectedDepartmentIds.length} selecionado(s)`}
                </p>
                {deptsLoading ? (
                  <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                    <Loader2 size={14} className="animate-spin motion-reduce:animate-none" />
                    Carregando departamentos...
                  </div>
                ) : companyDepartments.length === 0 ? (
                  <p className="text-xs text-lia-text-tertiary italic">
                    Nenhum departamento cadastrado. Cadastre em Configurações → Departamentos primeiro.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-1.5" role="group" aria-label="Departamentos específicos">
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
            </div>

            {/* ============ Operacional ============ */}
            <div className="border-t border-lia-border-subtle dark:border-lia-border-strong pt-3 space-y-2">
              <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>Operacional</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>{t("waitingPeriod")}</Label>
                  <Select
                    value={String(editingBenefit.waiting_period_days)}
                    onValueChange={(value) => setEditingBenefit({ ...editingBenefit, waiting_period_days: parseInt(value) })}
                  >
                    <SelectTrigger className="mt-1 rounded-md text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {WAITING_PERIODS.map((period) => (
                        <SelectItem key={period.id} value={String(period.id)} className="text-xs">
                          {period.name}
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
                        order: e.target.value === "" ? 0 : parseInt(e.target.value, 10) || 0,
                      })
                    }
                    placeholder="0"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center justify-between p-2.5 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>{t("activeLabel")}</Label>
                    <p className={textStyles.caption}>{t("activeDesc")}</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_active}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_active: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>{t("highlight")}</Label>
                    <p className={textStyles.caption}>{t("highlightDesc")}</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_highlighted}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_highlighted: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>{t("mandatoryLabel")}</Label>
                    <p className={textStyles.caption}>{t("mandatoryDesc")}</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_mandatory}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_mandatory: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <div>
                    <Label className={textStyles.label}>{t("payrollDeduction")}</Label>
                    <p className={textStyles.caption}>{t("payrollDeductionDesc")}</p>
                  </div>
                  <Switch
                    checked={editingBenefit.is_discount}
                    onCheckedChange={(checked: boolean) => setEditingBenefit({ ...editingBenefit, is_discount: checked })}
                  />
                </div>
              </div>
            </div>

            {/* ============ Provider (PII em provider_contact) ============ */}
            <div className="border-t border-lia-border-subtle dark:border-lia-border-strong pt-3 space-y-2">
              <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>Fornecedor</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className={textStyles.label}>{t("provider")}</Label>
                  <Input
                    value={editingBenefit.provider || ""}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, provider: e.target.value })}
                    placeholder={t("providerPlaceholder")}
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
                <div>
                  <Label className={`${textStyles.label} flex items-center gap-1`}>
                    <Lock className="w-3 h-3 text-lia-text-tertiary" />
                    Contato do fornecedor (interno)
                  </Label>
                  <Input
                    value={editingBenefit.provider_contact || ""}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, provider_contact: e.target.value })}
                    placeholder="email ou telefone"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                  <p className="text-[10px] text-lia-text-tertiary mt-0.5">
                    Informação interna — não é exibida para candidatos.
                  </p>
                </div>
              </div>
            </div>
            {/* ============ Cobertura e Vigência ============ */}
            <div className="border-t border-neutral-100 pt-5 mt-5">
              <h3 className="text-sm font-semibold text-neutral-700 mb-4">Cobertura e Vigência</h3>

              {/* provider_cnpj */}
              <div className="mb-4">
                <Label className={textStyles.label}>CNPJ do Fornecedor</Label>
                <Input
                  value={editingBenefit.provider_cnpj || ""}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, provider_cnpj: e.target.value })}
                  placeholder="XX.XXX.XXX/XXXX-XX"
                  maxLength={18}
                />
              </div>

              {/* Datas de vigência */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <Label className={textStyles.label}>Início do contrato</Label>
                  <Input
                    type="date"
                    value={editingBenefit.valid_from || ""}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, valid_from: e.target.value || null })}
                  />
                </div>
                <div>
                  <Label className={textStyles.label}>Fim do contrato</Label>
                  <Input
                    type="date"
                    value={editingBenefit.valid_until || ""}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, valid_until: e.target.value || null })}
                  />
                </div>
              </div>

              {/* Subsidiárias */}
              <div>
                <Label className={textStyles.label}>Filiais aplicáveis</Label>
                <p className="text-xs text-neutral-500 mb-2">Deixe em branco para aplicar a todas as entidades da empresa</p>
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
                        className="flex-1"
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
                        className="w-40"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const next = (editingBenefit.subsidiaries || []).filter((_, i) => i !== idx)
                          setEditingBenefit({ ...editingBenefit, subsidiaries: next })
                        }}
                        className="text-neutral-400 hover:text-red-500 transition-colors"
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
                      const next = [...(editingBenefit.subsidiaries || []), { name: "", cnpj: null }]
                      setEditingBenefit({ ...editingBenefit, subsidiaries: next })
                    }}
                  >
                    <Plus size={14} className="mr-1" /> Adicionar filial
                  </Button>
                </div>
              </div>
            </div>

            {/* ============ Histórico de Alterações ============ */}
            {editingBenefit.id && (
              <div className="border-t border-neutral-100 pt-5 mt-5">
                <h3 className="text-sm font-semibold text-neutral-700 mb-3">Histórico de Alterações</h3>
                {historyLoading ? (
                  <div className="flex items-center gap-2 text-xs text-neutral-500">
                    <Loader2 size={14} className="animate-spin" /> Carregando...
                  </div>
                ) : !history || history.length === 0 ? (
                  <p className="text-xs text-neutral-400 italic">Nenhuma alteração registrada ainda.</p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {history.map((entry) => (
                      <div key={entry.id} className="flex gap-3 text-xs border-l-2 border-neutral-200 pl-3 py-1">
                        <div className="flex-1">
                          <span className="font-medium text-neutral-700">
                            {entry.change_type === "created" ? "Criado" :
                             entry.change_type === "updated" ? "Atualizado" :
                             entry.change_type === "deactivated" ? "Desativado" : entry.change_type}
                          </span>
                          {entry.changed_by && (
                            <span className="text-neutral-500 ml-1">por {entry.changed_by}</span>
                          )}
                          {entry.change_notes && (
                            <p className="text-neutral-500 mt-0.5">{entry.change_notes}</p>
                          )}
                        </div>
                        <span className="text-neutral-400 shrink-0">
                          {new Date(entry.changed_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
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
            className="rounded-md text-xs"
          >
            {t("cancel")}
          </Button>
          <Button
            onClick={() => editingBenefit && onSave(editingBenefit)}
            disabled={isSaving || !editingBenefit?.name?.trim() || validationError !== null}
            className="rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
            title={validationError || undefined}
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                {t("savingBtn")}
              </>
            ) : (
              editingBenefit?.id ? t("saveChanges") : t("createBenefit")
            )}
          </Button>
        </DialogFooter>
      </DraggableDialogContent>
    </Dialog>
  )
}
