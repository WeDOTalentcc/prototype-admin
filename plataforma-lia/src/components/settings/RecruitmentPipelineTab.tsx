"use client"

import React, { useState } from"react"
import { Card, CardContent, CardHeader } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Layers, Save, CheckCircle, AlertCircle,
  Loader2, Pencil
} from"lucide-react"
import {
  RecruitmentJourneyConfig,
} from"@/components/settings/RecruitmentJourneyConfig"
import { PipelineTemplatesTab } from "@/components/settings/recruitment/pipeline-templates-tab"
import { useTranslations } from "next-intl"
import { textStyles, actionButtonStyles, tabStyles } from '@/lib/design-tokens'
import { useRecruitmentHub } from './useRecruitmentHub'
import { ConfigurableFieldCard } from "./_shared"
import { useLiaFieldTogglesForSection } from "@/hooks/settings/useLiaFieldTogglesForSection"
import { usePipelineTemplates } from '@/hooks/pipeline/use-pipeline-templates'

export function RecruitmentPipelineTab() {
  const t = useTranslations("settings")
  const hub = useRecruitmentHub('pipeline')
  const liaPipeline = useLiaFieldTogglesForSection(["pipeline"])
  const pipelineLiaField = liaPipeline.fields[0]
  const loading = hub.loading
  const error = hub.error
  const successMessage = hub.successMessage
  const recruitmentStages = hub.recruitmentStages
  const isEditingPipeline = hub.isEditingPipeline
  const hasStageChanges = hub.hasStageChanges
  const savingStages = hub.savingStages
  const onStagesChange = hub.handleStagesChange
  const onStartEdit = hub.handleStartEdit
  const onCancelEdit = hub.handleCancelEdit
  const onSave = hub.saveRecruitmentStages
  const onToggleSubStatus = hub.handleToggleSubStatus
  // Fase 4 Unify: Salvar como template
  const { createTemplate } = usePipelineTemplates()
  const [showSaveForm, setShowSaveForm] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [isSavingTemplate, setIsSavingTemplate] = useState(false)
  const [activeSubTab, setActiveSubTab] = useState<'default' | 'templates'>('default')

  const handleSaveAsTemplate = async () => {
    const trimmed = templateName.trim()
    if (!trimmed || isSavingTemplate) return
    setIsSavingTemplate(true)
    try {
      // Mapeia RecruitmentStage → PipelineStage (schema canônico)
      // Fase B Opcao 2: schema rico com sub-statuses embutidos
      const activeStages = recruitmentStages.filter(s => s.isActive)
      const stages = activeStages.map((s: any, idx: number) => ({
        name: s.name,
        display_name: s.display_name || s.name,
        order: s.order ?? idx + 1,
        color: s.color || null,
        icon: s.icon || null,
        stage_category: s.stageCategory || s.stage_category || 'custom',
        action_behavior: s.action_behavior || 'passive',
        default_channel: s.default_channel || 'email',
        sla_hours: s.sla ? s.sla * 24 : null,
        is_initial: false,
        is_final: ['hired', 'rejected'].includes(s.name),
        is_rejection: s.name === 'rejected',
        is_hired: s.name === 'hired',
        description: s.notes || s.description || '',
        sub_statuses: (s.sub_statuses || []).map((ss: any) => ({
          name: ss.name,
          display_name: ss.display_name,
          order: ss.sub_status_order ?? ss.order ?? 0,
          color: ss.color || null,
          icon: ss.icon || null,
          is_default: ss.is_default ?? false,
          is_waiting: ss.is_waiting ?? false,
          waiting_for: ss.waiting_for || null,
          sla_hours: ss.sla_hours || null,
        })),
        type: (() => {
          const ab = s.action_behavior || ''
          if (ab === 'screening' || ab === 'intake' || ab === 'trigger') return 'automatic' as const
          if (ab === 'proactive') return 'hybrid' as const
          return 'manual' as const
        })(),
        sla_days: s.sla ?? 3,
      }))
      await createTemplate({ name: trimmed, stages })
      setShowSaveForm(false)
      setTemplateName('')
    } catch {
      // createTemplate já exibe toast de erro
    } finally {
      setIsSavingTemplate(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="border-0 rounded-md backdrop-blur-sm animate-pulse motion-reduce:animate-none">
          <CardHeader className="pb-4">
            <div className="h-5 w-48 rounded-md bg-lia-border-medium opacity-30"></div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="w-28 h-16 rounded-md bg-lia-border-medium opacity-20"></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="w-full" data-testid="pipeline-tab-root">
      {pipelineLiaField && (
        <ConfigurableFieldCard
          label={pipelineLiaField.label}
          hint={pipelineLiaField.hint}
          instruction={pipelineLiaField.instruction}
          onInstructionSave={pipelineLiaField.onInstructionSave}
          showToggle
          isActive={pipelineLiaField.isActive}
          onToggleChange={pipelineLiaField.onToggleChange}
          isSaving={pipelineLiaField.isSaving}
          isReadOnly={!isEditingPipeline}
        />
      )}
      <div className={`${tabStyles.pillContainer} mb-4`} role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeSubTab === 'default'}
          onClick={() => setActiveSubTab('default')}
          data-testid="pipeline-subtab-default"
          className={activeSubTab === 'default' ? tabStyles.pillActive : tabStyles.pill}
        >
          {t("recruitment.pipeline.subTabs.default")}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeSubTab === 'templates'}
          onClick={() => setActiveSubTab('templates')}
          data-testid="pipeline-subtab-templates"
          className={activeSubTab === 'templates' ? tabStyles.pillActive : tabStyles.pill}
        >
          {t("recruitment.pipeline.subTabs.templates")}
        </button>
      </div>
      {activeSubTab === 'default' && (
    <div className="space-y-6" data-testid="pipeline-tab-default-content">
      {error && (
        <div className="px-2 py-1.5 rounded-full flex items-center gap-2 bg-status-error/10 border border-status-error/30 text-status-error">
          <AlertCircle className="w-4 h-4" />
          <span className={textStyles.body}>{error}</span>
        </div>
      )}
      {successMessage && (
        <div className="px-2 py-1.5 rounded-full flex items-center gap-2 bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-4 h-4" />
          <span className={textStyles.body}>{successMessage}</span>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {isEditingPipeline && hasStageChanges && (
            <Chip variant="neutral" className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-micro">
              {t("recruitment.pipeline.unsavedChanges")}
            </Chip>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isEditingPipeline ? (
            <>
              <button
                data-testid="pipeline-edit-cancel"
                onClick={onCancelEdit}
                disabled={savingStages}
                className={actionButtonStyles.smSecondary}
              >
                {t("recruitment.pipeline.cancel")}
              </button>
              <button
                data-testid="pipeline-edit-save"
                onClick={onSave}
                disabled={!hasStageChanges || savingStages}
                className={actionButtonStyles.smPrimary}
              >
                {savingStages ? (
                  <>
                    <Loader2 className={`${actionButtonStyles.icon} animate-spin motion-reduce:animate-none`} />
                    {t("recruitment.pipeline.saving")}
                  </>
                ) : (
                  <>
                    <Save className={actionButtonStyles.icon} />
                    {t("recruitment.pipeline.saveChanges")}
                  </>
                )}
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              {showSaveForm ? (
                <>
                  <input
                    type="text"
                    value={templateName}
                    onChange={e => setTemplateName(e.target.value)}
                    placeholder="Nome do template..."
                    aria-label="Nome do template"
                    className="text-xs px-2.5 py-1.5 rounded-md border border-lia-border-subtle bg-lia-bg-primary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 w-44"
                    onKeyDown={e => {
                      if (e.key === 'Enter') handleSaveAsTemplate()
                      if (e.key === 'Escape') { setShowSaveForm(false); setTemplateName('') }
                    }}
                    autoFocus
                  />
                  <button
                    onClick={handleSaveAsTemplate}
                    disabled={!templateName.trim() || isSavingTemplate}
                    className={actionButtonStyles.smPrimary}
                  >
                    {isSavingTemplate ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Salvar'}
                  </button>
                  <button
                    onClick={() => { setShowSaveForm(false); setTemplateName('') }}
                    className={actionButtonStyles.smSecondary}
                  >
                    Cancelar
                  </button>
                </>
              ) : (
                <button
                  data-testid="pipeline-save-as-template"
                  onClick={() => setShowSaveForm(true)}
                  className={actionButtonStyles.smOutline}
                  title="Criar template reutilizável a partir deste pipeline"
                >
                  <Layers className={actionButtonStyles.icon} />
                  Salvar como template
                </button>
              )}
              <button
                data-testid="pipeline-edit-start"
                onClick={onStartEdit}
                className={actionButtonStyles.smOutline}
              >
                <Pencil className={actionButtonStyles.icon} />
                {t("recruitment.pipeline.edit")}
              </button>
            </div>
          )}
        </div>
      </div>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
        <CardContent className="p-6">
          <RecruitmentJourneyConfig
            stages={recruitmentStages}
            onChange={onStagesChange}
            isEditMode={isEditingPipeline}
            onToggleSubStatus={onToggleSubStatus}
          />
        </CardContent>
      </Card>
    </div>
      )}
      {activeSubTab === 'templates' && (
        <div className="space-y-6" data-testid="pipeline-tab-templates-content">
          <PipelineTemplatesTab />
        </div>
      )}
    </div>
  )
}
