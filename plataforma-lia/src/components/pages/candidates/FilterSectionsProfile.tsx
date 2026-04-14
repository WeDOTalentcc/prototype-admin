"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { MapPin, DollarSign, Crown, Globe, Bookmark, Building, Layers, CheckCircle, Github } from "lucide-react"
import { CURRENCY_SYMBOL } from "@/lib/pricing"
import { textStyles } from "@/lib/design-tokens"
import { CheckableItem } from "./filters/CheckableItem"
import { TagInput } from "./filters/TagInput"
import type { TableFilters } from "./types"

export interface FilterSectionsProfileProps {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  onToggleFilter: (filterKey: keyof TableFilters, value: string) => void
}

export function FilterSectionsProfile({
  tableFilters,
  setTableFilters,
  onToggleFilter,
}: FilterSectionsProfileProps) {
  const t = useTranslations('candidates.filters')

  return (
    <>
      <div data-testid="filter-sections-profile" className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <MapPin className="w-3 h-3" />
          {t('location')}
        </h4>
        <TagInput
          placeholder={t('locationPlaceholder')}
          tags={tableFilters.locations}
          onAdd={(v) => setTableFilters((prev) => ({ ...prev, locations: [...prev.locations, v] }))}
          onRemove={(v) =>
            setTableFilters((prev) => ({ ...prev, locations: prev.locations.filter((l) => l !== v) }))
          }
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <DollarSign className="w-3 h-3" />
          {t('salaryRange')}
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor="filter-min-salary" className={`${textStyles.label} mb-1 block`}>{t('minSalary', { currency: CURRENCY_SYMBOL })}</label>
            <Input
              id="filter-min-salary"
              type="number"
              min={0}
              value={tableFilters.minSalary ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  minSalary: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="0"
            />
          </div>
          <div>
            <label htmlFor="filter-max-salary" className={`${textStyles.label} mb-1 block`}>{t('maxSalary', { currency: CURRENCY_SYMBOL })}</label>
            <Input
              id="filter-max-salary"
              type="number"
              min={0}
              value={tableFilters.maxSalary ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  maxSalary: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder="50000"
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Crown className="w-3 h-3" />
          {t('profileIndicators')}
        </h4>
        <div className="space-y-2">
          {[
            { key: "isOpenToWork" as const, label: t('openToProposals') },
            { key: "isDecisionMaker" as const, label: t('decisionMaker') },
            { key: "isTopUniversities" as const, label: t('topUniversities') },
            { key: "isStartup" as const, label: t('worksAtStartup') },
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
          <Globe className="w-3 h-3" />
          {t('candidateSource')}
        </h4>
        <div className="space-y-1.5">
          {[
            { value: "Base Global", label: t('globalBase') },
            { value: "Base Local", label: t('localBase') },
            { value: "LinkedIn", label: t('linkedIn') },
            { value: "Indicação", label: t('referral') },
            { value: "Site Carreiras", label: t('careerSite') },
          ].map((source) => {
            const isChecked = tableFilters.sources.includes(source.value)
            return (
              <CheckableItem
                key={source.value}
                label={source.label}
                checked={isChecked}
                onClick={() => onToggleFilter("sources", source.value)}
              />
            )
          })}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Bookmark className="w-3 h-3" />
          {t('tags')}
        </h4>
        <TagInput
          placeholder={t('tagsPlaceholder')}
          tags={tableFilters.tags}
          onAdd={(v) => setTableFilters((prev) => ({ ...prev, tags: [...prev.tags, v] }))}
          onRemove={(v) =>
            setTableFilters((prev) => ({ ...prev, tags: prev.tags.filter((t) => t !== v) }))
          }
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Building className="w-3 h-3" />
          {t('company')}
        </h4>
        <TagInput
          placeholder={t('companyPlaceholder')}
          tags={tableFilters.companies}
          onAdd={(v) => setTableFilters((prev) => ({ ...prev, companies: [...prev.companies, v] }))}
          onRemove={(v) =>
            setTableFilters((prev) => ({ ...prev, companies: prev.companies.filter((c) => c !== v) }))
          }
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Layers className="w-3 h-3" />
          {t('sectorIndustry')}
        </h4>
        <TagInput
          placeholder={t('sectorPlaceholder')}
          tags={tableFilters.industries}
          onAdd={(v) => setTableFilters((prev) => ({ ...prev, industries: [...prev.industries, v] }))}
          onRemove={(v) =>
            setTableFilters((prev) => ({
              ...prev,
              industries: prev.industries.filter((i) => i !== v),
            }))
          }
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Globe className="w-3 h-3" />
          {t('languages')}
        </h4>
        <TagInput
          placeholder={t('languagesPlaceholder')}
          tags={tableFilters.languages}
          onAdd={(v) => setTableFilters((prev) => ({ ...prev, languages: [...prev.languages, v] }))}
          onRemove={(v) =>
            setTableFilters((prev) => ({
              ...prev,
              languages: prev.languages.filter((l) => l !== v),
            }))
          }
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <CheckCircle className="w-3 h-3" />
          {t('status')}
        </h4>
        <div className="space-y-1.5">
          {[
            { value: "novo", label: t('statusNew') },
            { value: "em_analise", label: t('statusInReview') },
            { value: "entrevista", label: t('statusInterview') },
            { value: "aprovado", label: t('statusApproved') },
            { value: "reprovado", label: t('statusRejected') },
            { value: "contratado", label: t('statusHired') },
          ].map((status) => {
            const isChecked = tableFilters.statuses.includes(status.value)
            return (
              <CheckableItem
                key={status.value}
                label={status.label}
                checked={isChecked}
                onClick={() => onToggleFilter("statuses", status.value)}
              />
            )
          })}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Github className="w-3 h-3" />
          {t('onlinePresence')}
        </h4>
        <div className="space-y-2">
          {[
            { key: "hasGithub" as const, label: t('withGithub') },
            { key: "hasPortfolio" as const, label: t('withPortfolio') },
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
    </>
  )
}
