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
} from "lucide-react"

interface Benefit {
  id?: string
  name: string
  description: string
  category: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
}

interface BenefitFormModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  editingBenefit: Benefit | null
  setEditingBenefit: (b: Benefit | null) => void
  isSaving: boolean
  onSave: (benefit: Benefit) => void
}

export function BenefitFormModal({
  open,
  onOpenChange,
  editingBenefit,
  setEditingBenefit,
  isSaving,
  onSave,
}: BenefitFormModalProps) {
  const t = useTranslations("settings.benefits")

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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DraggableDialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
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
                <Label className={textStyles.label}>{t("provider")}</Label>
                <Input
                  value={editingBenefit.provider || ''}
                  onChange={(e) => setEditingBenefit({ ...editingBenefit, provider: e.target.value })}
                  placeholder={t("providerPlaceholder")}
                  className="mt-1 rounded-full text-xs py-1.5 px-2"
                />
              </div>

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

              {editingBenefit.value_type === 'monetary' && (
                <div>
                  <Label className={textStyles.label}>{t("valueCurrency", { currency: CURRENCY_SYMBOL })}</Label>
                  <Input
                    type="number"
                    value={editingBenefit.value || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, value: parseFloat(e.target.value) || undefined })}
                    placeholder="0,00"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              )}

              {editingBenefit.value_type === 'percentage' && (
                <div>
                  <Label className={textStyles.label}>{t("percentageLabel")}</Label>
                  <Input
                    type="number"
                    value={editingBenefit.percentage_value || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, percentage_value: parseFloat(e.target.value) || undefined })}
                    placeholder="0"
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              )}

              {editingBenefit.value_type === 'informative' && (
                <div className="col-span-2">
                  <Label className={textStyles.label}>{t("valueDetails")}</Label>
                  <Input
                    value={editingBenefit.value_details || ''}
                    onChange={(e) => setEditingBenefit({ ...editingBenefit, value_details: e.target.value })}
                    placeholder={t("valueDetailsPlaceholder")}
                    className="mt-1 rounded-full text-xs py-1.5 px-2"
                  />
                </div>
              )}

              <div>
                <Label className={textStyles.label}>{t("eligibility")}</Label>
                <Select
                  value={editingBenefit.seniority_levels[0] || 'all'}
                  onValueChange={(value) => setEditingBenefit({ ...editingBenefit, seniority_levels: [value] })}
                >
                  <SelectTrigger className="mt-1 rounded-md text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SENIORITY_LEVELS.map((level) => (
                      <SelectItem key={level.id} value={level.id} className="text-xs">
                        {level.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

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
            </div>

            <div className="border-t border-lia-border-subtle dark:border-lia-border-strong pt-3 space-y-2">
              <h4 className={`${textStyles.labelSmall} uppercase tracking-wider`}>
                {t("settings")}
              </h4>
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
            disabled={isSaving || !editingBenefit?.name}
            className="rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
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
