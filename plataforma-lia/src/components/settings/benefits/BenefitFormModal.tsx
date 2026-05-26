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
 * Refactor 2026-05-26:
 * - Seções maiores extraídas em sub-componentes (<280 LOC cada):
 *   BenefitFormSectionQuemRecebe, BenefitFormSectionComoFunciona, BenefitFormSectionVigencia
 * - Modal principal: 929 → ~370 LOC
 *
 * Aplica:
 * - canonical-fix: taxonomia 100% via hook canonical (single source of truth)
 * - production-quality (frontend): tokens DS, Rules of Hooks compliant
 * - design: hierarquia visual + agrupamento mental do recrutador
 */

import React from "react"
import { useTranslations } from "next-intl"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
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
import { Loader2, Lock } from "lucide-react"
import {
  type BenefitHistoryEntry,
  type BenefitTabRecord,
} from "./benefits-types"
import { useDepartmentsList } from "@/hooks/settings/useDepartmentsList"
import { useBenefitTaxonomy } from "@/hooks/settings/useBenefitTaxonomy"
import { BenefitFormSectionQuemRecebe } from "./BenefitFormSectionQuemRecebe"
import { BenefitFormSectionComoFunciona } from "./BenefitFormSectionComoFunciona"
import { BenefitFormSectionVigencia } from "./BenefitFormSectionVigencia"

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
        className={textStyles.subtitle}
      >
        {title}
      </h4>
      {children}
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
              <BenefitFormSectionQuemRecebe
                benefit={editingBenefit}
                onChange={setEditingBenefit}
                departments={companyDepartments}
                deptsLoading={deptsLoading}
              />
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 3 — COMO FUNCIONA (valor + carencia)             */}
            {/* ===================================================== */}
            <BenefitFormSection title="Como funciona">
              <BenefitFormSectionComoFunciona
                benefit={editingBenefit}
                onChange={setEditingBenefit}
                valueTypes={VALUE_TYPES}
                waitingPeriods={WAITING_PERIODS}
                taxonomyLoading={taxonomyLoading}
                validationError={validationError}
                t={t}
              />
            </BenefitFormSection>

            {/* ===================================================== */}
            {/* SECAO 4 — VIGENCIA & COBERTURA                         */}
            {/* ===================================================== */}
            <BenefitFormSection title="Vigência e cobertura">
              <BenefitFormSectionVigencia
                benefit={editingBenefit}
                onChange={setEditingBenefit}
              />
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
                  <Label className={textStyles.label}>
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
