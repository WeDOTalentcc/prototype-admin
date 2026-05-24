"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  MessageSquare, Plus, Trash2, Save, X,
  CheckCircle, AlertCircle,
  Lock, Eye, Loader2, Pencil,
  ChevronDown, ChevronUp, Library, Brain, Info,
} from"lucide-react"
import {
  useEligibilityTemplates,
  flattenTemplates,
  QUESTION_CATEGORIES,
  type FlatEligibilityQuestion,
  type QuestionCategory,
} from "@/hooks/screening/use-eligibility-templates"
import { EligibilityTemplatesManager } from "./EligibilityTemplatesManager"
import { useTranslations } from "next-intl"
import { textStyles, actionButtonStyles } from '@/lib/design-tokens'
import { useRecruitmentHub, type NewQuestionForm } from './useRecruitmentHub'
import { InteractiveSurface } from "@/components/ui/interactive-surface"

export function RecruitmentScreeningTab() {
  // F4 audit 2026-05-20: catalogo dinamico
  const { templates: _eligTemplates } = useEligibilityTemplates({ includeMaster: true })
  const ELIGIBILITY_QUESTIONS_BANK = flattenTemplates(_eligTemplates)

  const t = useTranslations("settings")
  const hub = useRecruitmentHub('screening')
  const error = hub.error
  const successMessage = hub.successMessage
  const questions = hub.questions
  const showQuestionForm = hub.showQuestionForm
  const setShowQuestionForm = hub.setShowQuestionForm
  const newQuestion = hub.newQuestion
  const setNewQuestion = hub.setNewQuestion
  const isEditingQuestions = hub.isEditingQuestions
  const savingQuestions = hub.savingQuestions
  const showQuestionBank = hub.showQuestionBank
  const setShowQuestionBank = hub.setShowQuestionBank
  const expandedCategories = hub.expandedCategories
  const selectedBankQuestions = hub.selectedBankQuestions
  const onStartEditQuestions = hub.handleStartEditQuestions
  const onCancelEditQuestions = hub.handleCancelEditQuestions
  const onSaveQuestions = hub.handleSaveQuestions
  const onAddQuestion = hub.handleAddQuestion
  const onDeleteQuestion = hub.handleDeleteQuestion
  const onToggleRequired = hub.handleToggleRequired
  const onToggleCategory = hub.toggleCategory
  const onToggleBankQuestion = hub.toggleBankQuestion
  const onAddFromBank = hub.handleAddFromBank
  const getQuestionsByCategory = hub.getQuestionsByCategory
  const isQuestionAlreadyAdded = hub.isQuestionAlreadyAdded
  return (
    <div className="space-y-6">
      {error && (
        <div className="px-2 py-1.5 rounded-xl flex items-center gap-2 bg-status-error/10 border border-status-error/30 text-status-error">
          <AlertCircle className="w-4 h-4" />
          <span className={textStyles.body}>{error}</span>
        </div>
      )}
      {successMessage && (
        <div className="px-2 py-1.5 rounded-xl flex items-center gap-2 bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success">
          <CheckCircle className="w-4 h-4" />
          <span className={textStyles.body}>{successMessage}</span>
        </div>
      )}

      <div className="flex items-start gap-3 p-4 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-subtle">
        <Info className="w-4 h-4 text-lia-text-secondary shrink-0 mt-0.5" />
        <p className={`${textStyles.caption} text-lia-text-secondary`}>
          <span className="font-semibold text-lia-text-primary">{t("recruitment.screening.autoQuestionsNote")}</span> {t("recruitment.screening.autoQuestionsDesc")}
        </p>
      </div>

      <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <MessageSquare className="w-3.5 h-3.5 text-lia-text-primary" />
                {t("recruitment.screening.catalogTitle")}
              </CardTitle>
              <p className={`${textStyles.description} mt-1`} aria-live="polite" aria-atomic="true">
                {t("recruitment.screening.catalogDesc")}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {isEditingQuestions ? (
                <>
                  <button onClick={() => setShowQuestionBank(!showQuestionBank)} className={actionButtonStyles.smOutline} data-action="toggle-question-bank" data-testid="screening-question-bank-button" aria-label="Banco de perguntas">
                    <Library className={actionButtonStyles.icon} />
                    {t("recruitment.screening.questionBank")}
                  </button>
                  <button onClick={() => setShowQuestionForm(true)} className={actionButtonStyles.smOutline} data-action="new-question" data-testid="screening-new-question-button" aria-label="Criar nova pergunta">
                    <Plus className={actionButtonStyles.icon} />
                    {t("recruitment.screening.newQuestion")}
                  </button>
                  <button onClick={onCancelEditQuestions} disabled={savingQuestions} className={actionButtonStyles.smSecondary} data-action="cancel" data-testid="screening-cancel-button" aria-label="Cancelar edição de triagem">
                    {t("recruitment.screening.cancel")}
                  </button>
                  <button onClick={onSaveQuestions} disabled={savingQuestions} className={actionButtonStyles.smPrimary} data-action="save" data-testid="screening-save-button" aria-label="Salvar perguntas de triagem">
                    {savingQuestions ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                        {t("recruitment.screening.saving")}
                      </>
                    ) : (
                      <>
                        <Save className="w-3.5 h-3.5" />
                        {t("recruitment.screening.saveChanges")}
                      </>
                    )}
                  </button>
                </>
              ) : (
                <button onClick={onStartEditQuestions} className={actionButtonStyles.smOutline} data-action="edit" data-testid="screening-edit-button" aria-label="Editar perguntas de triagem">
                  <Pencil className={actionButtonStyles.icon} />
                  {t("recruitment.screening.edit")}
                </button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isEditingQuestions && showQuestionBank && (
            <QuestionBankSection
              expandedCategories={expandedCategories}
              selectedBankQuestions={selectedBankQuestions}
              onClose={() => setShowQuestionBank(false)}
              onToggleCategory={onToggleCategory}
              onToggleBankQuestion={onToggleBankQuestion}
              onAddFromBank={onAddFromBank}
              getQuestionsByCategory={getQuestionsByCategory}
              isQuestionAlreadyAdded={isQuestionAlreadyAdded}
          bankSize={ELIGIBILITY_QUESTIONS_BANK.length}
        />
          )}

          {isEditingQuestions && showQuestionForm && (
            <QuestionFormSection
              newQuestion={newQuestion}
              setNewQuestion={setNewQuestion}
              onAdd={onAddQuestion}
              onCancel={() => setShowQuestionForm(false)}
            />
          )}

          <div className="space-y-2">
            {questions.map((q, index) => (
              <div
                key={q.id}
                className={`flex items-center gap-3 p-3 rounded-md border group transition-colors motion-reduce:transition-none ${
                  isEditingQuestions
                    ? 'bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:border-lia-border-subtle'
                    : 'bg-lia-bg-secondary/60 dark:bg-lia-bg-secondary/30 border-lia-border-subtle/60 dark:border-lia-border-subtle/60'
                }`}
              >
                <div
                  className={`flex items-center justify-center w-6 h-6 shrink-0 rounded-full bg-lia-btn-primary-bg font-inter text-micro font-semibold tabular-nums text-lia-btn-primary-text transition-opacity motion-reduce:transition-none ${!isEditingQuestions ? 'opacity-70' : ''}`}
                >
                  {index + 1}
                </div>
                <div className="flex-1">
                  <p className={`${textStyles.body} transition-colors motion-reduce:transition-none ${isEditingQuestions ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                    {q.question}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Chip variant="neutral" className={`text-micro py-0 px-1.5 ${!isEditingQuestions ? 'opacity-60' : ''}`}>
                      {q.type === 'text' ? t("recruitment.screening.typeText") : q.type === 'yes_no' ? t("recruitment.screening.typeYesNo") : t("recruitment.screening.typeScale")}
                    </Chip>
                    {q.required && (
                      <Chip variant="neutral" className={`text-micro py-0 px-1.5 ${!isEditingQuestions ? 'opacity-60' : ''}`}>{t("recruitment.screening.required")}</Chip>
                    )}
                    {q.is_eliminatory && (
                      <Chip variant="danger" muted className={`text-micro py-0 px-1.5 ${!isEditingQuestions ? 'opacity-60' : ''}`}>
                        {t("recruitment.screening.eliminatory")} {q.expected_answer && `(${q.expected_answer})`}
                      </Chip>
                    )}
                    {q.isDefault && (
                      <span className="text-micro text-lia-text-tertiary">{t("recruitment.screening.default")}</span>
                    )}
                  </div>
                </div>
                {isEditingQuestions && (
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => onToggleRequired(q.id)}>
                      {q.required ? <Lock className="w-3.5 h-3.5 text-lia-text-tertiary" /> : <Eye className="w-3.5 h-3.5 text-lia-text-tertiary" />}
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 hover:text-status-error" onClick={() => onDeleteQuestion(q.id)} disabled={q.isDefault}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <EligibilityTemplatesManager
        isAdmin={true}
        currentUserId={null}
      />
    </div>
  )
}

interface QuestionBankSectionProps {
  expandedCategories: Set<QuestionCategory>
  selectedBankQuestions: Set<string>
  onClose: () => void
  onToggleCategory: (category: QuestionCategory) => void
  onToggleBankQuestion: (questionId: string) => void
  onAddFromBank: () => void
  getQuestionsByCategory: (category: QuestionCategory) => FlatEligibilityQuestion[]
  isQuestionAlreadyAdded: (q: FlatEligibilityQuestion) => boolean
  bankSize: number  // F4: total items no catalogo (substitui bankSize antigo)
}

function QuestionBankSection({
  expandedCategories, selectedBankQuestions,
  onClose, onToggleCategory, onToggleBankQuestion, onAddFromBank,
  getQuestionsByCategory, isQuestionAlreadyAdded, bankSize,
}: QuestionBankSectionProps) {
  const t = useTranslations("settings")
  return (
    <Card className="border-2 border-dashed border-lia-border-default bg-lia-bg-secondary/30 dark:bg-lia-bg-secondary/10 rounded-xl">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <span className={textStyles.h4}>{t("recruitment.screening.suggestedBankTitle")}</span>
            <Chip variant="neutral" className="text-micro">{t("recruitment.screening.questionsCount", { count: bankSize })}</Chip>
          </div>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onClose}>
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
        <p className={`${textStyles.caption} mt-1`}>{t("recruitment.screening.selectByCategory")}</p>
      </CardHeader>
      <CardContent className="pt-0 space-y-2 max-h-content-lg overflow-y-auto">
        {(Object.keys(QUESTION_CATEGORIES) as QuestionCategory[]).filter(cat => cat !== 'general').map(category => {
          const categoryQuestions = getQuestionsByCategory(category)
          if (categoryQuestions.length === 0) return null
          const isExpanded = expandedCategories.has(category)
          const categoryInfo = QUESTION_CATEGORIES[category]

          return (
            <div key={category} className="border border-lia-border-subtle rounded-xl overflow-hidden">
              <InteractiveSurface
                variant="accordion"
                onClick={() => onToggleCategory(category)}
                className="p-2.5 !bg-lia-bg-secondary hover:!bg-lia-bg-tertiary"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">{categoryInfo.icon}</span>
                  <span className={textStyles.label}>{categoryInfo.label}</span>
                  <Chip variant="neutral" className="text-micro py-0 px-1.5">{categoryQuestions.length}</Chip>
                </div>
                {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-lia-text-tertiary" /> : <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />}
              </InteractiveSurface>

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
                            ? 'bg-lia-bg-tertiary border-lia-border-subtle opacity-60 dark:bg-lia-bg-elevated dark:border-lia-border-default'
                            : isSelected
                              ? 'bg-lia-bg-tertiary border-lia-border-default dark:bg-lia-bg-elevated dark:border-lia-border-default'
                              : 'bg-lia-bg-primary border-lia-border-subtle hover:border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle dark:hover:border-lia-border-medium'
                        }`}
                      >
                        <input type="checkbox" checked={isSelected} disabled={isAdded} onChange={() => onToggleBankQuestion(q.id)} className="mt-0.5 rounded-xl border-lia-border-default" />
                        <div className="flex-1 min-w-0">
                          <p className={textStyles.bodySmall}>{q.question}</p>
                          <div className="flex items-center gap-1.5 mt-1">
                            <Chip variant="neutral" className="text-micro py-0 px-1">
                              {q.type === 'text' ? t("recruitment.screening.typeText") : q.type === 'yes_no' ? t("recruitment.screening.typeYesNo") : q.type === 'scale' ? t("recruitment.screening.typeScale") : t("recruitment.screening.typeMultiple")}
                            </Chip>
                            <span className={textStyles.caption}>{q.contextHint}</span>
                            {isAdded && (
                              <Chip variant="neutral" muted className="text-micro py-0 px-1">{t("recruitment.screening.alreadyAdded")}</Chip>
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
          <div className="sticky bottom-0 pt-3 bg-gradient-to-t from-lia-bg-secondary/80 to-transparent dark:from-lia-btn-primary-hover/80">
            <Button
              onClick={onAddFromBank}
              size="sm"
              className={`w-full gap-1.5 rounded-md py-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active ${textStyles.label}`}
            >
              <Plus className="w-3.5 h-3.5" />
              {t("recruitment.screening.addSelected", { count: selectedBankQuestions.size })}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface QuestionFormSectionProps {
  newQuestion: NewQuestionForm
  setNewQuestion: React.Dispatch<React.SetStateAction<NewQuestionForm>>
  onAdd: () => void
  onCancel: () => void
}

function QuestionFormSection({ newQuestion, setNewQuestion, onAdd, onCancel }: QuestionFormSectionProps) {
  const t = useTranslations("settings")
  return (
    <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
      <CardContent className="p-3 space-y-4">
        <div>
          <label htmlFor="screening-question-text" className={`block mb-1.5 ${textStyles.labelSmall}`}>{t("recruitment.screening.questionLabel")}</label>
          <input
            id="screening-question-text"
            type="text"
            value={newQuestion.question}
            onChange={(e) => setNewQuestion(prev => ({ ...prev, question: e.target.value }))}
            data-field="question_text"
            data-testid="screening-question-text-input"
            aria-label="Texto da pergunta"
            className={`w-full px-2 py-1.5 border border-lia-border-subtle rounded-md bg-lia-bg-primary ${textStyles.body}`}
            placeholder={t("recruitment.screening.questionPlaceholder")}
          />
        </div>
        <div className="flex gap-3">
          <div className="flex-1">
            <label htmlFor="screening-question-type" className={`block mb-1.5 ${textStyles.labelSmall}`}>{t("recruitment.screening.typeLabel")}</label>
            <select
              id="screening-question-type"
              value={newQuestion.type}
              onChange={(e) => setNewQuestion(prev => ({ ...prev, type: e.target.value as 'text' | 'yes_no' | 'scale' | 'multiple' }))}
              data-field="question_type"
              data-testid="screening-question-type-select"
              aria-label="Tipo de pergunta"
              className={`w-full px-2 py-1.5 border border-lia-border-subtle rounded-md bg-lia-bg-primary ${textStyles.body}`}
            >
              <option value="text">{t("recruitment.screening.freeText")}</option>
              <option value="yes_no">{t("recruitment.screening.yesNo")}</option>
              <option value="scale">{t("recruitment.screening.scale15")}</option>
            </select>
          </div>
          <div className="flex items-end gap-4">
            <label className={`flex items-center gap-2 ${textStyles.description}`}>
              <input type="checkbox" checked={newQuestion.required} onChange={(e) => setNewQuestion(prev => ({ ...prev, required: e.target.checked }))} className="rounded-md" data-toggle="question_required" data-testid="screening-question-required-toggle" aria-label="Pergunta obrigatória" />
              {t("recruitment.screening.requiredCheckbox")}
            </label>
            <label className={`flex items-center gap-2 ${textStyles.description} text-status-error`}>
              <input type="checkbox" checked={newQuestion.is_eliminatory} onChange={(e) => setNewQuestion(prev => ({ ...prev, is_eliminatory: e.target.checked }))} className="rounded-md border-status-error/30" data-toggle="question_is_eliminatory" data-testid="screening-question-eliminatory-toggle" aria-label="Pergunta eliminatória" />
              {t("recruitment.screening.eliminatoryCheckbox")}
            </label>
          </div>
        </div>
        {newQuestion.is_eliminatory && newQuestion.type === 'yes_no' && (
          <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
            <label className={`block mb-1.5 ${textStyles.labelSmall} text-status-error`}>
              {t("recruitment.screening.expectedAnswer")}
            </label>
            <div className="flex gap-3">
              <label className={`flex items-center gap-2 ${textStyles.description}`}>
                <input type="radio" name="expected_answer" value="Sim" checked={newQuestion.expected_answer === 'Sim'} onChange={(e) => setNewQuestion(prev => ({ ...prev, expected_answer: e.target.value }))} className="border-lia-border-default" />
                {t("recruitment.screening.yes")}
              </label>
              <label className={`flex items-center gap-2 ${textStyles.description}`}>
                <input type="radio" name="expected_answer" value="Não" checked={newQuestion.expected_answer === 'Não'} onChange={(e) => setNewQuestion(prev => ({ ...prev, expected_answer: e.target.value }))} className="border-lia-border-default" />
                {t("recruitment.screening.no")}
              </label>
            </div>
            <p className={`${textStyles.caption} text-status-error mt-2`} aria-live="polite" aria-atomic="true">
              {t("recruitment.screening.eliminatoryWarning")}
            </p>
          </div>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" className={`py-1.5 px-2 ${textStyles.label}`} onClick={onCancel}>
            {t("recruitment.screening.cancel")}
          </Button>
          <Button size="sm" data-action="save-new-question" data-testid="screening-save-new-question-button" aria-label="Salvar nova pergunta" className={`py-1.5 px-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active ${textStyles.label}`} onClick={onAdd}>
            <Save className="w-3.5 h-3.5 mr-1" />
            {t("recruitment.screening.save")}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
