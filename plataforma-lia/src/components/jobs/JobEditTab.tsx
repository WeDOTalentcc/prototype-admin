"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Loader2, Send, Info, CheckCircle2, Circle, Save, Edit,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { ScreeningConfigContent, SCREENING_SECTIONS } from "@/components/screening-config"

import type { JobEditTabProps } from "./job-edit-tab/job-edit-tab.types"
import {
  SECTIONS,
  inputClass,
  labelClass,
  groupHeaderClass,
} from "./job-edit-tab/job-edit-tab.constants"
import { useJobEditTab } from "./job-edit-tab/useJobEditTab"
import { ScreeningBadge } from "./job-edit-tab/ScreeningBadge"
import { StatusChangeConfirmModal } from "./job-edit-tab/StatusChangeConfirmModal"
import { JobSectionHeader } from "./job-edit-tab/JobSectionHeader"
import { JobProcessSection } from "./job-edit-tab/JobProcessSection"
import { JobInfoGeralSection } from "./job-edit-tab/JobInfoGeralSection"
import { JobRemuneracaoSection } from "./job-edit-tab/JobRemuneracaoSection"

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
    vacancyId,
    templates,
    isLoadingTemplates,
    isApplyingTemplate,
    applyTemplate,
    saveStagesAsTemplate,
    isSavingAsTemplate,
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
          <div className="flex items-center gap-3 flex-1 bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 rounded-xl px-4 py-3">
            <Info className="w-4 h-4 text-status-warning flex-shrink-0" />
            <p className="text-sm text-status-warning">
              Vaga em rascunho — preencha os dados e publique quando estiver pronta
            </p>
          </div>
          <Button
            onClick={onPublish}
            disabled={isPublishing}
            className="ml-3 gap-2 px-5 py-2.5 text-sm font-medium rounded-xl bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active flex-shrink-0"
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
        <div className="flex-shrink-0 w-[220px]">
          <Card className="border border-lia-border-subtle bg-lia-bg-primary rounded-xl overflow-hidden">
            <nav className="p-3 h-full overflow-y-auto">
              <div className="mb-2">
                <span className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider px-3">
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
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans text-xs leading-[1.125rem] font-medium ${
                        activeSection === section.id
                          ? "bg-lia-bg-secondary border border-lia-btn-primary-bg text-wedo-cyan-dark"
                          : "hover:bg-lia-interactive-hover text-lia-text-primary border border-transparent"
                      }`}
                    >
                      <section.icon className="w-4 h-4 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className={`${textStyles.h4} 2xl:text-xs`}>{section.title}</div>
                        <div className={`${textStyles.description} 2xl:text-xs`}>{section.description}</div>
                      </div>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 text-status-success" />
                      ) : (
                        <Circle className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-disabled" />
                      )}
                    </button>
                  )
                })}
              </div>

              <div className="my-3 border-t border-lia-border-subtle" />

              <div className="mb-2">
                <span className="text-micro font-semibold text-lia-text-tertiary uppercase tracking-wider px-3">
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
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans text-xs leading-[1.125rem] font-medium ${
                        activeSection === section.id
                          ? "bg-lia-bg-secondary border border-lia-btn-primary-bg text-wedo-cyan-dark"
                          : "hover:bg-lia-interactive-hover text-lia-text-primary border border-transparent"
                      }`}
                    >
                      <section.icon className="w-4 h-4 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className={`${textStyles.h4} 2xl:text-xs`}>{section.title}</div>
                        <div className={`${textStyles.description} 2xl:text-xs`}>{section.description}</div>
                      </div>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 text-status-success" />
                      ) : (
                        <Circle className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-disabled" />
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

              {statusChangeConfirm && (
                <StatusChangeConfirmModal
                  state={statusChangeConfirm}
                  jobTitle={(job?.title as string) || (jobEditForm.title as string)}
                  onCancel={() => setStatusChangeConfirm(null)}
                  onChange={handleStatusChangeWithScreening}
                />
              )}

              {activeSection === "info-geral" && (
                <JobInfoGeralSection
                  jobEditForm={jobEditForm}
                  job={job as Record<string, unknown>}
                  companyDefaults={companyDefaults as Record<string, unknown> | undefined}
                  isEditing={isEditing}
                  updateField={updateField}
                  setActiveSection={setActiveSection}
                  setStatusChangeConfirm={setStatusChangeConfirm as (state: { newStatus: string; screeningImpact: string } | null) => void}
                  getScreeningImpact={getScreeningImpact}
                  publicLink={publicLink ?? undefined}
                />
              )}

              {activeSection === "pessoas" && (
                <div className="space-y-5">
                  <div>
                    <h3 className={groupHeaderClass}>Recrutador</h3>
                    <Card className="border border-lia-border-subtle">
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
                    <Card className="border border-lia-border-subtle">
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

              {activeSection === "processo" && (
                <JobProcessSection
                  stages={stages}
                  rawStages={rawStages}
                  loadingCompanyPipeline={loadingCompanyPipeline}
                  isEditing={isEditing}
                  LIA_ASSISTED_STAGES={LIA_ASSISTED_STAGES}
                  LIA_ASSISTED_STAGE_NAMES={LIA_ASSISTED_STAGE_NAMES}
                  addStage={addStage}
                  removeStage={removeStage}
                  updateStage={updateStage}
                  moveStage={moveStage}
                  vacancyId={vacancyId}
                  templates={templates}
                  isLoadingTemplates={isLoadingTemplates}
                  isApplyingTemplate={isApplyingTemplate}
                  onApplyTemplate={applyTemplate}
                  onSaveAsTemplate={saveStagesAsTemplate}
                  isSavingAsTemplate={isSavingAsTemplate}
                />
              )}

              {activeSection === "remuneracao" && (
                <JobRemuneracaoSection
                  jobEditForm={jobEditForm}
                  companyDefaults={companyDefaults as Record<string, unknown> | undefined}
                  isEditing={isEditing}
                  updateField={updateField}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
