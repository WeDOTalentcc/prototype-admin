"use client"

import React from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Save, CheckCircle, AlertCircle,
  Loader2, Pencil
} from "lucide-react"
import {
  RecruitmentJourneyConfig,
  RecruitmentStage,
} from "@/components/settings/RecruitmentJourneyConfig"
import { textStyles, actionButtonStyles } from '@/lib/design-tokens'

interface RecruitmentPipelineTabProps {
  loading: boolean
  error: string | null
  successMessage: string | null
  recruitmentStages: RecruitmentStage[]
  isEditingPipeline: boolean
  hasStageChanges: boolean
  savingStages: boolean
  onStagesChange: (stages: RecruitmentStage[]) => void
  onStartEdit: () => void
  onCancelEdit: () => void
  onSave: () => void
  onToggleSubStatus: (subStatusId: string, updates: { is_active?: boolean; is_default?: boolean }) => Promise<void>
}

export function RecruitmentPipelineTab({
  loading, error, successMessage,
  recruitmentStages, isEditingPipeline, hasStageChanges, savingStages,
  onStagesChange, onStartEdit, onCancelEdit, onSave, onToggleSubStatus,
}: RecruitmentPipelineTabProps) {
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
    <div className="space-y-6">
      {error && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-error/10 border border-status-error/30 text-status-error">
          <AlertCircle className="w-4 h-4" />
          <span className={textStyles.body}>{error}</span>
        </div>
      )}
      {successMessage && (
        <div className="px-2 py-1.5 rounded-md flex items-center gap-2 bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-4 h-4" />
          <span className={textStyles.body}>{successMessage}</span>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {isEditingPipeline && hasStageChanges && (
            <Badge variant="outline" className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle text-micro">
              Alterações não salvas
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isEditingPipeline ? (
            <>
              <button
                onClick={onCancelEdit}
                disabled={savingStages}
                className={actionButtonStyles.smSecondary}
              >
                Cancelar
              </button>
              <button
                onClick={onSave}
                disabled={!hasStageChanges || savingStages}
                className={actionButtonStyles.smPrimary}
              >
                {savingStages ? (
                  <>
                    <Loader2 className={`${actionButtonStyles.icon} animate-spin motion-reduce:animate-none`} />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Save className={actionButtonStyles.icon} />
                    Salvar Alterações
                  </>
                )}
              </button>
            </>
          ) : (
            <button
              onClick={onStartEdit}
              className={actionButtonStyles.smOutline}
            >
              <Pencil className={actionButtonStyles.icon} />
              Editar
            </button>
          )}
        </div>
      </div>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
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
  )
}
