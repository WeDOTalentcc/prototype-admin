"use client"

import React, { useState, useMemo } from 'react'
import { ChevronDown, ChevronUp, Building2, Plus, X } from 'lucide-react'
import { textStyles } from '@/lib/design-tokens'
import {
  ELIGIBILITY_QUESTIONS_BANK,
  QUESTION_CATEGORIES,
  type EligibilityQuestionTemplate,
  type QuestionCategory,
} from '@/components/settings/eligibility-questions-bank'

interface CompanyBankQuestionsProps {
  isEditing: boolean
  selectedQuestions: string[]
  questionOverrides?: Record<string, { character?: 'eliminatoria' | 'classificatoria', expectedAnswer?: string, contextHint?: string }>
  onToggleQuestion: (questionId: string, selected: boolean) => void
  onUpdateSelectedQuestion?: (questionId: string, updates: { character?: 'eliminatoria' | 'classificatoria', expectedAnswer?: string }) => void
  /** IDs to exclude from the bank picker (e.g. questions already in company defaults) */
  excludeIds?: string[]
}

interface BankQuestion {
  id: string
  question: string
  character: 'eliminatoria' | 'classificatoria'
  expectedAnswer?: string
  contextHint?: string
}

const STATIC_COMPANY_BANK: BankQuestion[] = ELIGIBILITY_QUESTIONS_BANK
  .filter(q => !q.isSystemDefault)
  .map(q => ({
    id: q.id,
    question: q.question,
    character: q.eliminatory ? 'eliminatoria' as const : 'classificatoria' as const,
    expectedAnswer: q.eliminatoryAnswer != null ? String(q.eliminatoryAnswer) : undefined,
    contextHint: q.contextHint,
  }))

export const COMPANY_QUESTION_BANK = STATIC_COMPANY_BANK
export type { CompanyBankQuestionsProps, BankQuestion }

function CharacterBadge({ character }: { character: 'eliminatoria' | 'classificatoria' }) {
  if (character === 'eliminatoria') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error">
        eliminatória
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-warning/10 text-status-warning dark:bg-status-warning/30">
      classificatória
    </span>
  )
}

