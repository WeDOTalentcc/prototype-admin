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
    <div className="border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <PenLine className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="font-['Open_Sans',sans-serif] text-xs uppercase tracking-wider font-semibold text-gray-500 dark:text-gray-400">
            Personalizadas
          </span>
          {questions.length > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {questions.length}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
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
                <div className="space-y-2 p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <input
                    type="text"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full text-xs font-['Open_Sans',sans-serif] rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 dark:focus:ring-gray-50/10 focus:border-gray-900 dark:focus:border-gray-50"
                    placeholder="Digite a pergunta..."
                    onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                  />
                  <div className="flex items-center justify-between">
                    <select
                      value={editCharacter}
                      onChange={(e) => setEditCharacter(e.target.value as 'eliminatoria' | 'classificatoria')}
                      className="text-xs font-['Open_Sans',sans-serif] rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-2.5 py-1.5 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-900/10 dark:focus:ring-gray-50/10"
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
                        className="h-7 w-7 p-0 rounded-lg bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  {editCharacter === 'eliminatoria' && (
                    <div className="flex items-center gap-2">
                      <label className="text-micro font-medium text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif] whitespace-nowrap">
                        Resposta esperada
                      </label>
                      <input
                        type="text"
                        value={editExpectedAnswer}
                        onChange={(e) => setEditExpectedAnswer(e.target.value)}
                        className="flex-1 text-xs font-['Open_Sans',sans-serif] rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 dark:focus:ring-gray-50/10 focus:border-gray-900 dark:focus:border-gray-50"
                        placeholder="Ex: Sim, Não, etc."
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group">
                  <div className="flex-1 flex flex-col gap-0.5">
                    <span className={`${textStyles.bodySmall}`}>
                      {question.question}
                    </span>
                    {question.expectedAnswer && (
                      <span className="text-micro text-gray-400 dark:text-gray-500">Resposta esperada: {question.expectedAnswer}</span>
                    )}
                  </div>
                  {question.character === 'eliminatoria' ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                      eliminatória{question.expectedAnswer ? ` (${question.expectedAnswer})` : ''}
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                      classificatória
                    </span>
                  )}
                  {isEditing && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleStartEdit(question)}
                        className="p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors"
                      >
                        <PenLine className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => onRemoveQuestion(question.id)}
                        className="p-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
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
            <div className="space-y-2 p-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
              <input
                type="text"
                value={newQuestionText}
                onChange={(e) => setNewQuestionText(e.target.value)}
                className="w-full text-xs font-['Open_Sans',sans-serif] rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 dark:focus:ring-gray-50/10 focus:border-gray-900 dark:focus:border-gray-50"
                placeholder="Digite a pergunta..."
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
              />
              <div className="flex items-center justify-between">
                <select
                  value={newQuestionCharacter}
                  onChange={(e) => setNewQuestionCharacter(e.target.value as 'eliminatoria' | 'classificatoria')}
                  className="text-xs font-['Open_Sans',sans-serif] rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-2.5 py-1.5 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-900/10 dark:focus:ring-gray-50/10"
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
                    className="h-7 w-7 p-0 rounded-lg bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
              {newQuestionCharacter === 'eliminatoria' && (
                <div className="flex items-center gap-2">
                  <label className="text-micro font-medium text-gray-500 dark:text-gray-400 font-['Open_Sans',sans-serif] whitespace-nowrap">
                    Resposta esperada
                  </label>
                  <input
                    type="text"
                    value={newQuestionExpectedAnswer}
                    onChange={(e) => setNewQuestionExpectedAnswer(e.target.value)}
                    className="flex-1 text-xs font-['Open_Sans',sans-serif] rounded-md border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-gray-800 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 dark:focus:ring-gray-50/10 focus:border-gray-900 dark:focus:border-gray-50"
                    placeholder="Ex: Sim, Não, etc."
                  />
                </div>
              )}
            </div>
          )}

          {isEditing && !isAdding && (
            <button
              onClick={() => setIsAdding(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-md text-gray-500 dark:text-gray-400 hover:border-gray-400 dark:hover:border-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors font-['Open_Sans',sans-serif] text-xs font-medium"
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
