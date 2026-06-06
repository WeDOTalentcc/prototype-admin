"use client"

import React, { useState } from "react"
import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Card, CardContent } from "@/components/ui/card"
import { Brain, ChevronDown, ChevronRight, Clock, Database, GripVertical, ListChecks, Lock, Trash2 } from "lucide-react"
import { inputClass, getCategoryBadge } from "./job-edit-tab.constants"
import type { Stage } from "./JobProcessSection"

interface JobProcessStageCardProps {
  stage: Stage
  index: number
  sortableId: string
  isEditing: boolean
  LIA_ASSISTED_STAGES: string[]
  LIA_ASSISTED_STAGE_NAMES: string[]
  updateStage: (index: number, field: string, value: unknown) => void
  removeStage: (index: number) => void
}

export function JobProcessStageCard({
  stage,
  index,
  sortableId,
  isEditing,
  LIA_ASSISTED_STAGES,
  LIA_ASSISTED_STAGE_NAMES,
  updateStage,
  removeStage,
}: JobProcessStageCardProps) {
  const badge = getCategoryBadge(stage.stageCategory)
  const BadgeIcon = badge.icon
  const isSystem = stage.stageCategory === "system"
  const canEditName = stage.isEditable !== false && !isSystem
  const canRemove = stage.isRemovable !== false && stage.stageCategory === "custom"
  const canReorder = stage.isReorderable !== false && !isSystem
  const stageIsActive = stage.isActive !== false
  const isLiaAssisted =
    stage.liaAssisted ||
    LIA_ASSISTED_STAGES.includes(stage.name || "") ||
    LIA_ASSISTED_STAGE_NAMES.includes(stage.stageName || "")
  const currentSla = stage.slaDays ?? stage.defaultSlaDays ?? 3
  const defaultSla = stage.defaultSlaDays ?? 3
  const slaModified = currentSla !== defaultSla

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: sortableId, disabled: !isEditing || !canReorder })
  const style = { transform: CSS.Transform.toString(transform), transition }

  // #5 Fase 1: sub-status + campos de coleta herdados da empresa (read-only).
  const [showInherited, setShowInherited] = useState(false)
  const subStatuses = stage.subStatuses ?? []
  const dataFields = stage.dataFields ?? []
  const hasInherited = subStatuses.length > 0 || dataFields.length > 0

  return (
    <div ref={setNodeRef} style={style} data-testid={`job-process-stage-card-${index}`}>
      <Card
        className={`border transition-colors ${!stageIsActive ? "opacity-40" : ""} ${
          isDragging ? "opacity-90 bg-lia-bg-secondary" : ""
        } ${
          isSystem
            ? "border-lia-border-subtle bg-lia-bg-secondary/50/30"
            : "border-lia-border-subtle hover:border-lia-border-default"
        }`}
      >
        <CardContent className="p-3">
          <div className="flex items-center gap-3">
            {isEditing && canReorder ? (
              <button
                type="button"
                {...attributes}
                {...listeners}
                aria-label="Arrastar para reordenar"
                className="cursor-grab active:cursor-grabbing p-1 rounded-md hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary shrink-0"
              >
                <GripVertical className="w-4 h-4" />
              </button>
            ) : isEditing && isSystem ? (
              <div className="p-1 shrink-0"><Lock className="w-4 h-4 text-lia-text-disabled" /></div>
            ) : null}
            <div className="w-8 h-8 rounded-full bg-lia-btn-primary-bg flex items-center justify-center text-xs font-bold text-white shrink-0">
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {isEditing && canEditName ? (
                  <input
                    type="text"
                    className={`${inputClass(!isEditing)} flex-1`}
                    value={stage.stageName}
                    onChange={(e) => updateStage(index, "stageName", e.target.value)}
                    placeholder="Nome da etapa"
                  />
                ) : (
                  <span
                    className={`text-base-ui font-semibold ${
                      isSystem ? "text-lia-text-secondary" : "text-lia-text-primary"
                    }`}
                  >
                    {stage.stageName || "Sem nome"}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1.5">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium ${badge.color}`}
                >
                  <BadgeIcon className="w-2.5 h-2.5" />
                  {badge.label}
                </span>
                {isLiaAssisted && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-wedo-cyan bg-wedo-cyan/10">
                    <Brain className="w-2.5 h-2.5 text-wedo-cyan" />IA auxilia
                  </span>
                )}
                <div className="flex items-center gap-1 ml-auto">
                  <Clock className="w-3 h-3 text-lia-text-tertiary" />
                  {isEditing ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        min={1}
                        max={90}
                        className="w-12 text-micro text-center px-1 py-0.5 border border-lia-border-subtle rounded-full bg-lia-bg-primary text-lia-text-primary"
                        value={currentSla}
                        onChange={(e) => updateStage(index, "slaDays", parseInt(e.target.value) || 1)}
                      />
                      <span className="text-micro text-lia-text-tertiary">dias</span>
                      {slaModified && (
                        <span className="text-micro text-status-warning">
                          (padrão: {defaultSla}d)
                        </span>
                      )}
                    </div>
                  ) : (
                    <span
                      className={`text-micro ${
                        slaModified ? "text-status-warning font-medium" : "text-lia-text-tertiary"
                      }`}
                    >
                      {currentSla} {currentSla === 1 ? "dia" : "dias"}
                      {slaModified && ` (padrão: ${defaultSla}d)`}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-0.5 shrink-0">
              {isEditing && canRemove && (
                <button
                  type="button"
                  onClick={() => removeStage(index)}
                  aria-label="Remover etapa"
                  className="p-1 rounded-md hover:bg-status-error/10 dark:hover:bg-status-error/10/30 text-lia-text-tertiary hover:text-status-error"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {hasInherited && (
            <div className="mt-2 pt-2 border-t border-lia-border-subtle">
              <button
                type="button"
                onClick={() => setShowInherited(v => !v)}
                aria-expanded={showInherited}
                className="flex items-center gap-1.5 text-micro text-lia-text-tertiary hover:text-lia-text-secondary"
              >
                {showInherited ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                <span>Sub-status e coleta</span>
                <span className="text-lia-text-disabled">
                  ({subStatuses.length} sub-status · {dataFields.length} campos · herdado)
                </span>
              </button>
              {showInherited && (
                <div className="mt-2 space-y-2 pl-4">
                  {subStatuses.length > 0 && (
                    <div className="flex items-start gap-1.5">
                      <ListChecks className="w-3 h-3 mt-0.5 text-lia-text-tertiary shrink-0" />
                      <div className="flex flex-wrap gap-1">
                        {subStatuses.map((ss, i) => (
                          <span
                            key={ss.id || ss.name || i}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-micro bg-lia-bg-secondary text-lia-text-secondary"
                          >
                            {ss.display_name || ss.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {dataFields.length > 0 && (
                    <div className="flex items-start gap-1.5">
                      <Database className="w-3 h-3 mt-0.5 text-lia-text-tertiary shrink-0" />
                      <div className="flex flex-wrap gap-1">
                        {dataFields.map((df, i) => (
                          <span
                            key={df.id || i}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-micro bg-lia-bg-secondary text-lia-text-secondary"
                          >
                            {df.displayName}
                            {df.required && <span className="text-status-warning">*</span>}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="text-micro text-lia-text-disabled">
                    Herdado da empresa — editar em Configurações › Jornada de Recrutamento.
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
