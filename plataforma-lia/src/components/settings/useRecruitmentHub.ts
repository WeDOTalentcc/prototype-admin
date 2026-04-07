"use client"

import { useState, useEffect } from "react"
import {
  RecruitmentStage,
  SubStatus,
  DEFAULT_STAGES
} from "@/components/settings/RecruitmentJourneyConfig"
import {
  ELIGIBILITY_QUESTIONS_BANK,
  QUESTION_CATEGORIES,
  QuestionCategory,
  EligibilityQuestionTemplate,
} from "@/components/settings/eligibility-questions-bank"

interface RawPipelineStage {
  id: string
  name: string
  display_name: string
  stage_order?: number
  is_active?: boolean
  description?: string
  sla_hours?: number
  stage_category?: string
  color?: string
  icon?: string
  action_behavior?: string
  default_channel?: string
  sub_statuses?: unknown[]
  catalog_id?: string
}

interface RawScreeningQuestion {
  id: string
  question_text?: string
  question?: string
  question_type?: string
  is_required?: boolean
  order?: number
  is_default?: boolean
  options?: string[]
  is_eliminatory?: boolean
  expected_answer?: string
}

export interface ScreeningQuestion {
  id: string
  question: string
  type: 'text' | 'yesno' | 'scale' | 'multiple'
  required: boolean
  order: number
  isDefault: boolean
  options?: string[]
  is_eliminatory?: boolean
  expected_answer?: string
}

export interface NewQuestionForm {
  question: string
  type: 'text' | 'yesno' | 'scale' | 'multiple'
  required: boolean
  is_eliminatory: boolean
  expected_answer: string
}

function mapRawPipelineStage(s: RawPipelineStage, idx: number): RecruitmentStage {
  return {
    id: s.id,
    name: s.name,
    display_name: s.display_name,
    order: s.stage_order || idx + 1,
    isActive: s.is_active ?? true,
    notes: s.description || "",
    sla: s.sla_hours ? Math.round(s.sla_hours / 24) : 0,
    type: s.stage_category === 'system' ? 'system' : (s.stage_category === 'catalog' ? 'default' : 'custom'),
    color: s.color,
    icon: s.icon,
    action_behavior: s.action_behavior,
    default_channel: s.default_channel || 'email',
    stage_category: s.stage_category,
    sub_statuses: (s.sub_statuses || []) as SubStatus[],
  }
}

