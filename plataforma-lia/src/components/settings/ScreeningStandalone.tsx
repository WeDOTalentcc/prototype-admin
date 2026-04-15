"use client"

import React from "react"
import { useRecruitmentHub } from './useRecruitmentHub'
import { RecruitmentScreeningTab } from './RecruitmentScreeningTab'

export function ScreeningStandalone() {
  const hub = useRecruitmentHub('screening')

  return (
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
  )
}

export default ScreeningStandalone
