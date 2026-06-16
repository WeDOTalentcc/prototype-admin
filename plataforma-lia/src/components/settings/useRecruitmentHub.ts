"use client"

import { useState } from "react"
import { useRecruitmentPersistence } from "./useRecruitmentPersistence"
import { useRecruitmentPipeline } from "./useRecruitmentPipeline"
import { useRecruitmentScreening } from "./useRecruitmentScreening"

export type { ScreeningQuestion, NewQuestionForm } from "./recruitment-types"

export function useRecruitmentHub(activeSubsection?: string) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'pipeline')
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const onSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }
  const onError = (msg: string) => {
    setError(msg)
    setTimeout(() => setError(null), 3000)
  }

  const persistence = useRecruitmentPersistence()
  const pipeline = useRecruitmentPipeline({ persistence, onSuccess, onError })
  const screening = useRecruitmentScreening({ persistence, onSuccess, onError })

  // P1-W1-04: merge fetchError from persistence into the hub error channel
  const effectiveError = error || persistence.fetchError

  return {
    activeTab,
    setActiveTab,
    loading: persistence.loading,
    error: effectiveError,
    successMessage,
    saving: screening.saving,

    // Pipeline
    recruitmentStages: pipeline.recruitmentStages,
    hasStageChanges: pipeline.hasStageChanges,
    savingStages: pipeline.savingStages,
    isEditingPipeline: pipeline.isEditingPipeline,
    handleStagesChange: pipeline.handleStagesChange,
    handleStartEdit: pipeline.handleStartEdit,
    handleCancelEdit: pipeline.handleCancelEdit,
    saveRecruitmentStages: pipeline.saveRecruitmentStages,
    handleToggleSubStatus: pipeline.handleToggleSubStatus,

    // Screening
    questions: screening.questions,
    setQuestions: screening.setQuestions,
    showQuestionForm: screening.showQuestionForm,
    setShowQuestionForm: screening.setShowQuestionForm,
    newQuestion: screening.newQuestion,
    setNewQuestion: screening.setNewQuestion,
    showQuestionBank: screening.showQuestionBank,
    setShowQuestionBank: screening.setShowQuestionBank,
    expandedCategories: screening.expandedCategories,
    selectedBankQuestions: screening.selectedBankQuestions,
    isEditingQuestions: screening.isEditingQuestions,
    savingQuestions: screening.savingQuestions,
    handleAddQuestion: screening.handleAddQuestion,
    handleDeleteQuestion: screening.handleDeleteQuestion,
    handleToggleRequired: screening.handleToggleRequired,
    toggleCategory: screening.toggleCategory,
    toggleBankQuestion: screening.toggleBankQuestion,
    handleAddFromBank: screening.handleAddFromBank,
    getQuestionsByCategory: screening.getQuestionsByCategory,
    isQuestionAlreadyAdded: screening.isQuestionAlreadyAdded,
    handleStartEditQuestions: screening.handleStartEditQuestions,
    handleCancelEditQuestions: screening.handleCancelEditQuestions,
    handleSaveQuestions: screening.handleSaveQuestions,
  }
}
