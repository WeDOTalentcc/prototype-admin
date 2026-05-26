"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Chip } from "@/components/ui/chip"
import { Label } from"@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  DollarSign,
  Layers,
  Heart,
  CheckCircle,
  Plus,
  Trash2,
  Loader2,
  ClipboardList,
  TrendingUp,
} from"lucide-react"
import {
  inputStyle,
} from '../edit-job-modal.constants'
import type { InterviewStage, PipelineTemplate, Job } from '../edit-job/edit-job.types'
import type { CompanyBenefit } from '@/types/benefits'

type BenefitItem = string | { id: string; name: string }

function benefitName(b: BenefitItem): string {
  return typeof b === 'string' ? b : b.name
}

function isBenefitAdded(benefits: BenefitItem[], candidate: CompanyBenefit): boolean {
  return benefits.some(b =>
    typeof b === 'string'
      ? b === candidate.name
      : (b as { id: string }).id === candidate.id
  )
}

interface EditJobModalRequirementsProps {
  formData: Partial<Job>
  setFormData: React.Dispatch<React.SetStateAction<Partial<Job>>>
  newBenefit: string
  setNewBenefit: (v: string) => void
  companyBenefits: CompanyBenefit[]
  addBenefit: () => void
  removeBenefit: (idx: number) => void
  activeCompensationPolicies: { id: string; name: string; policy_type?: string }[]
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

export function EditJobModalRequirements({
  formData,
  setFormData,
  newBenefit,
  setNewBenefit,
  companyBenefits,
  addBenefit,
  removeBenefit,
  activeCompensationPolicies,
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
}: EditJobModalRequirementsProps) {
  const benefits = (formData.benefits || []) as BenefitItem[]

  return (
    <>
      <section data-testid="edit-job-requirements-section">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-4 h-4 text-lia-text-secondary" />
          <h3 className="text-base-ui font-semibold text-lia-text-primary">Remuneração</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Faixa Salarial</Label>
            <div className="flex gap-3">
              <div className="flex-1">
                <span className="text-micro text-lia-text-tertiary mb-1 block">De</span>
                <Input
                  type="number"
                  value={formData.salaryMin || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, salaryMin: Number(e.target.value) }))}
                  className={inputStyle}
                  placeholder="12.000"
                />
              </div>
              <div className="flex-1">
                <span className="text-micro text-lia-text-tertiary mb-1 block">Até</span>
                <Input
                  type="number"
                  value={formData.salaryMax || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, salaryMax: Number(e.target.value) }))}
                  className={inputStyle}
                  placeholder="18.000"
                />
              </div>
            </div>
          </div>

          <div>
            <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Bônus Anual (opcional)</Label>
            <div className="flex gap-3">
              <div className="flex-1">
                <span className="text-micro text-lia-text-tertiary mb-1 block">De</span>
                <Input
                  type="number"
                  value={formData.bonusMin || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, bonusMin: Number(e.target.value) }))}
                  className={inputStyle}
                  placeholder="2.000"
                />
              </div>
              <div className="flex-1">
                <span className="text-micro text-lia-text-tertiary mb-1 block">Até</span>
                <Input
                  type="number"
                  value={formData.bonusMax || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, bonusMax: Number(e.target.value) }))}
                  className={inputStyle}
                  placeholder="6.000"
                />
              </div>
            </div>
          </div>

          {activeCompensationPolicies.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
                <Label className="text-xs font-medium text-lia-text-primary">Política de Remuneração Variável (opcional)</Label>
              </div>
              <Select
                value={formData.compensation_policy_id || 'none'}
                onValueChange={(v) =>
                  setFormData(prev => ({ ...prev, compensation_policy_id: v === 'none' ? undefined : v }))
                }
              >
                <SelectTrigger className="h-10 w-full text-sm bg-lia-bg-secondary border-lia-border-subtle">
                  <SelectValue placeholder="Nenhuma política vinculada" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none" className="text-xs text-lia-text-disabled">Nenhuma</SelectItem>
                  {activeCompensationPolicies.map(p => (
                    <SelectItem key={p.id} value={p.id} className="text-xs">
                      {p.name}
                      {p.policy_type && (
                        <span className="ml-2 text-lia-text-tertiary">({p.policy_type})</span>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {formData.compensation_policy_id && (
                <p className="text-micro text-lia-text-tertiary mt-1">
                  PRV desta política será referência para bônus e verbas variáveis.
                  {/* TODO(WIZARD-INT:005): Botão "Sugerir pacote com LIA" */}
                </p>
              )}
            </div>
          )}

          <div>
            <Label className="text-xs text-lia-text-secondary mb-2 block">Benefícios</Label>
            <div className="flex flex-wrap gap-2 mb-3">
              {benefits.map((benefit, idx) => (
                <Chip
                  key={idx}
                  variant="neutral"
                  className="flex items-center gap-1 py-0.5 px-2 text-xs bg-lia-bg-primary"
                >
                  <button
                    onClick={() => removeBenefit(idx)}
                    className="text-lia-text-secondary hover:text-status-error dark:hover:text-status-error mr-0.5"
                    type="button"
                  >
                    ×
                  </button>
                  {benefitName(benefit)}
                  {companyBenefits.find(cb => cb.name === benefitName(benefit))?.is_highlighted && (
                    <Heart className="w-3 h-3 text-wedo-magenta fill-pink-500" />
                  )}
                </Chip>
              ))}
            </div>
            {companyBenefits.length > 0 && (
              <div className="mb-3">
                <Label className="text-xs text-lia-text-tertiary mb-1.5 block">Sugestões da empresa</Label>
                <div className="flex flex-wrap gap-1.5">
                  {companyBenefits.map((benefit) => {
                    const isAdded = isBenefitAdded(benefits, benefit)
                    return (
                      <Chip
                        key={benefit.id}
                        variant="neutral"
                        className={`text-xs px-2 py-0.5 cursor-pointer transition-colors motion-reduce:transition-none ${
                          isAdded 
                            ? 'bg-lia-bg-tertiary border-lia-btn-primary-bg text-lia-text-primary' 
                            : 'bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary hover:bg-lia-interactive-hover hover:border-lia-border-medium hover:text-lia-text-primary'
                        }`}
                        onClick={() => {
                          if (!isAdded) {
                            setFormData(prev => ({
                              ...prev,
                              benefits: [...((prev.benefits || []) as BenefitItem[]), { id: benefit.id, name: benefit.name }]
                            }))
                          }
                        }}
                      >
                        {isAdded && <CheckCircle className="w-3 h-3 mr-1" />}
                        {benefit.is_highlighted && <Heart className="w-3 h-3 mr-1 text-wedo-magenta" />}
                        {benefit.name}
                        {!isAdded && <Plus className="w-3 h-3 ml-1" />}
                      </Chip>
                    )
                  })}
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <Input
                value={newBenefit}
                onChange={(e) => setNewBenefit(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addBenefit())}
                className={`${inputStyle} flex-1`}
                placeholder="Ex: Vale Refeição, Plano de Saúde..."
              />
              <Button
                variant="outline"
                className="h-10 px-4 text-sm border-lia-btn-primary-bg text-lia-text-primary hover:bg-lia-interactive-hover"
                onClick={addBenefit}
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Adicionar
              </Button>
            </div>
          </div>
        </div>
      </section>

      <hr className="border-lia-border-subtle" />

      <section>
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
                if (value && value !== 'none') {
                  applyPipelineTemplate(value)
                }
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
                  <Select 
                    value={String(stage.sla || 3)} 
                    onValueChange={(v) => updateInterviewStage(idx, 'sla', parseInt(v))}
                  >
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
                <Select 
                  value={stage.type || 'manual'} 
                  onValueChange={(v) => updateInterviewStage(idx, 'type', v)}
                >
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
              className={`${inputStyle}`}
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
    </>
  )
}
