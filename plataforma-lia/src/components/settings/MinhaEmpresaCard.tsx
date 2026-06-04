"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent } from "@/components/ui/card"
import {
  ChevronDown, ChevronUp, Pencil, Check, X, Loader2,
} from "lucide-react"
import type { CardBlock, CardField } from "@/hooks/settings/use-company-settings-cards"
import { textStyles } from "@/lib/design-tokens"
import type { LucideIcon } from "lucide-react"
import { BenefitsListSection } from "./benefits/BenefitsListSection"
import type { CompanyBenefit } from "@/types/benefits"
import { WorkforceHubContent } from "./WorkforceHubContent"
import { VariableCompCatalogSection } from "@/components/compensation/VariableCompCatalogSection"
import { SalaryBandsSection } from "@/components/compensation/SalaryBandsSection"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { SectionUploadDropZone, type TargetSection } from "./SectionUploadDropZone"
import { LogoUploadField } from "./LogoUploadField"
import { InteractiveSurface } from "@/components/ui/interactive-surface"

interface SectionUploadConfig {
  targetSection: TargetSection
  documentType: "handbook" | "tech_doc" | "org_chart" | "compensation"
  sectionLabelKey: string
  hintKey?: string
}

// Per-block contextual upload configuration. The target_section value is what
// the backend `process_uploaded_document` tool keys on to narrow the
// extraction to a single area of "Minha Empresa". `basic` has no upload —
// it's structured registration data, not a document-derived area.
const BLOCK_UPLOAD: Record<string, SectionUploadConfig | undefined> = {
  basic: undefined,
  culture: { targetSection: "culture", documentType: "handbook", sectionLabelKey: "cultureLabel", hintKey: "cultureHint" },
  tech: { targetSection: "tech_stack", documentType: "tech_doc", sectionLabelKey: "techLabel", hintKey: "techHint" },
  benefits: { targetSection: "benefits", documentType: "handbook", sectionLabelKey: "benefitsLabel", hintKey: "benefitsHint" },
  policy: { targetSection: "policy", documentType: "handbook", sectionLabelKey: "policyLabel", hintKey: "policyHint" },
  workforce: { targetSection: "workforce", documentType: "org_chart", sectionLabelKey: "workforceLabel", hintKey: "workforceHint" },
  documents: { targetSection: "compensation", documentType: "compensation", sectionLabelKey: "documentsLabel", hintKey: "documentsHint" },
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
  const t = useTranslations("settings.minhaEmpresaCard")
  const [localValue, setLocalValue] = useState(() => {
    if (currentValue === null || currentValue === undefined) return ""
    if (typeof currentValue === "boolean") return currentValue
    if (Array.isArray(currentValue)) return currentValue.join(", ")
    return String(currentValue)
  })
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleSave = () => {
    setValidationError(null)
    let parsed: unknown = localValue
    if (field.type === "number") {
      if (localValue === "" || localValue === null) {
        parsed = null
      } else {
        const n = Number(localValue)
        if (!Number.isFinite(n)) {
          setValidationError(t("invalidNumber"))
          return
        }
        parsed = n
      }
    } else if (field.type === "boolean") {
      parsed = localValue
    } else if (field.type === "list") {
      parsed = typeof localValue === "string"
        ? localValue.split(",").map((s: string) => s.trim()).filter(Boolean)
        : localValue
    } else if (field.type === "time-range") {
      const raw = String(localValue).trim()
      if (raw === "") {
        parsed = ""
      } else if (!/^\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}$/.test(raw)) {
        setValidationError(t("timeRangeFormat"))
        return
      } else {
        parsed = raw
      }
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
          className="p-0.5 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
        >
          <X className="w-3 h-3 text-lia-text-tertiary" />
        </button>
      </div>
    )
  }

  const placeholder = field.type === "list"
    ? "item1, item2, item3"
    : field.type === "time-range"
    ? "09:00 - 18:00"
    : ""

  return (
    <div className="flex flex-col items-end gap-0.5">
    <div className="flex items-center gap-1">
      <input
        type={field.type === "number" ? "number" : "text"}
        value={String(localValue)}
        onChange={(e) => { setLocalValue(e.target.value); if (validationError) setValidationError(null) }}
        onKeyDown={handleKeyDown}
        autoFocus
        disabled={isSaving}
        placeholder={placeholder}
        aria-invalid={validationError ? true : undefined}
        className={`w-40 text-xs font-medium text-lia-text-primary bg-lia-bg-primary dark:bg-lia-bg-secondary border rounded-md px-1.5 py-0.5 text-right focus:outline-none focus:ring-1 focus:ring-lia-border-medium ${validationError ? "border-status-error" : "border-lia-border-default"}`}
      />
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="p-0.5 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
      >
        {isSaving ? (
          <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
        ) : (
          <Check className="w-3 h-3 text-status-success" />
        )}
      </button>
      <button
        onClick={onCancel}
        className="p-0.5 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
      >
        <X className="w-3 h-3 text-lia-text-tertiary" />
      </button>
    </div>
      {validationError && (
        <span className="text-micro text-status-error">{validationError}</span>
      )}
    </div>
  )
}