export function CompanyBankQuestions({ isEditing, selectedQuestions, questionOverrides, onToggleQuestion, onUpdateSelectedQuestion, excludeIds = [] }: CompanyBankQuestionsProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({})

  const nonSystemTemplates = useMemo(() =>
    ELIGIBILITY_QUESTIONS_BANK.filter(q => !q.isSystemDefault && !excludeIds.includes(q.id)),
    [excludeIds]
  )

  const selectedCount = selectedQuestions.length

  const selectedBankQuestions = useMemo(() =>
    STATIC_COMPANY_BANK
      .filter(q => selectedQuestions.includes(q.id))
      .map(q => {
        const overrides = questionOverrides?.[q.id]
        if (!overrides) return q
        return { ...q, ...overrides }
      }),
    [selectedQuestions, questionOverrides]
  )

  const categorizedQuestions = useMemo(() => {
    const groups: Record<string, EligibilityQuestionTemplate[]> = {}
    for (const q of nonSystemTemplates) {
      if (selectedQuestions.includes(q.id)) continue
      if (!groups[q.category]) groups[q.category] = []
      groups[q.category].push(q)
    }
    return groups
  }, [nonSystemTemplates, selectedQuestions])

  const getTemplateById = (id: string) => ELIGIBILITY_QUESTIONS_BANK.find(q => q.id === id)

  const toggleCategory = (cat: string) => {
    setExpandedCategories(prev => ({ ...prev, [cat]: !prev[cat] }))
  }

  return (
    <div className="border border-lia-border-subtle rounded-xl bg-lia-bg-primary overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-lia-text-tertiary" />
          <span className="font-['Open_Sans',sans-serif] text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
            Banco da Empresa
          </span>
          {selectedCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
              {selectedCount} selecionadas
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-lia-text-disabled" />
        ) : (
          <ChevronDown className="w-4 h-4 text-lia-text-disabled" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4">
          {isEditing ? (
            <>
              <div className="space-y-1 mb-4">
                {Object.entries(categorizedQuestions).map(([category, questions]) => {
                  const catInfo = QUESTION_CATEGORIES[category as QuestionCategory]
                  if (!catInfo || questions.length === 0) return null
                  const isCatExpanded = expandedCategories[category] ?? false

                  return (
                    <div key={category}>
                      <button
                        onClick={() => toggleCategory(category)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover rounded-lg transition-colors motion-reduce:transition-none"
                      >
                        <span className="text-xs">{catInfo.icon}</span>
                        <span className="font-['Open_Sans',sans-serif] text-micro uppercase tracking-wider font-semibold text-lia-text-tertiary flex-1 text-left">
                          {catInfo.label}
                        </span>
                        <span className="font-['Open_Sans',sans-serif] text-micro text-lia-text-disabled">
                          {questions.length}
                        </span>
                        {isCatExpanded ? (
                          <ChevronUp className="w-3 h-3 text-lia-text-disabled" />
                        ) : (
                          <ChevronDown className="w-3 h-3 text-lia-text-disabled" />
                        )}
                      </button>

                      {isCatExpanded && (
                        <div className="space-y-1 ml-2 mt-1">
                          {questions.map((q) => (
                            <div
                              key={q.id}
                              className="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none group"
                            >
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className={`${textStyles.bodySmall} flex-1`}>
                                    {q.question}
                                  </span>
                                  <CharacterBadge character={q.eliminatory ? 'eliminatoria' : 'classificatoria'} />
                                </div>
                                <p className="font-['Open_Sans',sans-serif] text-micro text-lia-text-disabled italic mt-0.5">
                                  {q.contextHint}
                                </p>
                              </div>
                              <button
                                onClick={() => onToggleQuestion(q.id, true)}
                                className="rounded-lg bg-lia-bg-tertiary hover:bg-lia-interactive-active dark:hover:bg-lia-btn-primary-bg p-1 transition-colors motion-reduce:transition-none opacity-60 group-hover:opacity-100 mt-0.5 shrink-0"
                                title="Adicionar pergunta"
                              >
                                <Plus className="w-3.5 h-3.5 text-lia-text-secondary" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}

                {Object.keys(categorizedQuestions).length === 0 && (
                  <p className="text-xs font-['Open_Sans',sans-serif] text-lia-text-disabled text-center py-3">
                    Todas as perguntas já foram selecionadas.
                  </p>
                )}
              </div>

              <div className="border-t border-lia-border-subtle pt-3">
                <span className="font-['Open_Sans',sans-serif] text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
                  Perguntas Selecionadas ({selectedCount})
                </span>

                {selectedCount === 0 ? (
                  <p className="text-xs font-['Open_Sans',sans-serif] text-lia-text-disabled text-center py-4">
                    Nenhuma pergunta selecionada.
                  </p>
                ) : (
                  <div className="space-y-2 mt-2">
                    {selectedBankQuestions.map((question) => {
                      const template = getTemplateById(question.id)
                      const contextHint = question.contextHint || template?.contextHint

                      return (
                        <div
                          key={question.id}
                          className="px-3 py-2.5 rounded-lg bg-lia-bg-secondary/50 group"
                        >
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} flex-1 pt-0.5`}>
                              {question.question}
                            </span>
                            <button
                              onClick={() => onToggleQuestion(question.id, false)}
                              className="rounded-lg p-1 hover:bg-status-error/10 dark:hover:bg-status-error/20 text-lia-text-disabled hover:text-status-error dark:hover:text-status-error transition-colors motion-reduce:transition-none shrink-0"
                              title="Remover pergunta"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <div className="ml-0 mt-1.5 space-y-2 pb-1">
                            <div className="flex items-center gap-2">
                              <label className="font-['Open_Sans',sans-serif] text-micro font-medium text-lia-text-tertiary whitespace-nowrap">
                                Caráter:
                              </label>
                              <select
                                value={question.character}
                                onChange={(e) => onUpdateSelectedQuestion?.(question.id, { character: e.target.value as 'eliminatoria' | 'classificatoria' })}
                                className="font-['Open_Sans',sans-serif] text-xs rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary px-2 py-1 focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/10 cursor-pointer"
                              >
                                <option value="classificatoria">Classificatória</option>
                                <option value="eliminatoria">Eliminatória</option>
                              </select>
                            </div>

                            {question.character === 'eliminatoria' && (
                              <div className="flex items-center gap-2">
                                <label className="font-['Open_Sans',sans-serif] text-micro font-medium text-lia-text-tertiary whitespace-nowrap">
                                  Resposta esperada:
                                </label>
                                <input
                                  type="text"
                                  placeholder="Resposta esperada"
                                  value={question.expectedAnswer || ''}
                                  onChange={(e) => onUpdateSelectedQuestion?.(question.id, { expectedAnswer: e.target.value })}
                                  className="font-['Open_Sans',sans-serif] text-xs rounded-md border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary px-2 py-1 flex-1 max-w-[220px] placeholder-lia-text-tertiary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/10"
                                />
                              </div>
                            )}

                            {contextHint && (
                              <p className="font-['Open_Sans',sans-serif] text-micro text-lia-text-disabled italic">
                                {contextHint}
                              </p>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="space-y-2">
              {selectedCount === 0 ? (
                <p className="text-xs font-['Open_Sans',sans-serif] text-lia-text-disabled text-center py-3">
                  Nenhuma pergunta selecionada.
                </p>
              ) : (
                selectedBankQuestions.map((question) => {
                  const template = getTemplateById(question.id)
                  const contextHint = question.contextHint || template?.contextHint

                  return (
                    <div
                      key={question.id}
                      className="px-3 py-2.5 rounded-lg bg-lia-bg-secondary/50"
                    >
                      <div className="flex items-center gap-2">
                        <span className={`${textStyles.bodySmall} flex-1`}>
                          {question.question}
                        </span>
                        <CharacterBadge character={question.character} />
                      </div>

                      {(question.expectedAnswer || contextHint) && (
                        <div className="ml-8 mt-1 space-y-0.5">
                          {question.expectedAnswer && (
                            <p className="font-['Open_Sans',sans-serif] text-micro text-lia-text-tertiary">
                              <span className="font-semibold">Resposta esperada:</span> {question.expectedAnswer}
                            </p>
                          )}
                          {contextHint && (
                            <p className="font-['Open_Sans',sans-serif] text-micro text-lia-text-disabled italic">
                              {contextHint}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
