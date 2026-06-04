"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { ChevronDown, ChevronRight } from "lucide-react"
import { InteractiveSurface } from "@/components/ui/interactive-surface"
import { ALL_DATA_FIELDS, FIELD_CATEGORY_LABELS } from "./StageCardHelpers"
import type { RecruitmentStage, StageDataField } from "./recruitment-journey.types"

interface DataFieldsPanelProps {
  stage: RecruitmentStage
  isEditMode: boolean
  onUpdate: (id: string, updates: Partial<RecruitmentStage>) => void
}

export function DataFieldsPanel({ stage, isEditMode, onUpdate }: DataFieldsPanelProps) {
  const t = useTranslations("settings.dataFields")
  const [expanded, setExpanded] = React.useState(false)

  const dataFields = stage.data_fields || []
  const enabledCount = dataFields.length

  function isEnabled(fieldId: string) {
    return dataFields.some(f => f.id === fieldId)
  }

  function getField(fieldId: string): StageDataField | undefined {
    return dataFields.find(f => f.id === fieldId)
  }

  function toggleField(catalog: StageDataField) {
    if (isEnabled(catalog.id)) {
      onUpdate(stage.id, { data_fields: dataFields.filter(f => f.id !== catalog.id) })
    } else {
      onUpdate(stage.id, { data_fields: [...dataFields, { ...catalog }] })
    }
  }

  function toggleRequired(fieldId: string) {
    onUpdate(stage.id, {
      data_fields: dataFields.map(f => f.id === fieldId ? { ...f, required: !f.required } : f),
    })
  }

  function toggleAutoCollect(fieldId: string) {
    onUpdate(stage.id, {
      data_fields: dataFields.map(f => f.id === fieldId ? { ...f, auto_collect: !f.auto_collect } : f),
    })
  }

  const byCategory = ALL_DATA_FIELDS.reduce<Record<string, StageDataField[]>>((acc, f) => {
    acc[f.category] = acc[f.category] || []
    acc[f.category].push(f)
    return acc
  }, {})

  return (
    <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle mt-3 pt-2">
      <InteractiveSurface
        variant="accordion"
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-1.5 justify-start text-xs text-lia-text-secondary hover:text-lia-text-primary !bg-transparent hover:!bg-transparent"
        aria-expanded={expanded}
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <span className="font-medium">{t("collapseLabel")}</span>
        <span className="text-lia-text-tertiary">({t("fieldCount", { count: enabledCount })})</span>
      </InteractiveSurface>

      {expanded && (
        <div className="mt-2 space-y-3">
          {/* P0-W1-12: Ghost-setting banner — controls are not yet persisted */}
          <div className="rounded-lg border border-status-warning-border-light bg-status-warning-bg px-3 py-2.5 mb-2">
            <div className="flex items-start gap-2">
              <span className="inline-flex items-center rounded-full bg-status-warning/15 px-2 py-0.5 text-micro font-semibold text-status-warning flex-shrink-0 mt-0.5">
                {t("comingSoon")}
              </span>
              <p className="text-xs text-status-warning">
                {t("comingSoonText")}
              </p>
            </div>
          </div>
          {Object.entries(byCategory).map(([category, fields]) => (
            <div key={category}>
              <p className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wide mb-1.5 px-1">
                {FIELD_CATEGORY_LABELS[category] || category}
              </p>
              <div className="space-y-1">
                {fields.map(catalog => {
                  const active = isEnabled(catalog.id)
                  const field = getField(catalog.id)
                  return (
                    <div
                      key={catalog.id}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-md border transition-colors motion-reduce:transition-none ${
                        active
                          ? 'bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-default'
                          : 'bg-lia-bg-secondary dark:bg-lia-bg-primary/50 border-lia-border-subtle dark:border-lia-border-subtle'
                      }`}
                    >
                      {isEditMode ? (
                        <input
                          type="checkbox"
                          checked={active}
                          onChange={() => toggleField(catalog)}
                          className="h-3.5 w-3.5 rounded-xl border-lia-border-default text-lia-text-primary cursor-pointer"
                          aria-label={t("enableField", { name: catalog.displayName })}
                        />
                      ) : (
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${active ? 'bg-lia-btn-primary-bg' : 'bg-lia-interactive-active'}`} />
                      )}

                      <span className={`flex-1 text-xs font-medium ${active ? 'text-lia-text-primary' : 'text-lia-text-tertiary'}`}>
                        {catalog.displayName}
                      </span>

                      {active && isEditMode && (
                        <div className="flex items-center gap-3">
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={field?.required ?? false}
                              onChange={() => toggleRequired(catalog.id)}
                              className="h-3 w-3 rounded-xl border-lia-border-default text-lia-text-primary cursor-pointer"
                            />
                            <span className="text-micro text-lia-text-secondary">{t("required")}</span>
                          </label>
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={field?.auto_collect ?? false}
                              onChange={() => toggleAutoCollect(catalog.id)}
                              className="h-3 w-3 rounded-xl border-lia-border-default text-lia-text-primary cursor-pointer"
                            />
                            <span className="text-micro text-lia-text-secondary">{t("liaCollects")}</span>
                          </label>
                        </div>
                      )}

                      {active && !isEditMode && (
                        <div className="flex items-center gap-1.5">
                          {field?.required && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-status-error/10 text-status-error text-micro">
                              {t("required")}
                            </span>
                          )}
                          {field?.auto_collect && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan text-micro">
                              {t("liaCollects")}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
          <p className="text-micro text-lia-text-tertiary px-1 pt-1">
            {t("helpText")}
          </p>
        </div>
      )}
    </div>
  )
}
