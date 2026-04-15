"use client"

import React from "react"
import {
  Workflow, MessageSquare, ShieldCheck,
} from "lucide-react"
import { useTranslations } from "next-intl"
import { HiringPoliciesHub } from './HiringPoliciesHub'
import { tabStyles } from '@/lib/design-tokens'
import { useRecruitmentHub } from './useRecruitmentHub'
import { RecruitmentPipelineTab } from './RecruitmentPipelineTab'
import { RecruitmentScreeningTab } from './RecruitmentScreeningTab'

interface RecruitmentHubProps {
  activeSubsection?: string
  visibleTabs?: string[]
}

export function RecruitmentHub({ activeSubsection, visibleTabs }: RecruitmentHubProps) {
  const t = useTranslations("settings")
  const hub = useRecruitmentHub(activeSubsection)

  const allTabs = [
    { id: 'pipeline', label: t("recruitment.tabPipeline"), icon: Workflow },
    { id: 'screening', label: t("recruitment.tabScreening"), icon: MessageSquare },
    { id: 'hiring-policies', label: t("recruitment.tabHiringPolicies"), icon: ShieldCheck },
  ]

  const tabs = visibleTabs ? allTabs.filter(tab => visibleTabs.includes(tab.id)) : allTabs

  return (
    <div className="space-y-6">
      {tabs.length > 1 && (
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => hub.setActiveTab(tab.id)}
            className={hub.activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>
      )}

      {hub.activeTab === 'pipeline' && (
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
      )}

      {hub.activeTab === 'screening' && (
        <RecruitmentScreeningTab
          error={hub.error}
          successMessage={hub.successMessage}
          questions={hub.questions}
          showQuestionForm={hub.showQuestionForm}
          setShowQuestionForm={hub.setShowQuestionForm}
          newQuestion={hub.newQuestion}
          setNewQuestion={hub.setNewQuestion}
          isEditingQuestions={hub.isEditingQuestions}
          savingQuestions={hub.savingQuestions}
          showQuestionBank={hub.showQuestionBank}
          setShowQuestionBank={hub.setShowQuestionBank}
          expandedCategories={hub.expandedCategories}
          selectedBankQuestions={hub.selectedBankQuestions}
          onStartEditQuestions={hub.handleStartEditQuestions}
          onCancelEditQuestions={hub.handleCancelEditQuestions}
          onSaveQuestions={hub.handleSaveQuestions}
          onAddQuestion={hub.handleAddQuestion}
          onDeleteQuestion={hub.handleDeleteQuestion}
          onToggleRequired={hub.handleToggleRequired}
          onToggleCategory={hub.toggleCategory}
          onToggleBankQuestion={hub.toggleBankQuestion}
          onAddFromBank={hub.handleAddFromBank}
          getQuestionsByCategory={hub.getQuestionsByCategory}
          isQuestionAlreadyAdded={hub.isQuestionAlreadyAdded}
        />
      )}

      {hub.activeTab === 'hiring-policies' && <HiringPoliciesHub />}
    </div>
  )
}

export default RecruitmentHub
