"use client"

import { useState } from "react"
import {
  useEligibilityTemplates,
  flattenTemplates,
  type FlatEligibilityQuestion,
  type QuestionCategory,
} from "@/hooks/screening/use-eligibility-templates"
import type { NewQuestionForm, ScreeningQuestion } from "./recruitment-types"
import type { RecruitmentPersistenceState } from "./useRecruitmentPersistence"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

export interface RecruitmentScreeningState {
  questions: ScreeningQuestion[]
  setQuestions: React.Dispatch<React.SetStateAction<ScreeningQuestion[]>>
  showQuestionForm: boolean
  setShowQuestionForm: React.Dispatch<React.SetStateAction<boolean>>
  newQuestion: NewQuestionForm
  setNewQuestion: React.Dispatch<React.SetStateAction<NewQuestionForm>>
  saving: boolean
  showQuestionBank: boolean
  setShowQuestionBank: React.Dispatch<React.SetStateAction<boolean>>
  expandedCategories: Set<QuestionCategory>
  selectedBankQuestions: Set<string>
  isEditingQuestions: boolean
  savingQuestions: boolean
  handleAddQuestion: () => void
  handleDeleteQuestion: (id: string) => void
  handleToggleRequired: (id: string) => void
  toggleCategory: (category: QuestionCategory) => void
  toggleBankQuestion: (questionId: string) => void
  handleAddFromBank: () => void
  getQuestionsByCategory: (category: QuestionCategory) => FlatEligibilityQuestion[]
  isQuestionAlreadyAdded: (bankQuestion: FlatEligibilityQuestion) => boolean
  handleStartEditQuestions: () => void
  handleCancelEditQuestions: () => void
  handleSaveQuestions: () => Promise<void>
}

interface ScreeningHookOptions {
  persistence: RecruitmentPersistenceState
  onSuccess: (msg: string) => void
  onError: (msg: string) => void
}

