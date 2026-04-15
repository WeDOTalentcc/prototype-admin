"use client"

import React from "react"
import { useRecruitmentHub } from './useRecruitmentHub'
import { RecruitmentPipelineTab } from './RecruitmentPipelineTab'

export function PipelineStandalone() {
  const hub = useRecruitmentHub('pipeline')

  return (
    <RecruitmentPipelineTab
      loading={hub.loading}
      error={hub.error}
      successMessage={hub.successMessage}
      recruitmentStages={hub.recruitmentStages}
      isEditingPipeline={hub.isEditingPipeline}
      hasStageChanges={hub.hasStageChanges}
      savingStages={hub.savingStages}
      onStagesChange={hub.handleStagesChange}
      onStartEdit={hub.handleStartEdit}
      onCancelEdit={hub.handleCancelEdit}
      onSave={hub.saveRecruitmentStages}
      onToggleSubStatus={hub.handleToggleSubStatus}
    />
  )
}

export default PipelineStandalone
