"use client"

import React, { useState } from 'react'
import { ChevronDown, ChevronUp, PenLine, Plus, Trash2, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { textStyles } from '@/lib/design-tokens'

export interface CustomQuestion {
  id: string
  question: string
  character: 'eliminatoria' | 'classificatoria'
  expectedAnswer?: string
}

interface CustomQuestionsProps {
  isEditing: boolean
  questions: CustomQuestion[]
  onAddQuestion: (question: CustomQuestion) => void
  onRemoveQuestion: (questionId: string) => void
  onUpdateQuestion: (questionId: string, updates: Partial<CustomQuestion>) => void
}

export function CustomQuestions({ isEditing, questions, onAddQuestion, onRemoveQuestion, onUpdateQuestion }: CustomQuestionsProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [newQuestionText, setNewQuestionText] = useState('')
  const [newQuestionCharacter, setNewQuestionCharacter] = useState<'eliminatoria' | 'classificatoria'>('classificatoria')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  const [editCharacter, setEditCharacter] = useState<'eliminatoria' | 'classificatoria'>('classificatoria')
  const [newQuestionExpectedAnswer, setNewQuestionExpectedAnswer] = useState('')
  const [editExpectedAnswer, setEditExpectedAnswer] = useState('')

  const handleAdd = () => {
    if (!newQuestionText.trim()) return
    onAddQuestion({
      id: `custom_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      question: newQuestionText.trim(),
      character: newQuestionCharacter,
      ...(newQuestionCharacter === 'eliminatoria' && newQuestionExpectedAnswer.trim() ? { expectedAnswer: newQuestionExpectedAnswer.trim() } : {}),
    })
    setNewQuestionText('')
    setNewQuestionCharacter('classificatoria')
    setNewQuestionExpectedAnswer('')
    setIsAdding(false)
  }

  const handleStartEdit = (question: CustomQuestion) => {
    setEditingId(question.id)
    setEditText(question.question)
    setEditCharacter(question.character)
    setEditExpectedAnswer(question.expectedAnswer || '')
  }

  const handleSaveEdit = () => {
    if (!editingId || !editText.trim()) return
    onUpdateQuestion(editingId, {
      question: editText.trim(),
      character: editCharacter,
      ...(editCharacter === 'eliminatoria' && editExpectedAnswer.trim() ? { expectedAnswer: editExpectedAnswer.trim() } : { expectedAnswer: undefined }),
    })
    setEditingId(null)
    setEditText('')
    setEditExpectedAnswer('')
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditText('')
    setEditExpectedAnswer('')
  }

  return (
    <div className="border border-lia-border-subtle rounded-xl bg-lia-bg-primary overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <PenLine className="w-4 h-4 text-lia-text-tertiary" />
          <span className="text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
            Personalizadas
          </span>
          {questions.length > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
              {questions.length}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-lia-text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-lia-text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-2">
          {questions.length === 0 && !isAdding && (
            <div className="py-4 text-center">
              <p className={`${textStyles.description} italic`}>
                Nenhuma pergunta personalizada adicionada
              </p>
            </div>
          )}

          {questions.map((question) => (
            <div key={question.id}>
              {editingId === question.id ? (
                <div className="space-y-2 p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
                  <input
                    type="text"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full text-xs rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"
                    placeholder="Digite a pergunta..."
                    onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                  />
                  <div className="flex items-center justify-between">
                    <select
                      value={editCharacter}
                      onChange={(e) => setEditCharacter(e.target.value as 'eliminatoria' | 'classificatoria')}
                      className="text-xs rounded-xl border border-lia-border-subtle bg-lia-bg-primary px-2.5 py-1.5 text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/10"
                    >
                      <option value="classificatoria">Classificatória</option>
                      <option value="eliminatoria">Eliminatória</option>
                    </select>
                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCancelEdit}
                        className="h-7 w-7 p-0 rounded-lg"
                      >
                        <X className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSaveEdit}
                        disabled={!editText.trim()}
                        className="h-7 w-7 p-0 rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  {editCharacter === 'eliminatoria' && (
                    <div className="flex items-center gap-2">
                      <label className="text-micro font-medium text-lia-text-tertiary whitespace-nowrap">
                        Resposta esperada
                      </label>
                      <input
                        type="text"
                        value={editExpectedAnswer}
                        onChange={(e) => setEditExpectedAnswer(e.target.value)}
                        className="flex-1 text-xs rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"
                        placeholder="Ex: Sim, Não, etc."
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none group">
                  <div className="flex-1 flex flex-col gap-0.5">
                    <span className={`${textStyles.bodySmall}`}>
                      {question.question}
                    </span>
                    {question.expectedAnswer && (
                      <span className="text-micro text-lia-text-muted">Resposta esperada: {question.expectedAnswer}</span>
                    )}
                  </div>
                  {question.character === 'eliminatoria' ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error">
                      eliminatória{question.expectedAnswer ? ` (${question.expectedAnswer})` : ''}
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-warning/10 text-status-warning dark:bg-status-warning/30">
                      classificatória
                    </span>
                  )}
                  {isEditing && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                      <button
                        onClick={() => handleStartEdit(question)}
                        className="p-1 rounded-md hover:bg-lia-interactive-active dark:hover:bg-lia-btn-primary-bg text-lia-text-tertiary transition-colors motion-reduce:transition-none"
                      >
                        <PenLine className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => onRemoveQuestion(question.id)}
                        className="p-1 rounded-md hover:bg-status-error/10 dark:hover:bg-status-error/30 text-lia-text-tertiary hover:text-status-error dark:hover:text-status-error transition-colors motion-reduce:transition-none"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {isAdding && (
            <div className="space-y-2 p-3 border border-lia-border-subtle rounded-lg bg-lia-bg-secondary">
              <input
                type="text"
                value={newQuestionText}
                onChange={(e) => setNewQuestionText(e.target.value)}
                className="w-full text-xs rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"
                placeholder="Digite a pergunta..."
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
              />
              <div className="flex items-center justify-between">
                <select
                  value={newQuestionCharacter}
                  onChange={(e) => setNewQuestionCharacter(e.target.value as 'eliminatoria' | 'classificatoria')}
                  className="text-xs rounded-xl border border-lia-border-subtle bg-lia-bg-primary px-2.5 py-1.5 text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/10"
                >
                  <option value="classificatoria">Classificatória</option>
                  <option value="eliminatoria">Eliminatória</option>
                </select>
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setIsAdding(false)
                      setNewQuestionText('')
                      setNewQuestionExpectedAnswer('')
                    }}
                    className="h-7 w-7 p-0 rounded-lg"
                  >
                    <X className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleAdd}
                    disabled={!newQuestionText.trim()}
                    className="h-7 w-7 p-0 rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
              {newQuestionCharacter === 'eliminatoria' && (
                <div className="flex items-center gap-2">
                  <label className="text-micro font-medium text-lia-text-tertiary whitespace-nowrap">
                    Resposta esperada
                  </label>
                  <input
                    type="text"
                    value={newQuestionExpectedAnswer}
                    onChange={(e) => setNewQuestionExpectedAnswer(e.target.value)}
                    className="flex-1 text-xs rounded-md border border-lia-border-subtle bg-lia-bg-primary px-3 py-2 text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg"
                    placeholder="Ex: Sim, Não, etc."
                  />
                </div>
              )}
            </div>
          )}

          {isEditing && !isAdding && (
            <button
              onClick={() => setIsAdding(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-lia-border-default rounded-xl text-lia-text-tertiary hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:text-lia-text-secondary transition-colors motion-reduce:transition-none text-xs font-medium"
            >
              <Plus className="w-3.5 h-3.5" />
              Adicionar Pergunta
            </button>
          )}
        </div>
      )}
    </div>
  )
}