interface MinhaEmpresaCardProps {
  block: CardBlock
  IconComp: LucideIcon | undefined
  isExpanded: boolean
  recentlyUpdated: Set<string>
  editingField: { block: string; field: string } | null
  isSavingField: boolean
  benefits?: Array<Partial<CompanyBenefit> & { id?: string; name?: string }>
  companyId?: string | null
  /**
   * Sprint B.7 (2026-05-26): quando true, esconde edit buttons e mostra hint.
   * Wired via useSettingsEditMode("minha-empresa") no MinhaEmpresaHub.
   * Default false = backwards-compatible com tests/callers existentes.
   */
  isReadOnly?: boolean
  onBenefitsChanged?: () => Promise<void> | void
  onLogoUploaded?: () => Promise<void> | void
  onToggle: () => void
  onStartEditing: (block: string, field: string) => void
  onCancelEditing: () => void
  onSaveField: (block: string, field: string, value: unknown) => void
}

export function MinhaEmpresaCard({
  block,
  IconComp,
  isExpanded,
  recentlyUpdated,
  editingField,
  isSavingField,
  benefits = [],
  companyId = null,
  isReadOnly = false,
  onBenefitsChanged,
  onLogoUploaded,
  onToggle,
  onStartEditing,
  onCancelEditing,
  onSaveField,
}: MinhaEmpresaCardProps) {
  const t = useTranslations("settings.minhaEmpresaCard")

  const formatFieldValue = (value: unknown): string => {
    if (value === null || value === undefined || value === "") return t("valueNotDefined")
    if (typeof value === "boolean") return value ? t("valueYes") : t("valueNo")
    if (Array.isArray(value)) {
      if (value.length === 0) return t("valueNone")
      return value.join(", ")
    }
    return String(value)
  }

  const STATUS_STYLES = {
    configured: {
      badge: "bg-status-success/10 text-status-success border-status-success/30 dark:bg-status-success/20",
      label: t("statusConfigured"),
    },
    partial: {
      badge: "bg-status-warning/10 text-status-warning border-status-warning/30 dark:bg-status-warning/20",
      label: t("statusPartial"),
    },
    pending: {
      badge: "bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle dark:bg-lia-bg-elevated dark:border-lia-border-default",
      label: t("statusPending"),
    },
  } as const

  const statusStyle = STATUS_STYLES[block.status]

  const uploadConfig = BLOCK_UPLOAD[block.key]

  return (
    <Card
      className="bg-lia-bg-primary dark:bg-lia-bg-secondary overflow-hidden rounded-xl"
      data-block-anchor={block.key}
    >
      <InteractiveSurface
        variant="accordion"
        onClick={onToggle}
        className="px-4 py-3 hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse duration-150"
        aria-expanded={isExpanded}
        aria-label={`${block.title} - ${statusStyle.label}`}
      >
        <div className="flex items-center gap-2 min-w-0">
          {IconComp && <IconComp className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />}
          <span className={textStyles.h3}>{block.title}</span>
          {block.subtitle && (
            <span
              className={`${textStyles.description} truncate`}
              data-testid={`block-subtitle-${block.key}`}
            >
              · {block.subtitle}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {block.progress.total > 0 && (
            <span
              className="text-micro font-medium text-lia-text-secondary"
              data-testid={`block-progress-${block.key}`}
            >
              {t("fieldsFilled", { filled: block.progress.filled, total: block.progress.total })}
            </span>
          )}
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
      </InteractiveSurface>

      {isExpanded && (
        <CardContent className="px-4 py-3 border-t border-lia-border-subtle space-y-3">
          {isReadOnly && (
            <div
              className="text-xs text-lia-text-secondary italic px-2 py-1 rounded-md bg-lia-bg-secondary/40 border border-lia-border-subtle"
              data-testid={`readonly-hint-${block.key}`}
            >
              {t("readOnlyHint")}
            </div>
          )}
          {uploadConfig && (
            <SectionUploadDropZone
              targetSection={uploadConfig.targetSection}
              documentType={uploadConfig.documentType}
              sectionLabel={t(`blockUpload.${uploadConfig.sectionLabelKey}` as never)}
              hint={uploadConfig.hintKey ? t(`blockUpload.${uploadConfig.hintKey}` as never) : undefined}
            />
          )}
          {block.progress.missingLabels.length > 0 && (
            <div
              className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary/50 dark:bg-lia-bg-elevated px-2.5 py-2"
              data-testid={`block-missing-${block.key}`}
            >
              <p className={`${textStyles.captionBold} text-lia-text-primary mb-1`}>
                {t("missingFieldsTitle", { count: block.progress.missingLabels.length })}
              </p>
              <p className="text-micro text-lia-text-secondary">
                {block.progress.missingLabels.slice(0, 8).join(" · ")}
                {block.progress.missingLabels.length > 8
                  ? ` · +${block.progress.missingLabels.length - 8}`
                  : ""}
              </p>
              {uploadConfig && (
                <p className="text-micro text-lia-text-tertiary mt-1">
                  {t("uploadHint")}
                </p>
              )}
            </div>
          )}
          {block.key === "benefits" && (
            <BenefitsListSection
              benefits={benefits}
              companyId={companyId}
              onChanged={onBenefitsChanged || (() => {})}
            />
          )}
          {block.key === "workforce" && (
            <ErrorBoundarySection>
              <WorkforceHubContent />
            </ErrorBoundarySection>
          )}
          {block.key === "documents" && (
            <div className="mt-3 space-y-6">
              <ErrorBoundarySection>
                <SalaryBandsSection />
                <VariableCompCatalogSection />
              </ErrorBoundarySection>
            </div>
          )}
          {block.key !== "workforce" && (
          <div className="space-y-1">
            {block.fields.map((field) => {
              const isLogoField = field.key === "logo" && block.key === "basic"
              const isActionField = field.key === "import_spreadsheet" || field.key === "handbook" || field.key === "org_chart"

              if (isActionField) {
                return null
              }

              const isEditing =
                !isReadOnly &&
                editingField?.block === block.key &&
                editingField?.field === field.key
              const isUpdated = recentlyUpdated.has(field.key)

              // P1.13 audit 2026-05-20: campo Logo usa upload de arquivo canonical
              if (isLogoField) {
                return (
                  <div
                    key={field.key}
                    className="group flex items-center justify-between gap-2 py-1.5 px-1.5 rounded-md hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50"
                  >
                    <span className={`${textStyles.description} min-w-[120px] max-w-[60%] break-words leading-snug pr-2`}>
                      {field.label}
                    </span>
                    <LogoUploadField
                      currentValue={field.value as string | null}
                      onUploadSuccess={() => {
                        // Backend já persistiu via POST /logo. Só refetch profile
                        // pra UI mostrar o novo valor (saveField/PUT tem fieldMap
                        // sem mapping pra "logo" → payload era ignorado).
                        void onLogoUploaded?.()
                      }}
                    />
                  </div>
                )
              }

              return (
                <div
                  key={field.key}
                  className={`group flex items-center justify-between gap-2 py-1.5 px-1.5 rounded-md transition-colors motion-reduce:transition-none duration-300 ${
                    isUpdated
                      ? "bg-status-success/10 dark:bg-status-success/10"
                      : "hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/50"
                  }`}
                >
                  <span className={`${textStyles.description} min-w-[120px] max-w-[60%] break-words leading-snug pr-2`}>
                    {field.label}
                  </span>
                  {isEditing ? (
                    <InlineFieldEditor
                      field={field}
                      currentValue={field.value}
                      onSave={(newValue) => onSaveField(block.key, field.key, newValue)}
                      onCancel={onCancelEditing}
                      isSaving={isSavingField}
                    />
                  ) : (
                    <div className="flex items-center gap-1 min-w-0">
                      <span
                        className={`${textStyles.metricSmall} text-right truncate max-w-[320px] transition-colors motion-reduce:transition-none duration-300 ${
                          isUpdated ? "text-status-success" : ""
                        }`}
                        title={formatFieldValue(field.value)}
                      >
                        {formatFieldValue(field.value)}
                      </span>
                      {field.editable && !isReadOnly && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onStartEditing(block.key, field.key)
                          }}
                          className="opacity-0 group-hover:opacity-100 p-0.5 rounded-md hover:bg-lia-interactive-active dark:hover:bg-lia-border-medium transition-opacity motion-reduce:transition-none"
                          aria-label={t("editFieldAria", { label: field.label })}
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
          )}
        </CardContent>
      )}
    </Card>
  )
}