export function useRecruitmentHub(activeSubsection?: string) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'pipeline')
  const [questions, setQuestions] = useState<ScreeningQuestion[]>([])
  const [originalQuestions, setOriginalQuestions] = useState<ScreeningQuestion[]>([])
  const [showQuestionForm, setShowQuestionForm] = useState(false)
  const [newQuestion, setNewQuestion] = useState<NewQuestionForm>({
    question: '',
    type: 'text',
    required: true,
    is_eliminatory: false,
    expected_answer: ''
  })

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const [recruitmentStages, setRecruitmentStages] = useState<RecruitmentStage[]>(DEFAULT_STAGES)
  const [originalStages, setOriginalStages] = useState<RecruitmentStage[]>([])
  const [hasStageChanges, setHasStageChanges] = useState(false)
  const [savingStages, setSavingStages] = useState(false)
  const [isEditingPipeline, setIsEditingPipeline] = useState(false)
  const [stagesBeforeEdit, setStagesBeforeEdit] = useState<RecruitmentStage[]>([])

  const [showQuestionBank, setShowQuestionBank] = useState(false)
  const [expandedCategories, setExpandedCategories] = useState<Set<QuestionCategory>>(new Set())
  const [selectedBankQuestions, setSelectedBankQuestions] = useState<Set<string>>(new Set())

  const [isEditingQuestions, setIsEditingQuestions] = useState(false)
  const [questionsBeforeEdit, setQuestionsBeforeEdit] = useState<ScreeningQuestion[]>([])
  const [savingQuestions, setSavingQuestions] = useState(false)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)

        const [questionsRes, pipelineRes] = await Promise.all([
          fetch('/api/backend-proxy/company/screening-questions'),
          fetch('/api/backend-proxy/company-pipeline')
        ])

        if (questionsRes.ok) {
          const questionsResult = await questionsRes.json()
          const rawList: RawScreeningQuestion[] = questionsResult.items ?? (Array.isArray(questionsResult) ? questionsResult : [])
          const mapped = rawList.map((q: RawScreeningQuestion) => ({
            id: q.id,
            question: q.question_text || q.question,
            type: q.question_type === 'yes_no' ? 'yesno' : (q.question_type || 'text'),
            required: q.is_required ?? true,
            order: q.order || 0,
            isDefault: q.is_default ?? false,
            options: q.options || [],
            is_eliminatory: q.is_eliminatory ?? false,
            expected_answer: q.expected_answer || undefined,
          }))
          setQuestions(mapped as ScreeningQuestion[])
          setOriginalQuestions(mapped as ScreeningQuestion[])
        }

        if (pipelineRes.ok) {
          const pipelineData = await pipelineRes.json()
          if (pipelineData.pipeline && Array.isArray(pipelineData.pipeline)) {
            const stages = pipelineData.pipeline.map(mapRawPipelineStage)
            setRecruitmentStages(stages)
            setOriginalStages(stages)
          }
        }

      } catch (err) {
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const saveQuestionsToAPI = async (updatedQuestions: ScreeningQuestion[]) => {
    try {
      setSaving(true)
      const isTempId = (id: string) => id.startsWith('q-') || id.startsWith('bank-')

      const newOnes = updatedQuestions.filter(q => isTempId(q.id))
      const savedNew: ScreeningQuestion[] = []
      for (const q of newOnes) {
        const res = await fetch('/api/backend-proxy/company/screening-questions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question_text: q.question,
            question_type: q.type === 'yesno' ? 'yes_no' : q.type,
            is_required: q.required,
            order: q.order,
            options: q.options,
            is_eliminatory: q.is_eliminatory || false,
            expected_answer: q.expected_answer || null,
          }),
        })
        if (res.ok) {
          const data = await res.json()
          savedNew.push({ ...q, id: data.id || q.id })
        }
      }

      const updatedIds = new Set(updatedQuestions.filter(q => !isTempId(q.id)).map(q => q.id))
      const removed = originalQuestions.filter(q => !isTempId(q.id) && !updatedIds.has(q.id))
      for (const q of removed) {
        await fetch(`/api/backend-proxy/company/screening-questions/${q.id}`, { method: 'DELETE' })
      }

      const persisted = updatedQuestions
        .filter(q => !isTempId(q.id))
        .concat(savedNew)
      setQuestions(persisted)
      setOriginalQuestions(persisted)

      setSuccessMessage('Perguntas salvas com sucesso!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError('Erro ao salvar perguntas. Tente novamente.')
      setTimeout(() => setError(null), 3000)
    } finally {
      setSaving(false)
    }
  }

  const handleStagesChange = (newStages: RecruitmentStage[]) => {
    setRecruitmentStages(newStages)
    setHasStageChanges(JSON.stringify(newStages) !== JSON.stringify(originalStages))
  }

  const handleStartEdit = () => {
    setStagesBeforeEdit([...recruitmentStages])
    setIsEditingPipeline(true)
  }

  const handleCancelEdit = () => {
    setRecruitmentStages(stagesBeforeEdit)
    setHasStageChanges(false)
    setIsEditingPipeline(false)
  }

  const saveRecruitmentStages = async () => {
    setSavingStages(true)
    try {
      const stagesPayload = recruitmentStages.map((s, idx) => ({
        id: s.id.startsWith('stage-') || s.id.startsWith('catalog-') ? undefined : s.id,
        catalog_id: s.catalog_id || undefined,
        name: s.name,
        display_name: s.display_name || s.name,
        stage_order: idx + 1,
        color: s.color,
        icon: s.icon,
        sla_hours: s.sla ? s.sla * 24 : null,
        is_active: s.isActive,
        action_behavior: s.action_behavior || 'passive',
        default_channel: s.default_channel || 'email',
      }))

      const response = await fetch('/api/backend-proxy/company-pipeline', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: stagesPayload })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.pipeline) {
          const updatedStages = data.pipeline.map(mapRawPipelineStage)
          setRecruitmentStages(updatedStages)
          setOriginalStages(updatedStages)
        }
        setHasStageChanges(false)
        setIsEditingPipeline(false)
        setSuccessMessage('Pipeline salvo com sucesso!')
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        setError('Erro ao salvar pipeline. Tente novamente.')
        setTimeout(() => setError(null), 3000)
      }
    } catch (error) {
      setError('Erro ao salvar pipeline. Tente novamente.')
      setTimeout(() => setError(null), 3000)
    } finally {
      setSavingStages(false)
    }
  }

  const handleToggleSubStatus = async (
    subStatusId: string,
    updates: { is_active?: boolean; is_default?: boolean }
  ): Promise<void> => {
    try {
      const response = await fetch(
        `/api/backend-proxy/recruitment-stages/sub-statuses/${subStatusId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        }
      )
      if (response.ok && updates.is_active !== undefined) {
        setRecruitmentStages(prev => prev.map(s => {
          const sub = (s.sub_statuses || []).find(ss => ss.id === subStatusId)
          if (!sub) return s
          return {
            ...s,
            sub_statuses: updates.is_active
              ? s.sub_statuses
              : (s.sub_statuses || []).filter(ss => ss.id !== subStatusId),
          }
        }))
      }
    } catch {
    }
  }

  const handleAddQuestion = () => {
    if (newQuestion.question.trim()) {
      const question: ScreeningQuestion = {
        id: `q-${Date.now()}`,
        question: newQuestion.question,
        type: newQuestion.type,
        required: newQuestion.required,
        order: questions.length + 1,
        isDefault: false,
        is_eliminatory: newQuestion.is_eliminatory,
        expected_answer: newQuestion.is_eliminatory ? newQuestion.expected_answer : undefined
      }
      setQuestions(prev => [...prev, question])
      setNewQuestion({ question: '', type: 'text', required: true, is_eliminatory: false, expected_answer: '' })
      setShowQuestionForm(false)
    }
  }

  const handleDeleteQuestion = (id: string) => {
    setQuestions(prev => prev.filter(q => q.id !== id))
  }

  const handleToggleRequired = (id: string) => {
    setQuestions(prev => prev.map(q =>
      q.id === id ? { ...q, required: !q.required } : q
    ))
  }

  const toggleCategory = (category: QuestionCategory) => {
    setExpandedCategories(prev => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  const toggleBankQuestion = (questionId: string) => {
    setSelectedBankQuestions(prev => {
      const next = new Set(prev)
      if (next.has(questionId)) {
        next.delete(questionId)
      } else {
        next.add(questionId)
      }
      return next
    })
  }

  const handleAddFromBank = () => {
    const selectedQuestions = ELIGIBILITY_QUESTIONS_BANK.filter(q => selectedBankQuestions.has(q.id))
    const newQuestions: ScreeningQuestion[] = selectedQuestions.map((q, idx) => ({
      id: `bank-${Date.now()}-${idx}`,
      question: q.question,
      type: q.type,
      required: false,
      order: questions.length + idx + 1,
      isDefault: false,
      options: q.options,
      is_eliminatory: q.eliminatory ?? false,
      expected_answer: q.eliminatoryAnswer?.toString()
    }))
    setQuestions(prev => [...prev, ...newQuestions])
    setSelectedBankQuestions(new Set())
    setShowQuestionBank(false)
  }

  const getQuestionsByCategory = (category: QuestionCategory) => {
    return ELIGIBILITY_QUESTIONS_BANK.filter(q => q.category === category)
  }

  const isQuestionAlreadyAdded = (bankQuestion: EligibilityQuestionTemplate) => {
    return questions.some(q => q.question.toLowerCase() === bankQuestion.question.toLowerCase())
  }

  const handleStartEditQuestions = () => {
    setQuestionsBeforeEdit([...questions])
    setIsEditingQuestions(true)
  }

  const handleCancelEditQuestions = () => {
    setQuestions(questionsBeforeEdit)
    setIsEditingQuestions(false)
    setShowQuestionForm(false)
    setShowQuestionBank(false)
    setSelectedBankQuestions(new Set())
  }

  const handleSaveQuestions = async () => {
    setSavingQuestions(true)
    try {
      await saveQuestionsToAPI(questions)
      setIsEditingQuestions(false)
      setShowQuestionForm(false)
      setShowQuestionBank(false)
    } finally {
      setSavingQuestions(false)
    }
  }

  return {
    activeTab, setActiveTab,
    questions, setQuestions,
    showQuestionForm, setShowQuestionForm,
    newQuestion, setNewQuestion,
    loading, saving,
    error, successMessage,
    recruitmentStages,
    hasStageChanges, savingStages,
    isEditingPipeline,
    showQuestionBank, setShowQuestionBank,
    expandedCategories, selectedBankQuestions,
    isEditingQuestions, savingQuestions,
    handleStagesChange, handleStartEdit, handleCancelEdit,
    saveRecruitmentStages, handleToggleSubStatus,
    handleAddQuestion, handleDeleteQuestion, handleToggleRequired,
    toggleCategory, toggleBankQuestion, handleAddFromBank,
    getQuestionsByCategory, isQuestionAlreadyAdded,
    handleStartEditQuestions, handleCancelEditQuestions, handleSaveQuestions,
  }
}
