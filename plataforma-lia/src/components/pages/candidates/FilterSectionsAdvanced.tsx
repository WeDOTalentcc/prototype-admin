"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Chip } from "@/components/ui/chip"
import { Input } from "@/components/ui/input"
import { X, MapPin, Brain, Code, CheckCircle, Bookmark, Calendar } from "lucide-react"
import { badgeStyles, textStyles } from "@/lib/design-tokens"
import { TriStateButtons } from "./filters/TriStateButtons"
import type { TableFilters } from "./types"

export interface FilterSectionsAdvancedProps {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (v: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (v: string) => void
  onClearAll: () => void
}

export function FilterSectionsAdvanced({
  tableFilters,
  setTableFilters,
  newSoftSkillFilter,
  setNewSoftSkillFilter,
  newCertificationFilter,
  setNewCertificationFilter,
  onClearAll,
}: FilterSectionsAdvancedProps) {
  const t = useTranslations('candidates.filters')

  return (
    <div data-testid="filter-sections-advanced">
      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Brain className="w-3 h-3 text-wedo-cyan" />
          {t('softSkills')}
        </h4>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              value={newSoftSkillFilter}
              onChange={(e) => setNewSoftSkillFilter(e.target.value)}
              placeholder={t('softSkillsPlaceholder')}
              className="h-8 text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newSoftSkillFilter.trim()) {
                  if (!tableFilters.softSkills.includes(newSoftSkillFilter.trim())) {
                    setTableFilters((prev) => ({
                      ...prev,
                      softSkills: [...prev.softSkills, newSoftSkillFilter.trim()],
                    }))
                  }
                  setNewSoftSkillFilter("")
                }
              }}
            />
          </div>
          {tableFilters.softSkills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tableFilters.softSkills.map((skill) => (
                <Chip key={skill} variant="neutral" muted className={`${badgeStyles.default} px-2 py-0.5 flex items-center gap-1`}>
                  {skill}
                  <button
                    onClick={() =>
                      setTableFilters((prev) => ({
                        ...prev,
                        softSkills: prev.softSkills.filter((s) => s !== skill),
                      }))
                    }
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </Chip>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Code className="w-3 h-3" />
          {t('certifications')}
        </h4>
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              value={newCertificationFilter}
              onChange={(e) => setNewCertificationFilter(e.target.value)}
              placeholder={t('certificationsPlaceholder')}
              className="h-8 text-xs"
              onKeyDown={(e) => {
                if (e.key === "Enter" && newCertificationFilter.trim()) {
                  if (!tableFilters.certifications.includes(newCertificationFilter.trim())) {
                    setTableFilters((prev) => ({
                      ...prev,
                      certifications: [...prev.certifications, newCertificationFilter.trim()],
                    }))
                  }
                  setNewCertificationFilter("")
                }
              }}
            />
          </div>
          {tableFilters.certifications.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tableFilters.certifications.map((cert) => (
                <Chip key={cert} variant="neutral" muted className={`${badgeStyles.default} px-2 py-0.5 flex items-center gap-1`}>
                  {cert}
                  <button
                    onClick={() =>
                      setTableFilters((prev) => ({
                        ...prev,
                        certifications: prev.certifications.filter((c) => c !== cert),
                      }))
                    }
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </Chip>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <MapPin className="w-3 h-3" />
          {t('availability')}
        </h4>
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('willingToRelocate')}</label>
            <TriStateButtons
              value={tableFilters.willingToRelocate}
              onChange={(v) => setTableFilters((prev) => ({ ...prev, willingToRelocate: v }))}
            />
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('mobility')}</label>
            <TriStateButtons
              value={tableFilters.mobility}
              onChange={(v) => setTableFilters((prev) => ({ ...prev, mobility: v }))}
            />
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('availabilityLabel')}</label>
            <div className="grid grid-cols-2 gap-1.5">
              {[
                { value: "immediate", label: t('immediate') },
                { value: "15_days", label: t('fifteenDays') },
                { value: "30_days", label: t('thirtyDays') },
                { value: "60_days", label: t('sixtyDays') },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() =>
                    setTableFilters((prev) => ({
                      ...prev,
                      availabilityWindow:
                        prev.availabilityWindow === opt.value
                          ? undefined
                          : (opt.value as TableFilters["availabilityWindow"]),
                    }))
                  }
                  className="px-2 py-1.5 text-micro rounded-md transition-colors motion-reduce:transition-none"
                  style={{backgroundColor:
                      tableFilters.availabilityWindow === opt.value ? "var(--lia-btn-primary-bg)" : "var(--lia-bg-secondary)",
                    color: tableFilters.availabilityWindow === opt.value ? "white" : "var(--lia-text-secondary)",
                    border:
                      tableFilters.availabilityWindow === opt.value
                        ? "none"
                        : "1px solid var(--lia-border-subtle)"}}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Bookmark className="w-3 h-3" />
          {t('shortlisted')}
        </h4>
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('inclusionDate')}</label>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="date"
                value={tableFilters.shortlistedDateFrom ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    shortlistedDateFrom: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
              <Input
                type="date"
                value={tableFilters.shortlistedDateTo ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    shortlistedDateTo: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
            </div>
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('originVacancy')}</label>
            <Input
              type="text"
              value={tableFilters.shortlistedVacancyOrigin ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  shortlistedVacancyOrigin: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder={t('originVacancyPlaceholder')}
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <CheckCircle className="w-3 h-3" />
          {t('placement')}
        </h4>
        <div className="space-y-3">
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('placementDate')}</label>
            <div className="grid grid-cols-2 gap-2">
              <Input
                type="date"
                value={tableFilters.placementDateFrom ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    placementDateFrom: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
              <Input
                type="date"
                value={tableFilters.placementDateTo ?? ""}
                onChange={(e) =>
                  setTableFilters((prev) => ({
                    ...prev,
                    placementDateTo: e.target.value || undefined,
                  }))
                }
                className="h-8 text-xs"
              />
            </div>
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('destinationVacancy')}</label>
            <Input
              type="text"
              value={tableFilters.placementVacancyDestination ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  placementVacancyDestination: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder={t('destinationVacancyPlaceholder')}
            />
          </div>
          <div>
            <label className={`${textStyles.label} mb-1.5 block`}>{t('clientCompany')}</label>
            <Input
              type="text"
              value={tableFilters.placementClientCompany ?? ""}
              onChange={(e) =>
                setTableFilters((prev) => ({
                  ...prev,
                  placementClientCompany: e.target.value || undefined,
                }))
              }
              className="h-8 text-xs"
              placeholder={t('clientCompanyPlaceholder')}
            />
          </div>
        </div>
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Bookmark className="w-3 h-3" />
          {t('specificVacancy')}
        </h4>
        <Input
          type="text"
          value={tableFilters.specificVacancyId ?? ""}
          onChange={(e) =>
            setTableFilters((prev) => ({
              ...prev,
              specificVacancyId: e.target.value || undefined,
            }))
          }
          className="h-8 text-xs"
          placeholder={t('specificVacancyPlaceholder')}
        />
      </div>

      <div className="mb-5">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-lia-text-primary mb-3 flex items-center gap-1.5">
          <Calendar className="w-3 h-3" />
          {t('registrationDate')}
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="date"
            value={tableFilters.registrationDateFrom ?? ""}
            onChange={(e) =>
              setTableFilters((prev) => ({
                ...prev,
                registrationDateFrom: e.target.value || undefined,
              }))
            }
            className="h-8 text-xs"
            placeholder={t('from')}
          />
          <Input
            type="date"
            value={tableFilters.registrationDateTo ?? ""}
            onChange={(e) =>
              setTableFilters((prev) => ({
                ...prev,
                registrationDateTo: e.target.value || undefined,
              }))
            }
            className="h-8 text-xs"
            placeholder={t('to')}
          />
        </div>
      </div>

      <div className="pt-4 border-t border-lia-border-subtle space-y-2">
        <button
          className="w-full h-9 text-xs rounded-xl transition-colors motion-reduce:transition-none border border-lia-border-subtle hover:bg-lia-interactive-hover transition-colors cursor-pointer"
          onClick={onClearAll}
        >
          {t('clearAllFilters')}
        </button>
      </div>
    </div>
  )
}
