"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import {
  MessageSquare, Plus, Trash2, Save, X,
  CheckCircle, AlertCircle,
  Lock, Eye, Loader2, Pencil,
  ChevronDown, ChevronUp, Library, Brain,
} from"lucide-react"
import {
  ELIGIBILITY_QUESTIONS_BANK,
  QUESTION_CATEGORIES,
  QuestionCategory,
  EligibilityQuestionTemplate,
} from"@/components/settings/eligibility-questions-bank"
import { textStyles, actionButtonStyles } from '@/lib/design-tokens'
import { ScreeningQuestion, NewQuestionForm } from './useRecruitmentHub'

interface RecruitmentScreeningTabProps {
  error: string | null
  successMessage: string | null
  questions: ScreeningQuestion[]
  showQuestionForm: boolean
  setShowQuestionForm: (v: boolean) => void
  newQuestion: NewQuestionForm
  setNewQuestion: React.Dispatch<React.SetStateAction<NewQuestionForm>>
  isEditingQuestions: boolean
  savingQuestions: boolean
  showQuestionBank: boolean
  setShowQuestionBank: (v: boolean) => void
  expandedCategories: Set<QuestionCategory>
  selectedBankQuestions: Set<string>
  onStartEditQuestions: () => void
  onCancelEditQuestions: () => void
  onSaveQuestions: () => void
  onAddQuestion: () => void
  onDeleteQuestion: (id: string) => void
  onToggleRequired: (id: string) => void
  onToggleCategory: (category: QuestionCategory) => void
  onToggleBankQuestion: (questionId: string) => void
  onAddFromBank: () => void
  getQuestionsByCategory: (category: QuestionCategory) => EligibilityQuestionTemplate[]
  isQuestionAlreadyAdded: (q: EligibilityQuestionTemplate) => boolean
}

