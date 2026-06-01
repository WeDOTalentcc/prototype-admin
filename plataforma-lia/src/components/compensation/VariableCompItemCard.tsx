"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Switch } from "@/components/ui/switch"
import { DollarSign, Star, Clock, Pencil, Trash2 } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { formatCompTarget, FREQUENCY_OPTIONS, type VariableCompRecord } from "./variable-comp-types"

interface VariableCompItemCardProps {
  component: VariableCompRecord
  isEditing: boolean
  onToggle: (c: VariableCompRecord) => void
  onEdit: (c: VariableCompRecord) => void
  onDelete: (id: string) => void
  mode?: "catalog" | "vacancy"
  isLinked?: boolean
}

function freqLabel(f?: string | null): string {
  if (!f) return ""
  return FREQUENCY_OPTIONS.find((o) => o.id === f)?.label || f
}

export const VariableCompItemCard = React.memo(function VariableCompItemCard({
  component,
  isEditing,
  onToggle,
  onEdit,
  onDelete,
  mode = "catalog",
  isLinked = false,
}: VariableCompItemCardProps) {
  const isVacancy = mode === "vacancy"
  const toggleChecked = isVacancy ? !!isLinked : component.is_active !== false
  const suggested = isVacancy && !isLinked && !!component.matches_vaga
  const dimClass = !isVacancy && component.is_active === false ? " opacity-60" : ""
  const suggestedClass = suggested ? " bg-lia-btn-primary-bg/5" : ""

  return (
    <div className={"p-3 flex items-center justify-between hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none" + dimClass + suggestedClass}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className={textStyles.subtitle + " truncate"}>{component.name}</h4>
          {component.is_highlighted && <Star className="w-3.5 h-3.5 text-status-warning fill-yellow-500" />}
          {suggested && <Chip variant="neutral" className="text-micro">Sugerido</Chip>}
        </div>
        {component.description && (
          <p className={textStyles.description + " truncate mb-1.5"}>{component.description}</p>
        )}
        <div className="flex items-center gap-3 text-xs text-lia-text-secondary">
          <span className="flex items-center gap-1">
            <DollarSign className="w-3.5 h-3.5" />
            {formatCompTarget(component)}
          </span>
          {component.frequency && (
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {freqLabel(component.frequency)}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3 ml-3">
        <Switch
          checked={toggleChecked}
          onCheckedChange={() => onToggle(component)}
          disabled={!isEditing}
          className={!isEditing ? "opacity-60" : ""}
        />
        {isEditing && (
          <>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onEdit(component)} aria-label="Editar">
              <Pencil className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
            {!isVacancy && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10"
                onClick={() => component.id && onDelete(component.id)}
                aria-label="Excluir"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  )
})
