"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { ArrowUpDown, Zap, Star, Briefcase, Crown, MapPin, FileText } from "lucide-react"
import { CheckableItem } from "./filters/CheckableItem"
import type { TableFilters } from "./types"

export interface FilterSectionsBasicProps {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  searchSortBy: string
  onSortChange: (value: string) => void
  onToggleFilter: (filterKey: keyof TableFilters, value: string) => void
}

export function FilterSectionsBasic({
  tableFilters,
  setTableFilters,
  searchSortBy,
  onSortChange,
  onToggleFilter,
}: FilterSectionsBasicProps) {
  const t = useTranslations('candidates.filters')

  return (
    <div data-testid="filter-sections-basic">
      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <ArrowUpDown className="w-3 h-3" />
          {t('sorting')}
        </h4>
        <RadioGroup value={searchSortBy} onValueChange={onSortChange} className="space-y-1.5">
          {[
            { value: "relevance", label: t('relevance') },
            { value: "score_desc", label: t('highestScore') },
            { value: "score_asc", label: t('lowestScore') },
            { value: "name_asc", label: t('nameAZ') },
            { value: "name_desc", label: t('nameZA') },
            { value: "experience_desc", label: t('mostExperience') },
          ].map((option) => (
            <label
              key={option.value}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-md border cursor-pointer transition-colors text-xs",
                searchSortBy === option.value
                  ? "border-lia-btn-primary-bg bg-lia-bg-secondary font-medium text-lia-text-primary"
                  : "border-lia-border-subtle hover:border-lia-border-default text-lia-text-secondary"
              )}
            >
              <RadioGroupItem
                value={option.value}
                className="w-3.5 h-3.5 border-lia-border-medium data-[state=checked]:border-lia-btn-primary-bg data-[state=checked]:text-lia-text-primary"
              />
              {option.label}
            </label>
          ))}
        </RadioGroup>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Zap className="w-3 h-3" />
          {t('quickFilters')}
        </h4>
        <div className="space-y-2">
          {[
            { key: "hasEmail" as const, label: t('emailOnly') },
            { key: "hasPhone" as const, label: t('phoneOnly') },
            { key: "hasLinkedin" as const, label: t('linkedinOnly') },
            { key: "remoteOnly" as const, label: t('remoteOnly') },
          ].map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between py-1.5">
              <span className="text-xs text-lia-text-primary">{label}</span>
              <Switch
                checked={tableFilters[key] as boolean}
                onCheckedChange={(checked: boolean) =>
                  setTableFilters((prev) => ({ ...prev, [key]: checked }))
                }
                className="scale-75"
              />
            </div>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Briefcase className="w-3 h-3" />
          {t('experience')}
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor="filter-min-experience" className="text-xs text-lia-text-primary mb-1 block">{t('minYears')}</label>
            <Input
              id="filter-min-experience"
              type="number"
              min={0}
              max={30}
              value={tableFilters.minExperience ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  minExperience: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="0"
            />
          </div>
          <div>
            <label htmlFor="filter-max-experience" className="text-xs text-lia-text-primary mb-1 block">{t('maxYears')}</label>
            <Input
              id="filter-max-experience"
              type="number"
              min={0}
              max={30}
              value={tableFilters.maxExperience ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  maxExperience: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="30"
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Star className="w-3 h-3" />
          {t('scoreLia')}
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor="filter-min-score" className="text-xs text-lia-text-primary mb-1 block">{t('minScore')}</label>
            <Input
              id="filter-min-score"
              type="number"
              min={0}
              max={100}
              value={tableFilters.minScore ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  minScore: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="0"
            />
          </div>
          <div>
            <label htmlFor="filter-max-score" className="text-xs text-lia-text-primary mb-1 block">{t('maxScore')}</label>
            <Input
              id="filter-max-score"
              type="number"
              min={0}
              max={100}
              value={tableFilters.maxScore ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  maxScore: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="100"
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Crown className="w-3 h-3" />
          {t('seniority')}
        </h4>
        <div className="space-y-1.5">
          {[
            { value: "junior", label: t('junior') },
            { value: "pleno", label: t('midLevel') },
            { value: "senior", label: t('senior') },
            { value: "especialista", label: t('specialist') },
            { value: "lideranca", label: t('leadership') },
          ].map((level) => {
            const isChecked = tableFilters.seniorityLevels.includes(level.value)
            return (
              <CheckableItem
                key={level.value}
                label={level.label}
                checked={isChecked}
                onClick={() => onToggleFilter("seniorityLevels", level.value)}
              />
            )
          })}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <MapPin className="w-3 h-3" />
          {t('workModel')}
        </h4>
        <div className="space-y-1.5">
          {[
            { value: "remote", label: t('remote') },
            { value: "hybrid", label: t('hybrid') },
            { value: "onsite", label: t('onsite') },
          ].map((model) => {
            const isChecked = tableFilters.workModels.includes(model.value)
            return (
              <CheckableItem
                key={model.value}
                label={model.label}
                checked={isChecked}
                onClick={() => onToggleFilter("workModels", model.value)}
              />
            )
          })}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <FileText className="w-3 h-3" />
          {t('contractType')}
        </h4>
        <div className="space-y-1.5">
          {["CLT", "PJ", "Freelancer"].map((contract) => {
            const isChecked = tableFilters.contractTypes.includes(contract)
            return (
              <CheckableItem
                key={contract}
                label={contract}
                checked={isChecked}
                onClick={() => onToggleFilter("contractTypes", contract)}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}