export function RecruitmentScreeningTab({
  error, successMessage,
  questions, showQuestionForm, setShowQuestionForm,
  newQuestion, setNewQuestion,
  isEditingQuestions, savingQuestions,
  showQuestionBank, setShowQuestionBank,
  expandedCategories, selectedBankQuestions,
  onStartEditQuestions, onCancelEditQuestions, onSaveQuestions,
  onAddQuestion, onDeleteQuestion, onToggleRequired,
  onToggleCategory, onToggleBankQuestion, onAddFromBank,
  getQuestionsByCategory, isQuestionAlreadyAdded,
}: RecruitmentScreeningTabProps) {
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

      <div className="px-3 py-2.5 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border border-lia-border-subtle dark:border-lia-border-subtle">
        <p className={`${textStyles.caption} text-lia-text-secondary`}>
          <span className="font-semibold text-lia-text-primary">Perguntas automáticas</span> (modelo de trabalho, localização, idiomas, regime de contratação) são geradas automaticamente pela LIA a partir dos campos de cada vaga — não precisam ser configuradas aqui.
        </p>
      </div>

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h4} flex items-center gap-2`}>
                <MessageSquare className="w-3.5 h-3.5 text-lia-text-primary" />
                Catálogo de Perguntas de Elegibilidade
              </CardTitle>
              <p className={`${textStyles.description} mt-1`} aria-live="polite" aria-atomic="true">
                Perguntas padrão da empresa — aparecem ativas em todas as vagas por padrão. O recrutador pode desativar individualmente em cada vaga.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {isEditingQuestions ? (
                <>
                  <button onClick={() => setShowQuestionBank(!showQuestionBank)} className={actionButtonStyles.smOutline}>
                    <Library className={actionButtonStyles.icon} />
                    Banco de Perguntas
                  </button>
                  <button onClick={() => setShowQuestionForm(true)} className={actionButtonStyles.smOutline}>
                    <Plus className={actionButtonStyles.icon} />
                    Nova Pergunta
                  </button>
                  <button onClick={onCancelEditQuestions} disabled={savingQuestions} className={actionButtonStyles.smSecondary}>
                    Cancelar
                  </button>
                  <button onClick={onSaveQuestions} disabled={savingQuestions} className={actionButtonStyles.smPrimary}>
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
                <button onClick={onStartEditQuestions} className={actionButtonStyles.smOutline}>
                  <Pencil className={actionButtonStyles.icon} />
                  Editar
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
                  className={`flex items-center justify-center w-6 h-6 rounded-full bg-lia-btn-primary-bg text-lia-btn-primary-text transition-opacity motion-reduce:transition-none ${!isEditingQuestions ? 'opacity-60' : ''} ${textStyles.labelSmall}`}
                >
                  {index + 1}
                </div>
                <div className="flex-1">
                  <p className={`${textStyles.body} transition-colors motion-reduce:transition-none ${isEditingQuestions ? 'text-lia-text-primary' : 'text-lia-text-secondary'}`}>
                    {q.question}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className={`text-micro py-0 px-1.5 ${!isEditingQuestions ? 'opacity-60' : ''}`}>
                      {q.type === 'text' ? 'Texto' : q.type === 'yesno' ? 'Sim/Não' : 'Escala'}
                    </Badge>
                    {q.required && (
                      <Badge className={`text-micro py-0 px-1.5 bg-lia-btn-primary-bg text-lia-btn-primary-text ${!isEditingQuestions ? 'opacity-60' : ''}`}>Obrigatória</Badge>
                    )}
                    {q.is_eliminatory && (
                      <Badge className={`text-micro py-0 px-1.5  border border-status-error/30 ${!isEditingQuestions ? 'opacity-60' : ''}`}>
                        Eliminatória {q.expected_answer && `(${q.expected_answer})`}
                      </Badge>
                    )}
                    {q.isDefault && (
                      <span className="text-micro text-lia-text-tertiary">Padrão</span>
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
  getQuestionsByCategory: (category: QuestionCategory) => EligibilityQuestionTemplate[]
  isQuestionAlreadyAdded: (q: EligibilityQuestionTemplate) => boolean
}

function QuestionBankSection({
  expandedCategories, selectedBankQuestions,
  onClose, onToggleCategory, onToggleBankQuestion, onAddFromBank,
  getQuestionsByCategory, isQuestionAlreadyAdded,
}: QuestionBankSectionProps) {
  return (
    <Card className="border-2 border-dashed border-lia-border-default bg-lia-bg-secondary/30 dark:bg-lia-bg-secondary/10 rounded-xl">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            <span className={textStyles.h4}>Banco de Perguntas Sugeridas</span>
            <Badge variant="outline" className="text-micro">{ELIGIBILITY_QUESTIONS_BANK.length} perguntas</Badge>
          </div>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onClose}>
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
        <p className={`${textStyles.caption} mt-1`}>Selecione perguntas pré-definidas organizadas por categoria</p>
      </CardHeader>
      <CardContent className="pt-0 space-y-2 max-h-content-lg overflow-y-auto">
        {(Object.keys(QUESTION_CATEGORIES) as QuestionCategory[]).filter(cat => cat !== 'general').map(category => {
          const categoryQuestions = getQuestionsByCategory(category)
          if (categoryQuestions.length === 0) return null
          const isExpanded = expandedCategories.has(category)
          const categoryInfo = QUESTION_CATEGORIES[category]

          return (
            <div key={category} className="border border-lia-border-subtle rounded-xl overflow-hidden">
              <button
                onClick={() => onToggleCategory(category)}
                className="w-full flex items-center justify-between p-2.5 bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">{categoryInfo.icon}</span>
                  <span className={textStyles.label}>{categoryInfo.label}</span>
                  <Badge variant="outline" className="text-micro py-0 px-1.5">{categoryQuestions.length}</Badge>
                </div>
                {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-lia-text-tertiary" /> : <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />}
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
                            <Badge variant="outline" className="text-micro py-0 px-1">
                              {q.type === 'text' ? 'Texto' : q.type === 'yesno' ? 'Sim/Não' : q.type === 'scale' ? 'Escala' : 'Múltipla'}
                            </Badge>
                            <span className={textStyles.caption}>{q.contextHint}</span>
                            {isAdded && (
                              <Badge className="text-micro py-0 px-1">Já adicionada</Badge>
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
              Adicionar {selectedBankQuestions.size} pergunta{selectedBankQuestions.size > 1 ? 's' : ''} selecionada{selectedBankQuestions.size > 1 ? 's' : ''}
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
  return (
    <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl">
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
              <input type="checkbox" checked={newQuestion.required} onChange={(e) => setNewQuestion(prev => ({ ...prev, required: e.target.checked }))} className="rounded-md" />
              Obrigatória
            </label>
            <label className={`flex items-center gap-2 ${textStyles.description} text-status-error`}>
              <input type="checkbox" checked={newQuestion.is_eliminatory} onChange={(e) => setNewQuestion(prev => ({ ...prev, is_eliminatory: e.target.checked }))} className="rounded-md border-status-error/30" />
              Eliminatória
            </label>
          </div>
        </div>
        {newQuestion.is_eliminatory && newQuestion.type === 'yesno' && (
          <div className="p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
            <label className={`block mb-1.5 ${textStyles.labelSmall} text-status-error`}>
              Resposta esperada (candidato será avisado se não atender)
            </label>
            <div className="flex gap-3">
              <label className={`flex items-center gap-2 ${textStyles.description}`}>
                <input type="radio" name="expected_answer" value="Sim" checked={newQuestion.expected_answer === 'Sim'} onChange={(e) => setNewQuestion(prev => ({ ...prev, expected_answer: e.target.value }))} className="border-lia-border-default" />
                Sim
              </label>
              <label className={`flex items-center gap-2 ${textStyles.description}`}>
                <input type="radio" name="expected_answer" value="Não" checked={newQuestion.expected_answer === 'Não'} onChange={(e) => setNewQuestion(prev => ({ ...prev, expected_answer: e.target.value }))} className="border-lia-border-default" />
                Não
              </label>
            </div>
            <p className={`${textStyles.caption} text-status-error mt-2`} aria-live="polite" aria-atomic="true">
              Se o candidato responder diferente, será avisado e poderá reconsiderar ou ir para o banco de talentos.
            </p>
          </div>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" className={`py-1.5 px-2 ${textStyles.label}`} onClick={onCancel}>
            Cancelar
          </Button>
          <Button size="sm" className={`py-1.5 px-2 bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active ${textStyles.label}`} onClick={onAdd}>
            <Save className="w-3.5 h-3.5 mr-1" />
            Salvar
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
