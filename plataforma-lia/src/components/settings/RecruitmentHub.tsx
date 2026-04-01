"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Workflow, MessageSquare, Plus, Trash2, Save, X,
  CheckCircle, AlertCircle,
  Lock, Eye, Loader2, Pencil,
  ChevronDown, ChevronUp, Library, Brain, ShieldCheck,
} from "lucide-react"
import {
  RecruitmentJourneyConfig,
  RecruitmentStage,
  DEFAULT_STAGES
} from "@/components/settings/RecruitmentJourneyConfig"
import { 
  ELIGIBILITY_QUESTIONS_BANK,
  QUESTION_CATEGORIES,
  QuestionCategory,
  EligibilityQuestionTemplate,
} from "@/components/settings/eligibility-questions-bank"
import { HiringPoliciesHub } from './HiringPoliciesHub'
import { textStyles, tabStyles, actionButtonStyles } from '@/lib/design-tokens'

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

interface ScreeningQuestion {
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

interface RecruitmentHubProps {
  activeSubsection?: string
}


export function RecruitmentHub({ activeSubsection }: RecruitmentHubProps) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'pipeline')
  const [questions, setQuestions] = useState<ScreeningQuestion[]>([])
  const [originalQuestions, setOriginalQuestions] = useState<ScreeningQuestion[]>([])
  const [showQuestionForm, setShowQuestionForm] = useState(false)
  const [newQuestion, setNewQuestion] = useState<{
    question: string
    type: 'text' | 'yesno' | 'scale' | 'multiple'
    required: boolean
    is_eliminatory: boolean
    expected_answer: string
  }>({
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
          // @ts-ignore TODO: fix type — Argument of type '{ id: string; question: string | undefined; type: string; requ
          setQuestions(mapped)
          // @ts-ignore TODO: fix type — Argument of type '{ id: string; question: string | undefined; type: string; requ
          setOriginalQuestions(mapped)
        }
        
        if (pipelineRes.ok) {
          const pipelineData = await pipelineRes.json()
          if (pipelineData.pipeline && Array.isArray(pipelineData.pipeline)) {
            const stages: RecruitmentStage[] = pipelineData.pipeline.map((s: RawPipelineStage, idx: number) => ({
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
              sub_statuses: s.sub_statuses || [],
            }))
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

      // POST new questions (temp ids)
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

      // DELETE removed questions (existed before, not in updated list)
      const updatedIds = new Set(updatedQuestions.filter(q => !isTempId(q.id)).map(q => q.id))
      const removed = originalQuestions.filter(q => !isTempId(q.id) && !updatedIds.has(q.id))
      for (const q of removed) {
        await fetch(`/api/backend-proxy/company/screening-questions/${q.id}`, { method: 'DELETE' })
      }

      // Rebuild state with real ids
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

  const tabs = [
    { id: 'pipeline', label: 'Pipeline', icon: Workflow },
    { id: 'screening', label: 'Perguntas de Elegibilidade', icon: MessageSquare },
    { id: 'hiring-policies', label: 'Políticas de Recrutamento', icon: ShieldCheck },
  ]

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
          const updatedStages: RecruitmentStage[] = data.pipeline.map((s: RawPipelineStage, idx: number) => ({
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
            sub_statuses: s.sub_statuses || [],
          }))
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
        // Sync active count in local stage state
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
      // silent fail — SubStatusPanel manages its own optimistic state
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

  const renderPipeline = () => {
    if (loading) {
      return (
        <div className="space-y-6">
          <Card className="border-0 rounded-md backdrop-blur-sm animate-pulse motion-reduce:animate-none">
            <CardHeader className="pb-4">
              <div className="h-5 w-48 rounded-md bg-gray-400 opacity-30"></div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="w-28 h-16 rounded-md bg-gray-400 opacity-20"></div>
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
              <Badge variant="outline" className="bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-subtle text-micro">
                Alterações não salvas
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isEditingPipeline ? (
              <>
                <button
                  onClick={handleCancelEdit}
                  disabled={savingStages}
                  className={actionButtonStyles.smSecondary}
                >
                  Cancelar
                </button>
                <button
                  onClick={saveRecruitmentStages}
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
                onClick={handleStartEdit}
                className={actionButtonStyles.smOutline}
              >
                <Pencil className={actionButtonStyles.icon} />
                Editar
              </button>
            )}
          </div>
        </div>

        <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
          <CardContent className="p-6">
            <RecruitmentJourneyConfig
              stages={recruitmentStages}
              onChange={handleStagesChange}
              isEditMode={isEditingPipeline}
              onToggleSubStatus={handleToggleSubStatus}
            />
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderScreening = () => (
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

      <div className="px-3 py-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50 border border-lia-border-subtle dark:border-lia-border-subtle">
        <p className={`${textStyles.caption} lia-text-500`}>
          <span className="font-semibold lia-text-700 dark:text-lia-text-secondary">Perguntas automáticas</span> (modelo de trabalho, localização, idiomas, regime de contratação) são geradas automaticamente pela LIA a partir dos campos de cada vaga — não precisam ser configuradas aqui.
        </p>
      </div>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <MessageSquare className="w-3.5 h-3.5 lia-text-700 dark:text-lia-text-secondary" />
                Catálogo de Perguntas de Elegibilidade
              </CardTitle>
              <p className={`${textStyles.description} mt-1`} aria-live="polite" aria-atomic="true">
                Perguntas padrão da empresa — aparecem ativas em todas as vagas por padrão. O recrutador pode desativar individualmente em cada vaga.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {isEditingQuestions ? (
                <>
                  <button
                    onClick={() => setShowQuestionBank(!showQuestionBank)}
                    className={actionButtonStyles.smOutline}
                  >
                    <Library className={actionButtonStyles.icon} />
                    Banco de Perguntas
                  </button>
                  <button
                    onClick={() => setShowQuestionForm(true)}
                    className={actionButtonStyles.smOutline}
                  >
                    <Plus className={actionButtonStyles.icon} />
                    Nova Pergunta
                  </button>
                  <button
                    onClick={handleCancelEditQuestions}
                    disabled={savingQuestions}
                    className={actionButtonStyles.smSecondary}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleSaveQuestions}
                    disabled={savingQuestions}
                    className={actionButtonStyles.smPrimary}
                  >
                    {savingQuestions ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                        Salvando...
                      </>
                    ) : (
                      <>
                        <Save className="w-3.5 h-3.5" />
                        Salvar Alterações
                      </>
                    )}
                  </button>
                </>
              ) : (
                <button
                  onClick={handleStartEditQuestions}
                  className={actionButtonStyles.smOutline}
                >
                  <Pencil className={actionButtonStyles.icon} />
                  Editar
                </button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isEditingQuestions && showQuestionBank && (
            <Card className="border-2 border-dashed border-lia-border-default bg-gray-50/30 dark:bg-lia-bg-secondary/10 rounded-md">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span className={textStyles.h4}>
                      Banco de Perguntas Sugeridas
                    </span>
                    <Badge variant="outline" className="text-micro">{ELIGIBILITY_QUESTIONS_BANK.length} perguntas</Badge>
                  </div>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => setShowQuestionBank(false)}>
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </div>
                <p className={`${textStyles.caption} mt-1`}>
                  Selecione perguntas pré-definidas organizadas por categoria
                </p>
              </CardHeader>
              <CardContent className="pt-0 space-y-2 max-h-content-lg overflow-y-auto">
                {(Object.keys(QUESTION_CATEGORIES) as QuestionCategory[]).filter(cat => cat !== 'general').map(category => {
                  const categoryQuestions = getQuestionsByCategory(category)
                  if (categoryQuestions.length === 0) return null
                  const isExpanded = expandedCategories.has(category)
                  const categoryInfo = QUESTION_CATEGORIES[category]
                  
                  return (
                    <div key={category} className="border border-lia-border-subtle rounded-md overflow-hidden">
                      <button
                        onClick={() => toggleCategory(category)}
                        className="w-full flex items-center justify-between p-2.5 bg-gray-50 hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{categoryInfo.icon}</span>
                          <span className={textStyles.label}>
                            {categoryInfo.label}
                          </span>
                          <Badge variant="outline" className="text-micro py-0 px-1.5">
                            {categoryQuestions.length}
                          </Badge>
                        </div>
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5 lia-text-400" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5 lia-text-400" />
                        )}
                      </button>
                      
                      {isExpanded && (
                        <div className="p-2 space-y-1.5 bg-lia-bg-primary">
                          {categoryQuestions.map(q => {
                            const isAdded = isQuestionAlreadyAdded(q)
                            const isSelected = selectedBankQuestions.has(q.id)
                            
                            return (
                              <div 
                                key={q.id}
                                className={`flex items-start gap-2 p-2 rounded-md border transition-colors motion-reduce:transition-none ${
                                  isAdded 
                                    ? 'bg-gray-100 border-lia-border-subtle opacity-60 dark:bg-lia-bg-elevated dark:border-lia-border-default' 
                                    : isSelected 
                                      ? 'bg-gray-100 border-lia-border-default dark:bg-lia-bg-elevated dark:border-lia-border-default' 
                                      : 'bg-white border-lia-border-subtle hover:border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:border-gray-600'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  disabled={isAdded}
                                  onChange={() => toggleBankQuestion(q.id)}
                                  className="mt-0.5 rounded-md border-lia-border-default"
                                />
                                <div className="flex-1 min-w-0">
                                  <p className={textStyles.bodySmall}>
                                    {q.question}
                                  </p>
                                  <div className="flex items-center gap-1.5 mt-1">
                                    <Badge variant="outline" className="text-micro py-0 px-1">
                                      {q.type === 'text' ? 'Texto' : q.type === 'yesno' ? 'Sim/Não' : q.type === 'scale' ? 'Escala' : 'Múltipla'}
                                    </Badge>
                                    <span className={textStyles.caption}>
                                      {q.contextHint}
                                    </span>
                                    {isAdded && (
                                      <Badge className="text-micro py-0 px-1 bg-status-success/15 text-status-success">
                                        Já adicionada
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )
                })}
                
                {selectedBankQuestions.size > 0 && (
                  <div className="sticky bottom-0 pt-3 bg-gradient-to-t from-gray-50/80 to-transparent dark:lia-from-800/80">
                    <Button 
                      onClick={handleAddFromBank}
                      size="sm" 
                      className={`w-full gap-1.5 rounded-md py-2 bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 ${textStyles.label}`}
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Adicionar {selectedBankQuestions.size} pergunta{selectedBankQuestions.size > 1 ? 's' : ''} selecionada{selectedBankQuestions.size > 1 ? 's' : ''}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {isEditingQuestions && showQuestionForm && (
            <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-white/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
              <CardContent className="p-3 space-y-4">
                <div>
                  <label className={`block mb-1.5 ${textStyles.labelSmall}`}>Pergunta</label>
                  <input
                    type="text"
                    value={newQuestion.question}
                    onChange={(e) => setNewQuestion(prev => ({ ...prev, question: e.target.value }))}
                    className={`w-full px-2 py-1.5 border border-lia-border-subtle rounded-md bg-lia-bg-primary ${textStyles.body}`}
                    placeholder="Digite a pergunta..."
                  />
                </div>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className={`block mb-1.5 ${textStyles.labelSmall}`}>Tipo</label>
                    <select
                      value={newQuestion.type}
                      onChange={(e) => setNewQuestion(prev => ({ ...prev, type: e.target.value as 'text' | 'yesno' | 'scale' | 'multiple' }))}
                      className={`w-full px-2 py-1.5 border border-lia-border-subtle rounded-md bg-lia-bg-primary ${textStyles.body}`}
                    >
                      <option value="text">Texto livre</option>
                      <option value="yesno">Sim/Não</option>
                      <option value="scale">Escala 1-5</option>
                    </select>
                  </div>
                  <div className="flex items-end gap-4">
                    <label className={`flex items-center gap-2 ${textStyles.description}`}>
                      <input
                        type="checkbox"
                        checked={newQuestion.required}
                        onChange={(e) => setNewQuestion(prev => ({ ...prev, required: e.target.checked }))}
                        className="rounded-md"
                      />
                      Obrigatória
                    </label>
                    <label className={`flex items-center gap-2 ${textStyles.description} text-status-error`}>
                      <input
                        type="checkbox"
                        checked={newQuestion.is_eliminatory}
                        onChange={(e) => setNewQuestion(prev => ({ ...prev, is_eliminatory: e.target.checked }))}
                        className="rounded-md border-status-error/30"
                      />
                      Eliminatória
                    </label>
                  </div>
                </div>
                {newQuestion.is_eliminatory && newQuestion.type === 'yesno' && (
                  <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-md">
                    <label className={`block mb-1.5 ${textStyles.labelSmall} text-status-error`}>
                      Resposta esperada (candidato será avisado se não atender)
                    </label>
                    <div className="flex gap-3">
                      <label className={`flex items-center gap-2 ${textStyles.description}`}>
                        <input
                          type="radio"
                          name="expected_answer"
                          value="Sim"
                          checked={newQuestion.expected_answer === 'Sim'}
                          onChange={(e) => setNewQuestion(prev => ({ ...prev, expected_answer: e.target.value }))}
                          className="border-lia-border-default"
                        />
                        Sim
                      </label>
                      <label className={`flex items-center gap-2 ${textStyles.description}`}>
                        <input
                          type="radio"
                          name="expected_answer"
                          value="Não"
                          checked={newQuestion.expected_answer === 'Não'}
                          onChange={(e) => setNewQuestion(prev => ({ ...prev, expected_answer: e.target.value }))}
                          className="border-lia-border-default"
                        />
                        Não
                      </label>
                    </div>
                    <p className={`${textStyles.caption} text-status-error mt-2`} aria-live="polite" aria-atomic="true">
                      Se o candidato responder diferente, será avisado e poderá reconsiderar ou ir para o banco de talentos.
                    </p>
                  </div>
                )}
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="sm" className={`py-1.5 px-2 ${textStyles.label}`} onClick={() => setShowQuestionForm(false)}>
                    Cancelar
                  </Button>
                  <Button size="sm" className={`py-1.5 px-2 bg-gray-900 text-white hover:bg-gray-800 dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 ${textStyles.label}`} onClick={handleAddQuestion}>
                    <Save className="w-3.5 h-3.5 mr-1" />
                    Salvar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-2">
            {questions.map((q, index) => (
              <div 
                key={q.id} 
                className={`flex items-center gap-3 p-3 rounded-md border group transition-colors motion-reduce:transition-none ${
                  isEditingQuestions 
                    ? 'bg-gray-50 dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:border-lia-border-subtle' 
                    : 'bg-gray-50/60 dark:bg-lia-bg-secondary/30 border-lia-border-subtle/60 dark:border-lia-border-subtle/60'
                }`}
              >
                <div 
                  className={`flex items-center justify-center w-6 h-6 rounded-full bg-gray-900 text-white dark:lia-bg-50 dark:lia-text-900 transition-opacity motion-reduce:transition-none ${!isEditingQuestions ? 'opacity-60' : ''} ${textStyles.labelSmall}`}
                >
                  {index + 1}
                </div>
                <div className="flex-1">
 <p className={`${textStyles.body} transition-colors motion-reduce:transition-none ${isEditingQuestions ? 'lia-text-950' : 'lia-text-600 dark:text-lia-text-tertiary'}`}>
                    {q.question}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className={`text-micro py-0 px-1.5 ${!isEditingQuestions ? 'opacity-60' : ''}`}>
                      {q.type === 'text' ? 'Texto' : q.type === 'yesno' ? 'Sim/Não' : 'Escala'}
                    </Badge>
                    {q.required && (
                      <Badge className={`text-micro py-0 px-1.5 bg-gray-900 text-white dark:lia-bg-50 dark:lia-text-900 ${!isEditingQuestions ? 'opacity-60' : ''}`}>Obrigatória</Badge>
                    )}
                    {q.is_eliminatory && (
                      <Badge className={`text-micro py-0 px-1.5 bg-status-error/15 text-status-error border border-status-error/30 ${!isEditingQuestions ? 'opacity-60' : ''}`}>
                        Eliminatória {q.expected_answer && `(${q.expected_answer})`}
                      </Badge>
                    )}
                    {q.isDefault && (
                      <span className="text-micro lia-text-400">Padrão</span>
                    )}
                  </div>
                </div>
                {isEditingQuestions && (
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleToggleRequired(q.id)}
                    >
                      {q.required ? <Lock className="w-3.5 h-3.5 lia-text-400" /> : <Eye className="w-3.5 h-3.5 lia-text-400" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 hover:text-status-error"
                      onClick={() => handleDeleteQuestion(q.id)}
                      disabled={q.isDefault}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'pipeline' && renderPipeline()}
      {activeTab === 'screening' && renderScreening()}
      {activeTab === 'hiring-policies' && <HiringPoliciesHub />}
    </div>
  )


}

export default RecruitmentHub
