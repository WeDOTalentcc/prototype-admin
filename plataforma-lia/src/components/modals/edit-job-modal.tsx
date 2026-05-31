"use client"

import React from"react"

import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Chip } from "@/components/ui/chip"
import { Label } from"@/components/ui/label"
import { Textarea } from"@/components/ui/textarea"
import { Switch } from"@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  X,
  Briefcase,
  Users,
  Settings,
  Plus,
  Trash2,
  Save,
  Shield,
  Globe,
  Lock,
  Heart,
  Linkedin,
  ExternalLink,
  Target,
  Languages,
  UserPlus,
  Code,
  Brain,
  HelpCircle,
  Download,
  Check,
  Loader2,
} from"lucide-react"
import { toast } from"sonner"
import { cn } from"@/lib/utils"
import { liaApi, type JobVacancy } from"@/services/lia-api"
import type { CompanyBenefit } from '@/types/benefits'
import { useLiaChatContext } from '@/contexts/lia-float-context'
import {
  STATUS_OPTIONS,
  STAGE_OPTIONS,
  VISIBILITY_OPTIONS,
  inputStyle,
  selectTriggerStyle,
} from './edit-job-modal.constants'

import type { InterviewStage, PipelineTemplate, Job, EditJobModalProps, CompanyDefaultQuestion } from './edit-job/edit-job.types'
import { useEditJob } from './edit-job/useEditJob'

