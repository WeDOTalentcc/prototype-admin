"use client"

import React from "react"
import { SCREENING_STATUS_LABELS, type ScreeningStatus } from "@/types/screening"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import {
  Briefcase, Users, DollarSign, Target, Globe, Save, Loader2,
  Linkedin, Search, Edit, ListOrdered, GripVertical, Plus, Trash2,
  ChevronUp, ChevronDown, Lock, Settings, Clock, Brain, Languages,
  X, Filter, CheckCircle2, Circle, AlertTriangle, Play, Pause, Send,
  Link, Copy, ExternalLink, Info,
} from "lucide-react"
import { toast } from "sonner"
import { textStyles } from "@/lib/design-tokens"
import { ScreeningConfigContent, SCREENING_SECTIONS } from "@/components/screening-config"

import type { JobEditTabProps } from "./job-edit-tab/job-edit-tab.types"
import {
  SECTIONS,
  LANGUAGE_OPTIONS,
  LEVEL_OPTIONS,
  stageTypeLabels,
  inputClass,
  selectClass,
  labelClass,
  groupHeaderClass,
  formatDateValue,
  getCategoryBadge,
} from "./job-edit-tab/job-edit-tab.constants"
import { useJobEditTab } from "./job-edit-tab/useJobEditTab"
import { ScreeningBadge } from "./job-edit-tab/ScreeningBadge"
import { StatusChangeConfirmModal } from "./job-edit-tab/StatusChangeConfirmModal"
import { JobSectionHeader } from "./job-edit-tab/JobSectionHeader"

