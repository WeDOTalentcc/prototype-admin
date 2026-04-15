"use client"

import React, { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChevronDown, ChevronUp, Pencil, Check, X,
  Building, Heart, Code, Gift, Network, GitBranch,
  Loader2, RefreshCw, AlertCircle, CheckCircle,
} from "lucide-react"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import type { CardField } from "@/hooks/settings/use-company-settings-cards"
import { textStyles } from "@/lib/design-tokens"
import type { LucideIcon } from "lucide-react"

const ICON_MAP: Record<string, LucideIcon> = {
  Building,
  Heart,
  Code,
  Gift,
  Network,
  GitBranch,
}

function formatFieldValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Nao definido"
  if (typeof value === "boolean") return value ? "Sim" : "Nao"
  if (Array.isArray(value)) {
    if (value.length === 0) return "Nenhum"
    return value.join(", ")
  }
  return String(value)
}

function InlineFieldEditor({
  field,
  currentValue,
  onSave,
  onCancel,
  isSaving,
}: {
  field: CardField
  currentValue: unknown
  onSave: (value: unknown) => void
  onCancel: () => void
  isSaving: boolean
}) {
  const [localValue, setLocalValue] = useState(() => {
    if (currentValue === null || currentValue === undefined) return ""
    if (typeof currentValue === "boolean") return currentValue
    if (Array.isArray(currentValue)) return currentValue.join(", ")
    return String(currentValue)
  })

  const handleSave = () => {
    let parsed: unknown = localValue
    if (field.type === "number") {
      parsed = localValue === "" ? null : Number(localValue)
    } else if (field.type === "boolean") {
      parsed = localValue
    } else if (field.type === "list") {
      parsed = typeof localValue === "string"
        ? localValue.split(",").map((s: string) => s.trim()).filter(Boolean)
        : localValue
    }
    onSave(parsed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSave()
    } else if (e.key === "Escape") {
      onCancel()
    }
  }

  if (field.type === "boolean") {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={() => onSave(!currentValue)}
          disabled={isSaving}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors motion-reduce:transition-none ${
            currentValue ? "bg-lia-btn-primary-bg" : "bg-lia-border-default"
          }`}
        >
          <span
            className={`inline-block h-3.5 w-3.5 transform rounded-full bg-lia-bg-primary transition-transform motion-reduce:transition-none ${
              currentValue ? "translate-x-4" : "translate-x-0.5"
            }`}
          />
        </button>
        <button
          onClick={onCancel}
          className="p-0.5 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
        >
          <X className="w-3 h-3 text-lia-text-tertiary" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      <input
        type={field.type === "number" ? "number" : "text"}
        value={String(localValue)}
        onChange={(e) => setLocalValue(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
        disabled={isSaving}
        placeholder={field.type === "list" ? "item1, item2, item3" : ""}
        className="w-40 text-xs font-medium text-lia-text-primary bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-default rounded-md px-1.5 py-0.5 text-right focus:outline-none focus:ring-1 focus:ring-lia-border-medium"
      />
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="p-0.5 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
      >
        {isSaving ? (
          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        ) : (
          <Check className="w-3 h-3 text-status-success" />
        )}
      </button>
      <button
        onClick={onCancel}
        className="p-0.5 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
      >
        <X className="w-3 h-3 text-lia-text-tertiary" />
      </button>
    </div>
  )
}

const STATUS_STYLES = {
  configured: {
    badge: "bg-status-success/10 text-status-success border-status-success/30 dark:bg-status-success/20",
    label: "Configurado",
  },
  partial: {
    badge: "bg-status-warning/10 text-status-warning border-status-warning/30 dark:bg-status-warning/20",
    label: "Parcial",
  },
  pending: {
    badge: "bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle dark:bg-lia-bg-elevated dark:border-lia-border-default",
    label: "Pendente",
  },
}

export function MinhaEmpresaHub() {
  const {
    blocks,
    loading,
    error,
    successMessage,
    overallProgress,
    expandedBlocks,
    recentlyUpdated,
    editingField,
    isSavingField,
    toggleBlock,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll,
  } = useCompanySettingsCards()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        <span className={`ml-2 ${textStyles.body}`}>
          Carregando dados da empresa...
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {(error || successMessage) && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
          error
            ? "bg-status-error/10 text-status-error border border-status-error/30"
            : "bg-status-success/10 text-status-success border border-status-success/30"
        }`}>
          {error ? <AlertCircle className="w-4 h-4 flex-shrink-0" /> : <CheckCircle className="w-4 h-4 flex-shrink-0" />}
          <span>{error || successMessage}</span>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className={textStyles.h3}>Minha Empresa</h2>
            <p className={`${textStyles.description} mt-0.5`}>
              Converse com a LIA no chat lateral para preencher automaticamente. Ou edite diretamente nos cards.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={refreshAll}
              className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              aria-label="Atualizar dados"
            >
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
            </button>
            <span className={`${textStyles.metricSmall} flex-shrink-0`}>
              {overallProgress}% configurado
            </span>
            {overallProgress >= 80 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-success/10 text-status-success border border-status-success/30 flex-shrink-0">
                <CheckCircle className="w-3 h-3 mr-1" />
                Quase completo
              </span>
            )}
          </div>
        </div>
        <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full transition-[width] duration-500 bg-lia-btn-primary-bg"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {blocks.map((block) => {
          const IconComp = ICON_MAP[block.iconName]
          const isExpanded = expandedBlocks.has(block.key)
          const statusStyle = STATUS_STYLES[block.status]

          return (
            <Card
              key={block.key}
              className="bg-lia-bg-primary dark:bg-lia-bg-secondary overflow-hidden rounded-xl"
            >
              <button
                onClick={() => toggleBlock(block.key)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none duration-150"
                aria-expanded={isExpanded}
                aria-label={`${block.title} - ${statusStyle.label}`}
              >
                <div className="flex items-center gap-2">
                  {IconComp && <IconComp className="w-4 h-4 text-lia-text-secondary" />}
                  <span className={textStyles.h3}>{block.title}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium border ${statusStyle.badge}`}
                  >
                    {statusStyle.label}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
                  )}
                </div>
              </button>

              {isExpanded && (
                <CardContent className="px-4 py-3 border-t border-lia-border-subtle">
                  <div className="space-y-1">
                    {block.fields.map((field) => {
                      const isEditing =
                        editingField?.block === block.key &&
                        editingField?.field === field.key
                      const isUpdated = recentlyUpdated.has(field.key)

                      return (
                        <div
                          key={field.key}
                          className={`group flex items-center justify-between gap-2 py-1.5 px-1.5 rounded-md transition-colors motion-reduce:transition-none duration-300 ${
                            isUpdated
                              ? "bg-status-success/10 dark:bg-status-success/10"
                              : "hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50"
                          }`}
                        >
                          <span className={`${textStyles.description} flex-shrink-0 min-w-[120px]`}>
                            {field.label}
                          </span>
                          {isEditing ? (
                            <InlineFieldEditor
                              field={field}
                              currentValue={field.value}
                              onSave={(newValue) => saveField(block.key, field.key, newValue)}
                              onCancel={cancelEditing}
                              isSaving={isSavingField}
                            />
                          ) : (
                            <div className="flex items-center gap-1 min-w-0">
                              <span
                                className={`${textStyles.metricSmall} text-right truncate max-w-[200px] transition-colors motion-reduce:transition-none duration-300 ${
                                  isUpdated ? "text-status-success" : ""
                                }`}
                                title={formatFieldValue(field.value)}
                              >
                                {formatFieldValue(field.value)}
                              </span>
                              {field.editable && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    startEditing(block.key, field.key)
                                  }}
                                  className="opacity-0 group-hover:opacity-100 p-0.5 rounded-md hover:bg-lia-interactive-active dark:hover:bg-lia-border-medium transition-opacity motion-reduce:transition-none"
                                  aria-label={`Editar ${field.label}`}
                                >
                                  <Pencil className="w-3 h-3 text-lia-text-tertiary" />
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