export function useRecruitmentScreening({
  persistence,
  onSuccess,
  onError,
}: ScreeningHookOptions): RecruitmentScreeningState {
  // F4 audit 2026-05-20: catalogo dinamico via useEligibilityTemplates
  const { templates: _eligTemplates } = useEligibilityTemplates({ includeMaster: true })
  const ELIGIBILITY_QUESTIONS_BANK = flattenTemplates(_eligTemplates)

  const {
    questions,
    setQuestions,
    originalQuestions,
    setOriginalQuestions,
  } = persistence

  const [showQuestionForm, setShowQuestionForm] = useState(false)
  const [newQuestion, setNewQuestion] = useState<NewQuestionForm>({
    question: '',
    type: 'text',
    required: true,
    is_eliminatory: false,
    expected_answer: '',
  })
  const [saving, setSaving] = useState(false)
  const [showQuestionBank, setShowQuestionBank] = useState(false)
  const [expandedCategories, setExpandedCategories] = useState<Set<QuestionCategory>>(
    new Set()
  )
  const [selectedBankQuestions, setSelectedBankQuestions] = useState<Set<string>>(
    new Set()
  )
  const [isEditingQuestions, setIsEditingQuestions] = useState(false)
  const [questionsBeforeEdit, setQuestionsBeforeEdit] = useState<ScreeningQuestion[]>([])
  const [savingQuestions, setSavingQuestions] = useState(false)

  const saveQuestionsToAPI = async (updatedQuestions: ScreeningQuestion[]) => {
    try {
      setSaving(true)
      const isTempId = (id: string) => id.startsWith('q-') || id.startsWith('bank-')

      const newOnes = updatedQuestions.filter(q => isTempId(q.id))
      const savedNew: ScreeningQuestion[] = []
      for (const q of newOnes) {
        const res = await apiFetch('/api/backend-proxy/company/screening-questions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question_text: q.question,
            question_type: q.type,
            is_required: q.required,
            order: q.order,
            options: q.options,
            is_eliminatory: q.is_eliminatory || false,
            expected_answer: q.expected_answer || null,
            category: q.category || null,
          }),
        })
        if (res.ok) {
          notifyChatOfSettingsUpdate({ actionId: "configure_screening", section: "screening_rules" })
          const data = await res.json()
          savedNew.push({ ...q, id: data.id || q.id })
        }
      }

      const updatedIds = new Set(
        updatedQuestions.filter(q => !isTempId(q.id)).map(q => q.id)
      )
      const removed = originalQuestions.filter(
        q => !isTempId(q.id) && !updatedIds.has(q.id)
      )
      for (const q of removed) {
        await apiFetch(`/api/backend-proxy/company/screening-questions/${q.id}`, {
          method: 'DELETE',
        })
      }

      // P0-W1-07: PUT edições em perguntas existentes
      const originalMap = new Map(originalQuestions.map(q => [q.id, q]))
      const toUpdate = updatedQuestions.filter(q => {
        if (isTempId(q.id)) return false
        const orig = originalMap.get(q.id)
        if (!orig) return false
        return (
          q.question !== orig.question ||
          q.type !== orig.type ||
          q.required !== orig.required ||
          q.is_eliminatory !== orig.is_eliminatory ||
          q.expected_answer !== orig.expected_answer ||
          q.category !== orig.category
        )
      })
      for (const q of toUpdate) {
        await apiFetch(`/api/backend-proxy/company/screening-questions/${q.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question_text: q.question,
            question_type: q.type,
            is_required: q.required,
            is_eliminatory: q.is_eliminatory || false,
            expected_answer: q.expected_answer || null,
            category: q.category || null,
          }),
        })
      }

      const persisted = updatedQuestions
        .filter(q => !isTempId(q.id))
        .concat(savedNew)
      setQuestions(persisted)
      setOriginalQuestions(persisted)

      onSuccess('Perguntas salvas com sucesso!')
    } catch (err) {
      // P0-W1-07: falhar alto, nunca silenciosamente (REGRA 4 canonical)
      console.error('[saveQuestionsToAPI] failed:', err)
      onError('Erro ao salvar perguntas. Tente novamente.')
    } finally {
      setSaving(false)
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
        expected_answer: newQuestion.is_eliminatory ? newQuestion.expected_answer : undefined,
      }
      setQuestions(prev => [...prev, question])
      setNewQuestion({
        question: '',
        type: 'text',
        required: true,
        is_eliminatory: false,
        expected_answer: '',
      })
      setShowQuestionForm(false)
    }
  }

  const handleDeleteQuestion = (id: string) => {
    setQuestions(prev => prev.filter(q => q.id !== id))
  }

  const handleToggleRequired = (id: string) => {
    setQuestions(prev =>
      prev.map(q => (q.id === id ? { ...q, required: !q.required } : q))
    )
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
    const selectedQuestions = ELIGIBILITY_QUESTIONS_BANK.filter(q =>
      selectedBankQuestions.has(q.id)
    )
    const newQuestions: ScreeningQuestion[] = selectedQuestions.map((q, idx) => ({
      id: `bank-${Date.now()}-${idx}`,
      question: q.question,
      type: q.type,
      required: false,
      order: questions.length + idx + 1,
      isDefault: false,
      options: q.options,
      is_eliminatory: q.eliminatory ?? false,
      expected_answer: q.eliminatoryAnswer?.toString(),
      // P0-W1-09: preservar categoria do template de eligibility para serialização correta
      category: q.category || undefined,
    }))
    setQuestions(prev => [...prev, ...newQuestions])
    setSelectedBankQuestions(new Set())
    setShowQuestionBank(false)
  }

  const getQuestionsByCategory = (category: QuestionCategory) => {
    return ELIGIBILITY_QUESTIONS_BANK.filter(q => q.category === category)
  }

  const isQuestionAlreadyAdded = (bankQuestion: FlatEligibilityQuestion) => {
    return questions.some(
      q => q.question.toLowerCase() === bankQuestion.question.toLowerCase()
    )
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
    questions,
    setQuestions,
    showQuestionForm,
    setShowQuestionForm,
    newQuestion,
    setNewQuestion,
    saving,
    showQuestionBank,
    setShowQuestionBank,
    expandedCategories,
    selectedBankQuestions,
    isEditingQuestions,
    savingQuestions,
    handleAddQuestion,
    handleDeleteQuestion,
    handleToggleRequired,
    toggleCategory,
    toggleBankQuestion,
    handleAddFromBank,
    getQuestionsByCategory,
    isQuestionAlreadyAdded,
    handleStartEditQuestions,
    handleCancelEditQuestions,
    handleSaveQuestions,
  }
}