export function JobEditTab({
  jobEditForm,
  setJobEditForm,
  onSaveSection,
  savingSection,
  companyDefaults,
  job,
  onJobUpdate,
  onFormUpdate,
  isCreationMode,
  onPublish,
  isPublishing,
  publicLink,
}: JobEditTabProps) {
  const {
    activeSection,
    setActiveSection,
    statusChangeConfirm,
    setStatusChangeConfirm,
    currentSection,
    isEditing,
    filled,
    total,
    stages,
    rawStages,
    loadingCompanyPipeline,
    screeningCompletion,
    updateField,
    jobSectionCompletion,
    getScreeningImpact,
    handleStatusChangeWithScreening,
    handleStartEditing,
    handleCancel,
    handleSave,
    addStage,
    removeStage,
    updateStage,
    moveStage,
    LIA_ASSISTED_STAGES,
    LIA_ASSISTED_STAGE_NAMES,
  } = useJobEditTab({
    jobEditForm,
    setJobEditForm,
    onSaveSection,
    job,
    onJobUpdate,
    isCreationMode,
  })

  const isScreeningSection = SCREENING_SECTIONS.some((s) => s.id === activeSection)
  const isSaving = savingSection === activeSection
  const SectionIcon = currentSection.icon

  return (
    <div className="space-y-4">
      {isCreationMode && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-md px-4 py-3">
            <Info className="w-4 h-4 text-status-warning dark:text-status-warning flex-shrink-0" />
            <p className="text-sm text-status-warning dark:text-status-warning font-['Open_Sans',sans-serif]">
              Vaga em rascunho — preencha os dados e publique quando estiver pronta
            </p>
          </div>
          <Button
            onClick={onPublish}
            disabled={isPublishing}
            className="ml-3 gap-2 px-5 py-2.5 text-sm font-medium rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 flex-shrink-0"
          >
            {isPublishing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Publicando...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Publicar Vaga
              </>
            )}
          </Button>
        </div>
      )}

      <div className="flex gap-6">
        <div className="flex-shrink-0" style={{ width: "220px" }}>
          <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary rounded-md overflow-hidden">
            <nav className="p-3 h-full overflow-y-auto">
              <div className="mb-2">
                <span className="text-micro font-semibold lia-text-400 dark:lia-text-500 uppercase tracking-wider px-3 font-['Open_Sans',sans-serif]">
                  Configurações da Vaga
                </span>
              </div>
              <div className="space-y-1">
                {SECTIONS.map((section) => {
                  const isDone = jobSectionCompletion(section.fields)
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans ${
                        activeSection === section.id
                          ? "bg-gray-50 dark:bg-lia-bg-secondary border border-gray-900 dark:border-lia-border-subtle text-wedo-cyan-dark dark:text-lia-text-secondary"
                          : "hover:bg-gray-50 dark:hover:bg-gray-800 lia-text-800 dark:text-lia-text-primary border border-transparent"
                      }`}
                      style={{ fontSize: "0.6875rem", lineHeight: "1.125rem", fontWeight: "500" }}
                    >
                      <section.icon className="w-4 h-4 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className={`${textStyles.h4} 2xl:text-xs`}>{section.title}</div>
                        <div className={`${textStyles.description} 2xl:text-xs`}>{section.description}</div>
                      </div>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 text-status-success dark:text-status-success" />
                      ) : (
                        <Circle className="w-3.5 h-3.5 flex-shrink-0 lia-text-300 dark:lia-text-600" />
                      )}
                    </button>
                  )
                })}
              </div>

              <div className="my-3 border-t border-lia-border-subtle dark:border-lia-border-subtle" />

              <div className="mb-2">
                <span className="text-micro font-semibold lia-text-400 dark:lia-text-500 uppercase tracking-wider px-3 font-['Open_Sans',sans-serif]">
                  Configurações de Triagem
                </span>
              </div>
              <div className="space-y-1">
                {SCREENING_SECTIONS.map((section) => {
                  const isDone = screeningCompletion[section.id] || false
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans ${
                        activeSection === section.id
                          ? "bg-gray-50 dark:bg-lia-bg-secondary border border-gray-900 dark:border-lia-border-subtle text-wedo-cyan-dark dark:text-lia-text-secondary"
                          : "hover:bg-gray-50 dark:hover:bg-gray-800 lia-text-800 dark:text-lia-text-primary border border-transparent"
                      }`}
                      style={{ fontSize: "0.6875rem", lineHeight: "1.125rem", fontWeight: "500" }}
                    >
                      <section.icon className="w-4 h-4 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className={`${textStyles.h4} 2xl:text-xs`}>{section.title}</div>
                        <div className={`${textStyles.description} 2xl:text-xs`}>{section.description}</div>
                      </div>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 text-status-success dark:text-status-success" />
                      ) : (
                        <Circle className="w-3.5 h-3.5 flex-shrink-0 lia-text-300 dark:lia-text-600" />
                      )}
                    </button>
                  )
                })}
              </div>
            </nav>
          </Card>
        </div>

        <div className="flex-1 min-w-0">
          {isScreeningSection && job ? (
            <ScreeningConfigContent
              job={job}
              onJobUpdate={onJobUpdate}
              onFormUpdate={onFormUpdate}
              activeSection={activeSection as "configuracoes" | "descricao" | "perguntas"}
            />
          ) : (
            <div className="space-y-4">
              {/* Section header - extracted to JobSectionHeader */}
              <JobSectionHeader
                SectionIcon={SectionIcon}
                title={currentSection.title}
                description={currentSection.description}
                filled={filled}
                total={total}
                isCreationMode={isCreationMode}
                isEditing={isEditing}
                isSaving={isSaving}
                onSave={handleSave}
                onStartEditing={handleStartEditing}
                onCancel={handleCancel}
              />

              {/* Status change confirm modal */}
              {statusChangeConfirm && (
                <StatusChangeConfirmModal
                  state={statusChangeConfirm}
                  jobTitle={(job?.title as string) || (jobEditForm.title as string)}
                  onCancel={() => setStatusChangeConfirm(null)}
                  onChange={handleStatusChangeWithScreening}
                />
              )}

              {/* ── info-geral ─────────────────────────────────────────────── */}
              {activeSection === "info-geral" && (
                <div className="space-y-5">
                  {/* Gestão */}
                  <div>
                    <h3 className={groupHeaderClass}>Gestão</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-4 gap-4">
                          <div>
                            <label className={labelClass}>Status</label>
                            <select
                              value={(jobEditForm.status as string) || ""}
                              onChange={(e) => {
                                const newStatus = e.target.value
                                if (!newStatus) return
                                const impact = getScreeningImpact(newStatus)
                                if (impact !== "none") {
                                  setStatusChangeConfirm({ newStatus, screeningImpact: impact })
                                } else {
                                  updateField("status", newStatus)
                                }
                              }}
                              disabled={!isEditing}
                              className={selectClass(!isEditing)}
                            >
                              <option value="">Selecione...</option>
                              <option value="Rascunho">Rascunho</option>
                              <option value="Ativa">Ativa</option>
                              <option value="Paralisada">Paralisada</option>
                              <option value="Concluída">Concluída</option>
                              <option value="Cancelada">Cancelada</option>
                            </select>
                          </div>
                          <div>
                            <label className={labelClass}>Prioridade</label>
                            <select
                              value={(jobEditForm.priority as string) || ""}
                              onChange={(e) => updateField("priority", e.target.value)}
                              disabled={!isEditing}
                              className={selectClass(!isEditing)}
                            >
                              <option value="">Selecione...</option>
                              <option value="alta">Alta</option>
                              <option value="média">Média</option>
                              <option value="baixa">Baixa</option>
                            </select>
                          </div>
                          <div>
                            <label className={labelClass}>Nível de Urgência</label>
                            <select
                              value={jobEditForm.urgencyLevel?.toString() || ""}
                              onChange={(e) => updateField("urgencyLevel", parseInt(e.target.value))}
                              disabled={!isEditing}
                              className={selectClass(!isEditing)}
                            >
                              <option value="">Selecione...</option>
                              <option value="1">1 - Baixa</option>
                              <option value="2">2 - Moderada</option>
                              <option value="3">3 - Média</option>
                              <option value="4">4 - Alta</option>
                              <option value="5">5 - Crítica</option>
                            </select>
                          </div>
                          <div>
                            <label className={labelClass}>Triagem</label>
                            <div
                              className={`w-full px-3 py-2 text-xs rounded-md border cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 ${
                                (job?.screeningStatus || "not_configured") === "active"
                                  ? "border-status-success/30 bg-status-success/10/50 text-status-success dark:border-status-success/30 dark:bg-status-success/20 dark:text-status-success"
                                  : (job?.screeningStatus || "not_configured") === "paused"
                                  ? "border-status-warning/30 bg-status-warning/10/50 text-status-warning dark:border-status-warning/30 dark:bg-status-warning/20 dark:text-status-warning"
                                  : (job?.screeningStatus || "not_configured") === "completed"
                                  ? "border-wedo-cyan/30 bg-wedo-cyan/10/50 text-wedo-cyan-dark dark:border-wedo-cyan/30 dark:text-wedo-cyan-dark"
                                  : "border-lia-border-subtle bg-gray-50 lia-text-500 dark:border-lia-border-subtle dark:bg-lia-bg-secondary dark:lia-text-500"
                              }`}
                              onClick={() => setActiveSection("configuracoes")}
                              title="Clique para ir às Configurações de Triagem"
                            >
                              {(() => {
                                const s = (job?.screeningStatus || "not_configured") as ScreeningStatus
                                const icons: Record<ScreeningStatus, string> = {
                                  active: "●", paused: "◉", completed: "✓", not_started: "○", not_configured: "○",
                                }
                                return `${icons[s]} ${SCREENING_STATUS_LABELS[s]}`
                              })()}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Identificação */}
                  <div>
                    <h3 className={groupHeaderClass}>Identificação</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="col-span-2">
                            <label className={labelClass}>Título da Vaga<ScreeningBadge /></label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.title as string) || ""} onChange={(e) => updateField("title", e.target.value)} disabled={!isEditing} placeholder="Ex: Analista de Sistemas Sênior" />
                          </div>
                          <div>
                            <label className={labelClass}>Departamento<ScreeningBadge /></label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.department as string) || ""} onChange={(e) => updateField("department", e.target.value)} disabled={!isEditing} placeholder="Ex: Tecnologia" />
                          </div>
                          <div>
                            <label className={labelClass}>Localização<ScreeningBadge /></label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.location as string) || ""} onChange={(e) => updateField("location", e.target.value)} disabled={!isEditing} placeholder="Ex: São Paulo, SP" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Classificação */}
                  <div>
                    <h3 className={groupHeaderClass}>Classificação</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>
                              Modelo de Trabalho<ScreeningBadge />
                              {companyDefaults?.workModel && !jobEditForm.workModel && (
                                <span className="ml-1.5 text-micro text-wedo-cyan-dark dark:text-wedo-cyan font-normal">(padrão: {companyDefaults.workModel})</span>
                              )}
                            </label>
                            <select value={(jobEditForm.workModel as string) || ""} onChange={(e) => updateField("workModel", e.target.value)} disabled={!isEditing} className={selectClass(!isEditing)}>
                              <option value="">{companyDefaults?.workModel ? `Usar padrão (${companyDefaults.workModel})` : "Selecione..."}</option>
                              <option value="Presencial">Presencial</option>
                              <option value="Remoto">Remoto</option>
                              <option value="Híbrido">Híbrido</option>
                            </select>
                          </div>
                          <div>
                            <label className={labelClass}>
                              Tipo de Contrato<ScreeningBadge />
                              {companyDefaults?.employmentTypes && companyDefaults.employmentTypes.length > 0 && !jobEditForm.type && (
                                <span className="ml-1.5 text-micro text-wedo-cyan-dark dark:text-wedo-cyan font-normal">(padrão: {companyDefaults.employmentTypes[0]})</span>
                              )}
                            </label>
                            {(() => {
                              const staticTypes = ["CLT", "PJ", "Estágio", "Temporário", "Freelancer", "Aprendiz"]
                              const companyTypes = companyDefaults?.employmentTypes || []
                              const allTypes = [...new Set([...companyTypes, ...staticTypes])]
                              return (
                                <select value={(jobEditForm.type as string) || ""} onChange={(e) => updateField("type", e.target.value)} disabled={!isEditing} className={selectClass(!isEditing)}>
                                  <option value="">{companyTypes[0] ? `Usar padrão (${companyTypes[0]})` : "Selecione..."}</option>
                                  {allTypes.map((t) => (
                                    <option key={t} value={t}>{t}{companyTypes.includes(t) && !staticTypes.includes(t) ? " (empresa)" : ""}</option>
                                  ))}
                                </select>
                              )
                            })()}
                          </div>
                          <div>
                            <label className={labelClass}>Nível<ScreeningBadge /></label>
                            <select value={(jobEditForm.level as string) || ""} onChange={(e) => updateField("level", e.target.value)} disabled={!isEditing} className={selectClass(!isEditing)}>
                              <option value="">Selecione...</option>
                              <option value="Estágio">Estágio</option>
                              <option value="Júnior">Júnior</option>
                              <option value="Pleno">Pleno</option>
                              <option value="Sênior">Sênior</option>
                              <option value="Lead">Lead</option>
                              <option value="Gerente">Gerente</option>
                              <option value="Diretor">Diretor</option>
                            </select>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Prazos */}
                  <div>
                    <h3 className={groupHeaderClass}>Prazos & Timeline</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>Data de Abertura</label>
                            <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.openDate)} onChange={(e) => updateField("openDate", e.target.value)} disabled={!isEditing} />
                          </div>
                          <div>
                            <label className={labelClass}>Prazo Final</label>
                            <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadline)} onChange={(e) => updateField("deadline", e.target.value)} disabled={!isEditing} />
                          </div>
                          <div>
                            <label className={labelClass}>Prazo Triagem</label>
                            <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadlineScreening)} onChange={(e) => updateField("deadlineScreening", e.target.value)} disabled={!isEditing} />
                          </div>
                          <div>
                            <label className={labelClass}>Prazo Shortlist</label>
                            <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadlineShortlist)} onChange={(e) => updateField("deadlineShortlist", e.target.value)} disabled={!isEditing} />
                          </div>
                          <div className="col-span-2">
                            <label className={labelClass}>Prazo Fechamento</label>
                            <input type="date" className={inputClass(!isEditing)} value={formatDateValue(jobEditForm.deadlineClosing)} onChange={(e) => updateField("deadlineClosing", e.target.value)} disabled={!isEditing} />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Descrição */}
                  <div>
                    <h3 className={groupHeaderClass}>Descrição da Vaga</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div>
                          <label className={labelClass}>Descrição da Vaga<ScreeningBadge /></label>
                          <textarea className={`${inputClass(!isEditing)} resize-vertical`} rows={16} value={(jobEditForm.description as string) || ""} onChange={(e) => updateField("description", e.target.value)} disabled={!isEditing} placeholder="Descrição detalhada da vaga..." style={{ minHeight: "280px" }} />
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Idiomas */}
                  <div>
                    <h3 className={groupHeaderClass}>
                      Idiomas<ScreeningBadge />
                      {companyDefaults?.defaultLanguages && companyDefaults.defaultLanguages.length > 0 && (
                        <span className="ml-1.5 text-micro text-wedo-cyan-dark dark:text-wedo-cyan font-normal normal-case tracking-normal">
                          (padrão empresa: {companyDefaults.defaultLanguages.join(", ")})
                        </span>
                      )}
                    </h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        {(() => {
                          const langs = (jobEditForm.languages || []) as Array<{ language: string; level: string; required?: boolean }>
                          const addLanguage = () => updateField("languages", [...langs, { language: "", level: "intermediario", required: false }])
                          const removeLanguage = (idx: number) => updateField("languages", langs.filter((_, i) => i !== idx))
                          const updateLanguage = (idx: number, field: string, value: unknown) =>
                            updateField("languages", langs.map((l, i) => (i === idx ? { ...l, [field]: value } : l)))
                          return (
                            <div className="space-y-3">
                              {langs.length === 0 && !isEditing && (
                                <p className="text-xs lia-text-400 dark:lia-text-500 font-['Open_Sans',sans-serif] italic">Nenhum idioma adicionado</p>
                              )}
                              {langs.map((lang, idx) => (
                                <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
                                  <Languages className="w-4 h-4 lia-text-400 flex-shrink-0" />
                                  <div className="flex-1 grid grid-cols-3 gap-3">
                                    <div>
                                      <label className="text-micro lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif] mb-1 block">Idioma</label>
                                      <select className={selectClass(!isEditing)} value={lang.language || ""} onChange={(e) => updateLanguage(idx, "language", e.target.value)} disabled={!isEditing}>
                                        <option value="">Selecione...</option>
                                        {LANGUAGE_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                                      </select>
                                    </div>
                                    <div>
                                      <label className="text-micro lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif] mb-1 block">Nível</label>
                                      <select className={selectClass(!isEditing)} value={lang.level || "intermediario"} onChange={(e) => updateLanguage(idx, "level", e.target.value)} disabled={!isEditing}>
                                        {LEVEL_OPTIONS.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                                      </select>
                                    </div>
                                    <div className="flex items-end gap-2">
                                      <div className="flex-1">
                                        <label className="text-micro lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif] mb-1 block">Obrigatório</label>
                                        <div className="flex items-center gap-2 h-[38px]">
                                          <Switch checked={!!lang.required} onCheckedChange={(val: boolean) => updateLanguage(idx, "required", val)} disabled={!isEditing} className="data-[state=checked]:bg-gray-900 dark:data-[state=checked]:bg-gray-200" />
                                          <span className="text-xs lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif]">{lang.required ? "Sim" : "Não"}</span>
                                        </div>
                                      </div>
                                      {isEditing && (
                                        <button onClick={() => removeLanguage(idx)} className="p-1.5 mb-1 rounded-lg hover:bg-status-error/10 dark:hover:bg-status-error/10/30 lia-text-400 hover:text-status-error transition-colors">
                                          <X className="w-4 h-4" />
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                              {isEditing && (
                                <Button onClick={addLanguage} variant="outline" size="sm" className="gap-1.5 text-xs rounded-md w-full border-dashed">
                                  <Plus className="w-3.5 h-3.5" />Adicionar Idioma
                                </Button>
                              )}
                            </div>
                          )
                        })()}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Ações Afirmativas */}
                  <div>
                    <h3 className={groupHeaderClass}>Ações Afirmativas<ScreeningBadge /></h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="flex items-center gap-3">
                              <Switch checked={!!jobEditForm.isAffirmative} onCheckedChange={(val: boolean) => updateField("isAffirmative", val)} disabled={!isEditing} />
                              <label className={textStyles.label}>Vaga Afirmativa</label>
                            </div>
                            <div>
                              <label className={labelClass}>Critério Principal</label>
                              <select value={(jobEditForm.affirmativeCriteriaPrimary as string) || ""} onChange={(e) => updateField("affirmativeCriteriaPrimary", e.target.value)} disabled={!isEditing || !jobEditForm.isAffirmative} className={selectClass(!isEditing || !jobEditForm.isAffirmative)}>
                                <option value="">Selecione...</option>
                                <option value="gender">Gênero</option>
                                <option value="race_ethnicity">Raça/Etnia</option>
                                <option value="disability">PCD</option>
                                <option value="lgbtqia">LGBTQIA+</option>
                                <option value="age">50+</option>
                                <option value="refugee">Refugiado</option>
                                <option value="indigenous">Indígena</option>
                                <option value="other">Outro</option>
                              </select>
                            </div>
                          </div>
                          {(jobEditForm.isAffirmative as boolean) && (
                            <>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <label className={labelClass}>Critério Secundário (opcional)</label>
                                  <select value={(jobEditForm.affirmativeCriteriaSecondary as string) || ""} onChange={(e) => updateField("affirmativeCriteriaSecondary", e.target.value)} disabled={!isEditing} className={selectClass(!isEditing)}>
                                    <option value="">Nenhum</option>
                                    <option value="gender">Gênero</option>
                                    <option value="race_ethnicity">Raça/Etnia</option>
                                    <option value="disability">PCD</option>
                                    <option value="lgbtqia">LGBTQIA+</option>
                                    <option value="age">50+</option>
                                    <option value="refugee">Refugiado</option>
                                    <option value="indigenous">Indígena</option>
                                    <option value="other">Outro</option>
                                  </select>
                                </div>
                                <div>
                                  <label className={labelClass}>Descrição</label>
                                  <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.affirmativeDescription as string) || ""} onChange={(e) => updateField("affirmativeDescription", e.target.value)} disabled={!isEditing} placeholder="Ex: Mulheres negras, PCD motora" />
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-3">
                                  <Switch checked={!!jobEditForm.affirmativeDocumentRequired} onCheckedChange={(val: boolean) => updateField("affirmativeDocumentRequired", val)} disabled={!isEditing} />
                                  <label className={textStyles.label}>Exige Documentação</label>
                                </div>
                                {(jobEditForm.affirmativeDocumentRequired as boolean) && (
                                  <div>
                                    <label className={labelClass}>Tipos de Documento</label>
                                    <input type="text" className={inputClass(!isEditing)} value={((jobEditForm.affirmativeDocumentTypes as string[]) || []).join(", ")} onChange={(e) => updateField("affirmativeDocumentTypes", e.target.value.split(",").map((s: string) => s.trim()).filter(Boolean))} disabled={!isEditing} placeholder="Ex: laudo_pcd, autodeclaracao_racial" />
                                  </div>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Mercado-Alvo */}
                  <div>
                    <h3 className={groupHeaderClass}>Mercado-Alvo</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>Setor</label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.targetSector as string) || ""} onChange={(e) => updateField("targetSector", e.target.value)} disabled={!isEditing} placeholder="Ex: Tecnologia" />
                          </div>
                          <div>
                            <label className={labelClass}>Segmento</label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.targetSegment as string) || ""} onChange={(e) => updateField("targetSegment", e.target.value)} disabled={!isEditing} placeholder="Ex: Fintechs" />
                          </div>
                          <div className="col-span-2">
                            <label className={labelClass}>Público-Alvo</label>
                            <textarea className={`${inputClass(!isEditing)} resize-none`} rows={2} value={(jobEditForm.targetAudience as string) || ""} onChange={(e) => updateField("targetAudience", e.target.value)} disabled={!isEditing} placeholder="Descreva o perfil ideal do candidato..." />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Canais de Publicação */}
                  <div>
                    <h3 className={groupHeaderClass}>Canais de Publicação</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="space-y-0">
                          <div className="flex items-center justify-between py-2.5 border-b border-lia-border-subtle dark:lia-border-800">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-wedo-cyan/10 flex items-center justify-center"><Linkedin className="w-4 h-4 text-wedo-cyan-dark" /></div>
                              <div>
                                <span className="text-xs font-medium lia-text-900 dark:lia-text-50">LinkedIn</span>
                                <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">Publicar vaga no LinkedIn</p>
                              </div>
                            </div>
                            <Switch checked={!!jobEditForm.publishedLinkedIn} onCheckedChange={(val: boolean) => updateField("publishedLinkedIn", val)} disabled={!isEditing} />
                          </div>
                          <div className="flex items-center justify-between py-2.5 border-b border-lia-border-subtle dark:lia-border-800">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center"><Globe className="w-4 h-4 text-status-success" /></div>
                              <div>
                                <span className="text-xs font-medium lia-text-900 dark:lia-text-50">Website</span>
                                <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">Publicar no site da empresa</p>
                              </div>
                            </div>
                            <Switch checked={!!jobEditForm.publishedWebsite} onCheckedChange={(val: boolean) => updateField("publishedWebsite", val)} disabled={!isEditing} />
                          </div>
                          <div className="flex items-center justify-between py-2.5">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-lg bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center"><Search className="w-4 h-4 text-wedo-purple" /></div>
                              <div>
                                <span className="text-xs font-medium lia-text-900 dark:lia-text-50">Indeed</span>
                                <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">Publicar vaga no Indeed</p>
                              </div>
                            </div>
                            <Switch checked={!!jobEditForm.publishedIndeed} onCheckedChange={(val: boolean) => updateField("publishedIndeed", val)} disabled={!isEditing} />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Visibilidade */}
                  <div>
                    <h3 className={groupHeaderClass}>Visibilidade & Confidencialidade</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className={labelClass}>Visibilidade</label>
                              <select value={(jobEditForm.visibility as string) || ""} onChange={(e) => updateField("visibility", e.target.value)} disabled={!isEditing} className={selectClass(!isEditing)}>
                                <option value="">Selecione...</option>
                                <option value="Pública">Pública</option>
                                <option value="Interna">Interna</option>
                                <option value="Confidencial">Confidencial</option>
                              </select>
                            </div>
                            <div className="flex items-center gap-3 pt-6">
                              <Switch checked={!!jobEditForm.isConfidential} onCheckedChange={(val: boolean) => updateField("isConfidential", val)} disabled={!isEditing} />
                              <label className={textStyles.label}>Vaga Confidencial</label>
                            </div>
                          </div>
                          <div>
                            <label className={labelClass}>Nome da Empresa (mascarado)</label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.maskedCompanyName as string) || ""} onChange={(e) => updateField("maskedCompanyName", e.target.value)} disabled={!isEditing} placeholder="Ex: Empresa do segmento de tecnologia" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Link de Candidatura */}
                  <div>
                    <h3 className={groupHeaderClass}>Link de Candidatura</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        {(jobEditForm.status === "Ativa" || jobEditForm.status === "Paralisada" || jobEditForm.status === "Concluída") && (publicLink || jobEditForm.public_url) ? (
                          <div className="space-y-2">
                            <p className="text-xs lia-text-500 dark:text-lia-text-tertiary font-['Open_Sans',sans-serif]">Link público para candidatos se candidatarem:</p>
                            <div className="flex items-center gap-2">
                              <input type="text" readOnly value={publicLink || (jobEditForm.public_url as string) || ""} className="flex-1 px-3 py-2 text-xs lia-text-700 dark:text-lia-text-secondary bg-gray-50 dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md font-['Open_Sans',sans-serif]" onClick={(e) => (e.target as HTMLInputElement).select()} />
                              <button onClick={() => { navigator.clipboard.writeText(publicLink || (jobEditForm.public_url as string) || ""); toast.success("Link copiado!") }} className="p-2 rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 transition-colors flex-shrink-0" title="Copiar link">
                                <Copy className="w-3.5 h-3.5" />
                              </button>
                              <a href={publicLink || (jobEditForm.public_url as string) || "#"} target="_blank" rel="noopener noreferrer" className="p-2 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle lia-text-600 dark:text-lia-text-tertiary hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex-shrink-0" title="Abrir link">
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-xs lia-text-400 dark:lia-text-500 font-['Open_Sans',sans-serif]">
                            <Link className="w-3.5 h-3.5" />
                            <span>Publique a vaga para gerar o link de candidatura</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* ── pessoas ──────────────────────────────────────────────────── */}
              {activeSection === "pessoas" && (
                <div className="space-y-5">
                  <div>
                    <h3 className={groupHeaderClass}>Recrutador</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>Nome</label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.recruiter as string) || ""} onChange={(e) => updateField("recruiter", e.target.value)} disabled={!isEditing} placeholder="Nome do recrutador" />
                          </div>
                          <div>
                            <label className={labelClass}>Email</label>
                            <input type="email" className={inputClass(!isEditing)} value={(jobEditForm.recruiterEmail as string) || ""} onChange={(e) => updateField("recruiterEmail", e.target.value)} disabled={!isEditing} placeholder="email@empresa.com" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  <div>
                    <h3 className={groupHeaderClass}>Gestor da Vaga</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>Nome</label>
                            <input type="text" className={inputClass(!isEditing)} value={(jobEditForm.manager as string) || ""} onChange={(e) => updateField("manager", e.target.value)} disabled={!isEditing} placeholder="Nome do gestor" />
                          </div>
                          <div>
                            <label className={labelClass}>Email</label>
                            <input type="email" className={inputClass(!isEditing)} value={(jobEditForm.managerEmail as string) || ""} onChange={(e) => updateField("managerEmail", e.target.value)} disabled={!isEditing} placeholder="email@empresa.com" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* ── processo ─────────────────────────────────────────────────── */}
              {activeSection === "processo" && (
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
                          const isLiaAssisted = stage.liaAssisted || LIA_ASSISTED_STAGES.includes(stage.name || "") || LIA_ASSISTED_STAGE_NAMES.includes(stage.stageName || "")
                          const currentSla = stage.slaDays ?? stage.defaultSlaDays ?? 3
                          const defaultSla = stage.defaultSlaDays ?? 3
                          const slaModified = currentSla !== defaultSla
                          return (
                            <Card key={stage.name || index} className={`border transition-colors ${!stageIsActive ? "opacity-40" : ""} ${isSystem ? "border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50/50 dark:bg-lia-bg-secondary/30" : "border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default dark:hover:border-gray-600"}`}>
                              <CardContent className="p-3">
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 rounded-full bg-gray-900 dark:lia-bg-50 flex items-center justify-center text-xs font-bold text-white dark:lia-text-900 font-['Open_Sans',sans-serif] shrink-0">{index + 1}</div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      {isEditing && canEditName ? (
                                        <input type="text" className={`${inputClass(!isEditing)} flex-1`} value={stage.stageName} onChange={(e) => updateStage(index, "stageName", e.target.value)} placeholder="Nome da etapa" />
                                      ) : (
                                        <span className={`text-base-ui font-semibold font-['Open_Sans',sans-serif] ${isSystem ? "lia-text-500 dark:text-lia-text-tertiary" : "lia-text-900 dark:lia-text-50"}`}>{stage.stageName || "Sem nome"}</span>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-2 mt-1.5">
                                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-micro font-medium ${badge.color} font-['Open_Sans',sans-serif]`}>
                                        <BadgeIcon className="w-2.5 h-2.5" />{badge.label}
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
                                            <input type="number" min={1} max={90} className="w-12 text-xs text-center px-1 py-0.5 border border-lia-border-subtle dark:border-lia-border-subtle rounded-full bg-white dark:bg-lia-bg-primary lia-text-700 dark:text-lia-text-secondary font-['Open_Sans',sans-serif]" value={currentSla} onChange={(e) => updateStage(index, "slaDays", parseInt(e.target.value) || 1)} />
                                            <span className="text-micro lia-text-400 dark:lia-text-500 font-['Open_Sans',sans-serif]">dias</span>
                                            {slaModified && <span className="text-micro text-status-warning font-['Open_Sans',sans-serif]">(padrão: {defaultSla}d)</span>}
                                          </div>
                                        ) : (
                                          <span className={`text-micro font-['Open_Sans',sans-serif] ${slaModified ? "text-status-warning dark:text-status-warning font-medium" : "lia-text-400 dark:lia-text-500"}`}>
                                            {currentSla} {currentSla === 1 ? "dia" : "dias"}{slaModified && ` (padrão: ${defaultSla}d)`}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-0.5 shrink-0">
                                    {isEditing && canReorder && (
                                      <>
                                        <button type="button" onClick={() => moveStage(index, "up")} disabled={index === 0} className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 lia-text-400 hover:lia-text-600 disabled:opacity-30"><ChevronUp className="w-3.5 h-3.5" /></button>
                                        <button type="button" onClick={() => moveStage(index, "down")} disabled={index === stages.length - 1} className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 lia-text-400 hover:lia-text-600 disabled:opacity-30"><ChevronDown className="w-3.5 h-3.5" /></button>
                                      </>
                                    )}
                                    {isEditing && isSystem && <Lock className="w-3.5 h-3.5 lia-text-300 dark:lia-text-600" />}
                                    {isEditing && canRemove && (
                                      <button type="button" onClick={() => removeStage(index)} className="p-1 rounded-md hover:bg-status-error/10 dark:hover:bg-status-error/10/30 lia-text-400 hover:text-status-error">
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
                      <button type="button" onClick={addStage} className="flex items-center gap-2 text-xs lia-text-500 hover:lia-text-700 dark:hover:lia-text-300 py-2.5 px-3 rounded-md border border-dashed border-lia-border-default dark:border-lia-border-default hover:border-gray-400 w-full justify-center mt-3">
                        <Plus className="w-4 h-4" />Adicionar Etapa Customizada
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* ── remuneracao ──────────────────────────────────────────────── */}
              {activeSection === "remuneracao" && (
                <div className="space-y-5">
                  <div>
                    <h3 className={groupHeaderClass}>Faixa Salarial<ScreeningBadge /></h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>Mínimo</label>
                            <div className="relative">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs lia-text-400">R$</span>
                              <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.salaryMin as string) || ""} onChange={(e) => updateField("salaryMin", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                            </div>
                          </div>
                          <div>
                            <label className={labelClass}>Máximo</label>
                            <div className="relative">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs lia-text-400">R$</span>
                              <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.salaryMax as string) || ""} onChange={(e) => updateField("salaryMax", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  <div>
                    <h3 className={groupHeaderClass}>Bônus / Variável</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className={labelClass}>Mínimo</label>
                            <div className="relative">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs lia-text-400">R$</span>
                              <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.bonusMin as string) || ""} onChange={(e) => updateField("bonusMin", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                            </div>
                          </div>
                          <div>
                            <label className={labelClass}>Máximo</label>
                            <div className="relative">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs lia-text-400">R$</span>
                              <input type="number" className={`${inputClass(!isEditing)} pl-9`} value={(jobEditForm.bonusMax as string) || ""} onChange={(e) => updateField("bonusMax", e.target.value)} disabled={!isEditing} placeholder="0,00" />
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  <div>
                    <h3 className={groupHeaderClass}>Benefícios</h3>
                    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle">
                      <CardContent className="p-4">
                        {(() => {
                          const selectedBenefits: string[] = Array.isArray(jobEditForm.benefits)
                            ? jobEditForm.benefits
                            : typeof jobEditForm.benefits === "string" && jobEditForm.benefits
                            ? jobEditForm.benefits.split(",").map((b: string) => b.trim()).filter(Boolean)
                            : []
                          const companyBenefitNames = (companyDefaults?.benefits || []).map((b) => b.name)
                          const allAvailable = [...new Set([...companyBenefitNames, ...selectedBenefits])]
                          const toggleBenefit = (name: string) => {
                            const updated = selectedBenefits.includes(name)
                              ? selectedBenefits.filter((b) => b !== name)
                              : [...selectedBenefits, name]
                            updateField("benefits", updated)
                          }
                          return (
                            <div className="space-y-3">
                              <label className={labelClass}>
                                Benefícios da Vaga
                                {companyBenefitNames.length > 0 && (
                                  <span className="ml-1.5 text-micro text-wedo-cyan-dark dark:text-wedo-cyan font-normal">({companyBenefitNames.length} cadastrados na empresa)</span>
                                )}
                              </label>
                              {companyBenefitNames.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                  {allAvailable.map((name) => {
                                    const isSelected = selectedBenefits.includes(name)
                                    const isFromCompany = companyBenefitNames.includes(name)
                                    return (
                                      <button key={name} type="button" onClick={() => isEditing && toggleBenefit(name)} disabled={!isEditing} className={`px-3 py-1.5 rounded-md text-xs font-['Open_Sans',sans-serif] font-medium border transition-colors ${isSelected ? "bg-gray-900 text-white border-gray-900 dark:lia-bg-100 dark:lia-text-900 dark:border-lia-border-subtle" : "bg-white lia-text-600 border-lia-border-subtle hover:border-gray-400 dark:bg-lia-bg-secondary dark:text-lia-text-tertiary dark:border-lia-border-subtle"} ${!isEditing ? "cursor-default opacity-75" : "cursor-pointer"}`}>
                                        {isSelected ? "✓ " : ""}{name}
                                        {!isFromCompany && <span className="ml-1 text-micro opacity-60">(custom)</span>}
                                      </button>
                                    )
                                  })}
                                </div>
                              ) : (
                                <div className="flex flex-wrap gap-2">
                                  {selectedBenefits.map((name) => (
                                    <span key={name} className="px-3 py-1.5 rounded-full text-xs font-['Open_Sans',sans-serif] font-medium bg-gray-900 text-white dark:lia-bg-100 dark:lia-text-900 flex items-center gap-1.5">
                                      {name}
                                      {isEditing && <button onClick={() => toggleBenefit(name)} className="hover:text-status-error"><X className="w-3 h-3" /></button>}
                                    </span>
                                  ))}
                                </div>
                              )}
                              {isEditing && (
                                <div className="flex gap-2">
                                  <input type="text" className={`${inputClass(false)} flex-1`} placeholder="Adicionar benefício personalizado..." onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                      e.preventDefault()
                                      const val = (e.target as HTMLInputElement).value.trim()
                                      if (val && !selectedBenefits.includes(val)) {
                                        updateField("benefits", [...selectedBenefits, val]);
                                        (e.target as HTMLInputElement).value = ""
                                      }
                                    }
                                  }} />
                                </div>
                              )}
                              {selectedBenefits.length === 0 && !isEditing && (
                                <p className="text-xs lia-text-400 dark:lia-text-500 font-['Open_Sans',sans-serif] italic">Nenhum benefício selecionado</p>
                              )}
                            </div>
                          )
                        })()}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
