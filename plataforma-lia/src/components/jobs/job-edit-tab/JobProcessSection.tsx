"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import {
  Brain, ChevronUp, ChevronDown, Clock, Lock, Loader2, Plus, Settings, Target, Trash2,
} from "lucide-react"
import { inputClass, groupHeaderClass, getCategoryBadge } from "./job-edit-tab.constants"

interface Stage {
  name?: string
  stageName: string
  stageCategory?: string
  isEditable?: boolean
  isRemovable?: boolean
  isReorderable?: boolean
  isActive?: boolean
  liaAssisted?: boolean
  slaDays?: number
  defaultSlaDays?: number
}

interface JobProcessSectionProps {
  stages: Stage[]
  rawStages: Stage[]
  loadingCompanyPipeline: boolean
  isEditing: boolean
  LIA_ASSISTED_STAGES: string[]
  LIA_ASSISTED_STAGE_NAMES: string[]
  addStage: () => void
  removeStage: (index: number) => void
  updateStage: (index: number, field: string, value: unknown) => void
  moveStage: (index: number, direction: "up" | "down") => void
}

export function JobProcessSection({
  stages,
  rawStages,
  loadingCompanyPipeline,
  isEditing,
  LIA_ASSISTED_STAGES,
  LIA_ASSISTED_STAGE_NAMES,
  addStage,
  removeStage,
  updateStage,
  moveStage,
}: JobProcessSectionProps) {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4 text-micro lia-text-500 dark:text-lia-text-tertiary p-2.5 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-lg font-['Open_Sans',sans-serif] flex-1">
            <div className="flex items-center gap-1"><Lock className="w-3 h-3" /><span><strong>Sistema:</strong> Fixas</span></div>
            <div className="flex items-center gap-1"><Target className="w-3 h-3" /><span><strong>Padrão:</strong> Nome editável</span></div>
            <div className="flex items-center gap-1"><Settings className="w-3 h-3" /><span><strong>Custom:</strong> Editável</span></div>
            <div className="flex items-center gap-1 ml-auto"><Brain className="w-3 h-3 text-wedo-cyan" /><span className="text-wedo-cyan"><strong>LIA</strong> auxilia</span></div>
          </div>
        </div>
        <h3 className={groupHeaderClass}>Etapas do Processo</h3>
        {loadingCompanyPipeline && rawStages.length === 0 ? (
          <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
            <CardContent className="p-4">
              <div className="flex items-center justify-center gap-2 py-6">
                <Loader2 className="w-3.5 h-3.5 animate-spin lia-text-400 dark:lia-text-500" />
                <span className="text-xs lia-text-400 dark:lia-text-500 font-['Open_Sans',sans-serif]">Carregando etapas da empresa...</span>
              </div>
            </CardContent>
          </Card>
        ) : stages.length === 0 ? (
          <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
            <CardContent className="p-4">
              <p className="text-xs lia-text-400 dark:lia-text-500 text-center py-6 font-['Open_Sans',sans-serif]">
                Nenhuma etapa configurada. As etapas padrão da empresa serão utilizadas.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {stages.map((stage, index) => {
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
              return (
                <Card
                  key={stage.name || index}
                  className={`border transition-colors ${!stageIsActive ? "opacity-40" : ""} ${
                    isSystem
                      ? "border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50/50 dark:bg-lia-bg-secondary/30"
                      : "border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default dark:hover:border-gray-600"
                  }`}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gray-900 dark:lia-bg-50 flex items-center justify-center text-xs font-bold text-white dark:lia-text-900 font-['Open_Sans',sans-serif] shrink-0">
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
                              className={`text-base-ui font-semibold font-['Open_Sans',sans-serif] ${
                                isSystem ? "lia-text-500 dark:text-lia-text-tertiary" : "lia-text-900 dark:lia-text-50"
                              }`}
                            >
                              {stage.stageName || "Sem nome"}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium ${badge.color} font-['Open_Sans',sans-serif]`}
                          >
                            <BadgeIcon className="w-2.5 h-2.5" />
                            {badge.label}
                          </span>
                          {isLiaAssisted && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium text-wedo-cyan bg-wedo-cyan/10 font-['Open_Sans',sans-serif]">
                              <Brain className="w-2.5 h-2.5 text-wedo-cyan" />LIA auxilia
                            </span>
                          )}
                          <div className="flex items-center gap-1 ml-auto">
                            <Clock className="w-3 h-3 lia-text-400 dark:lia-text-500" />
                            {isEditing ? (
                              <div className="flex items-center gap-1">
                                <input
                                  type="number"
                                  min={1}
                                  max={90}
                                  className="w-12 text-xs text-center px-1 py-0.5 border border-lia-border-subtle dark:border-lia-border-subtle rounded-full bg-white dark:bg-lia-bg-primary lia-text-700 dark:text-lia-text-secondary font-['Open_Sans',sans-serif]"
                                  value={currentSla}
                                  onChange={(e) => updateStage(index, "slaDays", parseInt(e.target.value) || 1)}
                                />
                                <span className="text-micro lia-text-400 dark:lia-text-500 font-['Open_Sans',sans-serif]">dias</span>
                                {slaModified && (
                                  <span className="text-micro text-status-warning font-['Open_Sans',sans-serif]">
                                    (padrão: {defaultSla}d)
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span
                                className={`text-micro font-['Open_Sans',sans-serif] ${
                                  slaModified
                                    ? "text-status-warning dark:text-status-warning font-medium"
                                    : "lia-text-400 dark:lia-text-500"
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
                        {isEditing && canReorder && (
                          <>
                            <button
                              type="button"
                              onClick={() => moveStage(index, "up")}
                              disabled={index === 0}
                              className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 lia-text-400 hover:lia-text-600 disabled:opacity-30"
                            >
                              <ChevronUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => moveStage(index, "down")}
                              disabled={index === stages.length - 1}
                              className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 lia-text-400 hover:lia-text-600 disabled:opacity-30"
                            >
                              <ChevronDown className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                        {isEditing && isSystem && <Lock className="w-3.5 h-3.5 lia-text-300 dark:lia-text-600" />}
                        {isEditing && canRemove && (
                          <button
                            type="button"
                            onClick={() => removeStage(index)}
                            className="p-1 rounded-md hover:bg-status-error/10 dark:hover:bg-status-error/10/30 lia-text-400 hover:text-status-error"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
        {isEditing && (
          <button
            type="button"
            onClick={addStage}
            className="flex items-center gap-2 text-xs lia-text-500 hover:lia-text-700 dark:hover:lia-text-300 py-2.5 px-3 rounded-md border border-dashed border-lia-border-default dark:border-lia-border-default hover:border-gray-400 w-full justify-center mt-3"
          >
            <Plus className="w-4 h-4" />Adicionar Etapa Customizada
          </button>
        )}
      </div>
    </div>
  )
}
