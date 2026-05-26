"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Chip } from "@/components/ui/chip"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Layers, Trash2, Loader2, ClipboardList, Plus } from "lucide-react"
import { inputStyle } from '../edit-job-modal.constants'
import type { InterviewStage, PipelineTemplate, Job } from '../edit-job/edit-job.types'

interface EditJobModalProcessProps {
  formData: Partial<Job>
  newInterviewStageName: string
  setNewInterviewStageName: (v: string) => void
  newInterviewStageSLA: string
  setNewInterviewStageSLA: (v: string) => void
  newInterviewStageType: string
  setNewInterviewStageType: (v: string) => void
  addInterviewStage: () => void
  removeInterviewStage: (idx: number) => void
  updateInterviewStage: (idx: number, field: string, value: string | number) => void
  pipelineTemplates: PipelineTemplate[]
  isLoadingTemplates: boolean
  selectedTemplateId: string
  applyPipelineTemplate: (id: string) => Promise<void>
  fetchPipelineTemplates: () => void
}

export function EditJobModalProcess({
  formData,
  newInterviewStageName,
  setNewInterviewStageName,
  newInterviewStageSLA,
  setNewInterviewStageSLA,
  newInterviewStageType,
  setNewInterviewStageType,
  addInterviewStage,
  removeInterviewStage,
  updateInterviewStage,
  pipelineTemplates,
  isLoadingTemplates,
  selectedTemplateId,
  applyPipelineTemplate,
}: EditJobModalProcessProps) {
  return (
    <section data-testid="edit-job-process-section">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Etapas do Processo Seletivo</h3>
          {(formData.interviewStages || []).length > 0 && (
            <Chip density="relaxed" variant="neutral" className="bg-lia-bg-tertiary border-lia-border-default text-lia-text-secondary">
              {(formData.interviewStages || []).length} etapas
            </Chip>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ClipboardList className="w-3.5 h-3.5 text-lia-text-disabled" />
          <Select
            value={selectedTemplateId}
            onValueChange={(value) => {
              if (value && value !== 'none') applyPipelineTemplate(value)
            }}
          >
            <SelectTrigger className="h-8 w-[180px] text-xs bg-lia-bg-secondary border-lia-border-subtle">
              {isLoadingTemplates ? (
                <span className="flex items-center gap-1.5">
                  <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                  Carregando...
                </span>
              ) : (
                <SelectValue placeholder="Usar modelo" />
              )}
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none" className="text-xs text-lia-text-disabled">Selecionar template...</SelectItem>
              {pipelineTemplates.map(template => (
                <SelectItem key={template.id} value={template.id} className="text-xs">
                  <div className="flex items-center gap-2">
                    {template.is_default && <Chip variant="neutral" className="text-micro px-1 py-0 h-4">Padrão</Chip>}
                    {template.name}
                    <span className="text-lia-text-disabled">({template.stages.length} etapas)</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {(formData.interviewStages || []).map((stage: InterviewStage, idx: number) => (
          <div key={idx} className="flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
            <div className="flex items-center justify-center w-7 h-7 rounded-full bg-lia-bg-tertiary text-lia-text-secondary text-sm font-semibold shrink-0">
              {stage.order || idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <Input
                value={stage.stageName || ''}
                onChange={(e) => updateInterviewStage(idx, 'stageName', e.target.value)}
                className="h-8 text-sm bg-lia-bg-primary border-lia-border-subtle focus:border-lia-border-medium"
                placeholder="Nome da etapa"
              />
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <div className="flex items-center gap-1">
                <span className="text-xs text-lia-text-tertiary">SLA:</span>
                <Select value={String(stage.sla || 3)} onValueChange={(v) => updateInterviewStage(idx, 'sla', parseInt(v))}>
                  <SelectTrigger className="h-8 w-16 text-xs bg-lia-bg-secondary border-lia-border-subtle">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 5, 7, 10, 14].map(d => (
                      <SelectItem key={d} value={String(d)} className="text-xs">{d}d</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Select value={stage.type || 'manual'} onValueChange={(v) => updateInterviewStage(idx, 'type', v)}>
                <SelectTrigger className="h-8 w-24 text-xs bg-lia-bg-secondary border-lia-border-subtle">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="automated" className="text-xs">Auto</SelectItem>
                  <SelectItem value="manual" className="text-xs">Manual</SelectItem>
                  <SelectItem value="hybrid" className="text-xs">Híbrido</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 hover:bg-status-error/10"
                onClick={() => removeInterviewStage(idx)}
              >
                <Trash2 className="w-3.5 h-3.5 text-status-error" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 items-end">
        <div className="flex-1">
          <Input
            value={newInterviewStageName}
            onChange={(e) => setNewInterviewStageName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addInterviewStage())}
            className={inputStyle}
            placeholder="Nova etapa (ex: Entrevista Técnica)"
          />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs text-lia-text-tertiary">SLA:</span>
          <Select value={newInterviewStageSLA} onValueChange={setNewInterviewStageSLA}>
            <SelectTrigger className="h-10 w-16 text-xs bg-lia-bg-secondary border-lia-border-subtle">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 5, 7, 10, 14].map(d => (
                <SelectItem key={d} value={String(d)} className="text-xs">{d}d</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Select value={newInterviewStageType} onValueChange={setNewInterviewStageType}>
          <SelectTrigger className="h-10 w-24 text-xs bg-lia-bg-secondary border-lia-border-subtle">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="automated" className="text-xs">Auto</SelectItem>
            <SelectItem value="manual" className="text-xs">Manual</SelectItem>
            <SelectItem value="hybrid" className="text-xs">Híbrido</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          className="h-10 px-4 text-sm border-lia-btn-primary-bg text-lia-text-primary hover:bg-lia-interactive-hover"
          onClick={addInterviewStage}
        >
          <Plus className="w-4 h-4 mr-1.5" />
          Adicionar
        </Button>
      </div>
    </section>
  )
}
