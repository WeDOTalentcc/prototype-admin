"use client"

import React from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import { ALL_DATA_FIELDS, FIELD_CATEGORY_LABELS } from "./StageCardHelpers"
import type { RecruitmentStage, StageDataField } from "./recruitment-journey.types"

interface DataFieldsPanelProps {
  stage: RecruitmentStage
  isEditMode: boolean
  onUpdate: (id: string, updates: Partial<RecruitmentStage>) => void
}

export function DataFieldsPanel({ stage, isEditMode, onUpdate }: DataFieldsPanelProps) {
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
      <button
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-1.5 text-xs text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none w-full"
        aria-expanded={expanded}
        type="button"
      >
        {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <span className="font-medium">Dados a coletar</span>
        <span className="text-lia-text-tertiary">({enabledCount} campo{enabledCount !== 1 ? 's' : ''})</span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-3">
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
                          className="h-3.5 w-3.5 rounded-md border-lia-border-default text-lia-text-primary cursor-pointer"
                          aria-label={`Ativar campo ${catalog.displayName}`}
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
                              className="h-3 w-3 rounded-md border-lia-border-default text-lia-text-primary cursor-pointer"
                            />
                            <span className="text-micro text-lia-text-secondary">Obrigatório</span>
                          </label>
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={field?.auto_collect ?? false}
                              onChange={() => toggleAutoCollect(catalog.id)}
                              className="h-3 w-3 rounded-md border-lia-border-default text-lia-text-primary cursor-pointer"
                            />
                            <span className="text-micro text-lia-text-secondary">LIA coleta</span>
                          </label>
                        </div>
                      )}

                      {active && !isEditMode && (
                        <div className="flex items-center gap-1.5">
                          {field?.required && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-status-error/10 text-status-error text-micro">
                              Obrigatório
                            </span>
                          )}
                          {field?.auto_collect && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-wedo-cyan/10 text-wedo-cyan text-micro">
                              LIA coleta
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
            Marque "LIA coleta" para que a assistente solicite o dado durante a conversa nesta etapa.
          </p>
        </div>
      )}
    </div>
  )
}