import { EditJobModalBasicInfo, EditJobModalCompensation, EditJobModalProcess, EditJobModalPrivacy } from './edit-job-sections'
export function EditJobModal({ isOpen, onClose, job, onSave }: EditJobModalProps) {
  const {
    formData,
    setFormData,
    isSaving,
    newRequirement,
    setNewRequirement,
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
    activeCompensationPolicies,
    applyPipelineTemplate,
    fetchPipelineTemplates,
  } = useEditJob({ isOpen, job, onSave, onClose })

  // INT:005 — LIA chat trigger for 'Sugerir pacote com LIA' button
  const { sendChatMessage } = useLiaChatContext()

  if (!isOpen || !job) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" data-testid="edit-job-modal">
      <div 
        className="absolute inset-0 bg-lia-overlay/70 backdrop-blur-[2px]"
        onClick={onClose}
      />
      
      <div className="relative bg-lia-bg-primary rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 bg-lia-bg-primary shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-lia-text-primary">Editar Vaga</h2>
              <p className="text-xs text-lia-text-secondary mt-0.5">
                <span className="text-lia-text-secondary font-medium mr-1.5">{job.jobId}</span>
                {job.title}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 rounded-md hover:bg-lia-interactive-hover"
            onClick={onClose}
          >
            <X className="w-4 h-4 text-lia-text-tertiary" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
              <div className="space-y-6">
                
                <EditJobModalBasicInfo
                  formData={formData}
                  updateField={updateField}
                  companyDepartments={companyDepartments}
                />

                <hr className="border-lia-border-subtle" />

                <EditJobModalCompensation
                  formData={formData}
                  setFormData={setFormData}
                  activeCompensationPolicies={activeCompensationPolicies}
                  onSuggestWithLIA={() => {
                    // INT:005 — open LIA chat pre-filled with compensation suggestion prompt
                    sendChatMessage(
                      `Sugira um pacote de remuneração completo para a vaga ${job?.title || ''}: salário, PRV e benefícios`,
                      undefined,
                      undefined,
                    )
                  }}
                />

                <hr className="border-lia-border-subtle" />

                <EditJobModalProcess
                  formData={formData}
                  newInterviewStageName={newInterviewStageName}
                  setNewInterviewStageName={setNewInterviewStageName}
                  newInterviewStageSLA={newInterviewStageSLA}
                  setNewInterviewStageSLA={setNewInterviewStageSLA}
                  newInterviewStageType={newInterviewStageType}
                  setNewInterviewStageType={setNewInterviewStageType}
                  addInterviewStage={addInterviewStage}
                  removeInterviewStage={removeInterviewStage}
                  updateInterviewStage={updateInterviewStage}
                  pipelineTemplates={pipelineTemplates}
                  isLoadingTemplates={isLoadingTemplates}
                  selectedTemplateId={selectedTemplateId}
                  applyPipelineTemplate={applyPipelineTemplate}
                  fetchPipelineTemplates={fetchPipelineTemplates}
                />

                <hr className="border-lia-border-subtle" />

                {/* NEW: Configuração de Confidencialidade para LIA */}
                <EditJobModalPrivacy
                  formData={formData}
                  updateField={updateField}
                />

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

                    <div className="p-4 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4 text-wedo-orange" />
                          <span className="text-sm text-lia-text-secondary" aria-live="polite" aria-atomic="true">Vaga Confidencial</span>
                        </div>
                        <Switch
                          checked={formData.isConfidential || false}
                          onCheckedChange={(checked: boolean) => updateField('isConfidential', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-wedo-magenta" />
                          <span className="text-sm text-lia-text-secondary" aria-live="polite" aria-atomic="true">Vaga Afirmativa</span>
                        </div>
                        <Switch
                          checked={formData.isAffirmative || false}
                          onCheckedChange={(checked: boolean) => { updateField('isAffirmative', checked); if (!checked) updateField('affirmativeType', undefined); }}
                        />
                      </div>
                      {formData.isAffirmative && (
                        <div className="space-y-3 mt-3 p-4 bg-wedo-purple/10 rounded-xl border border-wedo-purple/30">
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
                                  className={cn("p-2.5 rounded-md border cursor-pointer transition-colors",
                                    formData.affirmativeType === option.value
                                      ?"border-wedo-purple/30 bg-wedo-purple/15"
                                      :"border-wedo-purple/30 bg-lia-bg-primary hover:border-wedo-purple/30"
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
                      <div className="space-y-4 mt-4 p-4 bg-wedo-orange/10 rounded-xl border border-wedo-orange/30">
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
                              className={inputStyle +" flex-1"}
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
                              <Chip density="relaxed" key={idx} variant="neutral" muted className="py-1 px-2 bg-lia-bg-primary border border-lia-border-subtle">
                                <UserPlus className="w-3 h-3 mr-1 text-lia-text-disabled" />
                                {email}
                                <button
                                  onClick={() => removeAccessEmail(idx)}
                                  className="ml-1.5 text-lia-text-disabled hover:text-status-error"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </Chip>
                            ))}
                          </div>
                          <p className="text-xs text-lia-text-tertiary mt-1" aria-live="polite" aria-atomic="true">Usuários com acesso à vaga confidencial</p>
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
                  
                  <div className="p-4 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle space-y-3">
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
                      <Chip variant="neutral" className="text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-secondary text-lia-text-disabled border-lia-border-subtle">
                        Somente leitura
                      </Chip>
                    </div>
                    
                    <div className="p-4 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
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
                      className="min-h-20 text-sm resize-none bg-lia-bg-secondary border-lia-border-subtle focus:border-lia-border-medium focus:ring-1 focus:ring-lia-btn-primary-bg/20"
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
                      className={inputStyle +" flex-1"}
                      placeholder="Ex: Inglês"
                    />
                    <Select value={newLanguageLevel} onValueChange={setNewLanguageLevel}>
                      <SelectTrigger className="w-32 h-9 text-xs bg-lia-bg-secondary border-lia-border-subtle">
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
                    {(formData.languages as { language: string; level: string; required?: boolean }[] || []).map((lang, idx) => (
                      <Chip density="relaxed" key={idx} variant="neutral" muted className="py-1 px-2 border border-wedo-purple/30">
                        {lang.language} ({lang.level})
                        <button
                          onClick={() => removeLanguage(idx)}
                          className="ml-1.5 text-wedo-purple hover:text-status-error"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Chip>
                    ))}
                  </div>
                </section>

              </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary shrink-0">
          <Button
            variant="outline"
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-lia-bg-primary border border-lia-border-default hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg text-lia-text-secondary"
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
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
        <div className="fixed inset-0 bg-lia-overlay/70 flex items-center justify-center z-overlay p-4">
          <div className="bg-lia-bg-primary rounded-xl max-w-lg w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4 text-status-warning" />
                <h3 className="text-base-ui font-semibold text-lia-text-primary">Importar Perguntas Padrão</h3>
              </div>
              <button
                onClick={() => setShowImportQuestionsModal(false)}
                className="p-1 hover:bg-lia-interactive-hover rounded-full transition-colors motion-reduce:transition-none"
              >
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5" role="status" aria-live="polite" aria-label="Carregando...">
              {isLoadingDefaultQuestions ? (
                <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
                  <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-status-warning" />
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
                      className={`flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-colors motion-reduce:transition-none ${
                        selectedDefaultQuestions.has(q.id)
                          ? 'bg-status-warning/10 border-status-warning/30'
                          : 'bg-lia-bg-primary border-lia-border-subtle hover:border-lia-border-default'
                      }`}
                    >
                      <div className="mt-0.5">
                        <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors motion-reduce:transition-none ${
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
                          <Chip variant="neutral" className="text-micro bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle">
                            {getCategoryLabel(q.category)}
                          </Chip>
                          <Chip variant="neutral" className="text-micro -dark border-wedo-cyan/30">
                            {q.question_type === 'yes_no' ? 'Sim/Não' : 
                             q.question_type === 'single_choice' ? 'Escolha única' : 
                             q.question_type === 'multiple_choice' ? 'Múltipla escolha' : 
                             q.question_type === 'scale' ? 'Escala' : 'Texto'}
                          </Chip>
                          {q.is_required && (
                            <Chip variant="danger" className="text-micro">
                              Obrigatória
                            </Chip>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
            
            <div className="flex items-center justify-between px-5 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
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
