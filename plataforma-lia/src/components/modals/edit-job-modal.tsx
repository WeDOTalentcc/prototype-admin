"use client"

import React from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  X,
  Briefcase,
  Users,
  Calendar,
  FileText,
  DollarSign,
  Layers,
  Settings,
  Plus,
  Trash2,
  GripVertical,
  Building,
  Save,
  Shield,
  Globe,
  Lock,
  AlertTriangle,
  Heart,
  Linkedin,
  ExternalLink,
  CheckCircle,
  Target,
  Languages,
  UserPlus,
  Code,
  Brain,
  HelpCircle,
  Download,
  Check,
  Loader2,
  ClipboardList,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import { liaApi, type JobVacancy } from "@/services/lia-api"
import type { CompanyBenefit } from '@/types/benefits'
import {
  WORK_MODELS,
  CONTRACT_TYPES,
  SENIORITY_LEVELS,
  STATUS_OPTIONS,
  STAGE_OPTIONS,
  VISIBILITY_OPTIONS,
  TECH_CATEGORIES,
  SKILL_LEVELS,
  COMPETENCY_WEIGHTS,
  inputStyle,
  selectTriggerStyle,
} from './edit-job-modal.constants'

import type { InterviewStage, PipelineTemplate, Job, EditJobModalProps, CompanyDefaultQuestion } from './edit-job/edit-job.types'
import { useEditJob } from './edit-job/useEditJob'

