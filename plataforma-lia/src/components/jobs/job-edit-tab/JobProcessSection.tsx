"use client"

import React from"react"
import { Card, CardContent } from"@/components/ui/card"
import {
  Brain, ChevronUp, ChevronDown, Clock, Layers, Lock, Loader2, Plus, Settings, Target, Trash2,
} from"lucide-react"
import { inputClass, groupHeaderClass, getCategoryBadge } from"./job-edit-tab.constants"
import type { PipelineTemplateFull } from"@/hooks/pipeline/use-pipeline-templates"

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
  moveStage: (index: number, direction:"up" |"down") => void
  // Fase 5 Unify: template selector
  vacancyId?: string
  templates?: PipelineTemplateFull[]
  isLoadingTemplates?: boolean
  isApplyingTemplate?: boolean
  onApplyTemplate?: (templateId: string) => void
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
  vacancyId,
  templates,
  isLoadingTemplates,
  isApplyingTemplate,
  onApplyTemplate,
}: JobProcessSectionProps) {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4 text-micro text-lia-text-secondary p-2.5 bg-lia-bg-secondary/50 rounded-lg flex-1">
            <div className="flex items-center gap-1"><Lock className="w-3 h-3" /><span><strong>Sistema:</strong> Fixas</span></div>
            <div className="flex items-center gap-1"><Target className="w-3 h-3" /><span><strong>Padrão:</strong> Nome editável</span></div>
            <div className="flex items-center gap-1"><Settings className="w-3 h-3" /><span><strong>Custom:</strong> Editável</span></div>
            <div className="flex items-center gap-1 ml-auto"><Brain className="w-3 h-3 text-wedo-cyan" /><span className="text-wedo-cyan"><strong>LIA</strong> auxilia</span></div>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <h3 className={groupHeaderClass}>Etapas do Processo</h3>
          {vacancyId && onApplyTemplate && templates && templates.length > 0 && (
            <div className="flex items-center gap-2">
              {isApplyingTemplate && <Loader2 className="w-3 h-3 animate-spin text-lia-text-tertiary" />}
              <select
                onChange={e => { if (e.target.value) onApplyTemplate(e.target.value) }}
                disabled={isApplyingTemplate}
                defaultValue=""
                className="text-xs py-1 px-2 rounded-lg border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:border-lia-border-medium disabled:opacity-50 focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20"
                aria-label="Selecionar template de pipeline"
              >
                <option value="" disabled>
                  <Layers className="inline w-3 h-3 mr-1" />
                  Aplicar template...
                </option>
                {templates.map(t => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.stages.length} etapas)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        {loadingCompanyPipeline && rawStages.length === 0 ? (
          <Card className="border border-lia-border-subtle">
            <CardContent className="p-4">
              <div className="flex items-center justify-center gap-2 py-6">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-lia-text-tertiary" />
                <span className="text-xs text-lia-text-tertiary">Carregando etapas da empresa...</span>
              </div>
            </CardContent>
          </Card>
        ) : stages.length === 0 ? (
          <Card className="border border-lia-border-subtle">
            <CardContent className="p-4">
              <p className="text-xs text-lia-text-tertiary text-center py-6">
                Nenhuma etapa configurada. As etapas padrão da empresa serão utilizadas.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {stages.map((stage, index) => {
              const badge = getCategoryBadge(stage.stageCategory)
              const BadgeIcon = badge.icon
              const isSystem = stage.stageCategory ==="system"
              const canEditName = stage.isEditable !== false && !isSystem
              const canRemove = stage.isRemovable !== false && stage.stageCategory ==="custom"
              const canReorder = stage.isReorderable !== false && !isSystem
              const stageIsActive = stage.isActive !== false
              const isLiaAssisted =
                stage.liaAssisted ||
                LIA_ASSISTED_STAGES.includes(stage.name ||"") ||
                LIA_ASSISTED_STAGE_NAMES.includes(stage.stageName ||"")
              const currentSla = stage.slaDays ?? stage.defaultSlaDays ?? 3
              const defaultSla = stage.defaultSlaDays ?? 3
              const slaModified = currentSla !== defaultSla
              return (
                <Card
                  key={stage.name || index}
                  className={`border transition-colors ${!stageIsActive ?"opacity-40" :""} ${
                    isSystem
                      ?"border-lia-border-subtle bg-lia-bg-secondary/50/30"
                      :"border-lia-border-subtle hover:border-lia-border-default"
                  }`}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
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
                              onChange={(e) => updateStage(index,"stageName", e.target.value)}
                              placeholder="Nome da etapa"
                            />
                          ) : (
                            <span
                              className={`text-base-ui font-semibold ${
                                isSystem ?"text-lia-text-secondary" :"text-lia-text-primary"
                              }`}
                            >
                              {stage.stageName ||"Sem nome"}
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
                              <Brain className="w-2.5 h-2.5 text-wedo-cyan" />LIA auxilia
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
                                  onChange={(e) => updateStage(index,"slaDays", parseInt(e.target.value) || 1)}
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
                                  slaModified
                                    ?"text-status-warning font-medium"
                                    :"text-lia-text-tertiary"
                                }`}
                              >
                                {currentSla} {currentSla === 1 ?"dia" :"dias"}
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
                              onClick={() => moveStage(index,"up")}
                              disabled={index === 0}
                              className="p-1 rounded-md hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary disabled:opacity-30"
                            >
                              <ChevronUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => moveStage(index,"down")}
                              disabled={index === stages.length - 1}
                              className="p-1 rounded-md hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary disabled:opacity-30"
                            >
                              <ChevronDown className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                        {isEditing && isSystem && <Lock className="w-3.5 h-3.5 text-lia-text-disabled" />}
                        {isEditing && canRemove && (
                          <button
                            type="button"
                            onClick={() => removeStage(index)}
                            className="p-1 rounded-md hover:bg-status-error/10 dark:hover:bg-status-error/10/30 text-lia-text-tertiary hover:text-status-error"
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
            className="flex items-center gap-2 text-xs text-lia-text-secondary hover:text-lia-text-primary py-2.5 px-3 rounded-xl border border-dashed border-lia-border-default hover:border-lia-border-medium w-full justify-center mt-3"
          >
            <Plus className="w-4 h-4" />Adicionar Etapa Customizada
          </button>
        )}
      </div>
    </div>
  )
}
