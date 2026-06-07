"use client"

import { useTranslations } from "next-intl"
import {
  PII_SALARY_FIELDS,
  PII_SENSITIVE_FIELDS,
  type PiiField,
  type PiiFieldVisibility,
} from "./user-management-types"

interface PiiFieldVisibilityMatrixProps {
  value: PiiFieldVisibility
  onChange: (next: PiiFieldVisibility) => void
  disabled?: boolean
}

type TriState = "inherited" | "show" | "hide"

function getTriState(value: PiiFieldVisibility, field: PiiField): TriState {
  if (value[field] === true) return "show"
  if (value[field] === false) return "hide"
  return "inherited"
}

function applyTriState(
  value: PiiFieldVisibility,
  field: PiiField,
  state: TriState,
): PiiFieldVisibility {
  if (state === "inherited") {
    const next = { ...value }
    delete next[field]
    return next
  }
  return { ...value, [field]: state === "show" }
}

function applyBulkToGroup(
  value: PiiFieldVisibility,
  fields: readonly PiiField[],
  state: TriState,
): PiiFieldVisibility {
  let next = { ...value }
  for (const field of fields) {
    if (state === "inherited") {
      delete next[field]
    } else {
      next = { ...next, [field]: state === "show" }
    }
  }
  return next
}

interface FieldRowProps {
  field: PiiField
  label: string
  currentState: TriState
  stateInherited: string
  stateShow: string
  stateHide: string
  disabled: boolean
  onChange: (state: TriState) => void
}

function FieldRow({
  field,
  label,
  currentState,
  stateInherited,
  stateShow,
  stateHide,
  disabled,
  onChange,
}: FieldRowProps) {
  const baseBtn =
    "px-2 py-0.5 text-xs rounded border transition-colors focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/50"
  const activeBtn =
    "bg-lia-btn-primary-bg text-white border-lia-btn-primary-bg"
  const inactiveBtn =
    "bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-elevated dark:hover:bg-lia-bg-primary"
  const disabledClass = disabled ? "opacity-50 cursor-not-allowed pointer-events-none" : ""

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-lia-border-default/40 last:border-b-0">
      <span className="text-xs text-lia-text-primary flex-1 mr-2">{label}</span>
      <div
        className={`flex gap-1 ${disabledClass}`}
        role="group"
        aria-label={`Visibilidade de ${label}`}
      >
        <button
          type="button"
          aria-label={`${label}: ${stateInherited}`}
          aria-pressed={currentState === "inherited"}
          disabled={disabled}
          className={`${baseBtn} ${currentState === "inherited" ? activeBtn : inactiveBtn}`}
          onClick={() => onChange("inherited")}
          data-testid={`pii-field-${field}-inherited`}
        >
          {stateInherited}
        </button>
        <button
          type="button"
          aria-label={`${label}: ${stateShow}`}
          aria-pressed={currentState === "show"}
          disabled={disabled}
          className={`${baseBtn} ${currentState === "show" ? activeBtn : inactiveBtn}`}
          onClick={() => onChange("show")}
          data-testid={`pii-field-${field}-show`}
        >
          {stateShow}
        </button>
        <button
          type="button"
          aria-label={`${label}: ${stateHide}`}
          aria-pressed={currentState === "hide"}
          disabled={disabled}
          className={`${baseBtn} ${currentState === "hide" ? activeBtn : inactiveBtn}`}
          onClick={() => onChange("hide")}
          data-testid={`pii-field-${field}-hide`}
        >
          {stateHide}
        </button>
      </div>
    </div>
  )
}

interface GroupSectionProps {
  title: string
  fields: readonly PiiField[]
  value: PiiFieldVisibility
  stateInherited: string
  stateShow: string
  stateHide: string
  disabled: boolean
  getLabel: (field: PiiField) => string
  onFieldChange: (field: PiiField, state: TriState) => void
  onBulkChange: (fields: readonly PiiField[], state: TriState) => void
}

function GroupSection({
  title,
  fields,
  value,
  stateInherited,
  stateShow,
  stateHide,
  disabled,
  getLabel,
  onFieldChange,
  onBulkChange,
}: GroupSectionProps) {
  const baseBtn =
    "px-2 py-0.5 text-xs rounded border transition-colors focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/50"
  const bulkBtn =
    "bg-lia-bg-primary dark:bg-lia-bg-elevated text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-elevated dark:hover:bg-lia-bg-primary"
  const disabledClass = disabled ? "opacity-50 cursor-not-allowed pointer-events-none" : ""

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide">
          {title}
        </h5>
        <div
          className={`flex gap-1 ${disabledClass}`}
          role="group"
          aria-label={`Definir todos de ${title}`}
        >
          <button
            type="button"
            disabled={disabled}
            className={`${baseBtn} ${bulkBtn}`}
            aria-label={`Todos ${title}: ${stateInherited}`}
            onClick={() => onBulkChange(fields, "inherited")}
          >
            {stateInherited}
          </button>
          <button
            type="button"
            disabled={disabled}
            className={`${baseBtn} ${bulkBtn}`}
            aria-label={`Todos ${title}: ${stateShow}`}
            onClick={() => onBulkChange(fields, "show")}
          >
            {stateShow}
          </button>
          <button
            type="button"
            disabled={disabled}
            className={`${baseBtn} ${bulkBtn}`}
            aria-label={`Todos ${title}: ${stateHide}`}
            onClick={() => onBulkChange(fields, "hide")}
          >
            {stateHide}
          </button>
        </div>
      </div>
      <div className="rounded-md border border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-elevated px-3 py-1">
        {fields.map((field) => (
          <FieldRow
            key={field}
            field={field}
            label={getLabel(field)}
            currentState={getTriState(value, field)}
            stateInherited={stateInherited}
            stateShow={stateShow}
            stateHide={stateHide}
            disabled={disabled}
            onChange={(state) => onFieldChange(field, state)}
          />
        ))}
      </div>
    </div>
  )
}

export function PiiFieldVisibilityMatrix({
  value,
  onChange,
  disabled = false,
}: PiiFieldVisibilityMatrixProps) {
  // ALL hooks at top — rules-of-hooks
  const t = useTranslations("settings.users.piiVisibility")

  const stateInherited = t("stateInherited")
  const stateShow = t("stateShow")
  const stateHide = t("stateHide")

  function handleFieldChange(field: PiiField, state: TriState) {
    onChange(applyTriState(value, field, state))
  }

  function handleBulkChange(fields: readonly PiiField[], state: TriState) {
    onChange(applyBulkToGroup(value, fields, state))
  }

  function getLabel(field: PiiField): string {
    return t(`fields.${field}`)
  }

  return (
    <div data-testid="pii-field-visibility-matrix">
      <GroupSection
        title={t("groupSalary")}
        fields={PII_SALARY_FIELDS}
        value={value}
        stateInherited={stateInherited}
        stateShow={stateShow}
        stateHide={stateHide}
        disabled={disabled}
        getLabel={getLabel}
        onFieldChange={handleFieldChange}
        onBulkChange={handleBulkChange}
      />
      <GroupSection
        title={t("groupSensitive")}
        fields={PII_SENSITIVE_FIELDS}
        value={value}
        stateInherited={stateInherited}
        stateShow={stateShow}
        stateHide={stateHide}
        disabled={disabled}
        getLabel={getLabel}
        onFieldChange={handleFieldChange}
        onBulkChange={handleBulkChange}
      />
    </div>
  )
}
