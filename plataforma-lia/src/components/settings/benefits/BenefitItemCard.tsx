"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import React from"react"
import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Switch } from"@/components/ui/switch"
import {
  DollarSign,
  Star,
  Users,
  Clock,
  Pencil,
  Trash2,
} from"lucide-react"
import { textStyles } from"@/lib/design-tokens"
import type { BenefitTabRecord } from "./benefits-types"

// Re-export local alias para compatibilidade com codigo antigo. Schema-alvo:
// 22 campos do contrato Rails (ats-api-copia/db/migrate/20250715000005_create_benefits.rb).
type Benefit = BenefitTabRecord

interface BenefitItemCardProps {
  benefit: Benefit
  isEditingBenefits: boolean
  onToggleStatus: (benefit: Benefit) => void
  onEdit: (benefit: Benefit) => void
  onDelete: (benefitId: string) => void
  /** 'vacancy' reflete o catalogo dentro da vaga: toggle = vincular/desvincular. */
  mode?: "catalog" | "vacancy"
  isLinked?: boolean
}

export const BenefitItemCard = React.memo(function BenefitItemCard({
  benefit,
  isEditingBenefits,
  onToggleStatus,
  onEdit,
  onDelete,
  mode = "catalog",
  isLinked = false,
}: BenefitItemCardProps) {
  const t = useTranslations("settings.benefits")

  const SENIORITY_LEVELS = [
    { id: "all", name: t("seniorityAll") },
    { id: "junior", name: t("seniorityJunior") },
    { id: "pleno", name: t("seniorityPleno") },
    { id: "senior", name: t("senioritySenior") },
    { id: "coordinator", name: t("seniorityCoordinator") },
    { id: "manager", name: t("seniorityManager") },
    { id: "director", name: t("seniorityDirector") },
    { id: "c-level", name: t("seniorityCLevel") },
  ]

  const WAITING_PERIODS = [
    { id: 0, name: t("waitingImmediate") },
    { id: 30, name: t("waiting30") },
    { id: 60, name: t("waiting60") },
    { id: 90, name: t("waiting90") },
    { id: 180, name: t("waiting180") },
    { id: 365, name: t("waiting365") },
  ]

  const formatBenefitValue = (b: Benefit) => {
    if (b.value_type ==="monetary" && b.value) {
      const prefix = b.is_discount ? `${t("discount")}: ` :""
      return prefix + CURRENCY_SYMBOL +"" +  b.value.toLocaleString(undefined, { minimumFractionDigits: 2 })
    }
    if (b.value_type ==="percentage" && b.percentage_value) {
      return b.percentage_value +"%"
    }
    if (b.value_type ==="informative") {
      return b.value_details || t("informative")
    }
    return"-"
  }

  const getSeniorityLabel = (levels: string[]) => {
    if (!levels || levels.length === 0 || levels.includes("all")) {
      return t("allLevels")
    }
    if (levels.length === 1) {
      return SENIORITY_LEVELS.find((l) => l.id === levels[0])?.name || levels[0]
    }
    return `${levels.length} ${t("levels")}`
  }

  const getWaitingPeriodLabel = (days: number) => {
    const period = WAITING_PERIODS.find((p) => p.id === days)
    return period ? period.name : `${days} ${t("waiting30").replace(/^\d+\s*/, "").trim() || "days"}`
  }

  const isVacancy = mode === "vacancy"
  const toggleChecked = isVacancy ? !!isLinked : benefit.is_active
  const toggleEditable = isEditingBenefits
  const suggested = isVacancy && !isLinked && !!(benefit as { matches_vaga?: boolean }).matches_vaga
  const activeClass = (!isVacancy && !benefit.is_active) ? " opacity-60" : ""
  const suggestedClass = suggested ? " bg-lia-btn-primary-bg/5" : ""

  return (
    <div
      className={"p-3 flex items-center justify-between hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none" + activeClass + suggestedClass}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className={textStyles.subtitle +" truncate"}>
            {benefit.name}
          </h4>
          {benefit.is_highlighted && (
            <Star className="w-3.5 h-3.5 text-status-warning fill-current" />
          )}
          {suggested && <Chip variant="neutral" className="text-micro">Sugerido</Chip>}
          {benefit.is_mandatory && (
            <Chip variant="neutral" muted className="text-micro">{t("mandatory")}</Chip>
          )}
          {benefit.is_discount && (
            <Chip variant="danger" className="text-micro">
              {t("discount")}
            </Chip>
          )}
        </div>
        <p className={textStyles.description +" truncate mb-1.5"}>
          {benefit.description || t("noDescription")}
        </p>
        <div className="flex items-center gap-3 text-xs text-lia-text-secondary">
          <span className="flex items-center gap-1">
            <DollarSign className="w-3.5 h-3.5" />
            {formatBenefitValue(benefit)}
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            {getSeniorityLabel(benefit.seniority_levels)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {getWaitingPeriodLabel(benefit.waiting_period_days)}
          </span>
          {benefit.provider && (
            <span className="text-lia-text-secondary">{benefit.provider}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3 ml-3">
        <Switch
          checked={toggleChecked}
          onCheckedChange={() => onToggleStatus(benefit)}
          disabled={!toggleEditable}
          className={!toggleEditable ?"opacity-60" :""}
        />
        {toggleEditable && (
          <>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onEdit(benefit)}
              aria-label="Editar"
            >
              <Pencil className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
            {!isVacancy && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20 dark:hover:text-status-error"
              onClick={() => benefit.id && onDelete(benefit.id)}
              aria-label="Excluir"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
            )}
          </>
        )}
      </div>
    </div>
  )
})
