"use client"

import React, { useState } from"react"
import { Card, CardContent } from"@/components/ui/card"
import {
  Brain, Layers, Lock, Loader2, Plus, Settings, Target,
} from"lucide-react"
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor,
  useSensor, useSensors, type DragEndEvent,
} from"@dnd-kit/core"
import {
  SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy,
} from"@dnd-kit/sortable"
import { groupHeaderClass } from"./job-edit-tab.constants"
import type { PipelineTemplateFull } from"@/hooks/pipeline/use-pipeline-templates"
import type { SubStatusOption, StageDataField } from"@/components/settings/recruitment-journey.types"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from"@/components/ui/select"
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from"@/components/ui/alert-dialog"
import { JobProcessStageCard } from"./JobProcessStageCard"

export interface Stage {
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
  subStatuses?: SubStatusOption[]
  dataFields?: StageDataField[]
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
  reorderStages: (fromIndex: number, toIndex: number) => void
  // Fase 5 Unify: template selector
  vacancyId?: string
  templates?: PipelineTemplateFull[]
  isLoadingTemplates?: boolean
  isApplyingTemplate?: boolean
  onApplyTemplate?: (templateId: string) => void
  // Fase 4 Unify: salvar como template
  onSaveAsTemplate?: (name: string) => Promise<void>
  isSavingAsTemplate?: boolean
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
  reorderStages,
  vacancyId,
  templates,
  isLoadingTemplates,
  isApplyingTemplate,
  onApplyTemplate,
  onSaveAsTemplate,
  isSavingAsTemplate,
}: JobProcessSectionProps) {
  const [showSaveForm, setShowSaveForm] = useState(false)
  const [saveTemplateName, setSaveTemplateName] = useState('')
  // Confirmação obrigatória: aplicar template substitui as etapas atuais (destrutivo)
  const [pendingTemplateId, setPendingTemplateId] = useState<string | null>(null)
  const pendingTemplate = templates?.find(t => t.id === pendingTemplateId) ?? null

  // dnd-kit: reordenação por arrastar (padrão canônico, igual à Jornada da empresa)
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )
  // ids estáveis por etapa (mesma estratégia do `key` existente)
  const stageIds = stages.map((s, i) => s.name || `stage-${i}`)
  const handleDragEnd = (event: DragEndEvent) => {
    if (!isEditing) return
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = stageIds.indexOf(String(active.id))
    const newIndex = stageIds.indexOf(String(over.id))
    if (oldIndex === -1 || newIndex === -1) return
    reorderStages(oldIndex, newIndex)
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4 text-micro text-lia-text-secondary p-2.5 bg-lia-bg-secondary/50 rounded-lg flex-1">
            <div className="flex items-center gap-1"><Lock className="w-3 h-3" /><span><strong>Sistema:</strong> Fixas</span></div>
            <div className="flex items-center gap-1"><Target className="w-3 h-3" /><span><strong>Padrão:</strong> Nome editável</span></div>
            <div className="flex items-center gap-1"><Settings className="w-3 h-3" /><span><strong>Custom:</strong> Editável</span></div>
            <div className="flex items-center gap-1 ml-auto"><Brain className="w-3 h-3 text-wedo-cyan" /><span className="text-wedo-cyan"><strong>IA</strong> auxilia</span></div>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <h3 className={groupHeaderClass}>Etapas do Processo</h3>
          {isEditing && vacancyId && onApplyTemplate && templates && templates.length > 0 && (
            <div className="flex items-center gap-2">
              {isApplyingTemplate && <Loader2 className="w-3 h-3 animate-spin text-lia-text-tertiary" />}
              <Select
                disabled={isApplyingTemplate}
                value=""
                onValueChange={value => { if (value) setPendingTemplateId(value) }}
              >
                <SelectTrigger
                  className="h-8 w-auto gap-1.5 text-xs px-2 py-1 text-lia-text-secondary"
                  aria-label="Selecionar template de pipeline"
                >
                  <Layers className="w-3 h-3 text-lia-text-tertiary" />
                  <SelectValue placeholder="Aplicar template..." />
                </SelectTrigger>
                <SelectContent>
                  {templates.map(t => (
                    <SelectItem key={t.id} value={t.id} className="text-xs">
                      {t.name} ({t.stages.length} etapas)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {isEditing && vacancyId && onSaveAsTemplate && (
            showSaveForm ? (
              <>
                <input
                  type="text"
                  value={saveTemplateName}
                  onChange={e => setSaveTemplateName(e.target.value)}
                  placeholder="Nome do template..."
                  aria-label="Nome do template"
                  className="text-xs px-2 py-1 rounded-lg border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 w-36"
                  onKeyDown={e => {
                    if (e.key === "Enter") { onSaveAsTemplate(saveTemplateName).then(() => { setShowSaveForm(false); setSaveTemplateName("") }) }
                    if (e.key === "Escape") { setShowSaveForm(false); setSaveTemplateName("") }
                  }}
                  autoFocus
                />
                <button
                  onClick={() => onSaveAsTemplate(saveTemplateName).then(() => { setShowSaveForm(false); setSaveTemplateName("") })}
                  disabled={!saveTemplateName.trim() || isSavingAsTemplate}
                  className="text-xs px-2 py-1 rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50"
                >
                  {isSavingAsTemplate ? <Loader2 className="w-3 h-3 animate-spin inline" /> : "Salvar"}
                </button>
                <button onClick={() => { setShowSaveForm(false); setSaveTemplateName("") }} className="text-xs text-lia-text-secondary hover:text-lia-text-primary px-1">✕</button>
              </>
            ) : (
              <button
                data-testid="job-save-stages-as-template"
                onClick={() => setShowSaveForm(true)}
                title="Salvar etapas como template reutilizável"
                className="text-xs text-lia-text-secondary hover:text-lia-btn-primary-bg flex items-center gap-1 transition-colors whitespace-nowrap"
              >
                <Layers className="w-3 h-3" />
                Salvar como template
              </button>
            )
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
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext items={stageIds} strategy={verticalListSortingStrategy}>
              <div className="space-y-2">
                {stages.map((stage, index) => (
                  <JobProcessStageCard
                    key={stageIds[index]}
                    sortableId={stageIds[index]}
                    stage={stage}
                    index={index}
                    isEditing={isEditing}
                    LIA_ASSISTED_STAGES={LIA_ASSISTED_STAGES}
                    LIA_ASSISTED_STAGE_NAMES={LIA_ASSISTED_STAGE_NAMES}
                    updateStage={updateStage}
                    removeStage={removeStage}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
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

      <AlertDialog
        open={pendingTemplateId !== null}
        onOpenChange={open => { if (!open) setPendingTemplateId(null) }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Aplicar template de pipeline?</AlertDialogTitle>
            <AlertDialogDescription>
              Isto substitui as {stages.length} {stages.length === 1 ?"etapa atual" :"etapas atuais"} desta vaga
              {pendingTemplate ? ` pelas etapas do template "${pendingTemplate.name}"` :" pelas etapas do template selecionado"}.
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setPendingTemplateId(null)}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingTemplateId && onApplyTemplate) onApplyTemplate(pendingTemplateId)
                setPendingTemplateId(null)
              }}
            >
              Aplicar template
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