export function EditJobModal({ isOpen, onClose, job, onSave }: EditJobModalProps) {
  const {
    formData,
    setFormData,
    isSaving,
    newRequirement,
    setNewRequirement,
    newBenefit,
    setNewBenefit,
    newStage,
    newAccessEmail,
    setNewAccessEmail,
    newLanguage,
    setNewLanguage,
    newLanguageLevel,
    setNewLanguageLevel,
    newTechSkill,
    newTechCategory,
    newTechLevel,
    newBehavioralSkill,
    newBehavioralWeight,
    newQuestion,
    newQuestionCategory,
    newInterviewStageName,
    setNewInterviewStageName,
    newInterviewStageSLA,
    setNewInterviewStageSLA,
    newInterviewStageType,
    setNewInterviewStageType,
    companyDepartments,
    companyBenefits,
    showImportQuestionsModal,
    setShowImportQuestionsModal,
    companyDefaultQuestions,
    selectedDefaultQuestions,
    isLoadingDefaultQuestions,
    pipelineTemplates,
    isLoadingTemplates,
    selectedTemplateId,
    updateField,
    addRequirement,
    removeRequirement,
    addBenefit,
    removeBenefit,
    addStage,
    removeStage,
    addInterviewStage,
    removeInterviewStage,
    updateInterviewStage,
    addAccessEmail,
    removeAccessEmail,
    addLanguage,
    removeLanguage,
    addTechnicalSkill,
    removeTechnicalSkill,
    addBehavioralSkill,
    removeBehavioralSkill,
    addScreeningQuestion,
    removeScreeningQuestion,
    fetchCompanyDefaultQuestions,
    openImportQuestionsModal,
    toggleQuestionSelection,
    importSelectedQuestions,
    getCategoryLabel,
    getCategoryColor,
    getWeightColor,
    handleSave,
    applyPipelineTemplate,
    fetchPipelineTemplates,
  } = useEditJob({ isOpen, job, onSave, onClose })

  if (!isOpen || !job) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/50 dark:bg-lia-bg-primary/70 backdrop-blur-[2px]"
        onClick={onClose}
      />
      
      <div className="relative bg-white dark:bg-lia-bg-secondary rounded-md w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gray-100 dark:bg-lia-bg-elevated flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">Editar Vaga</h2>
              <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5">
                <span className="text-lia-text-secondary font-medium mr-1.5">{job.jobId}</span>
                {job.title}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 rounded-md hover:bg-gray-100"
            onClick={onClose}
          >
            <X className="w-4 h-4 text-lia-text-tertiary" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
              <div className="space-y-6">
                
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Briefcase className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Informações Básicas</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Título da Vaga</Label>
                      <Input
                        value={formData.title || ''}
                        onChange={(e) => updateField('title', e.target.value)}
                        className={inputStyle}
                        placeholder="Ex: Desenvolvedor Full Stack"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Departamento</Label>
                        {companyDepartments.length > 0 ? (
                          <Select 
                            value={formData.department || ''} 
                            onValueChange={(v) => updateField('department', v)}
                          >
                            <SelectTrigger className={selectTriggerStyle}>
                              <SelectValue placeholder="Selecione um departamento" />
                            </SelectTrigger>
                            <SelectContent>
                              {companyDepartments.map(dept => (
                                <SelectItem key={dept.id} value={dept.name} className="text-sm">
                                  {dept.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={formData.department || ''}
                            onChange={(e) => updateField('department', e.target.value)}
                            className={inputStyle}
                            placeholder="Ex: Tecnologia"
                          />
                        )}
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Localização</Label>
                        <Input
                          value={formData.location || ''}
                          onChange={(e) => updateField('location', e.target.value)}
                          className={inputStyle}
                          placeholder="Ex: São Paulo, SP"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Modelo de Trabalho</Label>
                        <Select value={formData.workModel} onValueChange={(v) => updateField('workModel', v as Job['workModel'])}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {WORK_MODELS.map(m => (
                              <SelectItem key={m.value} value={m.value} className="text-sm">{m.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Tipo de Contrato</Label>
                        <Select value={formData.type} onValueChange={(v) => updateField('type', v)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {CONTRACT_TYPES.map(t => (
                              <SelectItem key={t.value} value={t.value} className="text-sm">{t.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Senioridade</Label>
                        <Select value={formData.level} onValueChange={(v) => updateField('level', v)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {SENIORITY_LEVELS.map(l => (
                              <SelectItem key={l.value} value={l.value} className="text-sm">{l.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Users className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Pessoas Responsáveis</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
                      <p className="text-xs font-medium uppercase text-lia-text-secondary mb-2">Recrutador(a)</p>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Nome</Label>
                          <Input
                            value={formData.recruiter || ''}
                            onChange={(e) => updateField('recruiter', e.target.value)}
                            className={`${inputStyle} bg-lia-bg-secondary`}
                            placeholder="Nome do recrutador"
                          />
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">E-mail</Label>
                          <Input
                            value={formData.recruiterEmail || ''}
                            onChange={(e) => updateField('recruiterEmail', e.target.value)}
                            className={`${inputStyle} bg-lia-bg-secondary`}
                            placeholder="email@empresa.com"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
                      <p className="text-xs font-medium uppercase text-lia-text-secondary mb-2">Gestor(a) Solicitante</p>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Nome</Label>
                          <Input
                            value={formData.manager || ''}
                            onChange={(e) => updateField('manager', e.target.value)}
                            className={`${inputStyle} bg-lia-bg-secondary`}
                            placeholder="Nome do gestor"
                          />
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">E-mail</Label>
                          <Input
                            value={formData.managerEmail || ''}
                            onChange={(e) => updateField('managerEmail', e.target.value)}
                            className={`${inputStyle} bg-lia-bg-secondary`}
                            placeholder="email@empresa.com"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <Calendar className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Timeline do Processo</h3>
                  </div>
                  
                  <div className="relative pl-4 border-l-2 border-lia-border-default space-y-4">
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-status-success border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                          <span className="text-status-success font-medium">1.</span> Data de Abertura
                        </Label>
                        <Input
                          type="date"
                          value={formData.openDate || ''}
                          onChange={(e) => updateField('openDate', e.target.value)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                    
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-cyan border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                          <span className="text-wedo-cyan-dark font-medium">2.</span> Prazo Screening
                          <span className="text-micro text-lia-text-disabled">(triagem inicial)</span>
                        </Label>
                        <Input
                          type="date"
                          value={formData.deadlineScreening || ''}
                          onChange={(e) => updateField('deadlineScreening', e.target.value)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                    
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-purple border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                          <span className="text-wedo-purple font-medium">3.</span> Prazo Shortlist
                          <span className="text-micro text-lia-text-disabled">(lista curta)</span>
                        </Label>
                        <Input
                          type="date"
                          value={formData.deadlineShortlist || ''}
                          onChange={(e) => updateField('deadlineShortlist', e.target.value)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                    
                    <div className="relative">
                      <div className="absolute -left-[21px] w-3 h-3 rounded-full bg-wedo-orange border-2 border-white" />
                      <div className="ml-4">
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-wedo-orange" />
                          <span className="text-wedo-orange font-medium">4.</span> Prazo Final
                        </Label>
                        <Input
                          type="date"
                          value={formData.deadline || ''}
                          onChange={(e) => updateField('deadline', e.target.value)}
                          className={`${inputStyle} w-48`}
                        />
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <FileText className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Descrição</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Descrição da Vaga</Label>
                      <Textarea
                        value={formData.description || ''}
                        onChange={(e) => updateField('description', e.target.value)}
                        className="min-h-[100px] text-sm resize-none bg-gray-50 border-lia-border-subtle focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20"
                        placeholder="Descreva as responsabilidades, objetivos e contexto da vaga..."
                      />
                    </div>

                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
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
                            onChange={(e) => updateField('salaryMin', Number(e.target.value))}
                            className={inputStyle}
                            placeholder="12.000"
                          />
                        </div>
                        <div className="flex-1">
                          <span className="text-micro text-lia-text-tertiary mb-1 block">Até</span>
                          <Input
                            type="number"
                            value={formData.salaryMax || ''}
                            onChange={(e) => updateField('salaryMax', Number(e.target.value))}
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
                            onChange={(e) => updateField('bonusMin', Number(e.target.value))}
                            className={inputStyle}
                            placeholder="2.000"
                          />
                        </div>
                        <div className="flex-1">
                          <span className="text-micro text-lia-text-tertiary mb-1 block">Até</span>
                          <Input
                            type="number"
                            value={formData.bonusMax || ''}
                            onChange={(e) => updateField('bonusMax', Number(e.target.value))}
                            className={inputStyle}
                            placeholder="6.000"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs text-lia-text-secondary mb-2 block">Benefícios</Label>
                      <div className="flex flex-wrap gap-2 mb-3">
                        {(formData.benefits || []).map((benefit, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="flex items-center gap-1 py-0.5 px-2 text-xs bg-white dark:bg-lia-bg-primary"
                          >
                            <button
                              onClick={() => removeBenefit(idx)}
                              className="text-lia-text-secondary dark:text-lia-text-tertiary hover:text-status-error dark:hover:text-status-error mr-0.5"
                              type="button"
                            >
                              ×
                            </button>
                            {benefit}
                            {companyBenefits.find(cb => cb.name === benefit)?.is_highlighted && (
                              <Heart className="w-3 h-3 text-wedo-magenta fill-pink-500" />
                            )}
                          </Badge>
                        ))}
                      </div>
                      {companyBenefits.length > 0 && (
                        <div className="mb-3">
                          <Label className="text-xs text-lia-text-tertiary mb-1.5 block">Sugestões da empresa</Label>
                          <div className="flex flex-wrap gap-1.5">
                            {companyBenefits.map((benefit) => {
                              const isAdded = (formData.benefits || []).includes(benefit.name)
                              return (
                                <Badge
                                  key={benefit.id}
                                  variant="outline"
                                  className={`text-xs px-2 py-0.5 cursor-pointer transition-colors ${
                                    isAdded 
                                      ? 'bg-gray-100 border-gray-900 text-lia-text-primary' 
                                      : 'bg-gray-50 border-lia-border-subtle text-lia-text-secondary hover:bg-gray-100 hover:border-gray-400 hover:text-lia-text-primary'
                                  }`}
                                  onClick={() => {
                                    if (!isAdded) {
                                      setFormData(prev => ({
                                        ...prev,
                                        benefits: [...(prev.benefits || []), benefit.name]
                                      }))
                                    }
                                  }}
                                >
                                  {isAdded && <CheckCircle className="w-3 h-3 mr-1" />}
                                  {benefit.is_highlighted && <Heart className="w-3 h-3 mr-1 text-wedo-magenta" />}
                                  {benefit.name}
                                  {!isAdded && <Plus className="w-3 h-3 ml-1" />}
                                </Badge>
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
                          className="h-10 px-4 text-sm border-gray-900 text-lia-text-primary hover:bg-gray-100"
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
                        <Badge variant="outline" className="text-xs bg-gray-100 border-lia-border-default text-lia-text-secondary">
                          {(formData.interviewStages || []).length} etapas
                        </Badge>
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
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Carregando...
                            </span>
                          ) : (
                            <SelectValue placeholder="Usar template" />
                          )}
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none" className="text-xs text-lia-text-disabled">Selecionar template...</SelectItem>
                          {pipelineTemplates.map(template => (
                            <SelectItem key={template.id} value={template.id} className="text-xs">
                              <div className="flex items-center gap-2">
                                {template.is_default && <Badge variant="outline" className="text-micro px-1 py-0 h-4">Padrão</Badge>}
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
                      <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
                        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-gray-100 text-lia-text-secondary text-sm font-semibold shrink-0">
                          {stage.order || idx + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <Input
                            value={stage.stageName || ''}
                            onChange={(e) => updateInterviewStage(idx, 'stageName', e.target.value)}
                            className="h-8 text-sm bg-lia-bg-primary border-lia-border-subtle focus:border-gray-400"
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
                        <SelectTrigger className="h-10 w-16 text-xs bg-gray-50 border-lia-border-subtle">
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
                      <SelectTrigger className="h-10 w-24 text-xs bg-gray-50 border-lia-border-subtle">
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
                      className="h-10 px-4 text-sm border-gray-900 text-lia-text-primary hover:bg-gray-100"
                      onClick={addInterviewStage}
                    >
                      <Plus className="w-4 h-4 mr-1.5" />
                      Adicionar
                    </Button>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                {/* NEW: Configuração de Confidencialidade para LIA */}
                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Shield className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Configuração de Confidencialidade para LIA</h3>
                  </div>
                  
                  <p className="text-xs text-lia-text-tertiary mb-3">
                    Configure o que a LIA pode ou não revelar durante conversas com candidatos.
                  </p>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <Building className="w-3.5 h-3.5 text-lia-text-tertiary" />
                        <span className="text-xs text-lia-text-secondary">LIA pode revelar o nome da empresa?</span>
                      </div>
                      <Switch
                        checked={(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_reveal_company_name ?? true}
                        onCheckedChange={(checked: boolean) => {
                          updateField('confidentialityConfig', {
                            ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                            can_reveal_company_name: checked
                          } as Job['confidentialityConfig'])
                        }}
                      />
                    </div>

                    {!(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_reveal_company_name && (
                      <div className="ml-4 p-2 bg-status-warning/10 rounded-md border border-status-warning/30">
                        <Label className="text-xs text-status-warning mb-1.5 block">
                          Apresentação mascarada para candidatos:
                        </Label>
                        <Input
                          value={(formData.confidentialityConfig as Job['confidentialityConfig'])?.masked_intro || ''}
                          onChange={(e) => {
                            updateField('confidentialityConfig', {
                              ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                              masked_intro: e.target.value
                            } as Job['confidentialityConfig'])
                          }}
                          className="h-8 text-xs bg-lia-bg-primary border-status-warning/30"
                          placeholder="Uma empresa líder no segmento de pagamentos"
                        />
                      </div>
                    )}

                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-3.5 h-3.5 text-lia-text-tertiary" />
                        <span className="text-xs text-lia-text-secondary">LIA pode discutir faixa salarial?</span>
                      </div>
                      <Switch
                        checked={(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_discuss_salary ?? true}
                        onCheckedChange={(checked: boolean) => {
                          updateField('confidentialityConfig', {
                            ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                            can_discuss_salary: checked
                          } as Job['confidentialityConfig'])
                        }}
                      />
                    </div>

                    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <Heart className="w-3.5 h-3.5 text-lia-text-tertiary" />
                        <span className="text-xs text-lia-text-secondary">LIA pode discutir benefícios?</span>
                      </div>
                      <Switch
                        checked={(formData.confidentialityConfig as Job['confidentialityConfig'])?.can_discuss_benefits ?? true}
                        onCheckedChange={(checked: boolean) => {
                          updateField('confidentialityConfig', {
                            ...((formData.confidentialityConfig || {}) as Job['confidentialityConfig']),
                            can_discuss_benefits: checked
                          } as Job['confidentialityConfig'])
                        }}
                      />
                    </div>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Settings className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Status e Configurações</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Status</Label>
                        <Select value={formData.status} onValueChange={(v) => updateField('status', v)}>
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {STATUS_OPTIONS.map(s => (
                              <SelectItem key={s.value} value={s.value} className="text-sm">{s.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Urgência</Label>
                        <Select 
                          value={String(formData.urgencyLevel)} 
                          onValueChange={(v) => updateField('urgencyLevel', parseInt(v) as Job['urgencyLevel'])}
                        >
                          <SelectTrigger className={selectTriggerStyle}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {[1, 2, 3, 4, 5].map(n => (
                              <SelectItem key={n} value={String(n)} className="text-sm">
                                {n} - {n === 1 ? 'Baixa' : n === 2 ? 'Normal' : n === 3 ? 'Média' : n === 4 ? 'Alta' : 'Crítica'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Visibilidade</Label>
                      <Select value={formData.visibility} onValueChange={(v) => updateField('visibility', v as Job['visibility'])}>
                        <SelectTrigger className={selectTriggerStyle}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {VISIBILITY_OPTIONS.map(v => (
                            <SelectItem key={v.value} value={v.value} className="text-sm">
                              <div className="flex items-center gap-2">
                                {v.icon}
                                {v.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-md border border-lia-border-subtle space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4 text-wedo-orange" />
                          <span className="text-sm text-lia-text-secondary">Vaga Confidencial</span>
                        </div>
                        <Switch
                          checked={formData.isConfidential || false}
                          onCheckedChange={(checked: boolean) => updateField('isConfidential', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-wedo-magenta" />
                          <span className="text-sm text-lia-text-secondary">Vaga Afirmativa</span>
                        </div>
                        <Switch
                          checked={formData.isAffirmative || false}
                          onCheckedChange={(checked: boolean) => { updateField('isAffirmative', checked); if (!checked) updateField('affirmativeType', undefined); }}
                        />
                      </div>
                      {formData.isAffirmative && (
                        <div className="space-y-3 mt-3 p-4 bg-wedo-purple/10 rounded-md border border-wedo-purple/30">
                          <div>
                            <Label className="text-xs font-medium text-lia-text-primary mb-2 block">Tipo de Ação Afirmativa</Label>
                            <div className="grid grid-cols-2 gap-2">
                              {[
                                { value: 'pcd', label: 'PCD', desc: 'Pessoas com Deficiência' },
                                { value: 'racial', label: 'Racial', desc: 'Pessoas negras (pretas e pardas)' },
                                { value: 'gender', label: 'Gênero', desc: 'Mulheres' },
                                { value: 'age', label: '50+', desc: 'Profissionais 50+' },
                                { value: 'lgbtqia+', label: 'LGBTQIA+', desc: 'Pessoas LGBTQIA+' },
                              ].map((option) => (
                                <div
                                  key={option.value}
                                  className={cn(
                                    "p-2.5 rounded-md border cursor-pointer transition-colors",
                                    formData.affirmativeType === option.value
                                      ? "border-wedo-purple/30 bg-wedo-purple/15"
                                      : "border-wedo-purple/30 bg-lia-bg-primary hover:border-wedo-purple/30"
                                  )}
                                  onClick={() => updateField('affirmativeType', formData.affirmativeType === option.value ? undefined : option.value as Job['affirmativeType'])}
                                >
                                  <span className="text-xs font-medium text-lia-text-primary block">{option.label}</span>
                                  <span className="text-micro text-lia-text-tertiary">{option.desc}</span>
                                </div>
                              ))}
                            </div>
                            <p className="text-micro text-lia-text-tertiary mt-2">A LIA incluirá uma pergunta de autodeclaração na triagem WSI</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {formData.isConfidential && (
                      <div className="space-y-4 mt-4 p-4 bg-wedo-orange/10 rounded-md border border-wedo-orange/30">
                        <div>
                          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Nome Mascarado da Empresa</Label>
                          <Input
                            value={formData.maskedCompanyName || ''}
                            onChange={(e) => updateField('maskedCompanyName', e.target.value)}
                            className={inputStyle}
                            placeholder="Ex: Empresa líder no segmento de tecnologia"
                          />
                          <p className="text-xs text-lia-text-tertiary mt-1">Nome exibido em publicações anônimas</p>
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Lista de Acesso</Label>
                          <div className="flex gap-2 mb-2">
                            <Input
                              value={newAccessEmail}
                              onChange={(e) => setNewAccessEmail(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAccessEmail())}
                              className={inputStyle + " flex-1"}
                              placeholder="email@empresa.com"
                            />
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={addAccessEmail}
                              className="h-9 px-3"
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {(formData.accessList || []).map((email, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs py-1 px-2 bg-lia-bg-primary border border-lia-border-subtle">
                                <UserPlus className="w-3 h-3 mr-1 text-lia-text-disabled" />
                                {email}
                                <button
                                  onClick={() => removeAccessEmail(idx)}
                                  className="ml-1.5 text-lia-text-disabled hover:text-status-error"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </Badge>
                            ))}
                          </div>
                          <p className="text-xs text-lia-text-tertiary mt-1">Usuários com acesso à vaga confidencial</p>
                        </div>
                      </div>
                    )}
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Globe className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Publicação</h3>
                  </div>
                  
                  <div className="p-4 bg-gray-50 rounded-md border border-lia-border-subtle space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                        <span className="text-sm text-lia-text-secondary">LinkedIn</span>
                      </div>
                      <Switch
                        checked={formData.publishedLinkedIn || false}
                        onCheckedChange={(checked: boolean) => updateField('publishedLinkedIn', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-status-success" />
                        <span className="text-sm text-lia-text-secondary">Website Corporativo</span>
                      </div>
                      <Switch
                        checked={formData.publishedWebsite || false}
                        onCheckedChange={(checked: boolean) => updateField('publishedWebsite', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-4 h-4 text-wedo-purple" />
                        <span className="text-sm text-lia-text-secondary">Indeed</span>
                      </div>
                      <Switch
                        checked={formData.publishedIndeed || false}
                        onCheckedChange={(checked: boolean) => updateField('publishedIndeed', checked)}
                      />
                    </div>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                {/* Informações do Registro (Read-only) */}
                {(job?.createdBy || job?.createdAt) && (
                  <section>
                    <div className="flex items-center gap-2 mb-4">
                      <Users className="w-4 h-4 text-lia-text-disabled" />
                      <h3 className="text-xs font-semibold text-lia-text-tertiary">Informações do Registro</h3>
                      <Badge variant="outline" className="text-micro px-1.5 py-0 h-4 bg-gray-50 text-lia-text-disabled border-lia-border-subtle">
                        Somente leitura
                      </Badge>
                    </div>
                    
                    <div className="p-4 bg-gray-50 rounded-md border border-lia-border-subtle">
                      <div className="grid grid-cols-2 gap-4">
                        {job?.createdBy && (
                          <div>
                            <Label className="text-xs text-lia-text-tertiary mb-1 block">Criado por</Label>
                            <div className="text-sm text-lia-text-secondary font-medium">{job.createdBy}</div>
                            {job?.createdByEmail && (
                              <div className="text-xs text-lia-text-tertiary">{job.createdByEmail}</div>
                            )}
                          </div>
                        )}
                        {job?.createdAt && (
                          <div>
                            <Label className="text-xs text-lia-text-tertiary mb-1 block">Data de Criação</Label>
                            <div className="text-sm text-lia-text-secondary">
                              {new Date(job.createdAt).toLocaleDateString('pt-BR', { 
                                day: '2-digit', 
                                month: 'long', 
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </section>
                )}

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Público-Alvo & Segmentação</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <Textarea
                      value={formData.targetAudience || ''}
                      onChange={(e) => updateField('targetAudience', e.target.value)}
                      className="min-h-20 text-sm resize-none bg-gray-50 border-lia-border-subtle focus:border-gray-400 focus:ring-1 focus:ring-gray-900/20"
                      placeholder="Descreva o perfil ideal de candidato para esta vaga..."
                    />
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Setor-Alvo</Label>
                        <Input
                          value={formData.targetSector || ''}
                          onChange={(e) => updateField('targetSector', e.target.value)}
                          className={inputStyle}
                          placeholder="Ex: Fintechs, Bancos Digitais"
                        />
                      </div>
                      <div>
                        <Label className="text-xs font-medium text-lia-text-primary mb-1 block">Segmento-Alvo</Label>
                        <Input
                          value={formData.targetSegment || ''}
                          onChange={(e) => updateField('targetSegment', e.target.value)}
                          className={inputStyle}
                          placeholder="Ex: Meios de Pagamento"
                        />
                      </div>
                    </div>
                  </div>
                </section>

                <hr className="border-lia-border-subtle" />

                <section>
                  <div className="flex items-center gap-2 mb-4">
                    <Languages className="w-4 h-4 text-lia-text-secondary" />
                    <h3 className="text-base-ui font-semibold text-lia-text-primary">Idiomas Requeridos</h3>
                    <span className="inline-flex items-center gap-1 text-xs text-lia-text-tertiary" title="Idiomas padrão vindos das configurações">
                      <Settings className="w-3 h-3" />
                      Settings
                    </span>
                  </div>
                  
                  <div className="flex gap-2 mb-2">
                    <Input
                      value={newLanguage}
                      onChange={(e) => setNewLanguage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addLanguage())}
                      className={inputStyle + " flex-1"}
                      placeholder="Ex: Inglês"
                    />
                    <Select value={newLanguageLevel} onValueChange={setNewLanguageLevel}>
                      <SelectTrigger className="w-32 h-9 text-xs bg-gray-50 border-lia-border-subtle">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Básico">Básico</SelectItem>
                        <SelectItem value="Intermediário">Intermediário</SelectItem>
                        <SelectItem value="Avançado">Avançado</SelectItem>
                        <SelectItem value="Fluente">Fluente</SelectItem>
                        <SelectItem value="Nativo">Nativo</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={addLanguage}
                      className="h-9 px-3"
                    >
                      <Plus className="w-3 h-3" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(formData.languages || []).map((lang, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs py-1 px-2 bg-wedo-purple/10 text-wedo-purple border border-wedo-purple/30">
                        {lang.language} ({lang.level})
                        <button
                          onClick={() => removeLanguage(idx)}
                          className="ml-1.5 text-wedo-purple hover:text-status-error"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </section>

              </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle shrink-0">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-white border border-lia-border-default hover:bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-gray-700 text-lia-text-secondary dark:text-lia-text-primary"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Salvar Alterações
              </>
            )}
          </Button>
        </div>
      </div>

      {showImportQuestionsModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-lia-bg-primary/70 flex items-center justify-center z-overlay p-4">
          <div className="bg-white dark:bg-lia-bg-secondary rounded-md max-w-lg w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4 text-status-warning" />
                <h3 className="text-base-ui font-semibold text-lia-text-primary">Importar Perguntas Padrão</h3>
              </div>
              <button
                onClick={() => setShowImportQuestionsModal(false)}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5">
              {isLoadingDefaultQuestions ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-status-warning" />
                  <span className="ml-2 text-sm text-lia-text-secondary">Carregando perguntas...</span>
                </div>
              ) : companyDefaultQuestions.length === 0 ? (
                <div className="text-center py-8">
                  <HelpCircle className="w-10 h-10 text-lia-text-disabled mx-auto mb-3" />
                  <p className="text-sm text-lia-text-tertiary">Nenhuma pergunta padrão encontrada.</p>
                  <p className="text-xs text-lia-text-disabled mt-1">Configure perguntas padrão nas Configurações da empresa.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {companyDefaultQuestions.map((q) => (
                    <label
                      key={q.id}
                      className={`flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                        selectedDefaultQuestions.has(q.id)
                          ? 'bg-status-warning/10 border-status-warning/30'
                          : 'bg-lia-bg-primary border-lia-border-subtle hover:border-lia-border-default'
                      }`}
                    >
                      <div className="mt-0.5">
                        <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors ${
                          selectedDefaultQuestions.has(q.id)
                            ? 'bg-status-warning border-status-warning/30'
                            : 'border-lia-border-default'
                        }`}>
                          {selectedDefaultQuestions.has(q.id) && (
                            <Check className="w-3.5 h-3.5 text-white" />
                          )}
                        </div>
                        <input
                          type="checkbox"
                          checked={selectedDefaultQuestions.has(q.id)}
                          onChange={() => toggleQuestionSelection(q.id)}
                          className="sr-only"
                        />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-lia-text-primary">{q.question_text}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <Badge variant="outline" className="text-micro bg-gray-50 text-lia-text-secondary border-lia-border-subtle">
                            {getCategoryLabel(q.category)}
                          </Badge>
                          <Badge variant="outline" className="text-micro bg-wedo-cyan/10 text-wedo-cyan-dark border-wedo-cyan/30">
                            {q.question_type === 'yes_no' ? 'Sim/Não' : 
                             q.question_type === 'single_choice' ? 'Escolha única' : 
                             q.question_type === 'multiple_choice' ? 'Múltipla escolha' : 
                             q.question_type === 'scale' ? 'Escala' : 'Texto'}
                          </Badge>
                          {q.is_required && (
                            <Badge variant="outline" className="text-micro bg-status-error/10 text-status-error border-status-error/30">
                              Obrigatória
                            </Badge>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex items-center justify-between px-5 py-4 border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle">
              <p className="text-xs text-lia-text-tertiary">
                {selectedDefaultQuestions.size} pergunta(s) selecionada(s)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowImportQuestionsModal(false)}
                  className="h-9 px-4"
                >
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={importSelectedQuestions}
                  disabled={selectedDefaultQuestions.size === 0}
                  className="h-9 px-4 bg-status-warning hover:bg-status-warning text-white"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  Importar ({selectedDefaultQuestions.size})
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
