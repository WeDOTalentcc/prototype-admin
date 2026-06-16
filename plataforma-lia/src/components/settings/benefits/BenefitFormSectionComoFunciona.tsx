"use client"

import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DollarSign,
  Percent,
  Info,
  Repeat,
  Receipt,
  Shield,
  type LucideIcon,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { type BenefitTabRecord } from "./benefits-types"

// ---------------------------------------------------------------------------
// Icon map (mirrors BenefitFormModal)
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
// SwitchRow (local)
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
// Props
// ---------------------------------------------------------------------------

export interface ValueTypeOption {
  id: string
  name: string
  icon: string
}

export interface WaitingPeriodOption {
  id: number
  label: string
}

export interface BenefitFormSectionComoFuncionaProps {
  benefit: BenefitTabRecord
  onChange: (updated: BenefitTabRecord) => void
  valueTypes: ValueTypeOption[]
  waitingPeriods: WaitingPeriodOption[]
  taxonomyLoading: boolean
  validationError: string | null
  t: (key: string, values?: Record<string, string>) => string
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BenefitFormSectionComoFunciona({
  benefit,
  onChange,
  valueTypes,
  waitingPeriods,
  taxonomyLoading,
  validationError,
  t,
}: BenefitFormSectionComoFuncionaProps) {
  return (
    <>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className={textStyles.label}>
            {t("valueType")} <span className="text-status-error">*</span>
          </Label>
          <Select
            value={benefit.value_type}
            onValueChange={(value) => onChange({ ...benefit, value_type: value })}
            disabled={taxonomyLoading}
          >
            <SelectTrigger className="mt-1 rounded-md text-sm">
              <SelectValue
                placeholder={taxonomyLoading ? "Carregando..." : "Selecione"}
              />
            </SelectTrigger>
            <SelectContent>
              {valueTypes.map((type) => {
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

        {benefit.value_type === "monetary" && (
          <div>
            <Label className={textStyles.label}>
              {t("valueCurrency", { currency: CURRENCY_SYMBOL })}
            </Label>
            <Input
              type="number"
              value={benefit.value ?? ""}
              onChange={(e) =>
                onChange({
                  ...benefit,
                  value:
                    e.target.value === "" ? undefined : parseFloat(e.target.value),
                })
              }
              placeholder="0,00"
              className="mt-1 rounded-md text-sm"
            />
          </div>
        )}

        {benefit.value_type === "percentage" && (
          <div>
            <Label className={textStyles.label}>{t("percentageLabel")}</Label>
            <Input
              type="number"
              value={benefit.percentage_value ?? ""}
              onChange={(e) =>
                onChange({
                  ...benefit,
                  percentage_value:
                    e.target.value === "" ? undefined : parseFloat(e.target.value),
                })
              }
              placeholder="0"
              className="mt-1 rounded-md text-sm"
            />
          </div>
        )}

        {(benefit.value_type === "informative" ||
          benefit.value_type === "match" ||
          benefit.value_type === "reimbursement" ||
          benefit.value_type === "coverage") && (
          <div>
            <Label className={textStyles.label}>
              {t("valueDetails")}
              {benefit.value_type !== "informative" && (
                <span className="text-status-error"> *</span>
              )}
            </Label>
            <Input
              value={benefit.value_details || ""}
              onChange={(e) =>
                onChange({ ...benefit, value_details: e.target.value })
              }
              placeholder={
                benefit.value_type === "match"
                  ? "Ex: empresa iguala até 5% do salário"
                  : benefit.value_type === "reimbursement"
                    ? "Ex: até R$ 500/mês mediante nota fiscal"
                    : benefit.value_type === "coverage"
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
            value={String(benefit.waiting_period_days)}
            onValueChange={(value) =>
              onChange({ ...benefit, waiting_period_days: parseInt(value) })
            }
            disabled={taxonomyLoading}
          >
            <SelectTrigger className="mt-1 rounded-md text-sm">
              <SelectValue
                placeholder={taxonomyLoading ? "Carregando..." : "Selecione"}
              />
            </SelectTrigger>
            <SelectContent>
              {waitingPeriods.map((period) => (
                <SelectItem key={period.id} value={String(period.id)} className="text-sm">
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
            value={benefit.order ?? 0}
            onChange={(e) =>
              onChange({
                ...benefit,
                order: e.target.value === "" ? 0 : parseInt(e.target.value, 10) || 0,
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
          checked={benefit.is_active}
          onCheckedChange={(checked) => onChange({ ...benefit, is_active: checked })}
        />
        <SwitchRow
          label={t("highlight")}
          description={t("highlightDesc")}
          checked={benefit.is_highlighted}
          onCheckedChange={(checked) => onChange({ ...benefit, is_highlighted: checked })}
        />
        <SwitchRow
          label={t("mandatoryLabel")}
          description={t("mandatoryDesc")}
          checked={benefit.is_mandatory}
          onCheckedChange={(checked) => onChange({ ...benefit, is_mandatory: checked })}
        />
        <SwitchRow
          label={t("payrollDeduction")}
          description={t("payrollDeductionDesc")}
          checked={benefit.is_discount}
          onCheckedChange={(checked) => onChange({ ...benefit, is_discount: checked })}
        />
      </div>
    </>
  )
}
